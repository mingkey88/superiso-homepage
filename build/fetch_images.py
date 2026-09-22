#!/usr/bin/env python3
"""Download the studio's source photography from the live site.

Only needed when adding or refreshing a project — the optimised WebP files in
assets/img/ are committed, so a normal build does not require this step.

    python3 build/fetch_images.py [dest_dir]     # default: /tmp/siso/orig

Each project page repeats the studio logo as its first image; that one is
skipped. Afterwards run build/images.py against the same directory.
"""
import re, subprocess, sys, pathlib, json
from concurrent.futures import ThreadPoolExecutor

# Slug used on this site -> path on the studio's live site.
# "coutryard-house" is spelled that way on the source site.
SLUGS = {
    "resort-living": "resort-living",
    "childhood-memories": "childhood-memories",
    "house-on-house": "house-on-house",
    "courtyard-house": "coutryard-house",
    "k-m-apartment": "k-m-apartment",
    "terrace-apartment": "terrace-apartment",
    "chefs-fillet": "chefs-fillet",
    "secret-garden": "secret-garden",
}
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/125.0 Safari/537.36")
REFERER = "https://www.superisostudio.com/"
IMG = re.compile(r'https://lh[0-9a-z-]*\.googleusercontent\.com/sitesv-images-rt/[A-Za-z0-9_-]+=w\d+')

dest_root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "/tmp/siso/orig")


def page_images(path):
    """Return the image URLs on one project page, in document order."""
    url = f"https://www.superisostudio.com/projects/{path}"
    html = subprocess.run(["curl", "-sSL", "-A", UA, url],
                          capture_output=True, text=True).stdout
    seen, urls = set(), []
    for match in IMG.findall(html):
        base = match.rsplit("=w", 1)[0]
        if base not in seen:
            seen.add(base)
            urls.append(base + "=w1600")
    return urls


def download(job):
    dest, url = job
    r = subprocess.run(
        ["curl", "-sS", "--retry", "3", "--max-time", "90",
         "-e", REFERER, "-A", UA, "-o", str(dest), "-w", "%{http_code}", url],
        capture_output=True, text=True)
    size = dest.stat().st_size if dest.exists() else 0
    return dest, r.stdout.strip(), size


def main():
    jobs, manifest = [], {}
    for slug, path in SLUGS.items():
        urls = page_images(path)
        manifest[slug] = urls
        (dest_root / slug).mkdir(parents=True, exist_ok=True)
        # Image 01 is the studio logo, repeated in every page header.
        for i, u in enumerate(urls, 1):
            if i == 1:
                continue
            jobs.append((dest_root / slug / f"{i:02d}.jpg", u))
        print(f"{slug:22} {len(urls) - 1} photos")

    with ThreadPoolExecutor(max_workers=8) as ex:
        results = list(ex.map(download, jobs))

    failed = [(str(d), code, size) for d, code, size in results if code != "200" or size < 5000]
    (dest_root / "sources.json").write_text(json.dumps(manifest, indent=1))
    print(f"\n{len(results) - len(failed)}/{len(results)} downloaded into {dest_root}")
    for f in failed:
        print("  FAILED", f)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
