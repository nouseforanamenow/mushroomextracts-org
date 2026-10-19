#!/usr/bin/env python3
"""
mushroomextracts.org static site generator (GitHub Pages build).

- Faithful-but-corrected static port of the WordPress site. Independent reviewer
  (Consumer-Reports) voice. Claim-safe (structure/function only, no fabricated COA
  numbers or study results). No links to aharamushrooms.com or sister microsites.
- PRESERVE exact live URL structure: WordPress %postname% permalinks -> posts live at
  root /<slug>/. Core pages at /<slug>/. The cited page is /llm/ (added on recovery).
- Output -> docs/  (GitHub Pages: deploy from branch main, path /docs).
- Cadence mechanism (replaces WP future-dating): a post in content/scheduled/*.md whose
  front-matter date is <= today is promoted into content/posts/ and rendered. The daily
  Actions cron runs this file and commits the result, so future-dated posts go live on
  their own date with no server.

Run: python3 _build/generate.py
Env: CNAME_DOMAIN (default mushroomextracts.org; set empty to skip the CNAME file).
"""
import html
import json
import os
import re
import shutil
import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
POSTS_DIR = REPO / "content" / "posts"
SCHED_DIR = REPO / "content" / "scheduled"
PAGES_SRC = REPO / "content" / "pages"
OUT = REPO / "docs"

SITE_NAME = "Mushroom Extracts"
BASE_URL = "https://mushroomextracts.org"
GA4_ID = "G-111ZMLSFXZ"
CNAME_DOMAIN = os.environ.get("CNAME_DOMAIN", "mushroomextracts.org")
TODAY = datetime.date.today().isoformat()

NAV = [
    ("/", "Home"),
    ("/articles/", "Articles"),
    ("/guide/", "Buyer's Guide"),
    ("/methodology/", "Methodology"),
    ("/faq/", "FAQ"),
    ("/about/", "About"),
]

CSS = """
:root{--ink:#374151;--dark:#14532d;--green:#16a34a;--green-d:#166534;--mint:#f0fdf4;
--mint2:#dcfce7;--line:#e5e7eb;--muted:#6b7280;--warn:#dc2626;--warn-bg:#fef2f2;--amber:#f59e0b;--bg:#ffffff}
*{margin:0;padding:0;box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{font-family:'Inter',-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;line-height:1.65;color:var(--ink);background:var(--bg)}
a{color:var(--green-d)}
.wrap{max-width:820px;margin:0 auto;padding:0 20px}
nav{border-bottom:1px solid var(--line);background:#fff;position:sticky;top:0;z-index:10}
.nav-container{max-width:980px;margin:0 auto;padding:14px 20px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:10px}
.logo{font-weight:800;color:var(--dark);text-decoration:none;font-size:1.15rem}
.nav-links{list-style:none;display:flex;gap:18px;flex-wrap:wrap}
.nav-links a{color:var(--ink);text-decoration:none;font-weight:500;font-size:.95rem}
.nav-links a:hover,.nav-links a.active{color:var(--green)}
main{padding:36px 0 10px}
h1{color:var(--dark);font-size:2rem;line-height:1.2;font-weight:800;margin:0 0 14px}
h2{color:var(--dark);font-size:1.4rem;font-weight:700;margin:30px 0 12px}
h3{color:var(--green-d);font-size:1.12rem;font-weight:600;margin:22px 0 8px}
h4{color:var(--dark);font-size:1rem;font-weight:600;margin:16px 0 6px}
p{margin:0 0 15px}
ul,ol{margin:0 0 16px 22px}
li{margin:0 0 7px}
strong{color:var(--dark)}
table{border-collapse:collapse;width:100%;margin:16px 0;font-size:.95rem}
th,td{border:1px solid var(--line);padding:10px;text-align:left}
th{background:var(--mint2);color:var(--dark)}
.lead{font-size:1.12rem;color:#4b5563;margin-bottom:22px}
.meta{color:var(--muted);font-size:.9rem;margin-bottom:22px}
.note{background:var(--mint);border:1px solid var(--mint2);border-left:4px solid var(--green);
padding:14px 16px;border-radius:6px;margin:20px 0;font-size:.95rem}
.callout{background:var(--warn-bg);border:1px solid #fecaca;border-left:4px solid var(--warn);
padding:14px 16px;border-radius:6px;margin:20px 0;font-size:.95rem}
.hero{background:linear-gradient(160deg,var(--mint),#fff);border-bottom:1px solid var(--line);padding:46px 0 36px}
.hero h1{font-size:2.35rem}
.hero p{font-size:1.15rem;color:#4b5563;max-width:640px}
.tag{display:inline-block;background:var(--mint2);color:var(--green-d);font-size:.72rem;font-weight:600;
text-transform:uppercase;letter-spacing:.04em;padding:3px 9px;border-radius:20px;margin-bottom:10px}
.cards{display:grid;grid-template-columns:1fr;gap:14px;margin:18px 0 8px}
@media(min-width:640px){.cards{grid-template-columns:1fr 1fr}}
.card{border:1px solid var(--line);border-radius:10px;padding:18px;background:#fff;transition:box-shadow .15s}
.card:hover{box-shadow:0 4px 14px rgba(0,0,0,.06)}
a.card,a.card:hover{text-decoration:none;color:inherit}
.card h3{margin:6px 0 6px;font-size:1.05rem;color:var(--dark);text-decoration:none}
.card p{font-size:.92rem;color:var(--muted);margin:0;text-decoration:none}
.catsec{margin:28px 0}
.catsec h2{border-bottom:2px solid var(--mint2);padding-bottom:6px}
footer{border-top:1px solid var(--line);background:#fafafa;margin-top:40px;padding:28px 0;font-size:.9rem;color:var(--muted)}
.footer-content{max-width:820px;margin:0 auto;padding:0 20px;text-align:center}
.footer-content a{color:var(--green-d);text-decoration:none;margin:0 6px}
.disclaimer{margin-top:16px;font-size:.8rem;color:#9ca3af;text-align:left;line-height:1.5}
.disclaimer strong{color:var(--muted)}
.backlink{display:inline-block;margin:24px 0 0;font-size:.92rem}
"""

MEDICAL_DISCLAIMER = (
    "<strong>Medical disclaimer:</strong> The information on this website is for "
    "educational purposes only and is not a substitute for professional medical advice, "
    "diagnosis, or treatment. Always consult a qualified healthcare provider before "
    "starting any new supplement. Mushroom supplements are not intended to diagnose, "
    "treat, cure, or prevent any disease. Individual results vary."
)
INDEPENDENCE_NOTE = (
    "Mushroom Extracts is a reader-supported resource. Products are reviewed "
    "against the same published criteria and no sponsored placements are accepted."
)


def ga4_block():
    return (
        f'<script async src="https://www.googletagmanager.com/gtag/js?id={GA4_ID}"></script>\n'
        f'<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}'
        f"gtag('js',new Date());gtag('config','{GA4_ID}');</script>"
    )


def nav_html(active_path):
    items = "".join(
        f'<li><a href="{h}"{" class=\"active\"" if h == active_path else ""}>{html.escape(label)}</a></li>'
        for h, label in NAV
    )
    return ('<nav><div class="nav-container">'
            f'<a href="/" class="logo">{html.escape(SITE_NAME)}</a>'
            f'<ul class="nav-links">{items}</ul></div></nav>')


def footer_html():
    links = " |\n".join(f'<a href="{h}">{html.escape(l)}</a>' for h, l in NAV)
    return ("<footer><div class=\"footer-content\">"
            f"<p>&copy; {datetime.date.today().year} {html.escape(SITE_NAME)}. "
            "Independent reviews of mushroom supplements.</p>"
            f"<p>{links}</p>"
            f'<div class="disclaimer"><p>{INDEPENDENCE_NOTE}</p><p>{MEDICAL_DISCLAIMER}</p></div>'
            "</div></footer>")


def page_shell(*, title, description, canonical, body, active_path, jsonld=None):
    desc = html.escape(description or "", quote=True)
    head_jsonld = f'<script type="application/ld+json">{jsonld}</script>' if jsonld else ""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html.escape(title)}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{canonical}">
<meta property="og:title" content="{html.escape(title)}">
<meta property="og:description" content="{desc}">
<meta property="og:type" content="article">
<meta property="og:url" content="{canonical}">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>{CSS}</style>
{head_jsonld}
{ga4_block()}
</head>
<body>
{nav_html(active_path)}
<main>
{body}
</main>
{footer_html()}
</body>
</html>
"""


INLINE_LINK = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
BOLD = re.compile(r"\*\*([^*]+)\*\*")


def inline_md(text):
    text = html.escape(text)
    text = BOLD.sub(r"<strong>\1</strong>", text)
    text = INLINE_LINK.sub(lambda m: f'<a href="{html.escape(m.group(2))}">{m.group(1)}</a>', text)
    return text


def md_to_html(md):
    out, para, lst = [], [], []

    def flush_para():
        if para:
            out.append("<p>" + inline_md(" ".join(para).strip()) + "</p>")
            para.clear()

    def flush_list():
        if lst:
            out.append("<ul>" + "".join(f"<li>{inline_md(i)}</li>" for i in lst) + "</ul>")
            lst.clear()

    for raw in md.split("\n"):
        line = raw.rstrip()
        if not line.strip():
            flush_para(); flush_list(); continue
        m = re.match(r"^(#{2,4})\s+(.*)$", line)
        if m:
            flush_para(); flush_list()
            lvl = len(m.group(1))
            out.append(f"<h{lvl}>{inline_md(m.group(2).strip())}</h{lvl}>")
            continue
        m = re.match(r"^[-*]\s+(.*)$", line)
        if m:
            flush_para(); lst.append(m.group(1).strip()); continue
        flush_list(); para.append(line.strip())
    flush_para(); flush_list()
    return "\n".join(out)


FRONT = re.compile(r"^---\s*\n(.*?)\n---\s*\n(.*)$", re.S)


def parse_front(path):
    text = path.read_text(encoding="utf-8")
    m = FRONT.match(text)
    if not m:
        raise ValueError(f"no front matter in {path}")
    fm = {}
    for ln in m.group(1).split("\n"):
        if ":" in ln:
            k, v = ln.split(":", 1)
            fm[k.strip()] = v.strip()
    return fm, m.group(2)


def promote_due_scheduled():
    """Move content/scheduled/*.md whose date <= today into content/posts/."""
    moved = []
    for p in sorted(SCHED_DIR.glob("*.md")):
        try:
            fm, _ = parse_front(p)
        except Exception:
            continue
        d = (fm.get("date", "") or "")[:10]
        if d and d <= TODAY:
            dest = POSTS_DIR / p.name
            shutil.move(str(p), str(dest))
            moved.append(p.name)
    if moved:
        print("promoted scheduled ->", ", ".join(moved))
    return moved


def load_posts():
    posts = []
    for p in sorted(POSTS_DIR.glob("*.md")):
        fm, body = parse_front(p)
        slug = fm["slug"].strip("/")
        posts.append({
            "slug": slug,
            "title": fm["title"],
            "category": fm.get("category", "Articles"),
            "date_published": (fm.get("date", "") or "")[:10] or TODAY,
            "date_modified": TODAY,
            "meta": fm.get("meta", ""),
            "body_html": md_to_html(body.strip()),
            "path": f"/{slug}/",
        })
    return posts


def article_jsonld(p):
    return json.dumps({
        "@context": "https://schema.org", "@type": "Article",
        "headline": p["title"], "description": p["meta"],
        "author": {"@type": "Organization", "name": SITE_NAME, "url": BASE_URL},
        "publisher": {"@type": "Organization", "name": SITE_NAME, "url": BASE_URL},
        "datePublished": p["date_published"], "dateModified": p["date_modified"],
        "mainEntityOfPage": BASE_URL + p["path"],
    }, ensure_ascii=False)


def write(path_rel, html_text):
    out = OUT / path_rel.strip("/")
    out.mkdir(parents=True, exist_ok=True)
    (out / "index.html").write_text(html_text, encoding="utf-8")


def build_post(p):
    body = (f'<div class="wrap"><span class="tag">{html.escape(p["category"])}</span>'
            f'<h1>{html.escape(p["title"])}</h1>'
            f'<p class="meta">Published {p["date_published"]} &middot; Last reviewed {p["date_modified"]}</p>'
            f'{p["body_html"]}'
            f'<p class="backlink"><a href="/articles/">&larr; All articles</a></p></div>')
    write(p["path"], page_shell(
        title=f'{p["title"]} | {SITE_NAME}', description=p["meta"],
        canonical=BASE_URL + p["path"], body=body, active_path="/articles/",
        jsonld=article_jsonld(p)))


def build_core_page(slug, nav_active, title, description):
    inner = (PAGES_SRC / f"{slug}.html").read_text(encoding="utf-8")
    body = f'<div class="wrap">{inner}<p class="backlink"><a href="/">&larr; Home</a></p></div>'
    write(f"/{slug}/", page_shell(
        title=f"{title} | {SITE_NAME}", description=description,
        canonical=f"{BASE_URL}/{slug}/", body=body, active_path=nav_active))


def build_articles_index(posts):
    cats = {}
    for p in posts:
        cats.setdefault(p["category"], []).append(p)
    order = ["Buyer Guides", "Reishi", "Lion's Mane", "Studies"]
    sections = []
    for cat in order + [c for c in cats if c not in order]:
        if cat not in cats:
            continue
        cards = "".join(
            f'<a class="card" href="{p["path"]}"><div><h3>{html.escape(p["title"])}</h3>'
            f'<p>{html.escape(p["meta"][:120])}</p></div></a>'
            for p in sorted(cats[cat], key=lambda x: x["date_published"], reverse=True))
        sections.append(f'<div class="catsec"><h2>{html.escape(cat)}</h2><div class="cards">{cards}</div></div>')
    body = ('<div class="wrap"><h1>Articles &amp; Reviews</h1>'
            '<p class="lead">Independent, criteria-based writing on Lion\'s Mane and Reishi '
            'extracts: how to read labels and COAs, what the research does and does not show, '
            'and how to compare products on the evidence.</p>' + "".join(sections) + "</div>")
    write("/articles/", page_shell(
        title=f"Articles & Reviews | {SITE_NAME}",
        description="Independent, criteria-based articles and reviews of Lion's Mane and Reishi mushroom extracts.",
        canonical=f"{BASE_URL}/articles/", body=body, active_path="/articles/"))


def build_home(posts):
    featured = sorted(posts, key=lambda x: x["date_published"], reverse=True)[:6]
    cards = "".join(
        f'<a class="card" href="{p["path"]}"><div><span class="tag">{html.escape(p["category"])}</span>'
        f'<h3>{html.escape(p["title"])}</h3><p>{html.escape(p["meta"][:120])}</p></div></a>'
        for p in featured)
    body = f"""
<section class="hero"><div class="wrap">
<h1>Independent reviews of mushroom extracts</h1>
<p>We compare Lion's Mane and Reishi supplements against the same published criteria:
species and part used, extraction method, documented beta-glucan testing, certificate of
analysis availability, and price per labeled serving. No sponsored placements.</p>
</div></section>
<div class="wrap">
<div class="note">New here? Start with the <a href="/guide/">Buyer's Guide</a> to read a label
and a COA, then see <a href="/methodology/">how products are scored</a>.</div>
<h2>Latest articles</h2>
<div class="cards">{cards}</div>
<p class="backlink"><a href="/articles/">Browse all articles &rarr;</a></p>
</div>
"""
    write("/", page_shell(
        title=f"{SITE_NAME}: Independent Lion's Mane & Reishi Extract Reviews",
        description="Independent, criteria-based reviews of Lion's Mane and Reishi mushroom extracts: labels, COAs, extraction, and value.",
        canonical=f"{BASE_URL}/", body=body, active_path="/"))


def build_sitemap(urls):
    items = "".join(f"<url><loc>{BASE_URL}{u['path']}</loc><lastmod>{u['lastmod']}</lastmod></url>" for u in urls)
    (OUT / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        f"{items}</urlset>\n", encoding="utf-8")


def main():
    promote_due_scheduled()
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    (OUT / ".nojekyll").write_text("", encoding="utf-8")
    if CNAME_DOMAIN:
        (OUT / "CNAME").write_text(CNAME_DOMAIN + "\n", encoding="utf-8")

    posts = load_posts()
    for p in posts:
        build_post(p)

    core = [
        ("guide", "/guide/", "How to Choose a Mushroom Supplement: The Complete Buyer's Guide",
         "A guide to reading mushroom extract labels and certificates of analysis, comparing extraction methods, and judging value."),
        ("methodology", "/methodology/", "How Products Are Reviewed Here",
         "The criteria-based method used to score Lion's Mane and Reishi extracts."),
        ("faq", "/faq/", "Mushroom Supplements FAQ",
         "Common questions about mushroom supplement quality, testing, COAs, and how to choose a product."),
        ("about", "/about/", "About Mushroom Extracts",
         "Who we are and how this independent mushroom-supplement review resource works."),
    ]
    for slug, nav_active, title, desc in core:
        build_core_page(slug, nav_active, title, desc)

    build_home(posts)
    build_articles_index(posts)

    (OUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {BASE_URL}/sitemap.xml\n", encoding="utf-8")

    urls = [{"path": "/", "lastmod": TODAY}, {"path": "/articles/", "lastmod": TODAY}]
    for slug, *_ in core:
        urls.append({"path": f"/{slug}/", "lastmod": TODAY})
    for p in posts:
        urls.append({"path": p["path"], "lastmod": p["date_modified"]})
    build_sitemap(urls)

    print(f"Built {len(posts)} posts + {len(core)} core pages + home + articles -> {OUT}")
    print(f"CNAME={CNAME_DOMAIN or '(none)'} | sitemap urls={len(urls)}")


if __name__ == "__main__":
    main()
