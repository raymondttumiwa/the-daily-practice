const D=JSON.parse(document.getElementById('training-data').textContent),$=id=>document.getElementById(id);
const valid=x=>typeof x==='number'&&Number.isFinite(x)&&x>=0, sum=(rows,key)=>rows.reduce((s,x)=>s+(valid(x[key])?x[key]:0),0),num=(x,d=1)=>valid(x)?x.toFixed(d):'—';
const esc=x=>String(x??'—').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const run=x=>/running/.test(x.activityType||''),bike=x=>/biking|cycling/.test(x.activityType||''),day=x=>(x.startTimeLocal||'').slice(0,10),sport=x=>(x||'Unknown').replaceAll('_',' ');
const time=x=>{if(!valid(x))return '—';let m=Math.round(x/60);return Math.floor(m/60)+'h '+String(m%60).padStart(2,'0')+'m'};
const pace=(s,m)=>{if(!(m>0&&s>0))return '—';let n=Math.round(s/(m/1000));return Math.floor(n/60)+':'+String(n%60).padStart(2,'0')};
const avg=a=>a.length?a.reduce((x,y)=>x+y,0)/a.length:null;
const palette=['#ff8957','#b9cf9e','#edc67e','#a5b6db','#c99cbf','#da9e8d','#a6c6be','#ccc4a4'];
const all=D.activities||[],health=(key)=>D[key]||[];
$('from').value=D.start;$('through').value=D.end;
const sports=[...new Set(all.map(x=>x.activityType||'unknown'))].sort();
$('sport').innerHTML='<option value="all">All sports</option>'+sports.map(s=>`<option value="${esc(s)}">${esc(sport(s))}</option>`).join('');
$('coverage').textContent=`${D.start} — ${D.end}`;
const failures=(D.requests||[]).filter(r=>r.status!=='ok'),extraFailures=D.extendedSync?.failures||[];
$('syncNotice').textContent=D.sample?'Only the original five-activity sample is loaded. Run python3 scripts/sync_history.py to populate August onward and recovery data.':`Last sync ${D.syncedAt?D.syncedAt.slice(0,16).replace('T',' '):'unavailable'}${failures.length||extraFailures.length?' · '+(failures.length+extraFailures.length)+' request gaps':''}`;
$('readiness').textContent=D.readinessStatus||'Not exposed in the documented Garmin Personal API.';
$('issues').innerHTML=`<p>Requested: ${esc(D.start)} through ${esc(D.end)}. Successful requests with no records indicate no returned data, not zero sleep or HRV.</p>`+(D.requests||[]).map(r=>`<div>${esc(r.series)} · ${esc(r.start)}–${esc(r.end)}: ${r.status==='ok'?esc(r.records)+' records':esc(r.reason)}</div>`).join('');
$('issues').innerHTML+='<p>Extra metrics: '+extraFailures.length+' failed requests'+(D.extendedSync?.updated?' · last updated '+esc(D.extendedSync.updated.slice(0,16).replace('T',' ')):'')+'.</p>'+extraFailures.map(r=>'<div>'+esc(r.series)+' · '+esc(r.reason)+'</div>').join('');
function dateRange(){const a=$('from').value,b=$('through').value;return {a,b,inRange:d=>d>=a&&d<=b}}
function group(rows,key){const m={};for(const r of rows){const k=key(r);(m[k]??=[]).push(r)}return m}
function monthKeys(a,b){const out=[];let t=new Date(a.slice(0,7)+'-01T00:00:00Z');while(!isNaN(t)&&t.toISOString().slice(0,10)<=b){out.push(t.toISOString().slice(0,7));t.setUTCMonth(t.getUTCMonth()+1)}return out}
function week(d){const t=new Date(d+'T00:00:00Z');if(isNaN(t))return 'Unknown';t.setUTCDate(t.getUTCDate()-(t.getUTCDay()+6)%7);return t.toISOString().slice(0,10)}
function record(rows,key,id,note,isDistance){const a=rows.filter(x=>valid(x[key])).sort((a,b)=>b[key]-a[key])[0];$(id).textContent=a?(isDistance?num(a[key]/1000,2)+' km':time(a[key])):'—';$(note).textContent=a?`${day(a)} · ${sport(a.activityType)} · ${isDistance?time(a.duration):num(a.distance/1000,2)+' km'}`:'No matching activities'}
function chart(id,rows,get,unit,a,b){
 const points=rows.map(r=>({d:r.calendarDate,v:get(r)})).filter(r=>valid(r.v)).sort((x,y)=>x.d.localeCompare(y.d));
 if(!points.length){$(id).innerHTML='<div class="empty">No data returned for this period.</div>';return}
 const start=Date.parse(a),end=Date.parse(b),lo=Math.min(...points.map(p=>p.v)),hi=Math.max(...points.map(p=>p.v)),padding=Math.max((hi-lo)*.15,1);
 const x=d=>35+(Date.parse(d)-start)/Math.max(end-start,86400000)*425,y=v=>120-(v-(lo-padding))/(hi-lo+padding*2)*105;
 let paths='';points.forEach((p,i)=>{const prev=points[i-1];if(prev&&Date.parse(p.d)-Date.parse(prev.d)<=86400000)paths+=`<line x1="${x(prev.d)}" y1="${y(prev.v)}" x2="${x(p.d)}" y2="${y(p.v)}" stroke="#b2c8ab" stroke-width="2"/>`;paths+=`<circle cx="${x(p.d)}" cy="${y(p.v)}" r="2.5" fill="#b2c8ab"><title>${esc(p.d)}: ${num(p.v)} ${unit}</title></circle>`});
 $(id).innerHTML=`<svg viewBox="0 0 470 145" class="chart" role="img" aria-label="${esc(id)} trend, ${points.length} dates, ${num(lo)} to ${num(hi)} ${unit}"><text x="0" y="15" fill="#b8c3bc" font-size="10">${num(hi)} ${unit}</text><text x="0" y="135" fill="#b8c3bc" font-size="10">${num(lo)}</text>${paths}</svg><div class="ticks"><span>${esc(a)}</span><span>${esc(b)}</span></div>`;
}
function trainingVolume(activities,a,b,filter){
 const out=[],start=Date.parse(a+'T00:00:00Z'),end=Date.parse(b+'T00:00:00Z');
 const daily=group(activities.filter(x=>filter==='all'||x.activityType===filter),day);
 for(let t=start;t<=end;t+=86400000){
  const d=new Date(t).toISOString().slice(0,10);if(d<D.start||d>D.end)continue;
  let seconds=0;for(let i=0;i<7;i++){const k=new Date(t-i*86400000).toISOString().slice(0,10);seconds+=sum(daily[k]||[],'duration')}
  out.push({calendarDate:d,hours:seconds/3600,partial:new Date(t-6*86400000).toISOString().slice(0,10)<D.start});
 }
 return out;
}
function trainingLoad(activities,a,b,filter){
 const out=[],start=Date.parse(a+'T00:00:00Z'),end=Date.parse(b+'T00:00:00Z');
 const selected=activities.filter(x=>filter==='all'||x.activityType===filter);
 const loadSupported=selected.some(x=>valid(x.activityTrainingLoad)&&x.activityTrainingLoad>0);
 for(let t=start;t<=end;t+=86400000){
  const d=new Date(t).toISOString().slice(0,10);if(d<D.start||d>D.end)continue;
  const first=new Date(t-6*86400000).toISOString().slice(0,10),rs=selected.filter(x=>day(x)>=first&&day(x)<=d);
  const known=rs.filter(x=>valid(x.activityTrainingLoad));
  out.push({calendarDate:d,load:loadSupported&&known.length===rs.length?sum(known,'activityTrainingLoad'):null,
    known:known.length,count:rs.length,partial:first<D.start});
 }
 return out;
}
function render(){
 const {a,b,inRange}=dateRange(),filter=$('sport').value;
 const rows=all.filter(x=>inRange(day(x))&&(filter==='all'||x.activityType===filter)).sort((x,y)=>(y.startTimeLocal||'').localeCompare(x.startTimeLocal||''));
 const runs=rows.filter(run),bikes=rows.filter(bike),sleeps=health('sleep').filter(x=>inRange(x.calendarDate)),hrvs=health('hrv').filter(x=>inRange(x.calendarDate)),well=health('wellness').filter(x=>inRange(x.calendarDate));
 $('hours').textContent=num(sum(rows,'duration')/3600)+' h';$('sessions').textContent=rows.length;$('runKm').textContent=num(sum(runs,'distance')/1000,2)+' km';$('bikeKm').textContent=num(sum(bikes,'distance')/1000,2)+' km';$('runPace').textContent=runs.length?pace(sum(runs,'duration'),sum(runs,'distance'))+' /km overall':'No runs in selection';$('bikeSpeed').textContent=sum(bikes,'duration')>0?num(sum(bikes,'distance')/sum(bikes,'duration')*3.6)+' km/h overall':'No cycling in selection';
 $('totalDistance').textContent=num(sum(rows,'distance')/1000,1)+' km';$('totalClimb').textContent=Math.round(sum(rows,'elevationGain')).toLocaleString()+' m';$('periodLabel').textContent=a+' — '+b;
 const sleepValues=sleeps.map(x=>x.sleepTimeSeconds).filter(valid);$('sleepAvg').textContent=time(avg(sleepValues));$('sleepCount').textContent=sleepValues.length+' recorded nights · excludes naps';
 record(runs,'distance','longRun','longRunNote',true);record(bikes,'distance','longBike','longBikeNote',true);record(rows,'duration','longTime','longTimeNote',false);
 const days=Object.entries(group(rows,day)).map(([d,rs])=>({d,s:sum(rs,'duration')})).sort((a,b)=>b.s-a.s);$('longDay').textContent=days.length?time(days[0].s):'—';$('longDayNote').textContent=days[0]?.d||'No matching activities';
 const sportList=[...new Set(rows.map(x=>x.activityType||'unknown'))].sort(),months=monthKeys(a,b),byMonth=group(rows,x=>day(x).slice(0,7));
 const maxMonth=Math.max(1,...months.map(m=>sum(byMonth[m]||[],'duration')));
 $('monthlyVisual').innerHTML=months.map(m=>{const rs=byMonth[m]||[],total=sum(rs,'duration');return `<div class="month-column"><span class="month-hours">${num(total/3600)} h</span><div class="month-stack" style="height:${Math.max(2,total/maxMonth*170)}px">`+sportList.map((s,i)=>{const seconds=sum(rs.filter(x=>(x.activityType||'unknown')===s),'duration');return `<span style="height:${total?seconds/total*100:0}%;background:${palette[i%palette.length]}" title="${esc(m)} · ${esc(sport(s))}: ${num(seconds/3600)} h"></span>`}).join('')+`</div><span class="month-name">${new Date(m+'-01T00:00:00Z').toLocaleDateString('en',{month:'short',timeZone:'UTC'})}</span></div>`}).join('');
 $('legend').innerHTML=sportList.map((s,i)=>`<span><i class="swatch" style="background:${palette[i%palette.length]}"></i>${esc(sport(s))}</span>`).join('');
 $('monthly').innerHTML='<thead><tr><th>Month</th>'+sportList.map(s=>`<th>${esc(sport(s))} h</th>`).join('')+'<th>Total h</th><th>Mix</th></tr></thead><tbody>'+months.map(m=>{const rs=byMonth[m]||[];return '<tr><td>'+m+'</td>'+sportList.map(s=>'<td class="num">'+num(sum(rs.filter(x=>(x.activityType||'unknown')===s),'duration')/3600)+'</td>').join('')+`<td class="num">${num(sum(rs,'duration')/3600)}</td><td><div class="monthlybar">`+sportList.map((s,i)=>`<span style="background:${palette[i%palette.length]};width:${sum(rs.filter(x=>(x.activityType||'unknown')===s),'duration')/maxMonth*100}%"></span>`).join('')+'</div></td></tr>'}).join('')+'</tbody>';
 const weeks=group(rows,x=>week(day(x)));$('weekly').innerHTML=Object.keys(weeks).sort().reverse().map(w=>{const r=weeks[w];return `<tr><td>${w}</td><td>${num(sum(r,'duration')/3600)}</td><td>${num(sum(r.filter(run),'distance')/1000,2)}</td><td>${num(sum(r.filter(bike),'distance')/1000,2)}</td><td>${r.length}</td></tr>`}).join('');
 chart('sleepChart',sleeps,x=>valid(x.sleepTimeSeconds)?x.sleepTimeSeconds/3600:null,'h',a,b);chart('hrvChart',hrvs,x=>x.lastNightAvg,'ms',a,b);chart('rhrChart',well,x=>x.heartRate?.restingValue,'bpm',a,b);chart('bbChart',well,x=>x.bodyBattery?.maxValue,'/100',a,b);chart('stressChart',well,x=>x.stress?.avgLevel,'/100',a,b);
 const loadRows=trainingLoad(all,a,b,filter);
 chart('loadChart',loadRows,x=>x.load,'pts',a,b);
 const lastLoad=loadRows.at(-1);
 $('loadValue').textContent=lastLoad&&valid(lastLoad.load)?num(lastLoad.load,0)+' pts':'Unavailable';
 $('loadSummary').textContent=lastLoad?`${lastLoad.calendarDate} · ${lastLoad.known}/${lastLoad.count} sessions with load${lastLoad.partial?' · partial window':''}`:'No synced coverage';
 const recent=[...hrvs].filter(x=>valid(x.lastNightAvg)).sort((a,b)=>b.calendarDate.localeCompare(a.calendarDate))[0];$('hrvSummary').textContent=recent?`7-day ${num(recent.weeklyAvg,0)} ms · ${(recent.status||'Unavailable').toLowerCase().replaceAll('_',' ')}`:'HRV unavailable; device support and overnight wear determine coverage.';
 $('sleepSummary').textContent=`Period average · ${sleepValues.length} nights`;
 const rhrValues=well.map(x=>x.heartRate?.restingValue).filter(valid);$('rhrSummary').textContent=rhrValues.length?`Period average · ${rhrValues.length} days`:'No resting heart-rate readings returned.';
 $('hrvValue').textContent=recent?num(recent.lastNightAvg,0)+' ms':'—';
 $('rhrValue').textContent=rhrValues.length?num(avg(rhrValues),0)+' bpm':'—';
 const latestWell=[...well].sort((x,y)=>y.calendarDate.localeCompare(x.calendarDate))[0];
 $('bbValue').textContent=valid(latestWell?.bodyBattery?.maxValue)?num(latestWell.bodyBattery.maxValue,0):'—';
 $('stressValue').textContent=valid(latestWell?.stress?.avgLevel)?num(latestWell.stress.avgLevel,0):'—';
 const fa=[...(D.fitnessAge||[])].filter(x=>inRange(x.calendarDate)).at(-1);
 const signals=[['Steps',valid(latestWell?.movement?.steps?.value)?latestWell.movement.steps.value.toLocaleString():'—'],['Respiration',valid(latestWell?.respiration?.avgValue)?latestWell.respiration.avgValue+' /min':'—'],['SpO₂',valid(latestWell?.pulseOx?.avgValue)?latestWell.pulseOx.avgValue+'%':'—'],['Energy burned',valid(latestWell?.calories?.burnedTotal)?latestWell.calories.burnedTotal+' kcal':'—'],['Fitness age',fa?num(fa.fitnessAge,1)+' years':'—'],['Date',latestWell?.calendarDate||'—']];
 $('healthSignals').innerHTML=signals.map(([k,v])=>`<div>${k}<strong>${v}</strong></div>`).join('');
 $('availableData').innerHTML=(D.availability||[]).map(x=>`<div>${esc(x.label)}<strong>${x.records?x.records+' usable records':'Unavailable'}</strong></div>`).join('');
 const byDate={};for(const [key,list] of [['s',sleeps],['h',hrvs],['w',well]])for(const item of list){(byDate[item.calendarDate]??={})[key]=item}
 $('healthRows').innerHTML=Object.keys(byDate).sort().reverse().map(d=>{const {s={},h={},w={}}=byDate[d];return `<tr><td>${d}</td><td>${time(s.sleepTimeSeconds)}</td><td>${num(s.sleepScores?.overall?.value,0)}</td><td>${num(h.lastNightAvg,0)}</td><td>${num(h.weeklyAvg,0)}</td><td>${esc(h.status)}</td><td>${num(w.heartRate?.restingValue,0)}</td><td>${num(w.bodyBattery?.maxValue,0)}</td><td>${num(w.stress?.avgLevel,0)}</td></tr>`}).join('')||'<tr><td colspan="9">Recovery history has not been downloaded or no readings are available.</td></tr>';
 $('activityRows').innerHTML=rows.map(x=>`<tr><td>${esc((x.startTimeLocal||'').slice(0,16))}</td><td>${esc(sport(x.activityType))}</td><td>${valid(x.distance)?num(x.distance/1000,2)+' km':'—'}</td><td>${time(x.duration)}</td><td>${run(x)?pace(x.duration,x.distance)+' /km':bike(x)&&x.duration>0?num(x.distance/x.duration*3.6)+' km/h':'—'}</td><td>${num(x.averageHR,0)}</td><td>${num(x.maxHR,0)}</td><td>${valid(x.elevationGain)?num(x.elevationGain,0)+' m':'—'}</td><td>${num(x.aerobicTrainingEffect)} / ${num(x.anaerobicTrainingEffect)}</td><td>${num(x.calories,0)}</td><td>${num(x.activityTrainingLoad,0)}</td></tr>`).join('')||'<tr><td colspan="10">No activities match these filters.</td></tr>';
}
for(const id of ['from','through','sport'])$(id).addEventListener('change',render);$('reset').addEventListener('click',()=>{$('from').value=D.start;$('through').value=D.end;$('sport').value='all';render()});render();

document.querySelectorAll('[data-period]').forEach(btn=>btn.addEventListener('click',()=>{const n=Number(btn.dataset.period);$('through').value=D.end;$('from').value=new Date(Math.max(Date.parse(D.start),Date.parse(D.end)-(n-1)*86400000)).toISOString().slice(0,10);document.querySelectorAll('.filter-shortcuts button').forEach(x=>x.classList.toggle('active',x===btn));render()}));
