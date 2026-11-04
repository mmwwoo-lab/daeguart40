#!/usr/bin/env python3
"""Download curator-authorized artwork previews for Daegu Art 40.
Runs within GitHub Actions with internet access. Saves exact image URLs only.
Never substitutes a different artist or mismatched work. Failures are logged.
"""
import json, io, time, urllib.request, re
from pathlib import Path
from PIL import Image, ImageOps
ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"data/artists.json"
DEST=ROOT/"assets/artworks"
DEST.mkdir(parents=True,exist_ok=True)
data=json.loads(DATA.read_text(encoding="utf-8"))
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit
import html as htmlmod
class ImageExtractor(HTMLParser):
    def __init__(self):
        super().__init__(); self.images=[]
    def handle_starttag(self,tag,attrs):
        if tag not in ("img","source"):return
        x=dict(attrs)
        label=htmlmod.unescape(x.get("alt","")+" "+x.get("title",""))
        urls=[x.get(k,"") for k in ("data-original","data-src","data-lazy-src","src")]
        self.images.append((label,[u for u in urls if u]))
def find_exact_captions(article,artist,title):
    try:
        req=urllib.request.Request(article,headers={"User-Agent":"Mozilla/5.0","Accept":"text/html"})
        with urllib.request.urlopen(req,timeout=18) as resp:
            raw=resp.read(4_000_000)
        doc=raw.decode("utf-8","replace")
        parser=ImageExtractor();parser.feed(doc)
        matches=[]
        for label,urls in parser.images:
            if title.lower() not in label.lower() or artist.lower() not in label.lower():continue
            for u in urls:
                u=urljoin(article,htmlmod.unescape(u))
                if u.startswith("https://") and not u.lower().endswith(".svg"):
                    matches.append((label,u))
        return matches
    except Exception as exc:
        print("CAPTION SCRAPE ERROR",artist,str(exc)[:180])
        return []

report=[]
for item in data["artists"]:
    if not item.get("image_source_url") and item.get("image_article_source") and item.get("image_expected_caption"):
        exact=find_exact_captions(item["image_article_source"],item["name"],item["image_expected_caption"])
        print("ARTICLE IMAGE MATCH",item["name"],len(exact),[(a[:85],u[:100]) for a,u in exact[:4]])
        if len(exact)==1:
            item["image_source_url"]=exact[0][1]
            item["image_attribution_url"]=item["image_article_source"]
            item["image_status"]="신문 이미지 alt에 작가명·작품명 일치 확인"
    url=item.get("image_source_url","")
    if not url.startswith("https://"):continue
    path=DEST/("artist-%02d.webp"%item["order"])
    if path.exists():
        item["image"]="assets/artworks/"+path.name
        report.append({"artist":item["name"],"status":"cached"})
        continue
    try:
        req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0 (Daegu Art Exhibition; artwork authorized)","Accept":"image/avif,image/webp,image/*,*/*;q=0.8"})
        with urllib.request.urlopen(req,timeout=18) as f:
            mimetype=f.headers.get("Content-Type","")
            raw=f.read(15*1024*1024+1)
        if len(raw)>15*1024*1024:raise ValueError("Too large")
        if mimetype and not mimetype.startswith("image/"):raise ValueError("Not image: "+mimetype)
        with Image.open(io.BytesIO(raw)) as im:
            im=ImageOps.exif_transpose(im).convert("RGB")
            if im.width<220 or im.height<170:raise ValueError("Image too small")
            # Preserve artwork aspect ratio when preparing the web preview.
            im.thumbnail((1500,1500),Image.Resampling.LANCZOS)
            im.save(path,"WEBP",quality=86,method=6)
        item["image"]="assets/artworks/"+path.name
        item["image_status"]="GitHub 저장 파일 등록 완료"
        report.append({"artist":item["name"],"status":"downloaded","file":item["image"],"bytes":path.stat().st_size})
    except Exception as exc:
        item["image_status"]="이미지 다운로드 오류 — 공개 출처 링크 확인"
        report.append({"artist":item["name"],"status":"failed","error":str(exc)[:250]})
    time.sleep(.15)

DATA.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
INDEX=ROOT/"index.html"
html=INDEX.read_text(encoding="utf-8")
start=html.index("const data=")
stop=html.index(";const artists=data.artists",start)
museum={"rooms":[{"title":r["title"],"count":r["count"]} for r in data["rooms"]],"artists":[]}
for x in data["artists"]:
    museum["artists"].append({"id":str(x["order"]).zfill(2),"name":x["name"],"theme":x["theme"],"room":int(x["room"]),"roomTitle":x["room_title"],"image":x.get("image",""),"biography":x.get("biography",""),"critique":x.get("critique",""),"work":x.get("work",{}),"workReview":x.get("work_review",""),"image_source":x.get("image_source_url",""),"image_credit":x.get("image_attribution_url",""),"image_note":x.get("image_note","")})
payload=json.dumps(museum,ensure_ascii=False,separators=(",",":")).replace("<","\\u003c")
html=html[:start]+"const data="+payload+html[stop:]
work_total=sum(bool(x.get("work",{}).get("title")) for x in data["artists"])
image_total=sum(bool(x.get("image","")) for x in data["artists"])
html=re.sub(r"작가 소개·평론 40인, 작품 제원 \\d+건, 작품 이미지 \\d+점",f"작가 소개·평론 40인, 작품 제원 {work_total}건, 작품 이미지 {image_total}점",html)
INDEX.write_text(html,encoding="utf-8")
(ROOT/"data/image_report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("ARTWORK IMAGE FILES: ",sum(r["status"] in ("downloaded","cached") for r in report))
for r in report:print(r)
