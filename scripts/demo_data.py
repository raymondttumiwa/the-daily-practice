"""Deterministic fictional data for the public GitHub Pages preview."""
from datetime import datetime, timedelta
import random
from zoneinfo import ZoneInfo


def bundle():
    rng = random.Random(73)
    end = datetime.now(ZoneInfo('Asia/Shanghai')).date()
    start = end - timedelta(days=149)
    data = {'start':start.isoformat(),'end':end.isoformat(),'syncedAt':end.isoformat(),
            'activities':[],'sleep':[],'hrv':[],'wellness':[],'fitnessAge':[],
            'requests':[],'demo':True,'readinessStatus':'Garmin readiness is not supplied by this API.'}
    for n in range(150):
        d = start+timedelta(days=n)
        ds = d.isoformat()
        if d.weekday() in (1,2,4,5):
            cycling = d.weekday()==4
            km = rng.uniform(15,32) if cycling else (rng.uniform(11,16) if d.weekday()==5 else rng.uniform(5,9))
            seconds = km*(rng.uniform(160,200) if cycling else rng.uniform(350,400))
            data['activities'].append({'startTimeLocal':ds+' 18:00:00','activityType':'cycling' if cycling else 'running',
               'distance':km*1000,'duration':seconds,'movingDuration':seconds,'elapsedDuration':seconds+60,
               'averageHR':rng.randint(132,155),'maxHR':rng.randint(165,180),'calories':km*(25 if cycling else 70),
               'aerobicTrainingEffect':round(rng.uniform(2,4),1),'anaerobicTrainingEffect':round(rng.uniform(0,2),1),
               'activityTrainingLoad':rng.uniform(65,170),'elevationGain':rng.uniform(12,200),
               'averageRunningCadenceInStepsPerMinute':168 if not cycling else None,'avgPower':240 if not cycling else 150,
               'vO2MaxValue':None})
        data['sleep'].append({'calendarDate':ds,'sleepTimeSeconds':rng.randint(24,31)*900,'deepSleepSeconds':4200,
                            'remSleepSeconds':5400,'lightSleepSeconds':15000,'awakeSleepSeconds':1200,
                            'sleepScores':{'overall':{'value':rng.randint(64,91)}}})
        data['hrv'].append({'calendarDate':ds,'lastNightAvg':rng.randint(52,75),'weeklyAvg':64,'status':'BALANCED'})
        data['wellness'].append({'calendarDate':ds,'heartRate':{'restingValue':rng.randint(46,53)},
                                'bodyBattery':{'maxValue':rng.randint(67,98)},'stress':{'avgLevel':rng.randint(18,35)},
                                'movement':{'steps':{'value':rng.randint(6500,16000)}},'calories':{'burnedTotal':rng.randint(2300,2900)},
                                'respiration':{'avgValue':rng.randint(13,17)},'pulseOx':{'avgValue':rng.randint(96,99)}})
    calendar=[]
    for n in range(-14,35):
        d=end+timedelta(days=n); title='Long Run' if d.weekday()==5 else 'Easy' if d.weekday() in (1,2,4) else 'Rest'
        calendar.append({'date':d.isoformat(),'title':title,'km':14 if title=='Long Run' else 6 if title=='Easy' else None,
          'description':'Comfortable, conversational effort.' if title!='Rest' else 'Rest and recover.',
          'pace':'Easy effort','hr':'Conversational','strength':'-','fuel':'Practise familiar run fuel.','source':'Fictional demo plan'})
    data['coach']={'calendar':calendar,'strength':[],'meals':[],'weights':[],
                  'profile':{'name':'Runner','raceDate':(end+timedelta(days=39)).isoformat(),'proteinTarget':150},
                  'sources':['Fictional demonstration data'],
                  'journal':{'meals':[{'id':'demo-breakfast','date':end.isoformat(),'food':'Oats, milk & banana','meal':'Breakfast',
                                       'quantity':1,'unit':'bowl','status':'eaten','kcal':460,'protein':20,'carbs':72}],
                             'workouts':[],'checkins':[]}}
    data['database']={'extendedRecords':0,'activities':len(data['activities'])}
    return data
