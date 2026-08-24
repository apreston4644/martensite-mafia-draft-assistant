function exportCsv(){let cols=Object.keys(S.board[0]||{}),esc=v=>{let s=String(v??'');return /[",\n]/.test(s)?'"'+s.replace(/"/g,'""')+'"':s},txt=[cols.join(','),...S.board.map(r=>cols.map(k=>esc(r[k])).join(','))].join('\n'),a=document.createElement('a');a.href=URL.createObjectURL(new Blob([txt],{type:'text/csv'}));a.download='martensite_mafia_draftnight_values.csv';a.click()}
async function importCsv(file){let b=parseBoard(await file.text());if(b.length){S.board=b;S.customBoard=true;renderAll();toast('Imported '+b.length+' valuation rows')}}

// 2026 official NFL bye-week overlay for Alex's keepers + primary auction targets.
const BYE_WEEK={
'Jaxson Dart':8,'Ashton Jeanty':13,'Jaylen Warren':9,'Alec Pierce':13,'Colston Loveland':10,'Tucker Kraft':11,
'Lamar Jackson':13,'Jayden Daniels':7,'Joe Burrow':6,'Caleb Williams':10,'Brock Purdy':8,'Patrick Mahomes II':5,
'Bijan Robinson':11,'Chase Brown':6,"De'Von Achane":6,'Saquon Barkley':10,'Kyren Williams':11,'Breece Hall':13,'Josh Jacobs':11,'Bucky Irving':10,'David Montgomery':6,
"Ja'Marr Chase":6,'Puka Nacua':11,'Amon-Ra St. Brown':6,'CeeDee Lamb':14,'A.J. Brown':11,'Justin Jefferson':6,'Nico Collins':8,'Malik Nabers':8,'Ladd McConkey':7,'Tee Higgins':6,'Mike Evans':10,'Marvin Harrison Jr.':14,'DK Metcalf':9,'Luther Burden III':10,
'Brock Bowers':13,'Kyle Pitts Sr.':11
};
function byeWeek(name){return BYE_WEEK[canon(name)]||null}
function alexRostered(){return [...S.teams.Alex.keepers,...S.teams.Alex.bought].map(p=>({name:canon(p.name||p.player),pos:p.pos||findBoard(p.name||p.player)?.pos||'',bye:byeWeek(p.name||p.player)}))}
function byeWarning(r){let w=byeWeek(r.name);if(!w)return'';let rostered=alexRostered().filter(p=>p.bye===w&&norm(p.name)!==norm(canon(r.name)));let sameRB=rostered.filter(p=>p.pos==='RB');if(r.pos==='RB'&&sameRB.length)return`🚨 RB BYE CONFLICT — Week ${w}: ${sameRB.map(p=>p.name).join(' + ')} already share this bye. Use this as a meaningful tiebreaker unless ${r.name} is a clear bargain.`;let skill=rostered.filter(p=>['QB','RB','WR','TE'].includes(p.pos));if(skill.length>=2)return`⚠️ BYE STACK — Week ${w}: adding ${r.name} would give you ${skill.length+1} skill players off together (${skill.map(p=>p.name).join(', ')} + ${r.name}). Fine at strong value; prefer a similar-priced player with a different bye.`;return''}
const _renderLiveNoBye=renderLive;
renderLive=function(){_renderLiveNoBye();let r=findBoard($('player').value.trim());if(!r)return;let w=byeWeek(r.name);if(w){let b=document.createElement('span');b.className='pill';b.textContent='Bye W'+w;$('badges').appendChild(b)}let warning=byeWarning(r);if(warning&&statusObj(r).label==='Available'){let s=document.createElement('span');s.style.cssText='display:block;margin-top:9px;padding:8px 9px;border:1px solid #5d4817;border-radius:9px;background:#281f0d;color:#e7d69e;font-weight:650';s.textContent=warning;$('reason').appendChild(s)}};

// Opening nomination: drain QB money first. Bowers remains a later drain nomination.
DRAIN_PLAN.splice(0,DRAIN_PLAN.length,
 {name:'Lamar Jackson',why:'Open here: Dart is viable, while QB-needy teams can burn meaningful money immediately.'},
 {name:'Saquon Barkley',why:'Useful player, but you prefer Chase Brown/Achane/value at similar money.'},
 {name:'Brock Bowers',why:'You already own Loveland + Kraft. Make a TE-needy team spend after the opening QB drain.'},
 {name:'Patrick Mahomes II',why:'QB name recognition can drain dollars while you already have Dart.'},
 {name:'Justin Jefferson',why:'You like him only at a big discount; invite someone else to overpay.'},
 {name:'Tyreek Hill',why:'Name-value trap in the current 2026 market.'}
);

async function init(){try{await loadBoard()}catch(e){document.body.innerHTML='<div style="padding:20px;color:white">Could not load draft-night valuation board: '+e.message+'</div>';return}initTeams();$('minBid').value=S.settings.minBid;$('fallback').value=S.settings.fallback;$('dynMarket').checked=S.settings.dynMarket;$('dynScarcity').checked=S.settings.dynScarcity;$('dynNeed').checked=S.settings.dynNeed;renderAll();document.querySelectorAll('.tab').forEach(b=>b.onclick=()=>{document.querySelectorAll('.tab,.pane').forEach(x=>x.classList.remove('active'));b.classList.add('active');$(b.dataset.tab).classList.add('active')});$('player').oninput=renderLive;$('bid').oninput=renderLive;$('minus').onclick=()=>{$('bid').value=Math.max(0,(+$('bid').value||0)-1);renderLive()};$('plus').onclick=()=>{$('bid').value=(+$('bid').value||0)+1;renderLive()};$('connect').onclick=connect;$('sync').onclick=syncPicks;$('draft').onchange=e=>selectDraft(e.target.value);$('auto').onchange=startTimer;$('search').oninput=renderTargets;$('pos').onchange=renderTargets;$('availability').onchange=renderTargets;$('refresh').onclick=syncPicks;$('clearSales').onclick=()=>{if(confirm('Clear all auction sales and start a fresh session?')){S.sales=[];S.processed={};initTeams();renderAll()}};$('export').onclick=exportCsv;$('import').onchange=e=>e.target.files[0]&&importCsv(e.target.files[0]);$('resetBoard').onclick=()=>{if(confirm('Reset valuation board to the bundled draft-night final board?')){S.board=structuredClone(S.baseBoard);S.customBoard=false;renderAll()}};[['minBid','minBid'],['fallback','fallback']].forEach(([id,k])=>$(id).onchange=e=>{S.settings[k]=+e.target.value;renderAll()});[['dynMarket','dynMarket'],['dynScarcity','dynScarcity'],['dynNeed','dynNeed']].forEach(([id,k])=>$(id).onchange=e=>{S.settings[k]=e.target.checked;renderAll()})}
init();
