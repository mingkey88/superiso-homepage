#!/usr/bin/env python3
"""Resize the studio's source photography into responsive WebP sets.

Source JPEGs live outside the repo (see build/fetch_images.py). Output lands in
assets/img/<slug>/ and a manifest of intrinsic sizes is written to
data/image-sizes.json so templates can set width/height and avoid layout shift.
"""
import json, pathlib, sys
from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path("/tmp/siso/orig")
OUT = ROOT / "assets/img"
WIDTHS = [800, 1400, 2000]

data = json.loads((ROOT / "data/projects.json").read_text())
sizes = {}

for proj in data["projects"]:
    slug = proj["slug"]
    (OUT / slug).mkdir(parents=True, exist_ok=True)
    for img in proj["images"]:
        src = SRC / slug / img["file"]
        im = Image.open(src).convert("RGB")
        stem = img["file"].split(".")[0]
        # Drawings and renders are flat graphics; they need a little more quality.
        q = 88 if img["type"] in ("drawing", "render") else 82
        # Clamp each target to the source width and drop duplicates, so a
        # 1600px source still yields its full native size rather than stopping
        # at the last width below it.
        targets = sorted({min(w, im.width) for w in WIDTHS})
        made = []
        for w in targets:
            h = round(im.height * w / im.width)
            dest = OUT / slug / f"{stem}-{w}.webp"
            im.resize((w, h), Image.LANCZOS).save(dest, "WEBP", quality=q, method=6)
            made.append(w)
        sizes[f"{slug}/{img['file']}"] = {
            "w": im.width, "h": im.height, "widths": made,
            "ratio": round(im.width / im.height, 4),
        }
        print(f"  {slug}/{stem}  {im.width}x{im.height} -> {made}")

(ROOT / "data/image-sizes.json").write_text(json.dumps(sizes, indent=1))
print(f"\n{len(sizes)} images processed")
