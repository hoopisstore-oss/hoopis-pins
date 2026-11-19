# render_pins.py — python3 render_pins.py pins.json photo_dir out_dir [id ...]
# Renders 1000x1500 Pinterest pin JPEGs from listing photos + themed template.
import json, math, random, sys, os, base64
from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.abspath(__file__))
F = os.path.join(os.path.dirname(ROOT), "fonts") if os.path.basename(ROOT) == "scripts" else ROOT + "/fonts"

def font_b64(path):
    return base64.b64encode(open(path, "rb").read()).decode()

FONTS = f"""
@font-face{{font-family:'Fraunces';font-weight:900;src:url(data:font/woff2;base64,{font_b64(F+'/fraunces-latin-900-normal.woff2')}) format('woff2');}}
@font-face{{font-family:'Patrick';font-weight:400;src:url(data:font/woff2;base64,{font_b64(F+'/patrick-hand-latin-400-normal.woff2')}) format('woff2');}}
@font-face{{font-family:'Mont';font-weight:700;src:url(data:font/woff2;base64,{font_b64(F+'/montserrat-latin-700-normal.woff2')}) format('woff2');}}
"""

THEMES = {
  # bg, primary (title 1), accent (title 2), decor colours, eyebrow, decor style
  "nature":    dict(bg="#F4EDE0", p="#3E5A38", a="#B8613D", d=["#4F7A45", "#6E9460", "#B8613D", "#D59A75"], eyebrow="CREATIVE DIY PROJECTS", deco="leaves"),
  "christmas": dict(bg="#F6EFE4", p="#1F4D36", a="#B3261E", d=["#2E6B47", "#3F8558", "#B3261E", "#D9A441"], eyebrow="COZY CHRISTMAS STITCHING", deco="holly"),
  "animals":   dict(bg="#F5EEE3", p="#4E3B2D", a="#C77A3E", d=["#7A9A6A", "#A7BE93", "#C77A3E", "#E3B48A"], eyebrow="CUTE DIY STITCHING", deco="paws"),
  "birds":     dict(bg="#EEF1EA", p="#2C4A57", a="#C0583B", d=["#5D8A74", "#87AE95", "#C0583B", "#E39A7E"], eyebrow="CREATIVE DIY PROJECTS", deco="berries"),
  "buildings": dict(bg="#F3ECE2", p="#2D3A5A", a="#C2603F", d=["#2D3A5A", "#C2603F", "#E9C46A", "#7FA59A"], eyebrow="COZY STOREFRONT STITCHING", deco="awning"),
  "black":     dict(bg="#F3F0EA", p="#1C1C1C", a="#9B7838", d=["#1C1C1C", "#3A3A3A", "#9B7838", "#C8B07A"], eyebrow="MODERN MONOCHROME DIY", deco="blackleaves"),
  "valentine": dict(bg="#FBEFEE", p="#8C2B3E", a="#D95E74", d=["#D95E74", "#EE9AA8", "#8C2B3E", "#F4C6CD"], eyebrow="SWEET VALENTINE DIY", deco="hearts"),
  "kitchen":   dict(bg="#F1F0EB", p="#284778", a="#C49A3E", d=["#284778", "#5E7FB5", "#C49A3E", "#A9BEDF"], eyebrow="COZY KITCHEN DIY", deco="bluefloral"),
  "halloween": dict(bg="#F3E8DA", p="#2A2230", a="#D86F24", d=["#2A2230", "#D86F24", "#F0A24A", "#6B8F4E"], eyebrow="SPOOKY-CUTE DIY PROJECTS", deco="bats"),
  "autumn":    dict(bg="#F5ECDF", p="#6A3A1E", a="#C8622A", d=["#C8622A", "#E0A23C", "#9E3E22", "#7D8B46"], eyebrow="COZY FALL DIY PROJECTS", deco="maple"),
  "modern":    dict(bg="#F1EEE8", p="#2F3B45", a="#C47A47", d=["#C47A47", "#7E9C8F", "#2F3B45", "#E2B98F"], eyebrow="MODERN DIY PROJECTS", deco="shapes"),
}

def leaf(x, y, ang, s, col):
    return (f'<path transform="translate({x:.1f},{y:.1f}) rotate({ang:.1f}) scale({s:.2f})" '
            f'd="M0,0 C18,-17 58,-19 86,0 C58,19 18,17 0,0 Z" fill="{col}"/>'
            f'<path transform="translate({x:.1f},{y:.1f}) rotate({ang:.1f}) scale({s:.2f})" d="M4,0 L78,0" '
            f'stroke="rgba(0,0,0,.18)" stroke-width="2" fill="none"/>')

def sprig(x, y, ang, length, n, cols, s=1.0, rnd=None):
    rnd = rnd or random.Random(1)
    out = []
    ex, ey = x + length * math.cos(math.radians(ang)), y + length * math.sin(math.radians(ang))
    out.append(f'<path d="M{x:.1f},{y:.1f} Q{(x+ex)/2+12:.1f},{(y+ey)/2-12:.1f} {ex:.1f},{ey:.1f}" stroke="{cols[0]}" stroke-width="5" fill="none" stroke-linecap="round"/>')
    for i in range(n):
        t = (i + 1) / (n + 1)
        px, py = x + (ex - x) * t, y + (ey - y) * t
        side = 1 if i % 2 else -1
        out.append(leaf(px, py, ang + side * 48 + rnd.uniform(-8, 8), s * (1.15 - 0.4 * t), cols[i % 2]))
    out.append(leaf(ex, ey, ang, s * 0.8, cols[1]))
    return "".join(out)

def holly_leaf(x, y, ang, s, col):
    d = "M0,0 L12,-12 L22,-6 L32,-18 L42,-8 L54,-16 L60,-4 L72,-6 L80,0 L72,6 L60,4 L54,16 L42,8 L32,18 L22,6 L12,12 Z"
    return f'<path transform="translate({x},{y}) rotate({ang}) scale({s})" d="{d}" fill="{col}"/>'

def snowflake(x, y, r, col):
    arms = "".join(f'<line x1="{x}" y1="{y}" x2="{x+r*math.cos(math.radians(a)):.1f}" y2="{y+r*math.sin(math.radians(a)):.1f}" stroke="{col}" stroke-width="3" stroke-linecap="round"/>' for a in range(0, 360, 60))
    return arms

def heart(x, y, s, col, ang=0):
    return f'<path transform="translate({x},{y}) rotate({ang}) scale({s})" d="M0,10 C0,-6 22,-6 22,8 C22,-6 44,-6 44,10 C44,26 22,36 22,44 C22,36 0,26 0,10 Z" fill="{col}"/>'

def maple(x, y, s, col, ang=0):
    d = "M0,-40 L8,-22 L22,-30 L18,-10 L38,-14 L28,2 L40,10 L16,12 L18,30 L4,20 L0,40 L-4,20 L-18,30 L-16,12 L-40,10 L-28,2 L-38,-14 L-18,-10 L-22,-30 L-8,-22 Z"
    return f'<path transform="translate({x},{y}) rotate({ang}) scale({s})" d="{d}" fill="{col}"/><line transform="translate({x},{y}) rotate({ang}) scale({s})" x1="0" y1="10" x2="0" y2="62" stroke="{col}" stroke-width="4"/>'

def bat(x, y, s, col, ang=0):
    d = "M0,0 C-8,-10 -18,-10 -26,-4 C-34,-14 -48,-14 -58,-6 C-50,-2 -46,6 -48,12 C-40,6 -30,8 -24,14 C-18,6 -8,6 0,10 C8,6 18,6 24,14 C30,8 40,6 48,12 C46,6 50,-2 58,-6 C48,-14 34,-14 26,-4 C18,-10 8,-10 0,0 Z"
    return f'<path transform="translate({x},{y}) rotate({ang}) scale({s})" d="{d}" fill="{col}"/>'

def pumpkin(x, y, s, col, stem):
    return (f'<g transform="translate({x},{y}) scale({s})"><ellipse cx="-14" cy="0" rx="20" ry="26" fill="{col}"/><ellipse cx="14" cy="0" rx="20" ry="26" fill="{col}"/>'
            f'<ellipse cx="0" cy="0" rx="18" ry="28" fill="{col}" stroke="rgba(0,0,0,.15)" stroke-width="2"/><rect x="-3" y="-38" width="7" height="14" rx="2" fill="{stem}"/></g>')

def paw(x, y, s, col, ang=0):
    return (f'<g transform="translate({x},{y}) rotate({ang}) scale({s})" fill="{col}"><ellipse cx="0" cy="10" rx="16" ry="13"/>'
            f'<circle cx="-17" cy="-8" r="7"/><circle cx="-6" cy="-18" r="7"/><circle cx="7" cy="-18" r="7"/><circle cx="18" cy="-8" r="7"/></g>')

def star(x, y, r, col):
    pts = []
    for i in range(10):
        rr = r if i % 2 == 0 else r * 0.45
        a = math.radians(-90 + i * 36)
        pts.append(f"{x+rr*math.cos(a):.1f},{y+rr*math.sin(a):.1f}")
    return f'<polygon points="{" ".join(pts)}" fill="{col}"/>'

def blob(x, y, r, col, op=0.85):
    return f'<circle cx="{x}" cy="{y}" r="{r}" fill="{col}" opacity="{op}"/>'

def decor(theme, seed):
    t = THEMES[theme]; d = t["d"]; R = random.Random(seed); s = []
    style = t["deco"]
    if style in ("leaves", "blackleaves", "berries", "paws", "bluefloral"):
        if style != "blackleaves":
            s += [blob(60, 1450, 120, d[2], .55), blob(950, 1440, 105, d[3], .6)]
        s.append(sprig(-10, 0, 18, 150, 4, d[:2], 0.9, R))
        s.append(sprig(1010, 0, 162, 150, 4, d[:2], 0.9, R))
        s.append(sprig(-10, 1500, -40, 250, 5, d[:2], 1.0, R))
        s.append(sprig(1010, 1500, -140, 250, 5, d[:2], 1.0, R))
        if style == "berries":
            for (bx, by) in [(70, 90), (95, 75), (905, 80), (930, 95), (130, 1360), (880, 1365)]:
                s.append(f'<circle cx="{bx}" cy="{by}" r="11" fill="{d[2]}"/>')
        if style == "paws":
            for (px, py, a) in [(940, 260, 20), (95, 1235, -20), (930, 1290, 15)]:
                s.append(paw(px, py, 0.9, d[3], a))
        if style == "bluefloral":
            for (fx, fy) in [(60, 70), (940, 70), (140, 1360), (870, 1350)]:
                for k in range(5):
                    a = math.radians(k * 72)
                    s.append(f'<circle cx="{fx+16*math.cos(a):.1f}" cy="{fy+16*math.sin(a):.1f}" r="12" fill="{d[1]}"/>')
                s.append(f'<circle cx="{fx}" cy="{fy}" r="8" fill="{d[2]}"/>')
    elif style == "holly":
        s += [blob(60, 1450, 115, d[2], .18), blob(950, 1445, 100, d[3], .25)]
        for (x, y, a) in [(10, 40, 15), (60, 20, -20), (990, 40, 165), (940, 20, 200), (10, 1430, -15), (990, 1430, -165), (40, 1360, -55), (960, 1360, -125), (110, 1480, -80), (890, 1480, -100)]:
            s.append(holly_leaf(x, y, a, 1.25, d[R.randint(0, 1)]))
        for (bx, by) in [(105, 95), (125, 112), (98, 120), (895, 95), (875, 112), (902, 120), (110, 1390), (130, 1372), (890, 1390), (870, 1372)]:
            s.append(f'<circle cx="{bx}" cy="{by}" r="12" fill="{d[2]}"/>')
        for _ in range(10):
            s.append(snowflake(R.choice([R.randint(30, 160), R.randint(840, 970)]), R.randint(220, 1250), R.randint(10, 18), "#C9D6DF"))
    elif style == "hearts":
        for _ in range(16):
            x = R.choice([R.randint(10, 90), R.randint(880, 950)]); y = R.choice([R.randint(10, 60), R.randint(1240, 1460)])
            s.append(heart(x, y, R.uniform(.7, 1.6), R.choice(d), R.randint(-30, 30)))
    elif style == "bats":
        s += [blob(60, 1450, 115, d[1], .35), blob(950, 1445, 100, d[2], .35)]
        for (x, y, sc, a) in [(70, 50, 1.0, -12), (930, 50, 1.0, 14), (60, 1250, .7, -8), (930, 1330, .7, 8)]:
            s.append(bat(x, y, sc, d[0], a))
        for (x, y, sc) in [(90, 1400, 1.5), (190, 1440, 1.0), (910, 1405, 1.4)]:
            s.append(pumpkin(x, y, sc, d[1], d[3]))
        for _ in range(8):
            s.append(star(R.choice([R.randint(30, 170), R.randint(830, 970)]), R.randint(200, 1200), R.randint(6, 11), d[2]))
    elif style == "maple":
        for _ in range(14):
            x = R.choice([R.randint(20, 100), R.randint(900, 980)]); y = R.choice([R.randint(20, 70), R.randint(1240, 1480)])
            s.append(maple(x, y, R.uniform(.9, 1.6), R.choice(d), R.randint(-40, 40)))
    elif style == "awning":
        w = 1000 / 10
        for i in range(10):
            col = d[1] if i % 2 == 0 else "#FFFFFF"
            s.append(f'<path d="M{i*w},0 H{(i+1)*w} V46 A{w/2},{w/2*0.55} 0 0 1 {i*w},46 Z" fill="{col}"/>')
        s.append(f'<rect x="0" y="0" width="1000" height="14" fill="{d[0]}"/>')
        for _ in range(12):
            s.append(star(R.choice([R.randint(40, 170), R.randint(830, 960)]), R.randint(140, 1250), R.randint(7, 13), d[2]))
        s += [blob(60, 1450, 115, d[3], .45), blob(950, 1445, 100, d[2], .45)]
    elif style == "shapes":
        s += [f'<path d="M-40,250 A160,160 0 0 1 280,250 Z" fill="{d[0]}" opacity=".8" transform="translate(-60,-170)"/>',
              f'<circle cx="940" cy="70" r="110" fill="{d[1]}" opacity=".7"/>',
              f'<path d="M780,1500 A170,170 0 0 1 1120,1500 Z" fill="{d[3]}" opacity=".9"/>',
              f'<rect x="-30" y="1330" width="200" height="200" rx="100" fill="{d[1]}" opacity=".55"/>']
    return "".join(s)

PUSHPIN = '<svg width="34" height="34" viewBox="0 0 24 24"><path fill="{c}" d="M14.5 2.5l7 7-2.2 1-3.6 3.6.6 4.4-1.5 1.5-4-4-5.3 5.3-1.4-1.4 5.3-5.3-4-4 1.5-1.5 4.4.6L15 6.1z"/></svg>'

def html_for(pin, photo_path):
    t = THEMES[pin["theme"]]
    img = base64.b64encode(open(photo_path, "rb").read()).decode()
    eyebrow = pin.get("eyebrow") or t["eyebrow"]
    tag = pin.get("tagline", "A Cozy Weekend Stitching Project")
    return f"""<!DOCTYPE html><html><head><style>{FONTS}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:1000px;height:1500px;background:{t['bg']};position:relative;overflow:hidden;font-family:'Mont'}}
.deco{{position:absolute;inset:0;z-index:0}}
.c{{position:absolute;left:0;right:0;text-align:center;z-index:2}}
.eb{{top:{108 if t['deco']=='awning' else 78}px;font-size:28px;letter-spacing:.2em;color:{t['p']}}}
.t1,.t2{{font-family:'Fraunces';font-weight:900;text-transform:uppercase;line-height:1;white-space:nowrap;letter-spacing:.01em}}
.t1{{top:{150 if t['deco']=='awning' else 122}px;color:{t['p']}}}
.t2{{top:{258 if t['deco']=='awning' else 232}px;color:{t['a']}}}
.tag{{top:{372 if t['deco']=='awning' else 346}px}}
.tag span{{display:inline-block;background:{t['bg']};color:{t['p']};font-size:34px;letter-spacing:.16em;padding:10px 26px 8px;border-radius:6px;box-shadow:0 2px 0 rgba(0,0,0,.05)}}
.photo{{position:absolute;left:100px;top:{404 if t['deco']=='awning' else 378}px;width:800px;height:800px;border-radius:26px;overflow:hidden;z-index:1;
  box-shadow:0 18px 40px rgba(40,30,20,.22);border:10px solid #fff;background:#fff}}
.photo img{{width:100%;height:100%;object-fit:cover;display:block}}
.tl{{top:1222px;font-family:'Patrick';font-size:58px;line-height:1.05;color:{t['p']};padding:0 120px}}
.pill{{top:1372px}}
.pill span{{display:inline-flex;align-items:center;gap:12px;background:{t['a']};color:#fff;font-size:26px;letter-spacing:.12em;padding:14px 34px;border-radius:40px}}
.site{{top:1450px;font-size:17px;letter-spacing:.22em;color:{t['p']};opacity:.75}}
</style></head><body>
<svg class="deco" width="1000" height="1500" viewBox="0 0 1000 1500">{decor(pin['theme'], int(pin['id']))}</svg>
<div class="c eb">{eyebrow}</div>
<div class="c t1"><span id="t1">{pin['subject']}</span></div>
<div class="c t2"><span id="t2">CROSS STITCH</span></div>
<div class="photo"><img src="data:image/jpeg;base64,{img}"></div>
<div class="c tag"><span>PATTERN</span></div>
<div class="c tl" id="tl">{tag}</div>
<div class="c pill"><span>SAVE TO TRY LATER {PUSHPIN.format(c='#fff')}</span></div>
<div class="c site">HOOPIS STITCH · INSTANT PDF DOWNLOAD</div>
</body></html>"""

FIT = """async () => { await document.fonts.ready;
function fit(id,max,maxW){const e=document.getElementById(id);let s=max;e.style.fontSize=s+'px';
 while(e.getBoundingClientRect().width>maxW&&s>40){s-=2;e.style.fontSize=s+'px';} return s;}
const a=fit('t1',108,740); const b=fit('t2',108,740);
document.getElementById('t2').style.fontSize=Math.min(b,Math.max(a,84))+'px';
const tl=document.getElementById('tl'); let fs=58; tl.style.fontSize=fs+'px';
while(tl.getBoundingClientRect().height>130&&fs>40){fs-=2;tl.style.fontSize=fs+'px';} }"""

def main():
    src, photodir, outdir = sys.argv[1], sys.argv[2], sys.argv[3]
    only = set(sys.argv[4:])
    pins = json.load(open(src, encoding="utf-8"))
    os.makedirs(outdir, exist_ok=True)
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=os.environ.get("CHROME_PATH", "/usr/bin/google-chrome"))
        pg = b.new_page(viewport={"width": 1000, "height": 1500})
        n = 0
        for pin in pins:
            if only and pin["id"] not in only:
                continue
            photo = f"{photodir}/{pin['id']}.jpg"
            if not os.path.exists(photo):
                print("missing photo", pin["id"]); continue
            pg.set_content(html_for(pin, photo))
            pg.evaluate("document.fonts.ready")
            pg.evaluate(FIT)
            pg.screenshot(path=f"{outdir}/{pin['file']}", type="jpeg", quality=90)
            n += 1
        b.close()
    print("rendered", n)

if __name__ == "__main__":
    main()
