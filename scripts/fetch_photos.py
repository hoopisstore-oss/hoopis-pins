# fetch_photos.py — python fetch_photos.py data/pins.json photos
import json, os, sys, time, urllib.request
src, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)
pins = json.load(open(src, encoding="utf-8"))
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Safari/537.36"
failed = []
for p in pins:
    dest = f"{out}/{p['id']}.jpg"
    manual = f"photos_manual/{p['id']}.jpg"
    if os.path.exists(manual):
        open(dest, "wb").write(open(manual, "rb").read()); continue
    if os.path.exists(dest) and os.path.getsize(dest) > 5000:
        continue
    for attempt in range(4):
        try:
            req = urllib.request.Request(p["etsy_image"], headers={"User-Agent": UA, "Referer": "https://www.etsy.com/"})
            data = urllib.request.urlopen(req, timeout=30).read()
            if len(data) < 5000:
                raise ValueError(f"too small: {len(data)} bytes")
            open(dest, "wb").write(data)
            break
        except Exception as e:
            err = e
            time.sleep(2 + attempt * 3)
    else:
        try:  # fall back to the listing page's og:image
            import re
            html = urllib.request.urlopen(urllib.request.Request(f"https://www.etsy.com/listing/{p['id']}", headers={"User-Agent": UA}), timeout=30).read().decode("utf-8", "ignore")
            url = re.search(r'property="og:image" content="([^"]+)"', html).group(1)
            data = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=30).read()
            open(dest, "wb").write(data)
            print("fixed via listing page:", p["id"], url)
            open(f"{out}/FIXED_URLS.txt", "a").write(f"{p['id']} {url}\n")
        except Exception as e2:
            failed.append(f"{p['id']} {err} / {e2}")
    time.sleep(0.3)
print(f"photos ok: {len(pins) - len(failed)} / {len(pins)}")
if failed:
    print("FAILED:\n" + "\n".join(failed))
    open(f"{out}/FAILED.txt", "w").write("\n".join(failed))
