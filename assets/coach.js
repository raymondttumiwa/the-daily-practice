
let coach=D.coach||{calendar:[],strength:[],meals:[],weights:[],profile:{proteinTarget:160},journal:{meals:[],workouts:[],checkins:[]}},live=false;
const cToday=new Intl.DateTimeFormat('en-CA',{timeZone:'Asia/Shanghai',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date());
$('coachDate').value=cToday;let calMonth=cToday.slice(0,7);
const chooseDate=()=>$('coachDate').value||cToday;
const cFmt=(n,d=0)=>typeof n==='number'&&Number.isFinite(n)?n.toFixed(d):'—';
const cDay=x=>x.startTimeLocal?.slice(0,10),cTime=s=>valid(s)?`${Math.floor(s/3600)}h ${Math.floor(s%3600/60)}m`:'Unavailable';
const cJournal=()=>coach.journal||{meals:[],workouts:[],checkins:[]};
function cPlan(d){return coach.calendar.find(p=>p.date===d)}
function cMeals(d){return [...coach.meals,...cJournal().meals].filter(m=>m.date===d&&m.status!=='planned')}
function cTotals(d){const rows=cMeals(d);return {rows,kcal:sum(rows,'kcal'),protein:sum(rows,'protein'),carbs:sum(rows,'carbs'),missing:rows.filter(x=>!valid(x.kcal)||!valid(x.protein)||!valid(x.carbs)).length}}
function cRecovery(d){return {sleep:(D.sleep||[]).find(x=>x.calendarDate===d),hrv:(D.hrv||[]).find(x=>x.calendarDate===d),well:(D.wellness||[]).find(x=>x.calendarDate===d)}}
function cAdvice(d){
 const p=cPlan(d),r=cRecovery(d),check=cJournal().checkins.filter(x=>x.date===d).sort((x,y)=>(x.createdAt||'').localeCompare(y.createdAt||'')).at(-1),reasons=[],score=r.sleep?.sleepScores?.overall?.value;
 let title=p?.title==='Rest'?'Keep the rest day restful.':p?'Follow the plan by effort, not a forced pace.':'No workout is scheduled in your imported calendar.';
 let steps=p?.title==='Rest'?['Take an easy walk if you feel like it; keep hard strength work for another day.']:[p?.description||'Choose easy movement based on how you feel.','Warm up gently and finish easy. Stop if pain changes your movement.'];
 let adjusted=false;
 if(r.sleep){reasons.push(`${cTime(r.sleep.sleepTimeSeconds)} sleep on ${d}; score ${cFmt(score)}/100.`)}else reasons.push(`No sleep data for ${d}; recovery is not assumed good.`);
 if(r.hrv)reasons.push(`Overnight HRV ${cFmt(r.hrv.lastNightAvg)} ms; Garmin status ${r.hrv.status||'unavailable'}. Balanced HRV does not cancel fatigue.`);
 if(valid(r.well?.heartRate?.restingValue))reasons.push(`Resting heart rate ${r.well.heartRate.restingValue} bpm.`);
 const poorSleep=(valid(score)&&score<60)||(valid(r.sleep?.sleepTimeSeconds)&&r.sleep.sleepTimeSeconds<21600),tired=check&&(check.fatigue>=4||check.soreness>=4);
 if(poorSleep||tired){title='Rest or 30–45 min easy.';adjusted=true;steps=['If you feel tired or unusually sore, take a rest day.','If you feel comfortable, walk/jog 10 min, run 15–30 min at full-sentence effort, then cool down 5 min.','Skip tempo, intervals and sets to failure; do not make up the missed intensity tomorrow.'];reasons.push(poorSleep?'Low sleep quality or short sleep is a reason to reduce intensity today.':'Your check-in reports high fatigue or soreness.');}
 if(check?.pain){title='Pause the workout and assess the pain.';adjusted=true;steps=['Avoid running or exercises that reproduce pain or change your movement.','Persistent focal pain, swelling or a limp warrants assessment before continuing.'];reasons.push('You reported pain affecting technique or stride.');}
 const todayRuns=all.filter(x=>cDay(x)===d&&run(x));if(todayRuns.length){reasons.push(`Already recorded: ${num(sum(todayRuns,'distance')/1000,2)} km running. Do not add another run to satisfy the calendar.`);title=check?.pain?title:'Run done. Recover well.';steps=check?.pain?steps:['Eat a balanced meal, drink to thirst and prioritise sleep.','Keep extra movement easy. Your next hard effort can wait.'];}
 const runs=all.filter(x=>run(x)&&cDay(x)<d&&cDay(x)>=new Date(Date.parse(d+'T00:00:00Z')-28*86400000).toISOString().slice(0,10));
 const recentLongest=Math.max(0,...runs.map(x=>x.distance||0))/1000;
 if(p?.km&&p.km>recentLongest*1.3&&p.km>12&&recentLongest>0)reasons.push(`The imported ${p.km} km is substantially above your recent four-week longest (${num(recentLongest,1)} km). Review the progression instead of chasing the calendar.`);
 if(!check)reasons.push('No fatigue or soreness check-in yet. Add one before choosing the session.');
 const isRest=p?.title==='Rest'||check?.pain,isLong=p?.title==='Long Run'&&!adjusted;
 return {title,steps,reasons,adjusted,p,target:isRest?2400:isLong?3200:2700,carbs:isRest?280:isLong?400:335};
}

function cSpark(values,label){
 const present=values.filter(valid);if(!present.length)return '<div class="spark"></div>';
 const lo=Math.min(...present),hi=Math.max(...present),y=v=>26-(v-lo)/Math.max(hi-lo,1)*21;
 let path='',last=false;values.forEach((v,i)=>{if(valid(v)){path+=(last?'L':'M')+(i*40+3)+','+y(v)+' ';last=true}else last=false});
 return `<svg class="spark" viewBox="0 0 246 30" preserveAspectRatio="none" role="img" aria-label="${esc(label)}"><line x1="0" x2="246" y1="28" y2="28"/><path d="${path}"/></svg>`;
}
function cOverview(d,r,tot,a){
 const dates=Array.from({length:7},(_,i)=>new Date(Date.parse(d+'T00:00:00Z')-(6-i)*86400000).toISOString().slice(0,10));
 const covered=dates.filter(x=>x>=D.start&&x<=D.end),sessions=all.filter(x=>covered.includes(cDay(x)));
 const training=dates.map(x=>covered.includes(x)?sum(all.filter(z=>cDay(z)===x),'duration')/3600:null);
 const sleeps=dates.map(x=>{const row=cRecovery(x).sleep;return valid(row?.sleepTimeSeconds)?row.sleepTimeSeconds/3600:null});
 const hearts=dates.map(x=>cRecovery(x).well?.heartRate?.restingValue);
 const score=r.sleep?.sleepScores?.overall?.value;
 const cards=[
  ['↗','Activity','Last 7 days',covered.length?num(sum(sessions,'duration')/3600,1)+' h':'Unavailable',sessions.length+' sessions · 7 days',cSpark(training,'Training hours over seven days')],
  ['☾','Sleep','Selected day',r.sleep?cTime(r.sleep.sleepTimeSeconds):'Unavailable',valid(score)?'Sleep score '+score+'/100':'No sleep score for this day',cSpark(sleeps,'Sleep duration over seven days')],
  ['♡','Heart','Resting',valid(r.well?.heartRate?.restingValue)?r.well.heartRate.restingValue+' bpm':'Unavailable',valid(r.hrv?.lastNightAvg)?'Overnight HRV '+r.hrv.lastNightAvg+' ms':'HRV unavailable for this day',cSpark(hearts,'Resting heart rate over seven days')],
  ['◒','Fuel','Logged today',cFmt(tot.kcal)+' kcal',cFmt(tot.protein)+' g protein · '+cFmt(tot.carbs)+' g carbs',`<div class="fuel-line"><span style="width:${Math.min(100,tot.kcal/a.target*100)}%"></span></div><div class="overview-note">~${a.target} kcal guide</div>`]
 ];
 $('overview').innerHTML=cards.map(([icon,title,period,value,note,chart])=>`<article class="overview-card"><div class="overview-top"><strong><span class="overview-icon" aria-hidden="true">${icon}</span>${title}</strong><small>${period}</small></div>${chart}<div class="overview-value">${value}</div><div class="overview-note">${note}</div></article>`).join('');
}
function cReveal(hash){
 const target=document.getElementById((hash||'').replace('#',''));if(!target)return;
 const drawer=target.classList?.contains('workspace-drawer')?target:target.closest?.('.workspace-drawer');
 if(drawer)drawer.open=true;
 document.querySelectorAll('.desk-nav a').forEach(link=>link.classList.toggle('active',link.getAttribute('href')===hash));
}
document.querySelectorAll('a[href^="#"]').forEach(link=>link.addEventListener('click',()=>cReveal(link.getAttribute('href'))));
if(location.hash)cReveal(location.hash);

function cRender(){
 const d=chooseDate(),a=cAdvice(d),r=cRecovery(d),tot=cTotals(d),j=cJournal();
 const hour=new Date().getHours(),greeting=hour<12?'Good morning':hour<18?'Good afternoon':'Good evening';
 $('greeting').innerHTML=esc(greeting+', '+(coach.profile.name||'Runner'))+'<span>.</span>';
 const strip=[['Steps',valid(r.well?.movement?.steps?.value)?r.well.movement.steps.value.toLocaleString():'—'],['Body Battery',valid(r.well?.bodyBattery?.maxValue)?r.well.bodyBattery.maxValue+' /100':'—'],['Respiration',valid(r.well?.respiration?.avgValue)?r.well.respiration.avgValue+' /min':'—'],['SpO₂',valid(r.well?.pulseOx?.avgValue)?r.well.pulseOx.avgValue+'%':'—']];
 $('dailySignals').innerHTML=strip.map(([k,v])=>`<div class="signal-item">${k}<strong>${v}</strong></div>`).join('');
 cOverview(d,r,tot,a);
 $('coachNotice').textContent=coach.profile.raceDate?`${Math.max(0,Math.ceil((Date.parse(coach.profile.raceDate+'T00:00:00Z')-Date.parse(d+'T00:00:00Z'))/86400000))} days to race`:'One day at a time';
 $('adviceTitle').textContent=a.title;$('adviceBody').innerHTML='<ol>'+a.steps.map(s=>'<li>'+esc(s)+'</li>').join('')+'</ol>';
 $('adviceReasons').innerHTML=a.reasons.map(s=>'<div>'+esc(s)+'</div>').join('');
 const p=a.p;$('originalWorkout').innerHTML=p?`<p><strong>${esc(p.title)}${p.km?' · '+p.km+' km':''}</strong><br>${esc(p.description)}<br>Imported pace: ${esc(p.pace)}<br>Imported HR: ${esc(p.hr)} (historical plan target, not newly validated)<br>Imported fuel: ${esc(p.fuel)}<br>Source: ${esc(p.source)}${p.overrideSource?'<br><strong>'+esc(p.overrideSource)+'</strong>; workbook originally '+p.originalKm+' km.':''}</p>`:'No imported session on this date.';
 const nextLong=coach.calendar.find(x=>x.date>=d&&x.title==='Long Run');
 const recentRuns=all.filter(x=>run(x)&&cDay(x)<d&&cDay(x)>=new Date(Date.parse(d+'T00:00:00Z')-28*86400000).toISOString().slice(0,10));
 const longestRecent=recentRuns.length?Math.max(...recentRuns.map(x=>x.distance||0))/1000:null;
 const rec=[['Distance',nextLong?.km?nextLong.km+' km':'Unavailable'],['Recent longest',valid(longestRecent)?num(longestRecent,2)+' km':'Unavailable']];
 $('todayRecovery').innerHTML=rec.map(([k,v])=>`<div><span class="label">${k}</span><div class="metric">${v}</div></div>`).join('');
 $('recoveryDate').textContent=nextLong?`${nextLong.date} · Easy effort`:'No upcoming long run in the imported calendar.';

 const acts=all.filter(x=>cDay(x)===d);$('todayActivity').innerHTML='<strong>Recorded today</strong><br>'+ (acts.length?acts.map(x=>esc(sport(x.activityType))+' · '+num(x.distance/1000,2)+' km · '+time(x.duration)).join('<br>'):'No activities yet.');
 $('workoutSteps').innerHTML='<h3>'+esc(a.title)+'</h3><ol>'+a.steps.map(s=>'<li>'+esc(s)+'</li>').join('')+'</ol>'+(p?.strength&&p.strength!=='-'?'<p><strong>Imported strength:</strong> '+esc(p.strength)+'. Use the library below, and reduce volume if sore.</p>':'<p class="note">No strength session is prescribed for this day. Optional push-ups should stay easy; avoid accumulating extra squat fatigue.</p>');
 $('strengthLibrary').innerHTML=['A','B'].map(section=>'<h3 style="margin-top:18px">Strength '+section+(section==='A'?' · lower body':' · core & hips')+'</h3><p class="note">Imported plan: 2 rounds. Choose the earlier repetition range if new to these movements. Use a stable low step for step-ups.</p>'+coach.strength.filter(x=>x.section===section).map(x=>`<div class="record"><strong>${esc(x.exercise)}</strong><br><span class="muted">Early / middle / late: ${esc(x.early)} / ${esc(x.middle)} / ${esc(x.late)}<br>${esc(x.instructions)}</span></div>`).join('')).join('');
 $('nutritionTarget').textContent=`Starting guide ~${a.target.toLocaleString()} kcal · ${cFmt(coach.profile.proteinTarget)} g protein · ${a.carbs} g carbs`;
 $('foodTotals').innerHTML=[['Calories',cFmt(tot.kcal)+' kcal'],['Protein',cFmt(tot.protein)+' g'],['Carbs',cFmt(tot.carbs)+' g']].map(([k,v])=>`<div><span class="label">${k} logged</span><strong>${v}</strong></div>`).join('');
 $('mealGuidance').textContent=tot.missing?`${tot.missing} item${tot.missing===1?' needs':'s need'} details. Totals exclude unquantified food.`:'Estimated intake. A single day does not determine your weight trend.';
 const mealHtml=m=>`<div class="record"><strong>${esc(m.food.replace(/ — .*/,'').replace(/ \(estimated\)/,''))}</strong><br><span class="muted">${m.quantity??''} ${esc(m.unit||'')} · ${valid(m.kcal)?'~'+cFmt(m.kcal)+' kcal':'Not quantified'} · ${cFmt(m.protein)} g protein · ${cFmt(m.carbs)} g carbs</span><details><summary>Details</summary><p class="note">${esc(m.notes||'Standard food estimate.')}</p>${m.source?'<p class="source-note">'+esc(m.source)+'</p>':`<button class="mini" type="button" data-delete="meals:${m.id}">Remove</button>`}${m.status==='planned'?`<button class="mini" type="button" data-eaten="${m.id}">Mark eaten</button>`:''}</details></div>`;
 const groups={};tot.rows.forEach(m=>{const key=m.meal==='Meal'?'Earlier meal':(m.meal||'Food');(groups[key]??=[]).push(m)});
 const order=['Breakfast','Earlier meal','Lunch','Run fuel','Dinner','Dinner — additional','Snack'];
 $('foodLogs').innerHTML=Object.keys(groups).sort((x,y)=>(order.indexOf(x)<0?99:order.indexOf(x))-(order.indexOf(y)<0?99:order.indexOf(y))).map(k=>'<div class="meal-group-label">'+esc(k)+'</div>'+groups[k].map(mealHtml).join('')).join('')||'<p class="empty-lines">Nothing logged yet.</p>';
 $('plannedMeals').innerHTML=j.meals.filter(m=>m.date===d&&m.status==='planned').map(mealHtml).join('')||'<p class="empty-lines">Use “Planned” in the meal form to prepare your next meal.</p>';
 $('workoutLogs').innerHTML=j.workouts.filter(w=>w.date===d).map(w=>`<div class="record"><strong>${esc(w.exercise)}</strong><br>${cFmt(w.sets)} sets × ${cFmt(w.reps)} reps · ${cFmt(w.minutes,1)} min<br><span class="muted">${esc(w.notes)}</span><br><button class="mini" type="button" data-delete="workouts:${w.id}">Remove</button></div>`).join('');
 const weights=[...coach.weights,...j.checkins.filter(c=>valid(c.kg))].sort((x,y)=>y.date.localeCompare(x.date));
 $('checkinLogs').innerHTML=weights.slice(0,14).map(w=>`<div class="record"><strong>${w.date} · ${esc(w.timing)}</strong><br>${cFmt(w.kg,2)} kg</div>`).join('')||'<p class="note">No weights recorded.</p>';
 $('checkinLogs').innerHTML+=j.checkins.filter(c=>c.date===d).map(c=>`<div class="record">Fatigue ${cFmt(c.fatigue)}/5 · soreness ${cFmt(c.soreness)}/5${c.pain?' · pain flagged':''}<br>${esc(c.notes)}<br><button class="mini" type="button" data-delete="checkins:${c.id}">Remove check-in</button></div>`).join('');
 $('sourceList').innerHTML=coach.sources?.map(s=>'<div>'+esc(s)+'</div>').join('')||'';
 $('upcoming').innerHTML=coach.calendar.filter(p=>p.date>=d&&p.date<new Date(Date.parse(d+'T00:00:00Z')+7*86400000).toISOString().slice(0,10)).map(p=>`<div class="record"><button type="button" class="mini" data-day="${p.date}">${p.date}</button> <strong>${esc(p.title)}${p.km?' · '+p.km+' km':''}</strong><br><span class="muted">${esc(p.description)}</span>${p.overrideSource?'<p class="source-note">'+esc(p.overrideSource)+'; original workbook '+p.originalKm+' km.</p>':''}</div>`).join('')||'<p class="note">No imported sessions in the next seven days.</p>';
 cCalendar();$('miniMonthGrid').innerHTML=$('monthGrid').innerHTML;$('miniMonthTitle').textContent=$('monthTitle').textContent;document.querySelectorAll('[data-day]').forEach(b=>b.onclick=()=>{$('coachDate').value=b.dataset.day;calMonth=b.dataset.day.slice(0,7);cRender()});
 document.querySelectorAll('[data-eaten]').forEach(b=>b.onclick=()=>cSave('meal-status',{id:b.dataset.eaten,status:'eaten'}));
 document.querySelectorAll('[data-delete]').forEach(b=>b.onclick=()=>{const [collection,id]=b.dataset.delete.split(':');cSave('delete',{collection,id})});
}
function cCalendar(){
 const [year,month]=calMonth.split('-').map(Number),first=new Date(Date.UTC(year,month-1,1)),days=new Date(Date.UTC(year,month,0)).getUTCDate(),offset=(first.getUTCDay()+6)%7;
 $('monthTitle').textContent=first.toLocaleDateString('en',{month:'long',year:'numeric',timeZone:'UTC'});
 let html=['Mon','Tue','Wed','Thu','Fri','Sat','Sun'].map(s=>'<div class="calendarlabel">'+s+'</div>').join('')+'<div></div>'.repeat(offset);
 for(let i=1;i<=days;i++){const d=calMonth+'-'+String(i).padStart(2,'0'),p=cPlan(d);html+=`<button type="button" data-day="${d}" class="daycell ${chooseDate()===d?'active':''} ${p?.km?'hasrun':''}">${i}<small>${p?esc(p.title)+(p.km?' '+p.km+'k':''):'—'}</small></button>`}$('monthGrid').innerHTML=html;
}
function cDemoSave(kind,payload){
 const j=cJournal();
 if(kind==='delete'){j[payload.collection]=j[payload.collection].filter(x=>x.id!==payload.id)}
 else if(kind==='meal-status'){const m=j.meals.find(x=>x.id===payload.id);if(m)m.status=payload.status}
 else j[kind].push({...payload,id:crypto.randomUUID(),createdAt:new Date().toISOString()});
 try{localStorage.setItem('daily-practice-demo',JSON.stringify(j))}catch(e){$('connection').textContent='Browser storage unavailable. Changes last for this visit.'}
 coach.journal=j;cRender();$('connection').textContent='Demo saved in this browser only.';return true;
}
async function cSave(kind,payload){if(D.demo)return cDemoSave(kind,payload);if(!live){$('connection').textContent='Open the local training desk to save logs. Your imported data remains available in this file.';return false}try{const res=await fetch('/api/'+kind,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});const data=await res.json();if(!res.ok)throw Error(data.error||'Save failed');coach=data;cRender();$('connection').textContent='Saved locally. Your recommendations and totals are updated.';return true}catch(e){$('connection').textContent='Could not save: '+e.message;return false}}
for(const [formId,kind] of [['mealForm','meals'],['workoutForm','workouts'],['checkinForm','checkins']])$(formId).addEventListener('submit',async e=>{e.preventDefault();const form=e.target,payload={date:chooseDate()};for(const [k,v] of new FormData(form))payload[k]=v;for(const k of ['quantity','kcal','protein','carbs','sets','reps','minutes','kg','fatigue','soreness'])if(k in payload)payload[k]=payload[k]===''?null:Number(payload[k]);if(kind==='checkins')payload.pain=form.elements.pain.checked;if(await cSave(kind,payload)){form.reset();$('foodPreset').value='custom'}});
const presets={rice:['Cooked white rice','g',1.3,.025,.28,170],breast:['Cooked skinless chicken breast','g',1.65,.31,0,150],thigh:['Cooked skinless chicken thigh','g',2.09,.26,0,150],egg:['Boiled egg','piece',77.5,6.5,.5,2],milk:['Whole fresh milk','ml',.61,.032,.048,200],banana:['Banana, edible portion','g',.89,.011,.228,100],alienergy:['Alienergy coconut electrolyte drink','ml',.8/4.184,0,.047,600]};
function cPreset(reset){const p=presets[$('foodPreset').value];if(!p)return;if(reset){$('foodName').value=p[0];$('foodUnit').value=p[1];$('foodQuantity').value=p[5];$('foodNotes').value='Standard estimate; replace with label/recipe where available.'}const q=Number($('foodQuantity').value);for(const [id,rate] of [['foodKcal',p[2]],['foodProtein',p[3]],['foodCarbs',p[4]]])$(id).value=(q*rate).toFixed(1)}
$('foodPreset').onchange=()=>cPreset(true);$('foodQuantity').oninput=()=>cPreset(false);
let timerElapsed=0,timerStart=null;function timerSeconds(){return timerElapsed+(timerStart===null?0:(Date.now()-timerStart)/1000)}
function timerPaint(){const n=Math.floor(timerSeconds());$('timer').textContent=String(Math.floor(n/60)).padStart(2,'0')+':'+String(n%60).padStart(2,'0')}
$('timerStart').onclick=()=>{if(timerStart===null)timerStart=Date.now()};$('timerStop').onclick=()=>{timerElapsed=timerSeconds();timerStart=null;$('workoutMinutes').value=(timerElapsed/60).toFixed(1);timerPaint()};$('timerReset').onclick=()=>{timerStart=null;timerElapsed=0;timerPaint()};setInterval(timerPaint,1000);
$('coachDate').onchange=()=>{calMonth=chooseDate().slice(0,7);cRender()};
for(const [id,dir] of [['monthPrev',-1],['monthNext',1],['miniMonthPrev',-1],['miniMonthNext',1]])$(id).onclick=()=>{let [y,m]=calMonth.split('-').map(Number);calMonth=new Date(Date.UTC(y,m-1+dir,1)).toISOString().slice(0,7);cRender()};
$('askForm').onsubmit=e=>{e.preventDefault();const q=$('question').value.toLowerCase(),d=chooseDate(),a=cAdvice(d),r=cRecovery(d),tot=cTotals(d);let answer;
 if(/eat|food|meal|carb|protein|calori|rice/.test(q))answer=`For ${d}, you logged ${cFmt(tot.kcal)} kcal, ${cFmt(tot.protein)} g protein and ${cFmt(tot.carbs)} g carbohydrate. The starting guide for the selected day is about ${a.target} kcal, ${cFmt(coach.profile.proteinTarget)} g protein and ${a.carbs} g carbohydrate. ${tot.missing?'Some entries are incomplete. ':''}Planned meals are excluded. This may be a partial-day log, so it does not establish your daily deficit.\nSource: food workbook + your saved food logs; planning targets from our discussion.`;
 else if(/sleep|hrv|recover|readiness|heart/.test(q))answer=`Recovery for ${d}: ${r.sleep?cTime(r.sleep.sleepTimeSeconds)+' sleep; score '+cFmt(r.sleep.sleepScores?.overall?.value):'sleep unavailable'}. ${r.hrv?'HRV '+cFmt(r.hrv.lastNightAvg)+' ms, 7-day '+cFmt(r.hrv.weeklyAvg)+' ms, status '+r.hrv.status:'HRV unavailable'}. Resting HR ${cFmt(r.well?.heartRate?.restingValue)} bpm.\n${a.title}\nGarmin training readiness is not exposed by the documented API. Source: Garmin recovery data for this date and your check-in.`;
 else if(/saturday|long run|calendar|next/.test(q)){const p=coach.calendar.find(p=>p.date>=d&&p.title==='Long Run');answer=p?`${p.date}: ${p.km} km. ${p.description}\nFuel: ${p.fuel}\nSource: ${p.overrideSource||p.source}${p.originalKm?'; original workbook '+p.originalKm+' km.':''}`:'No upcoming long run in the imported calendar.'}
 else if(/strength|push|squat|calisthenic/.test(q))answer=`Keep squats and push-ups 2–3 reps short of failure and log your sets here. Avoid hard leg training before the long run. Today’s imported strength: ${a.p?.strength&&a.p.strength!=='-'?a.p.strength:'none'}. If sore, reduce or skip additional work. See Strength A & B for the imported exercises.\nSource: imported strength plan and your running schedule.`;
 else if(/today|workout|train|run|do/.test(q))answer=`${a.title}\n${a.steps.join('\n')}\nWhy: ${a.reasons.join(' ')}\nSource: imported calendar, Garmin readings and check-in for ${d}.`;
 else answer='I can answer about the selected date’s workout, food totals, sleep, HRV, strength and upcoming long run. Try “What should I do today?” or “How much protein have I logged?”';$('answer').textContent=answer};
if(D.demo){
 try{const saved=JSON.parse(localStorage.getItem('daily-practice-demo'));if(saved&&Array.isArray(saved.meals)&&Array.isArray(saved.workouts)&&Array.isArray(saved.checkins))coach.journal=saved}catch(e){}
 $('modeBanner').hidden=false;$('modeBanner').textContent='Demo · fictional training data. Your changes save only in this browser.';
}
cRender();
if(D.demo)$('connection').textContent='Demo · fictional data';
else if(location.protocol==='http:'||location.protocol==='https:')fetch('/api/state').then(r=>{if(!r.ok)throw Error();return r.json()}).then(data=>{coach=data;live=true;cRender();$('connection').textContent='Connected · saved locally'}).catch(()=>{$('connection').textContent='Preview · open localhost:8765 to save'});
else $('connection').textContent='Preview · open localhost:8765 to save';
window.addEventListener('hashchange',()=>cReveal(location.hash));
