#!/usr/bin/env python3
"""Render animated SVG cards for Jeevan's GitHub profile README."""
import base64,html,json,os
from collections import defaultdict
from datetime import date,timedelta
from pathlib import Path
R=Path(__file__).resolve().parent; DATA=json.loads((R/'data/contributions.json').read_text()); OUT=R/'cards'; OUT.mkdir(exist_ok=True)
STATIC=os.getenv('STATIC')=='1'; PAPER='#F3F3F1'; INK='#111111'; BLUE='#2F55FF'; RED='#EF3B2D'; YELLOW='#FFC81A'; MUTED='#737373'
SERIF='Instrument Serif, Georgia, serif'; SANS='Geist, Arial, sans-serif'; MONO='Geist Mono, monospace'
def e(v): return html.escape(str(v),quote=True)
def t(x,y,s,z=18,w=400,c=INK,f=SANS,extra=''): return f'<text x="{x}" y="{y}" font-family="{f}" font-size="{z}" font-weight="{w}" fill="{c}" {extra}>{e(s)}</text>'
def wrap(title,body,w,h,delay):
 anim='' if STATIC else f'<style>.in{{opacity:0;transform:translateY(16px);animation:enter .75s ease-out {delay}s forwards}}@keyframes enter{{to{{opacity:1;transform:translateY(0)}}}}@media(prefers-reduced-motion:reduce){{.in{{animation:none!important;opacity:1!important;transform:none!important}}}}</style>'
 return f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{w}" height="{h}" viewBox="0 0 {w} {h}"><title>{e(title)}</title>{anim}<g class="in">{body}</g></svg>'
def save(name,title,body,w,h,delay): (OUT/name).write_text(wrap(title,body,w,h,delay)+'\n')
profile=DATA.get('profile',{}); name=profile.get('name','Jeevan Charugundla')
photo=base64.b64encode((R/'assets/portrait-embed.jpg').read_bytes()).decode()
body=f'<rect x="8" y="8" width="1084" height="344" rx="18" fill="{PAPER}"/><rect x="48" y="48" width="9" height="9" rx="2" fill="{BLUE}"/>{t(72,58,"AI PRODUCT ENGINEER / FULL-STACK BUILDER",14,500,MUTED,MONO)}{t(48,166,"Jeevan",92,400,INK,SERIF)}{t(48,250,"Charugundla",86,400,INK,SERIF,extra="font-style=\"italic\"")}{t(55,294,"I build AI-powered products, engineer useful experiences,",19,400,"#383838")}{t(55,322,"and turn ideas into reality.",19,400,"#383838")}{t(55,340,"jeevan-portfolio-delta.vercel.app ↗",14,500,BLUE,MONO)}<defs><clipPath id="portrait"><rect x="720" y="34" width="340" height="300" rx="8"/></clipPath><filter id="mono"><feColorMatrix type="saturate" values="0"/></filter></defs><image x="720" y="34" width="340" height="300" preserveAspectRatio="xMidYMid slice" clip-path="url(#portrait)" filter="url(#mono)" href="data:image/jpeg;base64,{photo}"/><rect x="720" y="34" width="340" height="300" rx="8" fill="none" stroke="#111" opacity=".15"/>'
save('01-hero.svg',f'{name} — AI Product Engineer',body,1100,360,0)
tiles=[('BUILD','AI & ENGINEERING','AI products, apps and systems',BLUE,'#fff','https://github.com/jeevan-charugundla'),('CREATE','DESIGN & EXPERIENCE','UI/UX and digital storytelling',RED,'#fff','https://jeevan-portfolio-delta.vercel.app/'),('LEARN','EXPLORE & EXPERIMENT','New tools, ideas and technology',YELLOW,INK,'https://www.linkedin.com/in/jeevan-charugundla/')]
for i,(title,sub,desc,col,fg,url) in enumerate(tiles,1):
 body=f'<a xlink:href="{url}"><rect x="7" y="7" width="346" height="142" rx="12" fill="{col}"/><rect x="18" y="18" width="324" height="120" rx="8" fill="none" stroke="{fg}" opacity=".25"/>{t(28,50,title,25,700,fg)}{t(28,82,sub,13,700,fg,MONO)}{t(28,111,desc,12,400,fg)}{t(320,130,"↗",22,700,fg)}</a>'
 save(f'02-tile-{i}.svg',title,body,360,156,.2*i)
daily=DATA.get('daily',[]); counts={date.fromisoformat(x['date']):int(x.get('count',x.get('contributionCount',0))) for x in daily}
if counts:
 today=date.today(); cursor=today if counts.get(today,0)>0 else today-timedelta(days=1); streak=0
 while counts.get(cursor,0)>0: streak+=1; cursor-=timedelta(days=1)
 active=sum(v>0 for v in counts.values()); total=sum(counts.values()); busiest=max(counts.items(),key=lambda x:x[1])
else: streak=active=total=0; busiest=(date.today(),0)
monthly=defaultdict(int)
for day,count in counts.items(): monthly[(day.year,day.month)]+=count
months=sorted(monthly)[-12:]; maxv=max([monthly[m] for m in months] or [1])
body=f'<rect x="8" y="8" width="1084" height="284" rx="18" fill="{PAPER}"/>{t(44,48,"CONTRIBUTION RHYTHM",14,700,MUTED,MONO)}'
for i,(cap,val,col) in enumerate([("CURRENT STREAK",f"{streak} days","#DCE4FF"),("ACTIVE DAYS",str(active),"#F9DCE7"),("BUSIEST DAY",f"{busiest[0].strftime('%b %d')} · {busiest[1]}","#E0E7FF")]):
 x=44+i*342; body+=f'<rect x="{x}" y="68" width="310" height="68" rx="9" fill="{col}"/>{t(x+16,94,cap,11,700,MUTED,MONO)}{t(x+16,122,val,22,700)}'
body+=t(44,172,f"{total:,} contributions · {len(daily)} tracked days",14,500)
for i,m in enumerate(months):
 x=52+i*82; bh=max(3,monthly[m]/maxv*82); body+=f'<rect x="{x}" y="{260-bh}" width="42" height="{bh}" rx="4" fill="{BLUE}"/>{t(x+21,280,date(m[0],m[1],1).strftime("%b").upper(),10,600,MUTED,MONO)}'
save('03-activity.svg','Monthly contributions and activity',body,1100,304,1)
end=max(counts) if counts else date.today(); start=end-timedelta(days=363); start-=timedelta(days=(start.weekday()+1)%7); maxc=max(counts.values()) if counts else 1
palette=['#E5E5E5','#DCE4FF','#AFC0FF','#718EFF',BLUE]
body=f'<rect x="8" y="8" width="1084" height="168" rx="18" fill="{PAPER}"/>{t(38,42,"A YEAR OF SHOWING UP",13,700,MUTED,MONO)}'
for week in range(53):
 for dow in range(7):
  day=start+timedelta(days=week*7+dow); val=counts.get(day,0); level=0 if val==0 else min(4,1+int(val/maxc*3)); body+=f'<rect x="{40+week*19}" y="{58+dow*15}" width="13" height="11" rx="2" fill="{palette[level]}"><title>{day}: {val} contributions</title></rect>'
save('04-heatmap.svg','GitHub contribution heatmap',body,1100,188,1.8)
for i,r in enumerate(DATA.get('featured_repos',[])[:5],1):
 nm=r.get('name','Featured project'); desc=r.get('description') or 'A project built to solve a real problem.'; lang=r.get('language') or 'Software'; url=r.get('html_url') or 'https://github.com/jeevan-charugundla'
 body=f'<a xlink:href="{url}"><rect x="8" y="8" width="1084" height="128" rx="14" fill="{PAPER}"/><rect x="28" y="28" width="70" height="70" rx="7" fill="{[BLUE,RED,YELLOW][(i-1)%3]}"/>{t(63,72,f"{i:02d}",22,700,"#fff" if i%3!=0 else INK,MONO)}{t(124,58,nm,25,700)}{t(126,85,desc[:100],13,400,"#444")}{t(126,113,str(lang).upper(),10,700,MUTED,MONO)}<rect x="914" y="44" width="148" height="44" rx="6" fill="{BLUE}"/>{t(988,72,"OPEN REPO ↗",11,700,"#fff",MONO)}</a>'
 save(f'project-{i:02d}.svg',nm,body,1100,144,2.4+i*.3)
