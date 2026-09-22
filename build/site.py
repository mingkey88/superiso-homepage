#!/usr/bin/env python3
"""Generate the static Superiso Studio site from data/projects.json.

Output is plain HTML with relative links, so it works unchanged on Cloudflare
Pages, GitHub Pages or any static host. Run:  python3 build/site.py
"""
import json, pathlib, html, shutil, datetime

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = json.loads((ROOT / "data/projects.json").read_text())
SIZES = json.loads((ROOT / "data/image-sizes.json").read_text())
SITE = DATA["site"]
PROJECTS = DATA["projects"]
BY_SLUG = {p["slug"]: p for p in PROJECTS}
TODAY = datetime.date.today().isoformat()

e = lambda s: html.escape(str(s), quote=True)


# --- image helpers ---------------------------------------------------------

def img_at(slug, filename, sizes, rel, cls="", eager=False):
    """Responsive <img> addressed from an arbitrary directory depth."""
    proj = BY_SLUG[slug]
    img = next(i for i in proj["images"] if i["file"] == filename)
    meta = SIZES[f"{slug}/{filename}"]
    stem = filename.split(".")[0]
    widths = meta["widths"]
    srcset = ", ".join(f"{rel}assets/img/{slug}/{stem}-{w}.webp {w}w" for w in widths)
    src = f"{rel}assets/img/{slug}/{stem}-{widths[-1]}.webp"
    loading = 'fetchpriority="high"' if eager else 'loading="lazy" decoding="async"'
    return (
        f'<img src="{src}" srcset="{srcset}" sizes="{sizes}" alt="{e(img["alt"])}" '
        f'width="{meta["w"]}" height="{meta["h"]}" {loading}'
        + (f' class="{cls}"' if cls else "")
        + ">"
    )


# --- page shell ------------------------------------------------------------

NAV = [("work", "Work", "work/"), ("studio", "Studio", "studio/"), ]


def head(title, desc, rel, page_key, canonical, extra_ld=""):
    robots = "index,follow" if SITE.get("indexable") else "noindex,nofollow"
    og_img = f"{SITE['baseUrl']}/assets/img/resort-living/04-1400.webp"
    ld = {
        "@context": "https://schema.org",
        "@type": "ArchitecturalService",
        "name": SITE["name"],
        "description": SITE["description"],
        "email": SITE["email"],
        "url": SITE["baseUrl"] + "/",
        "image": og_img,
        "areaServed": {"@type": "Country", "name": "Singapore"},
        "address": {"@type": "PostalAddress", "addressLocality": "Singapore", "addressCountry": "SG"},
        "sameAs": [SITE["instagram"]],
        "knowsAbout": ["Architecture", "Interior design", "Residential renovation"],
    }
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="robots" content="{robots}">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{e(canonical)}">
<meta property="og:type" content="website">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:image" content="{e(og_img)}">
<meta property="og:url" content="{e(canonical)}">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#f4f2eb">
<link rel="icon" href="{rel}assets/logo.png">
<link rel="stylesheet" href="{rel}assets/site.css">
<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>{extra_ld}
</head>
<body id="top">
<a class="skip" href="#main">Skip to content</a>
{header(rel, page_key)}
<main id="main">
"""


def header(rel, page_key):
    def link(key, label, href):
        cur = ' aria-current="page"' if key == page_key else ""
        return f'<a href="{rel}{href}"{cur}>{label}</a>'
    desk = "".join(link(k, l, h) for k, l, h in NAV)
    cur_c = ' aria-current="page"' if page_key == "contact" else ""
    mob = desk + f'<a href="{rel}contact/"{cur_c}>Start a conversation &#8599;</a>'
    return f"""<header class="site-header">
<a class="brand" href="{rel or '#top'}" aria-label="{'Superiso Studio, back to top' if not rel else 'Superiso Studio home'}"><img src="{rel}assets/logo.png" alt="" width="35" height="40">superiso studio</a>
<nav class="desktop-nav" aria-label="Main navigation">{desk}<a class="contact-link" href="{rel}contact/"{cur_c}>Start a conversation <span aria-hidden="true">&#8599;</span></a></nav>
<button class="mobile-toggle" type="button" aria-expanded="false" aria-controls="mobile-nav">Menu <span aria-hidden="true">&#9776;</span></button>
<nav class="mobile-nav" id="mobile-nav" aria-label="Mobile navigation" inert>{mob}</nav>
</header>"""


def foot(rel):
    return f"""</main>
<footer class="footer">
<div class="footer-top">
<a class="brand" href="{rel or '#top'}" aria-label="{'Superiso Studio, back to top' if not rel else 'Superiso Studio home'}"><img src="{rel}assets/logo.png" alt="" width="25" height="31">superiso studio</a>
<div class="footer-links">
<a href="{rel}work/">Work</a>
<a href="{rel}studio/">Studio</a>
<a href="{rel}contact/">Contact</a>
<a href="{e(SITE['instagram'])}" target="_blank" rel="noopener">Instagram &#8599;</a>
<a href="#top">Back to top &#8593;</a>
</div>
</div>
<div class="footer-bottom">
<span>Architecture &amp; interiors &middot; Singapore<br>{e(SITE['email'])}</span>
<span>Homepage and website concept, prepared for presentation.<br>Project imagery and information: Superiso Studio.</span>
</div>
</footer>
<script src="{rel}assets/site.js" defer></script>
</body>
</html>
"""


def write(path, content):
    dest = ROOT / path
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(content)
    return dest


# --- shared fragments ------------------------------------------------------

def meta_line(p):
    return f"{p['location']} &middot; {' &amp; '.join(p['scope'])} &middot; {p['area']}"


def project_card(p, rel, number):
    lead = p["images"][0]
    cls = "index-item is-drawing" if lead["type"] == "drawing" else "index-item"
    scope = " ".join(s.lower() for s in p["scope"])
    return f"""<article class="{cls}" data-scope="{scope}">
<a href="{rel}work/{p['slug']}/" aria-label="View {e(p['title'])}">
<div class="frame">{img_at(p['slug'], lead['file'], '(max-width:700px) 88vw, 44vw', rel)}<span class="image-cta" aria-hidden="true">&#8599;</span></div>
<div class="caption"><div><h2>{e(p['title'])}</h2><div class="meta">{meta_line(p)}</div></div><span class="number">{number:02d}</span></div>
</a>
<p>{e(p['summary'])}</p>
<span class="status-tag">{e(p['status'])}</span>
</article>"""


# --- pages -----------------------------------------------------------------

def build_home():
    rel = ""
    featured = [p for p in PROJECTS if p["featured"]]
    drawing = BY_SLUG["house-on-house"]
    out = head(
        "superiso studio — architecture & interiors, Singapore",
        SITE["description"], rel, "home", SITE["baseUrl"] + "/",
    )
    cards = ""
    for i, p in enumerate(featured, 1):
        lead = p["images"][0]
        cards += f"""<article class="project">
<a href="work/{p['slug']}/" aria-label="View {e(p['title'])}">
<div class="frame">{img_at(p['slug'], lead['file'], '(max-width:700px) 88vw, 46vw', rel)}<span class="image-cta" aria-hidden="true">&#8599;</span></div>
<div class="caption"><div><h3>{e(p['title'])}</h3><div class="meta">{meta_line(p)}</div></div><span class="number">{i:02d}</span></div>
</a>
<p class="project-note">{e(p['summary'])}</p>
</article>"""

    out += f"""<section class="hero" aria-labelledby="hero-title">
<div class="hero-copy">
<div><div class="eyebrow">Architecture &amp; interiors &middot; Singapore</div><p class="hero-intro">Thoughtful spaces.<br>Personal stories.<br>A different way of seeing.</p></div>
<div class="reveal"><h1 id="hero-title">Spaces<br>shaped by<br><em>stories.</em></h1>
<div class="hero-bottom"><p>We bring people, places and possibilities together.</p><a class="round-link" href="#work">Explore our work <span class="circle-arrow" aria-hidden="true">&#8595;</span></a></div></div>
</div>
<div class="hero-image">{img_at('resort-living', '04.jpg', '(max-width:700px) 100vw, 50vw', rel, eager=True)}
<div class="hero-caption"><div><small>Featured project &middot; East Coast</small><strong>Resort Living</strong></div>
<a class="photo-link" href="work/resort-living/" aria-label="View the Resort Living project">&#8599;</a></div></div>
</section>
<div class="intro-strip"><span>Architecture with a personal point of view</span><span>Considered spaces. Everyday possibilities.</span></div>

<section class="section" id="work" aria-labelledby="work-title">
<div class="section-header"><div><div class="eyebrow">01 / Selected work</div><h2 class="section-title" id="work-title">Places to live.<br>Stories to <em>unfold.</em></h2></div><a class="text-link" href="work/">View all projects <span aria-hidden="true">&#8599;</span></a></div>
<div class="work-grid">{cards}</div>
<article class="drawing-project">
<a class="drawing-frame" href="work/{drawing['slug']}/" aria-label="View {e(drawing['title'])}">{img_at(drawing['slug'], '02.jpg', '(max-width:700px) 88vw, 46vw', rel)}</a>
<div class="drawing-info"><div class="eyebrow">03 / From the drawing board</div><h3>{e(drawing['title'])}</h3>
<p>{e(drawing['summary'])}</p>
<p style="font-size:10px">{meta_line(drawing)}</p>
<a class="text-link" href="work/{drawing['slug']}/">Explore the project <span aria-hidden="true">&#8599;</span></a></div>
</article>
</section>

<section class="section studio" id="studio" aria-labelledby="studio-title">
<div class="studio-aside"><div class="eyebrow">02 / The studio</div>
<div class="detail-wrap"><div class="detail-image">{img_at('resort-living', '14.jpg', '170px', rel)}</div>
<p class="detail-caption">A closer look.<br>Timber detail, Resort Living.</p></div></div>
<div class="studio-main"><h2 id="studio-title">Good design starts<br>with a little<br><em>understanding.</em></h2>
<p>Every person brings a different story. We listen, explore and design together, shaping spaces around the lives they hold.</p>
<p>At Superiso Studio, our vision is to make sustainable design accessible, welcome play and emotion, and tread more lightly on the environment.</p>
<a class="text-link" href="studio/">Meet the studio <span aria-hidden="true">&#8599;</span></a></div>
</section>

<section class="section approach" id="approach" aria-labelledby="approach-title">
<div class="approach-intro"><div class="eyebrow">03 / Our approach</div><h2 class="section-title" id="approach-title">From a thought<br>to a <em>place.</em></h2>
<p>A conversation, a shared vision and a considered journey from first idea to lived experience.</p></div>
<div class="steps">{steps_html()}</div>
</section>

<section class="section contact" id="contact" aria-labelledby="contact-title">
<div class="eyebrow">04 / Let's begin</div>
<div class="contact-top"><div><h2 id="contact-title">What story will<br>your space <em>tell?</em></h2>
<a class="mail" href="mailto:{e(SITE['email'])}">{e(SITE['email'])} <span aria-hidden="true">&#8599;</span></a></div>
<p class="contact-annotation">A new home. A familiar place.<br>A possibility worth exploring.<br>Let's start a conversation.</p></div>
</section>
"""
    write("index.html", out + foot(rel))


def steps_html():
    out = ""
    for i, s in enumerate(SITE["process"]):
        op = " open" if i == 0 else ""
        out += (f'<details class="step"{op}><summary><span class="num">{s["num"]}</span>'
                f'<h3>{e(s["title"])}</h3><span class="plus" aria-hidden="true">+</span></summary>'
                f'<p>{e(s["body"])}</p></details>')
    return out


def build_work():
    rel = "../"
    scopes = sorted({s for p in PROJECTS for s in p["scope"]})
    buttons = '<button class="filter-btn" data-filter="all" aria-pressed="true">All</button>'
    for s in scopes:
        buttons += f'<button class="filter-btn" data-filter="{s.lower()}" aria-pressed="false">{e(s)}</button>'
    cards = "".join(project_card(p, rel, i) for i, p in enumerate(PROJECTS, 1))
    out = head("Work — superiso studio", 
               "Houses, apartments and mixed-use proposals across Singapore by Superiso Studio.",
               rel, "work", f"{SITE['baseUrl']}/work/")
    out += f"""<div class="page-head">
<div class="page-head-row"><div><div class="eyebrow">Selected work</div>
<h1>Eight places, <em>eight stories.</em></h1></div>
<p class="lede">Houses, apartments and proposals across Singapore — from a four-room flat in Punggol to a mixed-use block in Novena. Each one began with a conversation.</p></div>
<div class="filters"><span class="label">Filter by scope</span>{buttons}<span class="filter-count">{len(PROJECTS)} projects</span></div>
</div>
<div class="index-grid">{cards}<p class="no-results" hidden>No projects match that filter.</p></div>
"""
    write("work/index.html", out + foot(rel))


def build_project(p, prev_p, next_p):
    rel = "../../"
    lead = p["images"][0]
    hero_cls = "project-hero is-drawing" if lead["type"] == "drawing" else "project-hero"

    # A portrait image at full bleed becomes absurdly tall, so the "wide" hint
    # from the data file is only honoured for landscape shots. If that leaves a
    # project with no full-width image at all, promote its widest landscape one
    # so the gallery keeps some rhythm.
    rest = p["images"][1:]
    ratios = {i["file"]: SIZES[f"{p['slug']}/{i['file']}"]["ratio"] for i in rest}
    wides = {i["file"] for i in rest if i["span"] == "wide" and ratios[i["file"]] >= 1.3}
    if not wides:
        landscape = [i for i in rest if ratios[i["file"]] >= 1.3]
        if landscape:
            wides = {max(landscape, key=lambda i: ratios[i["file"]])["file"]}

    shots = ""
    for img in rest:
        wide = " is-wide" if img["file"] in wides else ""
        is_flat = " is-flat" if img["type"] == "drawing" else ""
        sizes = "(max-width:700px) 88vw, 88vw" if wide else "(max-width:700px) 88vw, 43vw"
        shots += (f'<figure class="shot{wide}{is_flat}"><button type="button" '
                  f'aria-label="Enlarge: {e(img["alt"])}">'
                  f'{img_at(p["slug"], img["file"], sizes, rel)}</button>'
                  f'<figcaption>{e(img["alt"])}</figcaption></figure>')

    body = "".join(f"<p>{e(par)}</p>" for par in p["body"])
    ld = json.dumps({
        "@context": "https://schema.org",
        "@type": "CreativeWork",
        "name": p["title"],
        "description": p["summary"],
        "creator": {"@type": "Organization", "name": SITE["name"]},
        "locationCreated": {"@type": "Place", "name": f"{p['location']}, Singapore"},
        "creativeWorkStatus": p["status"],
    }, ensure_ascii=False)

    out = head(f"{p['title']} — superiso studio",
               p["summary"], rel, "work",
               f"{SITE['baseUrl']}/work/{p['slug']}/",
               extra_ld=f'\n<script type="application/ld+json">{ld}</script>')

    out += f"""<div class="{hero_cls}">{img_at(p['slug'], lead['file'], '100vw', rel, eager=True)}</div>
<div class="project-title-block">
<div class="eyebrow">{e(p['location'])} &middot; {e(p['status'])}</div>
<h1>{e(p['title'])}</h1>
</div>
<div class="project-intro">
<dl class="spec">
<div><dt>Location</dt><dd>{e(p['location'])}</dd></div>
<div><dt>Typology</dt><dd>{e(p['typology'])}</dd></div>
<div><dt>Area</dt><dd>{e(p['area'])}</dd></div>
<div><dt>Scope</dt><dd>{' &amp; '.join(e(s) for s in p['scope'])}</dd></div>
<div><dt>Status</dt><dd>{e(p['status'])}</dd></div>
</dl>
<div class="project-body">{body}</div>
</div>
<div class="gallery">{shots}</div>
<div class="lightbox" hidden role="dialog" aria-modal="true" aria-label="Enlarged project image">
<button class="lb-btn lb-close" type="button" aria-label="Close">&times;</button>
<button class="lb-btn lb-prev" type="button" aria-label="Previous image">&#8592;</button>
<figure><img alt="" hidden><figcaption></figcaption></figure>
<button class="lb-btn lb-next" type="button" aria-label="Next image">&#8594;</button>
<span class="lb-count"></span>
</div>
<section class="next-project">
<div><div class="eyebrow">Next project</div><h2>{e(next_p['title'])}</h2>
<div class="meta">{meta_line(next_p)}</div></div>
<a class="round-link" href="{rel}work/{next_p['slug']}/">View project <span class="circle-arrow" aria-hidden="true">&#8594;</span></a>
</section>
"""
    write(f"work/{p['slug']}/index.html", out + foot(rel))


def build_studio():
    rel = "../"
    principles = ""
    for i, pr in enumerate(SITE["principles"], 1):
        principles += (f'<div class="principle"><span class="num">{i:02d}</span>'
                       f'<h3>{e(pr["title"])}</h3><p>{e(pr["body"])}</p></div>')
    completed = sum(1 for p in PROJECTS if p["status"] == "Completed")
    stats = [
        (str(len(PROJECTS)), "Projects in the studio portfolio"),
        (str(completed), "Completed and lived in"),
        ("92&ndash;3,420", "Square metres, smallest to largest"),
        ("Singapore", "Where we design and build"),
    ]
    stats_html = "".join(f'<div class="stat"><strong>{v}</strong><span>{l}</span></div>' for v, l in stats)

    out = head("Studio — superiso studio",
               "Superiso Studio is an architecture and interior practice in Singapore. Our vision, our principles and how we work.",
               rel, "studio", f"{SITE['baseUrl']}/studio/")
    out += f"""<div class="page-head">
<div class="page-head-row"><div><div class="eyebrow">The studio</div>
<h1>Good design starts with a little <em>understanding.</em></h1></div>
<p class="lede">Superiso Studio is an architecture and interior design practice based in Singapore. We work on houses, apartments and the occasional building — mostly for people who intend to stay a while.</p></div>
</div>
<section class="studio-portrait">
<figure style="margin:0">
<div class="frame">{img_at('resort-living', '03.jpg', '92vw', rel)}</div>
<figcaption>Resort Living, East Coast — the terrace built around an existing frangipani tree.</figcaption>
</figure>
</section>
<section class="quote-band">
<blockquote>{e(SITE['quote']['text'])}</blockquote>
<cite>{e(SITE['quote']['author'])}</cite>
</section>
<section class="section" aria-labelledby="vision-title">
<div class="section-header"><div><div class="eyebrow">01 / Vision</div>
<h2 class="section-title" id="vision-title">Design that reaches<br><em>further.</em></h2></div></div>
<div class="studio-main" style="max-width:640px">
<p>Every person brings a different story. We listen, explore and design together, shaping spaces around the lives they hold rather than around a house style of our own.</p>
<p>Our vision is to develop sustainable designs that reach a broad audience, honour the narratives of the people we design for, and generate a genuine emotional response — the feeling that a place understands you.</p>
</div>
</section>
<section aria-labelledby="principles-title">
<div class="section-header" style="padding:0 var(--pad);margin-bottom:44px"><div><div class="eyebrow">02 / Principles</div>
<h2 class="section-title" id="principles-title">Three things we<br>hold <em>on to.</em></h2></div></div>
<div class="principles">{principles}</div>
</section>
<section class="section approach" aria-labelledby="process-title">
<div class="approach-intro"><div class="eyebrow">03 / Process</div><h2 class="section-title" id="process-title">From a thought<br>to a <em>place.</em></h2>
<p>A conversation, a shared vision and a considered journey from first idea to lived experience.</p></div>
<div class="steps">{steps_html()}</div>
</section>
<section aria-labelledby="numbers-title">
<div class="section-header" style="padding:110px var(--pad) 0;margin-bottom:44px"><div><div class="eyebrow">04 / The studio in numbers</div>
<h2 class="section-title" id="numbers-title">Where we've <em>been.</em></h2></div></div>
<div class="stats">{stats_html}</div>
</section>
<section class="section contact">
<div class="eyebrow">Let's begin</div>
<div class="contact-top"><div><h2>What story will<br>your space <em>tell?</em></h2>
<a class="mail" href="mailto:{e(SITE['email'])}">{e(SITE['email'])} <span aria-hidden="true">&#8599;</span></a></div>
<p class="contact-annotation">A new home. A familiar place.<br>A possibility worth exploring.</p></div>
</section>
"""
    write("studio/index.html", out + foot(rel))


def build_contact():
    rel = "../"
    out = head("Contact — superiso studio",
               "Start a conversation with Superiso Studio. Architecture and interior design in Singapore.",
               rel, "contact", f"{SITE['baseUrl']}/contact/")
    out += f"""<div class="contact-page">
<div class="eyebrow">Let's begin</div>
<h1>Hello.</h1>
</div>
<div class="contact-grid">
<div class="contact-methods">
<a href="mailto:{e(SITE['email'])}"><span class="what">Email</span><span class="val">{e(SITE['email'])} &#8599;</span></a>
<a href="{e(SITE['instagram'])}" target="_blank" rel="noopener"><span class="what">Instagram</span><span class="val">{e(SITE['instagramHandle'])} &#8599;</span></a>
<div><span class="what">Studio</span><span class="val">Singapore</span></div>
</div>
<div class="contact-side">
<p>Tell us about the place and the people who will live in it. A sentence is enough to start — we will ask the rest.</p>
<p>If you already have plans, a site address or a rough budget in mind, send those along too. It helps us give you a useful answer quickly.</p>
<p>We work on houses, apartments and mixed-use buildings across Singapore, at every stage from first sketch to handover.</p>
</div>
</div>
"""
    write("contact/index.html", out + foot(rel))


def build_404():
    rel = ""
    out = head("Page not found — superiso studio", "That page could not be found.",
               rel, "", SITE["baseUrl"] + "/404.html")
    out += f"""<div class="contact-page">
<div class="eyebrow">404</div>
<h1>Lost.</h1>
</div>
<div class="contact-grid">
<div class="contact-methods">
<a href="{rel}work/"><span class="what">Try</span><span class="val">Selected work &#8599;</span></a>
<a href="{rel}studio/"><span class="what">Try</span><span class="val">The studio &#8599;</span></a>
<a href="{rel}"><span class="what">Try</span><span class="val">Home &#8599;</span></a>
</div>
<div class="contact-side"><p>That page doesn't exist — it may have moved. The work is all still here.</p></div>
</div>
"""
    write("404.html", out + foot(rel))


def build_meta_files():
    urls = ["/", "/work/", "/studio/", "/contact/"] + [f"/work/{p['slug']}/" for p in PROJECTS]
    body = "".join(
        f"<url><loc>{SITE['baseUrl']}{u}</loc><lastmod>{TODAY}</lastmod>"
        f"<priority>{'1.0' if u == '/' else '0.8' if u.count('/') == 2 else '0.6'}</priority></url>"
        for u in urls
    )
    write("sitemap.xml",
          '<?xml version="1.0" encoding="UTF-8"?>\n'
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
          + body + "</urlset>\n")

    if SITE.get("indexable"):
        robots = f"User-agent: *\nAllow: /\n\nSitemap: {SITE['baseUrl']}/sitemap.xml\n"
    else:
        robots = ("# Presentation build — not for indexing.\n"
                  "User-agent: *\nDisallow: /\n")
    write("robots.txt", robots)


def main():
    for d in ("work", "studio", "contact"):
        shutil.rmtree(ROOT / d, ignore_errors=True)
    build_home()
    build_work()
    for i, p in enumerate(PROJECTS):
        build_project(p, PROJECTS[i - 1], PROJECTS[(i + 1) % len(PROJECTS)])
    build_studio()
    build_contact()
    build_404()
    build_meta_files()
    pages = sorted(str(p.relative_to(ROOT)) for p in ROOT.rglob("*.html")
                   if "assets" not in p.parts and "build" not in p.parts)
    print(f"built {len(pages)} pages:")
    for p in pages:
        print("  ", p)


if __name__ == "__main__":
    main()
