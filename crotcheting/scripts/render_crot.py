# render_crot.py — python render_crot.py pins.json photo_dir out_dir [id ...]
# 1000x1500 Crotcheting-style pins: full-bleed photo, arched script title, "PDF PATTERN", outlined pill, CROTCHETING mark.
import base64, json, os, sys
from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.abspath(__file__))
F = os.path.join(os.path.dirname(ROOT), "fonts")
if not os.path.isdir(F):
    F = os.path.join(os.path.dirname(ROOT), "fonts")

def b64(p):
    return base64.b64encode(open(p, "rb").read()).decode()

FONTS = "".join(
    f"@font-face{{font-family:'{n}';src:url(data:font/woff2;base64,{b64(os.path.join(F, f))}) format('woff2');}}"
    for n, f in (("Script", "leckerli-one-latin-400-normal.woff2"),
                 ("Lilita", "lilita-one-latin-400-normal.woff2"),
                 ("Archivo", "archivo-black-latin-400-normal.woff2")))

# The Etsy main photo carries its own title in the top band; crop it away.
CROP_TOP = 0.18

def edge_colors(photo):
    from PIL import Image, ImageStat
    im = Image.open(photo).convert("RGB"); w, h = im.size
    def avg(box):
        return ImageStat.Stat(im.crop(box)).mean
    top = avg((0, int(h*.19), w, int(h*.24)))
    bot = avg((0, int(h*.90), w, h))
    hexc = lambda c: "#%02x%02x%02x" % tuple(int(max(0, min(255, v))) for v in c)
    return hexc(top), hexc(bot)

def html(pin, photo):
    img = b64(photo)
    top, bot = edge_colors(photo)
    title = pin["image_title"]
    pill = pin["pill"]
    return f"""<!DOCTYPE html><html><head><style>{FONTS}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:1000px;height:1500px;overflow:hidden;position:relative;background:#e9dccd}}
.bg{{position:absolute;inset:0;background:linear-gradient(to bottom,{top} 0%,{top} 30%,{bot} 75%,{bot} 100%)}}
.ph{{position:absolute;left:-330px;right:-330px;top:350px;height:960px;
  background:url(data:image/jpeg;base64,{img}) no-repeat;background-size:1660px auto;background-position:center {-1660*801/1080*CROP_TOP:.0f}px;
  -webkit-mask-image:linear-gradient(to bottom,transparent 0,rgba(0,0,0,.6) 70px,#000 150px,#000 800px,transparent 960px),
                     linear-gradient(to right,transparent 0,#000 260px,#000 1400px,transparent 1660px);
  -webkit-mask-composite:source-in;mask-composite:intersect}}
svg.t{{position:absolute;left:0;top:40px;width:1000px;height:380px;overflow:visible}}
.tt{{font-family:'Script';fill:#fff;filter:drop-shadow(0 3px 6px rgba(70,40,20,.35))}}
.sub{{font-family:'Lilita';fill:#fff;letter-spacing:3px;filter:drop-shadow(0 2px 4px rgba(70,40,20,.35))}}
.pill{{position:absolute;left:0;right:0;top:1258px;text-align:center}}
.pill span{{display:inline-block;min-width:440px;padding:6px 46px 12px;border:5px solid #fff;border-radius:60px;
  font-family:'Script';font-size:52px;color:#fff;text-shadow:0 2px 8px rgba(60,35,15,.5);box-shadow:0 2px 8px rgba(70,40,20,.15);background:rgba(60,35,15,.10)}}
.logo{{position:absolute;left:0;right:0;top:1372px;text-align:center;color:#fff;filter:drop-shadow(0 2px 6px rgba(50,30,10,.5))}}
.logo .w{{font-family:'Archivo';font-size:66px;font-style:italic;transform:skewX(-8deg);display:inline-block;letter-spacing:1px;line-height:1}}
.logo .s{{font-family:'Archivo';font-size:15px;letter-spacing:4px;margin-top:6px;display:flex;align-items:center;justify-content:center;gap:16px}}
.logo .s i{{display:inline-block;width:150px;height:2px;background:#fff}}
</style></head><body>
<div class="bg"></div><div class="ph"></div>
<svg class="t" viewBox="0 0 1000 380">
 <defs><path id="arc" d="M 60,330 Q 500,40 940,330"/><path id="arc2" d="M 290,375 Q 500,250 710,375"/></defs>
 <text class="tt" id="tt" font-size="118" text-anchor="middle"><textPath href="#arc" startOffset="50%">{title}</textPath></text>
 <text class="sub" font-size="40" text-anchor="middle"><textPath href="#arc2" startOffset="50%">PDF PATTERN</textPath></text>
</svg>
<div class="pill"><span>{pill}</span></div>
<div class="logo"><div class="w">CROTCHETING</div><div class="s"><i></i>CROCHET PATTERNS<i></i></div></div>
</body></html>"""

FIT = """async () => { await document.fonts.ready;
 const t=document.getElementById('tt'); const arc=document.getElementById('arc'); const L=arc.getTotalLength();
 let s=118; t.setAttribute('font-size',s);
 while(t.getComputedTextLength()>L*0.92 && s>60){ s-=3; t.setAttribute('font-size',s); } }"""

def main():
    src, photodir, outdir = sys.argv[1:4]
    only = set(sys.argv[4:])
    pins = json.load(open(src, encoding="utf-8"))
    os.makedirs(outdir, exist_ok=True)
    n = 0
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=os.environ.get("CHROME_PATH", "/usr/bin/google-chrome"))
        pg = b.new_page(viewport={"width": 1000, "height": 1500})
        for pin in pins:
            if only and pin["id"] not in only:
                continue
            photo = os.path.join(photodir, pin["id"] + ".jpg")
            if not os.path.exists(photo):
                print("missing photo", pin["id"]); continue
            pg.set_content(html(pin, photo))
            pg.evaluate(FIT)
            pg.screenshot(path=os.path.join(outdir, pin["file"]), type="jpeg", quality=88)
            n += 1
        b.close()
    print("rendered", n)

if __name__ == "__main__":
    main()
