from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager
from typing import Optional
from datetime import datetime
import aiosqlite
from database import init_db, get_db
from models import FolderCreate, ApartmentCreate
from services.api import fetch_apartment_data, search_apartments
from config import PORT

SIGUNGU_MAP = {
    "종로구":"11110","중구":"11140","용산구":"11170","성동구":"11200",
    "광진구":"11215","동대문구":"11230","중랑구":"11260","성북구":"11290",
    "강북구":"11305","도봉구":"11320","노원구":"11350","은평구":"11380",
    "서대문구":"11410","마포구":"11440","양천구":"11470","강서구":"11500",
    "구로구":"11530","금천구":"11545","영등포구":"11560","동작구":"11590",
    "관악구":"11620","서초구":"11650","강남구":"11680","송파구":"11710",
    "강동구":"11740",
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

app = FastAPI(title="apt-tracker", lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/folders")
async def get_folders(db=Depends(get_db)):
    cursor = await db.execute("""SELECT f.id, f.name, COUNT(fa.apartment_id) as apartment_count
        FROM folders f LEFT JOIN folder_apartments fa ON f.id = fa.folder_id
        GROUP BY f.id ORDER BY f.created_at""")
    return [dict(r) for r in await cursor.fetchall()]

@app.post("/api/folders")
async def create_folder(folder: FolderCreate, db=Depends(get_db)):
    try:
        cursor = await db.execute("INSERT INTO folders (name) VALUES (?)", (folder.name,))
        await db.commit()
        return {"id": cursor.lastrowid, "name": folder.name, "apartment_count": 0}
    except aiosqlite.IntegrityError:
        raise HTTPException(400, "이미 같은 이름의 폴더가 있습니다.")

@app.delete("/api/folders/{folder_id}")
async def delete_folder(folder_id: int, db=Depends(get_db)):
    await db.execute("DELETE FROM folders WHERE id = ?", (folder_id,))
    await db.commit()
    return {"ok": True}

@app.get("/api/apartments")
async def get_apartments(folder_id: Optional[int] = None, db=Depends(get_db)):
    if folder_id:
        cursor = await db.execute("""SELECT a.* FROM apartments a
            JOIN folder_apartments fa ON a.id = fa.apartment_id
            WHERE fa.folder_id = ? ORDER BY a.created_at""", (folder_id,))
    else:
        cursor = await db.execute("SELECT * FROM apartments ORDER BY created_at")
    return [dict(r) for r in await cursor.fetchall()]

@app.post("/api/apartments")
async def add_apartment(apt: ApartmentCreate, db=Depends(get_db)):
    try:
        cursor = await db.execute(
            "INSERT INTO apartments (apt_name, sigungu_code, dong, sigungu_name) VALUES (?,?,?,?)",
            (apt.apt_name, apt.sigungu_code, apt.dong, apt.sigungu_name))
        apt_id = cursor.lastrowid
    except aiosqlite.IntegrityError:
        cursor = await db.execute(
            "SELECT id FROM apartments WHERE apt_name = ? AND sigungu_code = ?",
            (apt.apt_name, apt.sigungu_code))
        row = await cursor.fetchone()
        apt_id = row["id"]
    if apt.folder_id:
        try:
            await db.execute("INSERT INTO folder_apartments (folder_id, apartment_id) VALUES (?,?)",
                (apt.folder_id, apt_id))
        except aiosqlite.IntegrityError:
            pass
    await db.commit()
    return {"id": apt_id, **apt.model_dump()}

@app.delete("/api/apartments/{apt_id}")
async def delete_apartment(apt_id: int, db=Depends(get_db)):
    await db.execute("DELETE FROM apartments WHERE id = ?", (apt_id,))
    await db.commit()
    return {"ok": True}

@app.get("/api/search")
async def search_apt(q: str, sigungu: Optional[str] = None):
    if not q: return {"results": []}
    if not sigungu:
        return {"results": [], "districts": [{"sigungu_name":n,"sigungu_code":c} for n,c in SIGUNGU_MAP.items() if q in n]}
    code = SIGUNGU_MAP.get(sigungu, sigungu)
    now = datetime.now()
    ym = f"{now.year}{now.month:02d}"
    apts = await search_apartments(code, ym)
    filtered = [a for a in apts if q in a["apt_name"]]
    return {"results": [{"apt_name":a["apt_name"],"dong":a["dong"],"sigungu_code":code,"sigungu_name":sigungu} for a in filtered[:20]]}

@app.get("/api/transactions/{apt_id}")
async def get_transactions(apt_id: int, years: int = 5, db=Depends(get_db)):
    cursor = await db.execute("SELECT * FROM apartments WHERE id = ?", (apt_id,))
    apt = await cursor.fetchone()
    if not apt: raise HTTPException(404, "아파트를 찾을 수 없습니다.")
    apt = dict(apt)
    cursor = await db.execute("SELECT * FROM transactions WHERE apartment_id = ? ORDER BY deal_year DESC, deal_month DESC, deal_day DESC", (apt_id,))
    rows = [dict(r) for r in await cursor.fetchall()]
    if not rows:
        txs = await fetch_apartment_data(apt["sigungu_code"], apt["apt_name"], years)
        for tx in txs:
            try:
                await db.execute("INSERT OR IGNORE INTO transactions (apartment_id,deal_amount,area,floor,build_year,deal_year,deal_month,deal_day) VALUES (?,?,?,?,?,?,?,?)",
                    (apt_id, tx["deal_amount"], tx["area"], tx["floor"], tx["build_year"], tx["deal_year"], tx["deal_month"], tx["deal_day"]))
            except: continue
        now_ym = f"{datetime.now().year}{datetime.now().month:02d}"
        await db.execute("UPDATE apartments SET last_updated = ? WHERE id = ?", (now_ym, apt_id))
        await db.commit()
        cursor = await db.execute("SELECT * FROM transactions WHERE apartment_id = ? ORDER BY deal_year DESC, deal_month DESC, deal_day DESC", (apt_id,))
        rows = [dict(r) for r in await cursor.fetchall()]
    chart = _build_chart(rows, years)
    return {"apt_name":apt["apt_name"],"location":f"{apt['sigungu_name'] or ''} {apt['dong'] or ''}".strip(),"last_updated":apt.get("last_updated"),"chart":chart,"transactions":rows[:50]}

@app.post("/api/transactions/{apt_id}/update")
async def update_tx(apt_id: int, db=Depends(get_db)):
    cursor = await db.execute("SELECT * FROM apartments WHERE id = ?", (apt_id,))
    apt = await cursor.fetchone()
    if not apt: raise HTTPException(404)
    apt = dict(apt)
    txs = await fetch_apartment_data(apt["sigungu_code"], apt["apt_name"], 5, apt.get("last_updated"))
    nc = 0
    for tx in txs:
        try:
            r = await db.execute("INSERT OR IGNORE INTO transactions (apartment_id,deal_amount,area,floor,build_year,deal_year,deal_month,deal_day) VALUES (?,?,?,?,?,?,?,?)",
                (apt_id, tx["deal_amount"], tx["area"], tx["floor"], tx["build_year"], tx["deal_year"], tx["deal_month"], tx["deal_day"]))
            if r.rowcount > 0: nc += 1
        except: continue
    now_ym = f"{datetime.now().year}{datetime.now().month:02d}"
    await db.execute("UPDATE apartments SET last_updated = ? WHERE id = ?", (now_ym, apt_id))
    await db.commit()
    return {"updated": nc, "message": f"{nc}건 새 데이터 추가됨"}

def _build_chart(rows, years=5):
    now = datetime.now()
    sy = now.year - years
    ag = {}
    for tx in rows:
        if tx["deal_year"] < sy: continue
        ak = round(tx["area"])
        if ak not in ag: ag[ak] = {}
        ym = f"{tx['deal_year']}-{tx['deal_month']:02d}"
        if ym not in ag[ak]: ag[ak][ym] = []
        ag[ak][ym].append(tx["deal_amount"])
    labels = []
    y, m = sy, now.month
    while (y, m) <= (now.year, now.month):
        labels.append(f"{y}-{m:02d}")
        m += 1
        if m > 12: m = 1; y += 1
    datasets = []
    for ak in sorted(ag.keys()):
        data = [sum(ag[ak][l])//len(ag[ak][l]) if l in ag[ak] else None for l in labels]
        datasets.append({"label": f"{ak}㎡", "data": data})
    return {"labels": labels, "datasets": datasets}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=True)
