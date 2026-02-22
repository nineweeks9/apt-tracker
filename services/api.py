import httpx
import asyncio
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Optional
from config import PUBLIC_DATA_API_KEY

APT_TRADE_URL = "http://apis.data.go.kr/1613000/RTMSDataSvcAptTrade/getRTMSDataSvcAptTrade"

async def fetch_month(client, sigungu_code, year_month):
    params = {
        "serviceKey": PUBLIC_DATA_API_KEY,
        "LAWD_CD": sigungu_code,
        "DEAL_YMD": year_month,
        "pageNo": "1",
        "numOfRows": "9999",
    }
    try:
        resp = await client.get(APT_TRADE_URL, params=params, timeout=30.0)
        if resp.status_code != 200:
            return []
        ct = resp.headers.get("content-type", "")
        if "json" in ct:
            return _parse_json(resp.json())
        return _parse_xml(resp.text)
    except Exception as e:
        print(f"API error ({year_month}): {e}")
        return []

def _parse_json(data):
    try:
        body = data.get("response", {}).get("body", {})
        items = body.get("items", {})
        if not items:
            return []
        item_list = items.get("item", [])
        if isinstance(item_list, dict):
            item_list = [item_list]
        results = []
        for item in item_list:
            try:
                amt = int(str(item.get("dealAmount", item.get("거래금액", "0"))).replace(",", "").strip())
                results.append({
                    "apt_name": str(item.get("aptNm", item.get("아파트", ""))).strip(),
                    "dong": str(item.get("umdNm", item.get("법정동", ""))).strip(),
                    "deal_amount": amt,
                    "area": float(item.get("excluUseAr", item.get("전용면적", 0))),
                    "floor": _si(item.get("floor", item.get("층"))),
                    "build_year": _si(item.get("buildYear", item.get("건축년도"))),
                    "deal_year": _si(item.get("dealYear", item.get("년"))),
                    "deal_month": _si(item.get("dealMonth", item.get("월"))),
                    "deal_day": _si(item.get("dealDay", item.get("일"))),
                })
            except:
                continue
        return results
    except:
        return []

def _parse_xml(text):
    try:
        root = ET.fromstring(text)
        rc = root.findtext(".//resultCode")
        if rc and rc != "00":
            print(f"API error: {rc} - {root.findtext('.//resultMsg','')}")
            return []
        results = []
        for item in root.findall(".//item"):
            try:
                amt = int((item.findtext("거래금액") or "0").replace(",","").strip())
                results.append({
                    "apt_name": (item.findtext("아파트") or "").strip(),
                    "dong": (item.findtext("법정동") or "").strip(),
                    "deal_amount": amt,
                    "area": float(item.findtext("전용면적") or 0),
                    "floor": _si(item.findtext("층")),
                    "build_year": _si(item.findtext("건축년도")),
                    "deal_y
cat > services/api.py << 'APIEOF'
import httpx
import asyncio
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Optional
from config import PUBLIC_DATA_API_KEY

APT_TRADE_URL = "http://apis.data.go.kr/1613000/RTMSDataSvcAptTrade/getRTMSDataSvcAptTrade"

async def fetch_month(client, sigungu_code, year_month):
    params = {
        "serviceKey": PUBLIC_DATA_API_KEY,
        "LAWD_CD": sigungu_code,
        "DEAL_YMD": year_month,
        "pageNo": "1",
        "numOfRows": "9999",
    }
    try:
        resp = await client.get(APT_TRADE_URL, params=params, timeout=30.0)
        if resp.status_code != 200:
            return []
        ct = resp.headers.get("content-type", "")
        if "json" in ct:
            return _parse_json(resp.json())
        return _parse_xml(resp.text)
    except Exception as e:
        print(f"API error ({year_month}): {e}")
        return []

def _parse_json(data):
    try:
        body = data.get("response", {}).get("body", {})
        items = body.get("items", {})
        if not items:
            return []
        item_list = items.get("item", [])
        if isinstance(item_list, dict):
            item_list = [item_list]
        results = []
        for item in item_list:
            try:
                amt = int(str(item.get("dealAmount", item.get("거래금액", "0"))).replace(",", "").strip())
                results.append({
                    "apt_name": str(item.get("aptNm", item.get("아파트", ""))).strip(),
                    "dong": str(item.get("umdNm", item.get("법정동", ""))).strip(),
                    "deal_amount": amt,
                    "area": float(item.get("excluUseAr", item.get("전용면적", 0))),
                    "floor": _si(item.get("floor", item.get("층"))),
                    "build_year": _si(item.get("buildYear", item.get("건축년도"))),
                    "deal_year": _si(item.get("dealYear", item.get("년"))),
                    "deal_month": _si(item.get("dealMonth", item.get("월"))),
                    "deal_day": _si(item.get("dealDay", item.get("일"))),
                })
            except:
                continue
        return results
    except:
        return []

def _parse_xml(text):
    try:
        root = ET.fromstring(text)
        rc = root.findtext(".//resultCode")
        if rc and rc != "00":
            print(f"API error: {rc} - {root.findtext('.//resultMsg','')}")
            return []
        results = []
        for item in root.findall(".//item"):
            try:
                amt = int((item.findtext("거래금액") or "0").replace(",","").strip())
                results.append({
                    "apt_name": (item.findtext("아파트") or "").strip(),
                    "dong": (item.findtext("법정동") or "").strip(),
                    "deal_amount": amt,
                    "area": float(item.findtext("전용면적") or 0),
                    "floor": _si(item.findtext("층")),
                    "build_year": _si(item.findtext("건축년도")),
                    "deal_year": _si(item.findtext("년")),
                    "deal_month": _si(item.findtext("월")),
                    "deal_day": _si(item.findtext("일")),
                })
            except:
                continue
        return results
    except Exception as e:
        print(f"XML parse error: {e}")
        return []

async def fetch_apartment_data(sigungu_code, apt_name, years=5, last_updated=None):
    now = datetime.now()
    if last_updated:
        sy, sm = int(last_updated[:4]), int(last_updated[4:6])
    else:
        sy, sm = now.year - years, now.month
    months = []
    y, m = sy, sm
    while (y, m) <= (now.year, now.month):
        months.append(f"{y}{m:02d}")
        m += 1
        if m > 12: m = 1; y += 1
    print(f"Fetching {apt_name}: {len(months)} months")
    all_tx = []
    async with httpx.AsyncClient() as client:
        for i in range(0, len(months), 5):
            batch = months[i:i+5]
            results = await asyncio.gather(*[fetch_month(client, sigungu_code, ym) for ym in batch])
            for month_data in results:
                for tx in month_data:
                    if tx["apt_name"] == apt_name:
                        all_tx.append(tx)
            if i + 5 < len(months):
                await asyncio.sleep(0.3)
    print(f"  Done: {len(all_tx)} transactions")
    return all_tx

async def search_apartments(sigungu_code, year_month):
    async with httpx.AsyncClient() as client:
        data = await fetch_month(client, sigungu_code, year_month)
    seen = set()
    results = []
    for tx in data:
        if tx["apt_name"] and tx["apt_name"] not in seen:
            seen.add(tx["apt_name"])
            results.append({"apt_name": tx["apt_name"], "dong": tx["dong"]})
    results.sort(key=lambda x: x["apt_name"])
    return results

def _si(val):
    if val is None: return None
    try: return int(str(val).strip())
    except: return None
