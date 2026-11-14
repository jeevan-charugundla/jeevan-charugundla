#!/usr/bin/env python3
"""Render self-contained animated SVG cards for Jeevan's GitHub README."""
import base64,datetime,html,json,os,re,subprocess,tempfile,urllib.request
from collections import defaultdict
from pathlib import Path
from PIL import Image,ImageOps,ImageEnhance,ImageFile
ImageFile.LOAD_TRUNCATED_IMAGES=True
R=Path(__file__).resolve().parent; DATA=R/"data/contributions.json"; OUT=R/"cards"; FD=R/"assets/fonts"; PHOTO=R/"assets/portrait-embed.jpg"
STATIC=os.getenv("STATIC","0")=="1"; W=880
PAPER="#F3F3F1"; DEEP="#E2E2DE"; INK="#111111"; SOFT="#3A3A3C"; MUTED="#6E6E73"; RULE="#DCDCD7"; BLUE="#2F55FF"; RED="#EF3B2D"; YELLOW="#FFC81A"
SERIF="'Instrument Serif',Georgia,serif"; SANS="Geist,system-ui,sans-serif"; MONO="'Geist Mono',ui-monospace,Menlo,monospace"
FONTS={"serif":("Instrument Serif","normal",400,"serif-400.woff"),"serif-i":("Instrument Serif","italic",400,"serif-italic.woff"),"sans":("Geist","normal",400,"geist-400.woff"),"sans-b":("Geist","normal",600,"geist-600.woff"),"mono":("Geist Mono","normal",400,"geistmono-400.woff")}
FONT_BASE="https://raw.githubusercontent.com/AVIVASHISHTA29/AVIVASHISHTA29/main/fonts/"
CSS="""
@keyframes rise{from{opacity:0;transform:translateY(16px)}to{opacity:1;transform:none}}
@keyframes fade{from{opacity:0}to{opacity:1}}
@keyframes grow{from{transform:scaleY(0)}to{transform:scaleY(1)}}
@keyframes pop{0%{opacity:0;transform:scale(.3)}70%{opacity:1;transform:scale(1.15)}100%{opacity:1;transform:none}}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.25}}
@keyframes nudge{0%,100%{transform:none}50%{transform:translateX(4px)}}
@keyframes tilein{0%{opacity:0;transform:translateY(90px) scale(.6) rotate(-9deg)}55%{opacity:1;transform:translateY(-10px) scale(1.05) rotate(2deg)}75%{transform:translateY(3px) scale(.98) rotate(-.8deg)}100%{opacity:1;transform:none}}
@keyframes slidein{from{opacity:0;transform:translateX(-26px)}to{opacity:1;transform:none}}
@keyframes sheen{0%{transform:translateX(-260px) skewX(-20deg)}22%,100%{transform:translateX(420px) skewX(-20deg)}}
@keyframes ring{0%{opacity:.7;transform:scale(.2)}100%{opacity:0;transform:scale(2.4)}}
@keyframes arrowin{0%{opacity:0;transform:translateX(-30px)}60%{opacity:1;transform:translateX(6px)}100%{opacity:1;transform:none}}
@keyframes roll{from{transform:translateY(60px)}to{transform:none}}
.r{opacity:0;animation:rise .8s cubic-bezier(.2,.7,.2,1) both;transform-box:fill-box}
.f{opacity:0;animation:fade .9s ease-out both}
.g{transform-box:fill-box;transform-origin:bottom;transform:scaleY(0);animation:grow .8s cubic-bezier(.2,.7,.2,1) both}
.p{opacity:0;transform-box:fill-box;transform-origin:center;animation:pop .4s ease-out both}
.live{animation:pulse 1.6s ease-in-out infinite}
.n{transform-box:fill-box;animation:nudge 1.8s ease-in-out infinite}
.ti{opacity:0;transform-box:fill-box;transform-origin:50% 60%;animation:tilein 1.1s cubic-bezier(.2,.8,.2,1) both}
.sl{opacity:0;transform-box:fill-box;animation:slidein .6s cubic-bezier(.2,.7,.2,1) both}
.ai{opacity:0;transform-box:fill-box;animation:arrowin .7s cubic-bezier(.2,.7,.2,1) both}
.ro{transform-box:fill-box;animation:roll .8s cubic-bezier(.15,.8,.2,1) both}
.sh{animation:sheen 5s ease-in-out infinite}
.rg{opacity:0;transform-box:fill-box;animation:ring 1s ease-out both}
@media(prefers-reduced-motion:reduce){.r,.f,.g,.p,.live,.n,.ti,.sl,.ai,.ro,.rg{animation:none!important;opacity:1!important;transform:none!important}.sh,.rg,animate,animateTransform,set{display:none!important}}
"""
def E(v): return html.escape(str(v),quote=True)
def D(x): return f'style="animation-delay:{x:.3f}s"'
def T(x,y,s,z=18,wt=400,c=INK,f=SANS,extra=""): return f'<text x="{x}" y="{y}" font-family="{f}" font-size="{z}" font-weight="{wt}" fill="{c}" {extra}>{E(s)}</text>'
def wrap(s,n=34):
 out=[]; line=""
 for word in str(s).split():
  if line and len(line)+len(word)+1>n: out.append(line); line=word
  else: line=(line+" "+word).strip()
 if line: out.append(line)
 return out
def textlines(x,y,arr,lh,attrs): return "".join(f'<text x="{x}" y="{y+i*lh}" {attrs}>{E(v)}</text>' for i,v in enumerate(arr))
def ensure_fonts():
 FD.mkdir(parents=True,exist_ok=True)
 for f in [x[3] for x in FONTS.values()]:
  if not (FD/f).exists(): urllib.request.urlretrieve(FONT_BASE+f,FD/f)
 (FD/"LICENSE.txt").write_text("Instrument Serif, Geist and Geist Mono subsets. SIL Open Font License 1.1. Source: AVIVASHISHTA29/AVIVASHISHTA29/fonts. https://openfontlicense.org/\\n")
def font_css(chars):
 out=[]
 with tempfile.TemporaryDirectory() as td:
  for key,(family,style,weight,filename) in FONTS.items():
   src=FD/filename; dst=Path(td)/(key+".woff")
   try:
    subprocess.run(["pyftsubset",str(src),f"--output-file={dst}","--flavor=woff",f"--text={chars}","--layout-features=*","--glyph-names"],check=True,capture_output=True,text=True)
    raw=dst.read_bytes()
   except (FileNotFoundError,subprocess.CalledProcessError): raw=src.read_bytes()
   out.append(f"@font-face{{font-family:'{family}';font-style:{style};font-weight:{weight};src:url(data:font/woff;base64,{base64.b64encode(raw).decode()}) format('woff')}}")
 return "".join(out)
def svg(w,h,body,fonts,label):
 css=fonts+CSS
 if STATIC: css+=".r,.f,.g,.p,.live,.n,.ti,.sl,.ai,.ro,.rg{animation:none!important;opacity:1!important;transform:none!important}.sh,.rg,animate,animateTransform,set{display:none!important}"
 return f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{w:.3f}" height="{h}" viewBox="0 0 {w:.3f} {h}" role="img" aria-label="{E(label)}"><title>{E(label)}</title><style>{css}</style>{body}</svg>'
def save(name,body,fonts,w,h,label): (OUT/name).write_text(svg(w,h,body,fonts,label),encoding="utf-8")
def ascii_portrait():
 im=ImageOps.exif_transpose(Image.open(PHOTO)).convert("L"); w,h=im.size
 im=im.crop((int(w*.30),int(h*.43),int(w*.86),int(h*.94)))
 im=ImageOps.fit(im,(100,84),method=Image.Resampling.LANCZOS,centering=(.52,.48)); im=ImageEnhance.Contrast(im).enhance(1.35); px=im.load(); ramp=" .,:;irsXA253hMHGS#9B&@"
 return ["".join(ramp[min(len(ramp)-1,int((255-px[x,y])/256*len(ramp)))] for x in range(im.width)) for y in range(im.height)]
def hero(fonts):
 rows=ascii_portrait(); portrait=[]
 for i,row in enumerate(rows): portrait.append(f'<text class="f" style="animation-delay:{.25+i*.018:.3f}s;animation-duration:.35s" xml:space="preserve" x="20" y="{37+i*8.2:.1f}" fill="{INK}" font-size="7.2" textLength="800" lengthAdjust="spacing">{E(row)}</text>')
 grad=f'<linearGradient id="shine" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="600" y2="0"><stop offset="0" stop-color="{INK}"/><stop offset=".42" stop-color="{INK}"/><stop offset=".5" stop-color="{BLUE}"/><stop offset=".58" stop-color="{INK}"/><stop offset="1" stop-color="{INK}"/><animateTransform attributeName="gradientTransform" type="translate" values="-600 0;600 0;600 0" keyTimes="0;.45;1" dur="7s" begin="1.6s" repeatCount="indefinite"/></linearGradient>'
 body=f'<defs>{grad}</defs><rect width="{W}" height="420" rx="14" fill="{PAPER}"/><g class="f" {D(0)}><rect class="live" x="48" y="49" width="8" height="8" rx="2" fill="{BLUE}"/>{T(66,57,"AI PRODUCT ENGINEER / FULL-STACK BUILDER",12,400,MUTED,MONO,'letter-spacing="1"')}</g><text class="r" {D(.15)} x="44" y="190" font-family="{SERIF}" font-size="116" letter-spacing="-2.5" fill="{INK}">Jeevan</text><text class="r" {D(.30)} x="44" y="290" font-family="{SERIF}" font-style="italic" font-size="108" letter-spacing="-2.5" fill="url(#shine)">Charugundla</text><g class="r" {D(.55)}>{textlines(48,338,["I build AI-powered products, engineer useful experiences,","and turn ideas into reality."],27,f'font-family="{SANS}" font-size="18" fill="{SOFT}"')}</g><g class="f" {D(.85)}>{T(48,396,"jeevan-portfolio-delta.vercel.app",13,400,INK,MONO)}<text x="246" y="396" class="n" font-family="{MONO}" font-size="13" fill="{BLUE}">↗</text></g><g transform="translate(520 55) scale(.41) translate(-20 -37)" font-family="ui-monospace,Menlo,Consolas,monospace">{''.join(portrait)}</g>'
 save("01-hero.svg",body,fonts,W,420,"Jeevan Charugundla — AI Product Engineer")
def counter(num,unit,x,y,attrs,start):
 m=re.match(r"([\d.]+)(.*)",str(num)); n=float(m.group(1)); suffix=m.group(2); decimals=len(m.group(1).split(".")[1]) if "." in m.group(1) else 0
 tail=f' <tspan font-style="italic">{E(unit)}</tspan>'
 if STATIC:return f'<text x="{x}" y="{y}" {attrs}>{E(num)}{tail}</text>'
 parts=[]
 for i in range(19):
  ease=1-(1-i/18)**3; label=str(num) if i==18 else f"{n*ease:.{decimals}f}{suffix}"; begin=start+1.1*i/18
  hide=f'<set attributeName="opacity" to="0" begin="{start+1.1*(i+1)/18:.3f}s"/>' if i<18 else ""
  parts.append(f'<text x="{x}" y="{y}" {attrs} opacity="0">{E(label)}{tail}<set attributeName="opacity" to="1" begin="{begin:.3f}s"/>{hide}</text>')
 return "".join(parts)
def tile(filename,title,color,fg,ordinal,copy,start,fonts):
 w=W/3-8; desc="".join(f'<text class="r" {D(start+.75+i*.1)} x="24" y="{154+i*20}" font-family="{SANS}" font-size="13.5" fill="{fg}">{E(v)}</text>' for i,v in enumerate(wrap(copy,33)[:3]))
 body=f'<defs><clipPath id="card"><rect width="{w}" height="222" rx="14"/></clipPath><clipPath id="slot"><rect x="0" y="62" width="{w}" height="65"/></clipPath><linearGradient id="gl" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity=".38"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient></defs><g class="ti" {D(start)}><g clip-path="url(#card)"><rect width="{w}" height="222" fill="{color}"/><circle class="rg" {D(start+.5)} cx="{w-38}" cy="184" r="58" fill="none" stroke="{fg}" stroke-opacity=".5" stroke-width="2"/><rect class="sh" style="animation-delay:{start+1.4:.2f}s" x="0" y="-20" width="90" height="262" fill="url(#gl)"/></g><text class="sl" {D(start+.35)} x="24" y="38" font-family="{MONO}" font-size="12" letter-spacing="1.2" fill="{fg}">{E(title)}</text><g class="ai" {D(start+.5)}><text class="n" x="{w-38}" y="38" font-family="{MONO}" font-size="14" fill="{fg}">↗</text></g><g clip-path="url(#slot)"><g class="ro" {D(start+.45)}>{counter(ordinal,"world",22,116,f'font-family="{SERIF}" font-size="46" fill="{fg}"',start+.45)}</g></g>{desc}</g>'
 save(filename,body,fonts,w+8,234,f"{title}: {copy}")
def daily_rows(data):
 result=[]
 for x in data.get("daily",[]):
  try:result.append((datetime.date.fromisoformat(x["date"]),int(x.get("contributionCount",x.get("count",0)))))
  except (KeyError,TypeError,ValueError):pass
 return sorted(result)
def stats(rows):
 if not rows:return 0,0,0,"—",0
 counts=dict(rows); last=max(counts); cur=last if counts.get(last,0)>0 else last-datetime.timedelta(days=1); streak=0
 while counts.get(cur,0)>0:streak+=1;cur-=datetime.timedelta(days=1)
 best=max(rows,key=lambda v:v[1])
 return sum(v for _,v in rows),sum(v>0 for _,v in rows),streak,best[0].strftime("%b %d"),best[1]
def activity(rows,fonts):
 total,active,streak,bday,bcount=stats(rows); monthly=defaultdict(int)
 for d,n in rows:monthly[(d.year,d.month)]+=n
 months=[{"month":f"{y:04d}-{m:02d}","total":v} for (y,m),v in sorted(monthly.items())][-12:]
 best=max(months[:-1] or months,key=lambda x:x["total"]) if months else {"total":1}; peak=max(1,best["total"])
 x0,x1,base,maxh,gap=40,600,292,140,10; bw=(x1-x0-gap*(len(months)-1))/max(1,len(months)); bars=[]
 for i,m in enumerate(months):
  bh=max(4,round(m["total"]/peak*maxh)); x=x0+i*(bw+gap); chosen=m is best; partial=i==len(months)-1
  color=BLUE if chosen else "#C9C9C4" if partial else INK; lab=datetime.date.fromisoformat(m["month"]+"-01").strftime("%b")
  bars.append(f'<rect class="g" style="animation-delay:{2.2+i*.07:.2f}s" x="{x:.1f}" y="{base-bh}" width="{bw:.1f}" height="{bh}" rx="4" fill="{color}"><title>{lab}: {m["total"]}</title></rect><text class="f" style="animation-delay:{2.2+i*.07:.2f}s" x="{x+bw/2:.1f}" y="{base+22}" text-anchor="middle" font-family="{MONO}" font-size="11" fill="{MUTED}">{lab}</text>')
  if chosen:bars.append(f'<text class="p" style="animation-delay:3.2s" x="{x+bw/2:.1f}" y="{base-bh-10}" text-anchor="middle" font-family="{MONO}" font-size="11" fill="{BLUE}">{m["total"]}</text>')
 metrics=[(f'{streak} <tspan font-style="italic">days</tspan>',"current streak"),(f'{active}<tspan fill="#8e8e93"> / {len(rows)}</tspan>',"days with a contribution"),(str(bcount),f"on {bday}, the busiest day")]; side=[]
 for i,(big,small) in enumerate(metrics):
  y=104+i*92; side.append(f'<g class="r" {D(2.6+i*.15)}><text x="650" y="{y}" font-family="{SERIF}" font-size="40" fill="{INK}">{big}</text><text x="650" y="{y+24}" font-family="{SANS}" font-size="13" fill="{MUTED}">{E(small)}</text></g>')
  if i<2:side.append(f'<rect class="f" {D(2.6)} x="650" y="{y+44}" width="190" height="1" fill="{RULE}"/>')
 body=f'<rect width="{W}" height="352" rx="14" fill="{PAPER}"/><text class="f" {D(1.9)} x="40" y="58" font-family="{MONO}" font-size="12" letter-spacing="1" fill="{MUTED}">THE LAST 12 MONTHS ON GITHUB</text><text class="r" {D(2)} x="38" y="114" font-family="{SERIF}" font-size="52" fill="{INK}">{total:,} <tspan font-style="italic">contributions</tspan></text>{"".join(bars)}{"".join(side)}'
 save("03-activity.svg",body,fonts,W,352,f"{total:,} contributions, {streak}-day streak, {active} active days")
LEVEL=[DEEP,"#C8D3FF","#94A8FF","#6280FF",BLUE,"#1A3BE0"]
def heatmap(rows,fonts):
 if not rows:rows=[(datetime.date.today(),0)]
 lead=(rows[0][0].weekday()+1)%7; gx,gy,step,cell=44,96,15,12; cells=[]; months=[]; seen=set()
 for i,(d,n) in enumerate(rows):
  col,row=divmod(i+lead,7)
  if d.day<=7 and (d.year,d.month) not in seen and row==0:seen.add((d.year,d.month));months.append((col,d.strftime("%b")))
  lvl=0 if n==0 else 1 if n<=5 else 2 if n<=15 else 3 if n<=30 else 4 if n<=50 else 5
  cells.append(f'<rect class="p" style="animation-delay:{1+col*.03+row*.02:.2f}s" x="{gx+col*step}" y="{gy+row*step}" width="{cell}" height="{cell}" rx="3" fill="{LEVEL[lvl]}"><title>{d.isoformat()}: {n} contributions</title></rect>')
 cols=(len(rows)+lead+6)//7; right=gx+cols*step-3; h=gy+7*step+44
 labels="".join(f'<text x="{gx+c*step}" y="{gy+7*step+16}" font-family="{MONO}" font-size="11" fill="{MUTED}">{m}</text>' for c,m in months if c<cols-1)
 lx=right-len(LEVEL)*14; legend="".join(f'<rect x="{lx+i*14}" y="{gy+7*step+6}" width="11" height="11" rx="2.5" fill="{c}"/>' for i,c in enumerate(LEVEL))
 total,active,streak,bday,bcount=stats(rows)
 body=f'<rect width="{W}" height="{h}" rx="14" fill="{PAPER}"/><text class="r" {D(.8)} x="42" y="62" font-family="{SERIF}" font-size="34" fill="{INK}">Every day, <tspan font-style="italic" fill="{BLUE}">in blue</tspan></text><text class="f" {D(.8)} x="{right}" y="60" text-anchor="end" font-family="{MONO}" font-size="12" letter-spacing="1" fill="{MUTED}">REFRESHED DAILY</text>{"".join(cells)}<g class="f" {D(2.4)}>{labels}<text x="{lx-8}" y="{gy+7*step+16}" text-anchor="end" font-family="{MONO}" font-size="11" fill="{MUTED}">less</text>{legend}<text x="{lx+len(LEVEL)*14+2}" y="{gy+7*step+16}" font-family="{MONO}" font-size="11" fill="{MUTED}">more</text></g>'
 save("04-heatmap.svg",body,fonts,W,h,f"Contribution graph: {total:,} contributions")
def repo_card(i,r,fonts):
 w=W/3-8; h=182; name=r.get("name","Featured project"); desc=r.get("description") or "A project built to solve a real problem."; lang=r.get("language") or "Software"; stars=int(r.get("stargazers_count",0) or 0)
 color=[BLUE,RED,YELLOW][i%3]; meta=f"{lang} · ★ {stars}" if stars else f"{lang} · in progress"
 desc_svg=textlines(24,76,wrap(desc,34)[:4],20,f'font-family="{SANS}" font-size="13.5" fill="{SOFT}"')
 body=f'<rect width="{w}" height="{h}" rx="14" fill="{PAPER}"/><g class="r" {D(4.6+i*.12)}><rect x="24" y="28" width="8" height="8" rx="2" fill="{color}"/>{T(42,38,name,17,600,INK,SANS)}{desc_svg}{T(24,h-22,meta,10,400,MUTED,MONO)}</g>'
 save(f"project-{i+1:02d}.svg",body,fonts,w+8,h,f"{name}: {desc}")
def section_title(fonts):
 body=f"<text class=\"r\" {D(4.4)} x=\"2\" y=\"46\" font-family=\"{SERIF}\" font-size=\"34\" fill=\"{INK}\">What I'm <tspan font-style=\"italic\">coding</tspan></text>"
 save("title-coding.svg",body,fonts,W,64,"What I'm coding")

def main():
 ensure_fonts(); data=json.loads(DATA.read_text(encoding="utf-8")); rows=daily_rows(data)
 chars=json.dumps(data,ensure_ascii=False)+"0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz .,;:!?/+-_()[]↗∞·★"
 fonts=font_css(chars); OUT.mkdir(parents=True,exist_ok=True)
 hero(fonts); heatmap(rows,fonts); activity(rows,fonts)
 tile("02-tile-1.svg","BUILD",BLUE,"#FFFFFF","01","AI products, apps and practical engineering.",3.10,fonts)
 tile("02-tile-2.svg","CREATE",RED,"#FFFFFF","02","Thoughtful interfaces, visual design and digital experiences.",3.35,fonts)
 tile("02-tile-3.svg","LEARN",YELLOW,INK,"03","Exploring new tools, ideas and emerging technology.",3.60,fonts)
 for i,r in enumerate(data.get("featured_repos",[])[:8]):repo_card(i,r,fonts)
 print(f"Rendered {len(list(OUT.glob('*.svg')))} SVG cards (STATIC={int(STATIC)}).")
if __name__=="__main__":main()
