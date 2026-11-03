#!/usr/bin/env python3
"""Download exhibition-owner-authorized artwork previews for Daegu Art 40.
Runs within GitHub Actions with internet access. Saves exact image URLs only.
Never substitutes a different artist or mismatched work. Failures are logged.
"""
import json, io, time, urllib.request
from pathlib import Path
from PIL import Image, ImageOps
ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"data/artists.json"
DEST=ROOT/"assets/artworks"
DEST.mkdir(parents=True,exist_ok=True)
data=json.loads(DATA.read_text(encoding="utf-8"))
report=[]
for item in data["artists"]:
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
            im.thumbnail((1500,1500),Image.Resampling.LANCZOS)
            im.save(path,"WEBP",quality=86,method=6)
        item["image"]="assets/artworks/"+path.name
        item["image_status"]="GitHub 저장 파일 등록 완료"
        report.append({"artist":item["name"],"status":"downloaded","file":item["image"],"bytes":path.stat().st_size})
    except Exception as exc:
        item["image_status"]="이미지 다운로드 오류 — 공개 출처 링크 확인"
        report.append({"artist":item["name"],"status":"failed","error":str(exc)[:250]})
    time.sleep(.2)

DATA.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
INDEX=ROOT/"index.html"
html=INDEX.read_text(encoding="utf-8")
start=html.index("const data=")
stop=html.index(";const museumWorks=",start)
museum={"rooms":[{"title":r["title"],"count":r["count"]} for r in data["rooms"]],"artists":[]}
for x in data["artists"]:
    museum["artists"].append({"id":str(x["order"]).zfill(2),"name":x["name"],"theme":x["theme"],"room":int(x["room"]),"roomTitle":x["room_title"],"image":x.get("image",""),"biography":x.get("biography",""),"critique":x.get("critique",""),"work":x.get("work",{}),"workReview":x.get("work_review",""),"image_source":x.get("image_source_url",""),"image_credit":x.get("image_attribution_url","")})
payload=json.dumps(museum,ensure_ascii=False,separators=(",",":")).replace("<","\\u003c")
html=html[:start]+"const data="+payload+html[stop:]
INDEX.write_text(html,encoding="utf-8")
(ROOT/"data/image_report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("WORKS SAVED:",sum(r["status"] in ("downloaded","cached") for r in report))
for r in report:print(r)
