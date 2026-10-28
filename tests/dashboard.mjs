import fs from 'node:fs';
import vm from 'node:vm';
import assert from 'node:assert/strict';
const file=process.argv[2]||'site/index.html';
const html=fs.readFileSync(file,'utf8');
const scripts=[...html.matchAll(/<script([^>]*)>([\s\S]*?)<\/script>/g)];
const ids=[...html.matchAll(/\bid="([^\"]+)"/g)].map(x=>x[1]);
assert.equal(ids.length,new Set(ids).size,'Unique HTML IDs');
const nodes={};
for(const [,attrs,code] of scripts)if(attrs.includes('training-data'))nodes['training-data']={textContent:code};
function element(id){
 assert(ids.includes(id),'Missing element '+id);
 return nodes[id]??(nodes[id]={value:id==='sport'?'all':'',dataset:{},innerHTML:'',addEventListener(){},reset(){},classList:{contains(){return false},toggle(){}}});
}
const context=vm.createContext({document:{getElementById:element,querySelectorAll:()=>[]},location:{protocol:'file:',hash:''},window:{addEventListener(){}},localStorage:{getItem(){return null},setItem(){}},crypto:{randomUUID(){return 'demo-id'}},setInterval(){},console,FormData:class{},Intl,Date});
for(const [,attrs,code] of scripts)if(!attrs.includes('application/json'))vm.runInContext(code,context);
vm.runInContext(`
 const synthetic=[{startTimeLocal:'2026-06-01T10:00:00',activityType:'running',duration:3600,activityTrainingLoad:100},{startTimeLocal:'2026-06-07T10:00:00',activityType:'cycling',duration:1800,activityTrainingLoad:50}];
 const originalStart=D.start,originalEnd=D.end;D.start='2026-06-01';D.end='2026-06-20';
 if(trainingLoad(synthetic,'2026-06-07','2026-06-08','all')[0].load!==150)throw Error('Load sum');
 if(trainingLoad(synthetic,'2026-06-07','2026-06-08','all')[1].load!==50)throw Error('Rolling cutoff');
 if(trainingLoad(synthetic,'2026-06-07','2026-06-07','running')[0].load!==100)throw Error('Load sport filter');
 const missing=[...synthetic,{startTimeLocal:'2026-06-07T12:00:00',activityType:'running'}];
 if(trainingLoad(missing,'2026-06-07','2026-06-07','all')[0].load!==null)throw Error('Missing load treated as zero');
 if(trainingLoad(synthetic,'2026-07-01','2026-07-02','all').length!==0)throw Error('Future zero');
 D.start=originalStart;D.end=originalEnd;
 const d=chooseDate(),before=cTotals(d).kcal;
 coach.journal.meals.push({id:'planned',date:d,food:'Planned',status:'planned',kcal:100,protein:5,carbs:15});
 if(cTotals(d).kcal!==before)throw Error('Planned food counted');
 coach.journal.meals.at(-1).status='eaten';
 if(cTotals(d).kcal!==before+100)throw Error('Eaten food missing');
 coach.journal.meals.pop();
 coach.journal.checkins.push({date:d,pain:true,createdAt:new Date().toISOString()});
 if(!cAdvice(d).title.includes('Pause'))throw Error('Pain ignored');
`,context);
assert(nodes.monthlyVisual.innerHTML.includes('month-column'),'Monthly chart rendered');
assert(nodes.loadChart.innerHTML.includes('<svg'),'Actual load graph rendered');
assert(!html.includes('sleepTargetForm'),'Old goal card removed');
console.log('PASS:',file,'— load windows, missing data, nutrition, check-ins and page structure');
