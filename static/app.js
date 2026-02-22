const S={folders:[],apartments:[],selFolder:'all',selApt:null,selArea:'all',chart:null,pending:null,currentData:null};
const COLORS=['#6c9eff','#51cf66','#ffd43b','#ff6b6b','#cc5de8','#20c997','#ff922b'];
const GU_LIST=["강남구","강동구","강북구","강서구","관악구","광진구","구로구","금천구","노원구","도봉구","동대문구","동작구","마포구","서대문구","서초구","성동구","성북구","송파구","양천구","영등포구","용산구","은평구","종로구","중구","중랑구"];

async function api(path,opts={}){const r=await fetch(path,{headers:{'Content-Type':'application/json'},...opts});if(!r.ok){const e=await r.json().catch(()=>({}));throw new Error(e.detail||'요청 실패');}return r.json();}

const guSelect=document.getElementById('gu-select');
const searchInput=document.getElementById('search-input');
const searchDD=document.getElementById('search-dropdown');
let debounce=null;

GU_LIST.forEach(g=>{const o=document.createElement('option');o.value=g;o.textContent=g;guSelect.appendChild(o);});

guSelect.addEventListener('change',()=>{searchInput.disabled=!guSelect.value;searchInput.value='';searchDD.innerHTML='';if(guSelect.value)searchInput.focus();});

searchInput.addEventListener('input',()=>{
    clearTimeout(debounce);
    const q=searchInput.value.trim(),gu=guSelect.value;
    if(!q||!gu){searchDD.innerHTML='';return;}
    debounce=setTimeout(async()=>{
        searchDD.innerHTML='<div class="search-loading"><div class="spinner"></div>검색 중...</div>';
        try{
            const d=await api('/api/search?q='+encodeURIComponent(q)+'&sigungu='+encodeURIComponent(gu));
            if(!d.results.length){searchDD.innerHTML='<div class="search-no-result">검색 결과가 없습니다</div>';return;}
            searchDD.innerHTML=d.results.map(a=>'<div class="search-result-item" data-apt=\''+JSON.stringify(a).replace(/'/g,"&apos;")+'\'><div><div class="result-name">'+esc(a.apt_name)+'</div><div class="result-location">'+esc(a.sigungu_name)+' '+esc(a.dong)+'</div></div><button class="result-add">+ 추가</button></div>').join('');
            searchDD.querySelectorAll('.search-result-item').forEach(el=>{el.addEventListener('click',()=>{openAddModal(JSON.parse(el.dataset.apt.replace(/&apos;/g,"'")));searchDD.innerHTML='';searchInput.value='';});});
        }catch(e){searchDD.innerHTML='<div class="search-no-result">검색 오류: '+e.message+'</div>';}
    },500);
});

searchInput.addEventListener('keydown',e=>{if(e.key==='Escape'){searchDD.innerHTML='';searchInput.blur();}});
document.addEventListener('click',e=>{if(!e.target.closest('.search-input-wrapper'))searchDD.innerHTML='';});

function openAddModal(apt){
    S.pending=apt;
    document.getElementById('modal-apt-name').textContent=apt.apt_name;
    document.getElementById('modal-apt-location').textContent=apt.sigungu_name+' '+apt.dong;
    const sel=document.getElementById('modal-folder-select');
    sel.innerHTML='<option value="">폴더 없음</option>'+S.folders.map(f=>'<option value="'+f.id+'">'+esc(f.name)+'</option>').join('');
    if(S.selFolder!=='all')sel.value=S.selFolder;
    openModal('modal-add-apt');
}

document.getElementById('btn-confirm-add-apt').addEventListener('click',async()=>{
    if(!S.pending)return;
    const fid=document.getElementById('modal-folder-select').value||null;
    try{
        const r=await api('/api/apartments',{method:'POST',body:JSON.stringify({...S.pending,folder_id:fid?parseInt(fid):null})});
        closeModal('modal-add-apt');await loadAll();selectApt(r.id);toast(''+S.pending.apt_name+' 추가됨');
    }catch(e){toast(e.message,true);}
});

document.getElementById('btn-add-folder').addEventListener('click',()=>{openModal('modal-folder');document.getElementById('folder-name-input').value='';setTimeout(()=>document.getElementById('folder-name-input').focus(),100);});
document.getElementById('btn-confirm-folder').addEventListener('click',createFolder);
document.getElementById('folder-name-input').addEventListener('keydown',e=>{if(e.key==='Enter')createFolder();if(e.key==='Escape')closeModal('modal-folder');});

async function createFolder(){
    const name=document.getElementById('folder-name-input').value.trim();
    if(!name)return;
    try{await api('/api/folders',{method:'POST',body:JSON.stringify({name})});closeModal('modal-folder');await loadFolders();toast('"'+name+'" 폴더 생성됨');}catch(e){toast(e.message,true);}
}

async function deleteFolder(id){
    const f=S.folders.find(x=>x.id===id);
    if(!confirm('"'+f.name+'" 폴더를 삭제하시겠습니까?'))return;
    await api('/api/folders/'+id,{method:'DELETE'});
    if(S.selFolder===id)S.selFolder='all';
    await loadAll();
}

function selFolder(id){S.selFolder=id;renderFolders();loadApartments();}

async function loadFolders(){S.folders=await api('/api/folders');renderFolders();}

function renderFolders(){
    const el=document.getElementById('folder-list');
    el.innerHTML='<li class="folder-item '+(S.selFolder==='all'?'active':'')+'" onclick="selFolder(\'all\')"><span class="folder-icon">&#11088;</span><span class="folder-name">전체</span><span class="folder-count">'+S.apartments.length+'</span></li>'+S.folders.map(f=>{
        const cnt=f.apartment_count||0;
        return '<li class="folder-item '+(S.selFolder===f.id?'active':'')+'" onclick="selFolder('+f.id+')"><span class="folder-icon">&#128193;</span><span class="folder-name">'+esc(f.name)+'</span><span class="folder-count">'+cnt+'</span><button class="item-delete" onclick="event.stopPropagation();deleteFolder('+f.id+')">&#10005;</button></li>';
    }).join('');
}

async function loadApartments(){
    const p=S.selFolder!=='all'?'?folder_id='+S.selFolder:'';
    S.apartments=await api('/api/apartments'+p);
    renderApts();renderFolders();
}

function renderApts(){
    const el=document.getElementById('apt-list');
    if(!S.apartments.length){el.innerHTML='<li class="apt-list-empty">'+(S.selFolder==='all'?'구를 선택하고 아파트를 검색하세요':'이 폴더에 아파트가 없습니다')+'</li>';return;}
    el.innerHTML=S.apartments.map(a=>'<li class="apt-item '+(S.selApt===a.id?'active':'')+'" onclick="selectApt('+a.id+')"><span class="apt-name">'+esc(a.apt_name)+'</span><span class="apt-location">'+esc(a.sigungu_name||'')+'</span><button class="item-delete" onclick="event.stopPropagation();deleteApt('+a.id+')">&#128465;</button></li>').join('');
}

async function selectApt(id){
    S.selApt=id;S.selArea='all';renderApts();
    const apt=S.apartments.find(a=>a.id===id);if(!apt)return;
    document.getElementById('empty-state').style.display='none';
    document.getElementById('chart-area').style.display='block';
    document.getElementById('chart-title').textContent=apt.apt_name;
    document.getElementById('chart-subtitle').textContent=(apt.sigungu_name||'')+' '+(apt.dong||'');
    document.getElementById('chart-loading').style.display='flex';
    document.getElementById('chart-loading').innerHTML='<div class="spinner"></div><span>데이터 수집 중... (최대 1~2분 소요)</span>';
    document.getElementById('price-chart').style.display='none';
    document.getElementById('filter-chips').innerHTML='';
    document.getElementById('table-body').innerHTML='';
    try{
        const d=await api('/api/transactions/'+id+'?years=5');
        S.currentData=d;
        document.getElementById('chart-loading').style.display='none';
        document.getElementById('price-chart').style.display='block';
        if(d.chart&&d.chart.datasets&&d.chart.datasets.length>0){renderFilterChips(d.chart.datasets);renderChart(d.chart);renderTable(d.transactions);document.getElementById('last-updated').textContent=d.last_updated||'-';}
        else{document.getElementById('chart-loading').style.display='flex';document.getElementById('chart-loading').innerHTML='거래 데이터가 없습니다.';document.getElementById('price-chart').style.display='none';}
    }catch(e){document.getElementById('chart-loading').style.display='flex';document.getElementById('chart-loading').innerHTML='데이터 로드 실패: '+e.message;document.getElementById('price-chart').style.display='none';}
}

async function deleteApt(id){
    const a=S.apartments.find(x=>x.id===id);
    if(!confirm('"'+a.apt_name+'" 삭제하시겠습니까?'))return;
    await api('/api/apartments/'+id,{method:'DELETE'});
    if(S.selApt===id){S.selApt=null;document.getElementById('chart-area').style.display='none';document.getElementById('empty-state').style.display='flex';}
    await loadAll();toast(a.apt_name+' 삭제됨');
}

document.getElementById('btn-update').addEventListener('click',async()=>{
    if(!S.selApt)return;
    const btn=document.getElementById('btn-update');
    btn.disabled=true;btn.textContent='업데이트 중...';
    try{const r=await api('/api/transactions/'+S.selApt+'/update',{method:'POST'});toast(r.message);await selectApt(S.selApt);}catch(e){toast(e.message,true);}
    btn.disabled=false;btn.textContent='🔄 업데이트';
});

function renderFilterChips(datasets){
    document.getElementById('filter-chips').innerHTML='<button class="chip '+(S.selArea==='all'?'active':'')+'" onclick="filterArea(\'all\')">전체</button>'+datasets.map(ds=>'<button class="chip '+(S.selArea===ds.label?'active':'')+'" onclick="filterArea(\''+ds.label+'\')">'+ds.label+'</button>').join('');
}

function filterArea(a){S.selArea=a;if(!S.currentData)return;renderFilterChips(S.currentData.chart.datasets);renderChart(S.currentData.chart);renderTable(S.currentData.transactions);}

function renderChart(cd){
    const ctx=document.getElementById('price-chart');
    if(S.chart)S.chart.destroy();
    let ds=cd.datasets;if(S.selArea!=='all')ds=ds.filter(d=>d.label===S.selArea);
    S.chart=new Chart(ctx,{type:'line',data:{labels:cd.labels,datasets:ds.map((d,i)=>({label:d.label,data:d.data,borderColor:COLORS[i%COLORS.length],backgroundColor:COLORS[i%COLORS.length]+'14',fill:true,tension:0.3,pointRadius:0,pointHoverRadius:5,borderWidth:2,spanGaps:true}))},options:{responsive:true,maintainAspectRatio:false,interaction:{mode:'index',intersect:false},plugins:{legend:{labels:{color:'#9aa0a6',font:{family:"'Noto Sans KR'",size:12},usePointStyle:true,pointStyle:'circle'}},tooltip:{backgroundColor:'#1c1f2e',borderColor:'#2a2d3e',borderWidth:1,titleFont:{family:"'Noto Sans KR'"},bodyFont:{family:"'Noto Sans KR'"},callbacks:{label:c=>{const v=c.parsed.y;if(!v)return'';if(v>=10000){const a=Math.floor(v/10000),b=v%10000;return c.dataset.label+': '+a+'억'+(b?' '+b.toLocaleString()+'만':'')+'원';}return c.dataset.label+': '+v.toLocaleString()+'만원';}}}},scales:{x:{ticks:{color:'#5f6368',font:{size:11},maxTicksLimit:12},grid:{color:'rgba(42,45,62,0.5)'}},y:{ticks:{color:'#5f6368',font:{size:11},callback:v=>v>=10000?(v/10000).toFixed(1)+'억':(v/1000).toFixed(0)+'천'},grid:{color:'rgba(42,45,62,0.5)'}}}}});
}

function renderTable(txs){
    const tb=document.getElementById('table-body');
    let f=txs;if(S.selArea!=='all'){const n=parseInt(S.selArea);f=txs.filter(t=>Math.round(t.area)===n);}
    if(!f.length){tb.innerHTML='<tr><td colspan="4" style="text-align:center;color:var(--text-muted);padding:24px;">거래 데이터가 없습니다</td></tr>';return;}
    tb.innerHTML=f.slice(0,50).map(t=>'<tr><td>'+t.deal_year+'.'+String(t.deal_month).padStart(2,'0')+'.'+String(t.deal_day||0).padStart(2,'0')+'</td><td>'+t.area+'㎡</td><td>'+(t.floor?t.floor+'층':'-')+'</td><td style="font-weight:600">'+fmtAmt(t.deal_amount)+'</td></tr>').join('');
}

function fmtAmt(v){if(v>=10000){const a=Math.floor(v/10000),b=v%10000;return b>0?a+'억 '+b.toLocaleString():a+'억';}return v.toLocaleString()+'만';}
function esc(t){if(!t)return'';const d=document.createElement('div');d.textContent=t;return d.innerHTML;}
function openModal(id){document.getElementById(id).classList.add('show');}
function closeModal(id){document.getElementById(id).classList.remove('show');}
function toast(m,err=false){const e=document.createElement('div');e.className='toast'+(err?' error':'');e.textContent=m;document.body.appendChild(e);setTimeout(()=>e.remove(),3000);}
async function loadAll(){await loadFolders();await loadApartments();}
document.querySelectorAll('.modal-overlay').forEach(o=>o.addEventListener('click',e=>{if(e.target===o)o.classList.remove('show');}));
loadAll();
