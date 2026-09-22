# Superiso Studio — website concept

A complete website concept for [Superiso Studio](https://www.superisostudio.com),
an architecture and interior design practice in Singapore. Prepared for
presentation to the studio.

**Preview:** https://mingkey88.github.io/superiso-homepage/

## Pages

| Path | Page |
|---|---|
| `/` | Home — hero, featured work, studio, approach, contact |
| `/work/` | All eight projects, filterable by scope |
| `/work/<slug>/` | Project pages, one per project, with gallery and lightbox |
| `/studio/` | Vision, principles, process, the studio in numbers |
| `/contact/` | Email and Instagram |
| `/404.html` | Not found |

## Running it

There is no build step to deploy — the HTML is committed. Because pages use
clean directory URLs (`/work/resort-living/`), preview over HTTP rather than
opening the files directly:

```sh
python3 -m http.server 8777
# then open http://localhost:8777
```

## Editing content

All copy and project data lives in `data/projects.json`. Edit it, then
regenerate the pages:

```sh
python3 build/site.py
```

Nothing else needs touching — page titles, the work index, project pages,
the sitemap and structured data are all generated from that one file.

### Adding or refreshing photography

The optimised images are committed, so this is only needed when a project's
photography changes:

```sh
python3 build/fetch_images.py /tmp/siso/orig   # download sources from the live site
python3 build/images.py /tmp/siso/orig         # resize to responsive WebP
python3 build/site.py                          # rebuild pages
```

`build/images.py` requires Pillow (`pip install Pillow`). It writes three
widths per image plus `data/image-sizes.json`, which supplies the `width` and
`height` attributes that stop the page shifting as images load.

## Layout of the repo

```
data/projects.json      all copy, project metadata and image captions
data/image-sizes.json   generated — intrinsic image dimensions
build/site.py           generates the HTML pages
build/images.py         source JPEGs -> responsive WebP
build/fetch_images.py   downloads source photography from the live site
assets/site.css         all styling
assets/site.js          mobile nav, work filters, gallery lightbox
assets/img/<slug>/      optimised project photography
```

## Before this goes live

Two settings in `data/projects.json` under `site`:

- `baseUrl` — set to the real domain. It feeds canonical URLs, the sitemap
  and social share cards.
- `indexable` — `false` while this is a presentation build, which keeps
  `robots.txt` and the page meta set to no-index so it cannot compete with
  the studio's existing site in search. Set it to `true` at launch.

Rebuild after changing either.

## Attribution

Project imagery and project information belong to Superiso Studio. Page copy
and design are proposed, written for this concept. This is not the studio's
official website.
