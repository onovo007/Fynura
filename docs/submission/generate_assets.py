"""Regenerate code-native architecture SVG and PNG.

Run from the repository root: python docs/submission/generate_assets.py
Requires Pillow. No network, model calls or edits to production assets.
"""
from pathlib import Path
from html import escape
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
W, H = 1920, 1080
im = Image.new('RGB', (W, H), '#f4f7f5')
d = ImageDraw.Draw(im)
svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">', '<rect width="1920" height="1080" fill="#f4f7f5"/>']

def font(size, bold=False):
    names = [Path('C:/Windows/Fonts') / ('arialbd.ttf' if bold else 'arial.ttf'),
             Path('/usr/share/fonts/truetype/dejavu') / ('DejaVuSans-Bold.ttf' if bold else 'DejaVuSans.ttf')]
    for name in names:
        if name.exists():
            return ImageFont.truetype(str(name), size)
    return ImageFont.load_default(size=size)

def text(x,y,value,size=23,color='#16352c',bold=False):
    d.text((x,y),value,font=font(size,bold),fill=color)
    svg.append(f'<text x="{x}" y="{y+size*.92}" font-family="Arial, sans-serif" font-size="{size}" font-weight="{700 if bold else 400}" fill="{color}">{escape(value)}</text>')

def rect(x,y,w,h,fill='#ffffff',stroke='#c9d9d0',radius=18):
    d.rounded_rectangle((x,y,x+w,y+h),radius=radius,fill=fill,outline=stroke,width=2)
    svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" fill="{fill}" stroke="{stroke}" stroke-width="2"/>')

def box(x,y,w,h,title,lines,fill='#ffffff'):
    rect(x,y,w,h,fill)
    title_size=25
    while d.textlength(title,font=font(title_size,True))>w-44:
        title_size-=1
    text(x+22,y+16,title,title_size,bold=True)
    for i,line in enumerate(lines):
        size=21
        while d.textlength(line,font=font(size))>w-44:
            size-=1
        text(x+22,y+58+i*30,line,size)

def arrow(x1,y1,x2,y2,color='#168664'):
    import math
    d.line((x1,y1,x2,y2),fill=color,width=4)
    a=math.atan2(y2-y1,x2-x1)
    pts=[(x2,y2),(x2-13*math.cos(a-.5),y2-13*math.sin(a-.5)),(x2-13*math.cos(a+.5),y2-13*math.sin(a+.5))]
    d.polygon(pts,fill=color)
    svg.append(f'<path d="M{x1},{y1} L{x2},{y2}" stroke="{color}" stroke-width="4"/><polygon points="'+ ' '.join(f'{x},{y}' for x,y in pts)+f'" fill="{color}"/>')

text(55,35,'FYNURA',48,bold=True)
text(55,100,'Traceable surveillance. Source-grounded research.',29)
text(1320,55,'PRODUCTION ARCHITECTURE',21,bold=True)
text(1320,89,'31 AUG 2026',21)

rect(360,160,1175,770,'#eaf3ef','#97b9a8',24)
text(390,178,'GOOGLE CLOUD',29,bold=True)
text(390,220,'Cloud Run hosts API + frontend; managed services connect below.',24)

box(35,275,295,190,'STRUCTURED INPUTS',['Selected WHO reports','Cholera / Measles / Ebola','HTTP retrieval + parsing'])
box(35,515,295,170,'HISTORICAL FILES',['WHO / CDC archives','OWID WHO-derived data','Bundled snapshots'])
box(35,750,295,150,'SEARCH SOURCES',['Official authorities first','News as labeled context'])

box(395,280,515,145,'Cloud Scheduler → RefreshService',['OIDC-validated refresh; lease + due time','Cached evidence retained on failure'])
box(395,465,515,180,'Deterministic evidence processing',['WHO adapters → typed observations','Compatibility grouping + guarded metrics','Provenance + heuristic confidence'])
box(395,685,515,155,'Firestore evidence store',['Chunked assessments + latest pointers','Application/session records'])
arrow(330,370,395,370)
arrow(650,425,650,465)
arrow(650,645,650,685)

box(955,280,545,190,'Shared intent → ADK research / review',['Question + audience + optional chart','Eight recent successful exchanges','Google Search; bounded provider retries','Grounding metadata → linked answer'])
box(955,515,545,155,'Vertex AI / Google GenAI SDK',['Gemini 3.7 Flash · global','Research and explanatory synthesis'])
box(955,710,545,130,'Historical analytics',['Country series + guarded period totals','Exploratory monthly measles CUSUM'])
arrow(1230,470,1230,515)
arrow(910,755,955,405)
text(395,850,'Store → research: supplementary evidence context',19)
text(390,893,'Identity: Firebase Auth   |   Config: Secret Manager   |   Operations: Cloud Logging',20)

box(1580,280,305,210,'BROWSER WORKSPACE',['Maps / charts / history','Ask Fynura + follow-ups','Source inspection','Briefs / infographic exports'])
box(1580,535,305,165,'GOOGLE SIGN-IN',['Verified Google identity','Country + consent','Application access session'])
box(1580,745,305,170,'PEOPLE',['Public / health professionals','Clinicians / researchers','Journalists / policymakers'])
arrow(1500,370,1580,370)
arrow(1500,770,1580,450)
arrow(1730,700,1730,745)

# Routed input connectors avoid running over component text.
def route(points,color):
    for (x1,y1),(x2,y2) in zip(points[:-2],points[1:-1]):
        d.line((x1,y1,x2,y2),fill=color,width=3)
        svg.append(f'<path d="M{x1},{y1} L{x2},{y2}" stroke="{color}" stroke-width="3"/>')
    arrow(*points[-2],*points[-1],color=color)
route([(330,600),(345,600),(345,875),(930,875),(930,780),(955,780)],'#168664')
route([(330,820),(352,820),(352,252),(932,252),(932,330),(955,330)],'#356ba2')

text(55,954,'Separate responsibilities: deterministic calculations own dashboard numbers; Gemini researches and explains.',24,bold=True)
text(55,996,'Build/deploy: Cloud Build + Artifact Registry. Archives are not continuously refreshed. Search does not update canonical snapshots.',21)
text(55,1032,'Verified production inference: Gemini 3.7 Flash on Vertex AI.',21,color='#35624e')
svg.append('</svg>')
(ROOT/'fynura_architecture.svg').write_text('\n'.join(svg),encoding='utf-8')
im.save(ROOT/'fynura_architecture.png')

print(f"Generated architecture SVG and PNG ({W}x{H}).")
