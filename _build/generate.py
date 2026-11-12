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
:root{--ink:#374151;--dark:#172e77;--green:#7ecfd7;--green-d:#172e77;--mint:#ffffff;
--mint2:#edf8fa;--line:#e5e7eb;--muted:#6b7280;--warn:#dc2626;--warn-bg:#fef2f2;--amber:#f59e0b;--bg:#ffffff}
*{margin:0;padding:0;box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;line-height:1.65;color:var(--ink);background:var(--bg)}
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
th{background:var(--dark);color:#ffffff}
tbody tr:nth-child(even){background:#f9f9f9}
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
.wrap.wide{max-width:1080px}
.tscroll{overflow-x:auto;-webkit-overflow-scrolling:touch;margin:16px 0}
.ctable{min-width:760px;margin:0;font-size:.9rem}
.ctable th{font-size:.78rem;text-transform:uppercase;letter-spacing:.03em;white-space:nowrap}
.ctable td{vertical-align:top}
.ctable tbody tr:nth-child(even){background:#fafafa}
.brandcell{font-weight:600;color:var(--dark)}
.brandcell span{display:block;font-weight:400;font-size:.84rem;color:var(--muted)}
.stars{color:var(--amber);white-space:nowrap;font-size:1rem;letter-spacing:.06em}
.scoreno{display:block;margin-top:5px;color:var(--muted);font-size:.84rem;line-height:1.45}
.yes{color:var(--green-d);font-weight:600}
.no{color:var(--warn);font-weight:600}
.unk{color:var(--muted)}
.commercial{border:1px solid var(--line);border-left:4px solid var(--amber);background:#fffbeb;
padding:14px 16px;border-radius:6px;margin:22px 0;font-size:.93rem}
.commercial .marker{display:block;font-size:.78rem;font-weight:600;text-transform:uppercase;
letter-spacing:.04em;color:#92400e;margin-bottom:6px}
.pending{font-size:.93rem;color:var(--muted)}
"""

MEDICAL_DISCLAIMER = (
    "<strong>Medical disclaimer:</strong> The information on this website is for "
    "educational purposes only and is not a substitute for professional medical advice, "
    "diagnosis, or treatment. Always consult a qualified healthcare provider before "
    "starting any new supplement. Mushroom supplements are not intended to diagnose, "
    "treat, cure, or prevent any disease. Individual results vary."
)
INDEPENDENCE_NOTE = (
    "Every product on this site is judged against the same published criteria: species and "
    "part used, extraction method, documented active-compound testing, certificate of "
    "analysis access, and price per labeled serving. Figures are quoted from the brand's own "
    "published page or COA, and a figure we could not verify is marked as unverified rather "
    "than estimated. Commercial links are labelled at the point of use."
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


# ---------------------------------------------------------------------------
# Extract comparison (homepage)
#
# SCOPE: concentrated extracts only (hot-water, alcohol, or dual). Mycelium-on-grain
# biomass, whole-mushroom powders and gummies are out of scope by definition and are
# listed under EXCLUDED instead of being scored.
#
# SOURCING RULE: every cell is quoted from the brand's own published product page or
# COA. Nothing here is estimated. A figure we have not confirmed says so in the cell.
# Source notes live in Content/11_Microsite_Overhaul/mushroomextracts/brand_coa_scan.md
# and homepage_table_additions.md.
#
# AHARA is deliberately NOT a row: an owned product never enters a scored or ranked
# table. The labelled commercial link below the tables is the approved placement.
# ---------------------------------------------------------------------------

COMPARISON_COLUMNS = [
    "Brand / product", "Part used", "Extraction", "Published actives",
    "COA access", "Format", "Rating",
]

# Rating rubric, applied the same way to every row:
# 5 stars = fruiting body, a stated extraction method, a published active-compound
# figure, and a COA a reader can open in one click. Each one missing drops a star.
# A polysaccharide total is NOT a beta-glucan figure and does not earn that point.

LIONS_MANE_ROWS = [
    {
        "brand": "Eversio Wellness", "product": "Lion's Mane capsules",
        "url": "https://www.eversiowellness.com/products/lions-mane-capsules",
        "part": "Fruiting body, grown outdoors on hardwood",
        "extraction": "Dual, hot water and alcohol (8:1)",
        "actives": "Beta-glucan 35%, standardized; 350 mg per 1,000 mg serving",
        "coa": ("yes", "One click, assayed by SGS"),
        "format": "Capsules", "stars": 5,
        "why": "An outside lab stands behind the published percentage.",
    },
    {
        "brand": "Mushroom Revival", "product": "Focus Lion's Mane capsules",
        "url": "https://www.mushroomrevival.com/products/focus-lions-mane-capsules",
        "part": "Fruiting body, no mycelium on grain",
        "extraction": "Dual; no ratio published",
        "actives": "Beta-glucan 37.1%, printed on the product page",
        "coa": ("yes", "One click from the product page"),
        "format": "Capsules", "stars": 5,
        "why": "Highest published beta-glucan in the set, with the COA next to it.",
    },
    {
        "brand": "Oriveda", "product": "Lion's Mane extract",
        "url": "https://oriveda.com/coa.php",
        "part": "Fruiting body", "extraction": "Hot water (1:1)",
        "actives": "Beta-glucan published per lot",
        "coa": ("yes", "Full COAs published"),
        "format": "Capsules", "stars": 5,
        "why": "Publishes complete COAs, glucan figures included.",
    },
    {
        "brand": "Nootropics Depot", "product": "Lion's Mane 1:1 fruiting body",
        "url": "https://nootropicsdepot.com/lions-mane-mushroom-extract-capsules/",
        "part": "Whole fruiting body, explicitly not mycelium-on-grain",
        "extraction": "Hot water (1:1)",
        "actives": "Beta-glucan 25%, standardized",
        "coa": ("yes", "10 per-lot COA PDFs, with heavy-metal and microbial panels"),
        "format": "Capsules, powder", "stars": 5,
        "why": "Per-lot COAs and a standardized figure on the label.",
    },
    {
        "brand": "FreshCap", "product": "Organic Lion's Mane",
        "url": "https://freshcap.com/products/lions-mane-capsules",
        "part": "Fruiting body", "extraction": "Dual (14:1)",
        "actives": "Beta-glucan 31% or higher, standardized",
        "coa": ("no", "No COA on the site; a blog post describes the testing"),
        "format": "Capsules, powder, stick packs", "stars": 4,
        "why": "A strong number with nothing published to check it against.",
    },
    {
        "brand": "Hifas da Terra", "product": "Mico Leo",
        "url": "https://hifasdaterra.co.uk/products/mico-leo-extract-vitamin-c",
        "part": "Fruiting body only",
        "extraction": "Concentrated extract; solvent not published",
        "actives": "Beta-(1,3)(1,6)-D-glucans 200 mg per 2 capsules; 52.34% in the COA",
        "coa": ("yes", "Six PDFs on the product page; the glucan assay is their own lab"),
        "format": "Capsules", "stars": 4,
        "why": "Unusually complete documents, assayed in-house rather than outside.",
    },
    {
        "brand": "Gaia Herbs", "product": "Lion's Mane Mushroom",
        "url": "https://www.gaiaherbs.com/products/lions-mane-mushroom",
        "part": "Fruiting body, no mycelium, grain or growing medium",
        "extraction": "Extract; method not stated. 450 mg equals 2.5 g dried",
        "actives": "Beta-glucans 83 mg or more per serving",
        "coa": ("yes", "On-site results table, ISO/IEC 17025 accreditation 107080"),
        "format": "Capsules", "stars": 4,
        "why": "A verified minimum, but the extraction method is never named.",
    },
    {
        "brand": "Real Mushrooms", "product": "Lion's Mane extract",
        "url": "https://realmushrooms.com/product/lions-mane-mushroom-powder/",
        "part": "Fruiting body", "extraction": "Hot water",
        "actives": "Beta-glucan \u201cover 30%\u201d guaranteed",
        "coa": ("part", "Third-party tested, COA on request rather than one click"),
        "format": "Powder, capsules", "stars": 4,
        "why": "A real published number, a less accessible COA.",
    },
    {
        "brand": "Birch Boys", "product": "Organic Lion's Mane tincture",
        "url": "https://birchboys.com/products/lions-mane-tincture",
        "part": "Fruiting body only, hardwood-grown",
        "extraction": "Double: water at 178\u00b0F for 72 hours, plus 95% organic cane alcohol",
        "actives": "None for the bottled tincture; the 6% beta-glucan figure describes a reference powder",
        "coa": ("off", "One Medallion Labs PDF, on the process page rather than the product page"),
        "format": "Tincture", "stars": 3,
        "why": "The clearest extraction description here, attached to the wrong number.",
    },
    {
        "brand": "Terrasoul Superfoods", "product": "Lion's Mane 4:1 extract powder",
        "url": "https://terrasoul.com/products/lion-s-mane-4-1-extract-powder",
        "part": "Fruiting body, log-grown, \u201cnot the mycelium\u201d",
        "extraction": "Water extracted (4:1)",
        "actives": "Not published",
        "coa": ("no", "Not available; the site says only that each batch is lab tested"),
        "format": "Powder", "stars": 3,
        "why": "Honest about the mushroom, silent about the chemistry.",
    },
    {
        "brand": "NOW Foods", "product": "Lion's Mane 500 mg",
        "url": "https://www.nowfoods.com/products/supplements/lions-mane-500-mg-veg-capsules",
        "part": "Fruiting body", "extraction": "\u201cExtract powder\u201d; no method, no ratio",
        "actives": "Not published; the page cites \u201cnaturally occurring beta-glucans\u201d with no figure",
        "coa": ("no", "Not available; site search returns no COA"),
        "format": "Capsules", "stars": 2,
        "why": "Labelled an extract and documented like a commodity.",
    },
    {
        "brand": "Swanson", "product": "Premium Organic Lion's Mane 500 mg",
        "url": "https://www.swansonvitamins.com/p/swanson-premium-organic-lions-mane-mushroom-500-mg-60-vegan-caps",
        "part": "Fruiting body and mycelium",
        "extraction": "Standardized extract; no method, no ratio",
        "actives": "Polysaccharides 40%. That is a total, not a beta-glucan figure",
        "coa": ("no", "Not available"),
        "format": "Capsules", "stars": 2,
        "why": "A polysaccharide total on a mycelium blend tells you very little.",
    },
    {
        "brand": "Micro Ingredients", "product": "Organic Lion's Mane powder",
        "url": "https://www.microingredients.com/products/organic-lions-mane-mushroom-powder",
        "part": "Fruiting body and mycelium; the substrate is not stated",
        "extraction": "\u201cFreeze-dried extract\u201d. Freeze-drying is a drying step, not an extraction",
        "actives": "Not published",
        "coa": ("no", "Not available; the quality and lab-testing pages 404"),
        "format": "Powder", "stars": 2,
        "why": "Sold as an extract on the strength of a drying method.",
    },
]

REISHI_ROWS = [
    {
        "brand": "Eversio Wellness", "product": "Reishi capsules",
        "url": "https://www.eversiowellness.com/products/reishi-mushroom-supplement",
        "part": "Fruiting body, 100%",
        "extraction": "Dual, hot water and alcohol (15:1)",
        "actives": "Beta-glucan 45%, standardized; triterpenes 25 mg per 500 mg serving",
        "coa": ("yes", "One click, assayed by SGS"),
        "format": "Capsules", "stars": 5,
        "why": "The highest standardized beta-glucan here, on an outside lab's COA.",
    },
    {
        "brand": "Oriveda", "product": "Reishi Primo",
        "url": "https://oriveda.com/coa.php",
        "part": "Fruiting body", "extraction": "Dual, alcohol-free",
        "actives": "Ganoderic acids 6% or higher",
        "coa": ("yes", "Full COAs published"),
        "format": "Capsules", "stars": 5,
        "why": "One of only two here publishing a triterpene figure and the COA behind it.",
    },
    {
        "brand": "Nootropics Depot", "product": "Red Reishi 8:1 / 1:1",
        "url": "https://nootropicsdepot.com/reishi-mushroom-extract-capsules/",
        "part": "Whole fruiting body", "extraction": "Hot water (8:1 and 1:1 lines)",
        "actives": "Beta-glucan 35% minimum, guaranteed; triterpenes not published as a percentage",
        "coa": ("yes", "Per-lot COA PDFs"),
        "format": "Capsules, powder", "stars": 5,
        "why": "Hot water cannot carry triterpenes, and the label does not pretend otherwise.",
    },
    {
        "brand": "Mushroom Revival", "product": "Calm Reishi capsules",
        "url": "https://www.mushroomrevival.com/products/calm-reishi-mushroom-capsules",
        "part": "Fruiting body", "extraction": "Dual; no ratio published",
        "actives": "Beta-glucan 27.8%, printed on the product page",
        "coa": ("yes", "One click from the product page"),
        "format": "Capsules", "stars": 5,
        "why": "Number on the page, COA beside it, no ratio.",
    },
    {
        "brand": "FreshCap", "product": "Organic Reishi",
        "url": "https://freshcap.com/products/reishi-capsules",
        "part": "Fruiting body on the panel; the FAQ on the same page says fruiting body and spore",
        "extraction": "Dual (14:1)",
        "actives": "Beta-glucan 27% and triterpenes 1.4%, both standardized",
        "coa": ("no", "No COA on the site; a blog post describes the testing"),
        "format": "Capsules, powder", "stars": 4,
        "why": "Both compound classes declared, nothing published to check them.",
    },
    {
        "brand": "Hifas da Terra", "product": "Mico Rei",
        "url": "https://hifasdaterra.co.uk/products/mico-rei-pure-eco-extract-of-reishi",
        "part": "Fruiting body only",
        "extraction": "Concentrated extract; solvent and ratio not published",
        "actives": "Beta-glucans 248 mg and triterpenoids 50 mg per 2 capsules; 58% polysaccharides",
        "coa": ("yes", "Six PDFs on the product page; the glucan assay is their own lab"),
        "format": "Capsules", "stars": 4,
        "why": "Milligrams for both compound classes, assayed in-house.",
    },
    {
        "brand": "Gaia Herbs", "product": "Reishi Mushroom",
        "url": "https://www.gaiaherbs.com/products/reishi-mushroom",
        "part": "Fruiting body, no fillers, starch, grain or mycelium",
        "extraction": "Extract; method not stated. 450 mg equals 2.5 g dried",
        "actives": "Beta-glucans 113 mg or more per serving; no triterpene figure",
        "coa": ("yes", "On-site results table, ISO/IEC 17025 accreditation 107080"),
        "format": "Capsules", "stars": 4,
        "why": "A verified minimum, but the extraction method is never named.",
    },
    {
        "brand": "Real Mushrooms", "product": "Reishi extract",
        "url": "https://realmushrooms.com/product/reishi-mushroom-powder/",
        "part": "Fruiting body", "extraction": "Hot water",
        "actives": "Beta-glucan guaranteed across the line; the Reishi-specific figure is unverified",
        "coa": ("part", "Third-party tested, COA on request rather than one click"),
        "format": "Powder, capsules", "stars": 4,
        "why": "Guarantee is real, the per-SKU number is not yet confirmed.",
    },
    {
        "brand": "Birch Boys", "product": "Organic Reishi tincture",
        "url": "https://birchboys.com/products/reishi-tincture",
        "part": "Fruiting body only, wild-harvested. The species is Ganoderma tsugae, not G. lucidum",
        "extraction": "Double: water at 178\u00b0F for 72 hours, plus 95% organic cane alcohol",
        "actives": "None for the bottled tincture; the 4% beta-glucan figure describes a reference powder",
        "coa": ("off", "One Medallion Labs PDF, on the process page rather than the product page"),
        "format": "Tincture", "stars": 3,
        "why": "A different species from every other row, which is worth knowing before you compare.",
    },
    {
        "brand": "Double Wood", "product": "Reishi Mushroom Extract",
        "url": "https://doublewoodsupplements.com/products/reishi-mushroom-extract",
        "part": "Fruiting body and mycelium",
        "extraction": "4:1 extract; solvent not stated",
        "actives": "Not published; triterpenoids and polysaccharides named with no figure",
        "coa": ("yes", "Published inline with a lot lookup, but it assays identity, metals and micro, not actives"),
        "format": "Capsules", "stars": 3,
        "why": "A COA that answers a different question than the one on the label.",
    },
    {
        "brand": "Terrasoul Superfoods", "product": "Reishi 4:1 extract powder",
        "url": "https://terrasoul.com/products/reishi-4-1-extract-powder",
        "part": "Fruiting body, log-grown, \u201cnot the mycelium\u201d",
        "extraction": "Water extracted (4:1)",
        "actives": "Polysaccharides 20% minimum. That is a total, not a beta-glucan figure",
        "coa": ("no", "Not available; the site says only that each batch is lab tested"),
        "format": "Powder", "stars": 3,
        "why": "Good sourcing disclosure, a number that cannot be compared.",
    },
    {
        "brand": "Swanson", "product": "Superior Herbs Reishi Extract 500 mg",
        "url": "https://www.swansonvitamins.com/p/swanson-superior-herbs-reishi-mushroom-extract-500-mg-90-caps",
        "part": "Fruiting body",
        "extraction": "Extract; no method, no ratio",
        "actives": "Polysaccharides 10%. That is a total, not a beta-glucan figure",
        "coa": ("no", "Not available"),
        "format": "Capsules", "stars": 2,
        "why": "The lowest standardization figure here, and it is the wrong measurement.",
    },
    {
        "brand": "Micro Ingredients", "product": "Organic Reishi powder",
        "url": "https://www.microingredients.com/products/organic-reishi-mushroom-powder",
        "part": "Not stated anywhere on the page",
        "extraction": "100:1 ratio claimed; method not stated",
        "actives": "Not published; beta-glucans named with no figure",
        "coa": ("no", "Not available; the quality and lab-testing pages 404"),
        "format": "Powder", "stars": 1,
        "why": "The biggest ratio claim in the set with the least behind it.",
    },
]

EXCLUDED_ROWS = [
    ("Host Defense", "Mycelium grown on fermented brown rice, milled rather than extracted. Their own FAQ: "
     "\u201cwe don\u2019t isolate or concentrate any particular compounds in our powdered products.\u201d "
     "The \u201cover 55% polysaccharides\u201d guarantee is a polysaccharide total on a rice matrix, not a "
     "beta-glucan figure. Their liquid extracts do contain fruiting body, but as a proprietary blend with no ratio."),
    ("Om Mushrooms", "Mycelial biomass and fruit body cultured on whole oats, with the oats included in the "
     "2 g serving. Their own FAQ: \u201cNo. We don\u2019t use hot water or alcohol extraction.\u201d"),
    ("Genius Mushrooms", "Mycelium on oats, and extract-free by design: \u201cMade with 100% extract-free, "
     "100% organic mushrooms.\u201d"),
    ("Solaray", "Fermented mycelium cultured on whole oats or brown rice. No extraction method and no ratio published."),
    ("Nutricost", "Labelled mushroom powder, not an extract. No method, no ratio, no actives figure."),
    ("Swanson Full Spectrum", "Their own page: \u201ccontains whole reishi mushroom rather than a concentrated extract.\u201d"),
    ("Double Wood Lion\u2019s Mane", "Their own answer on the product page: \u201cThis product is not an extract. "
     "Our Lions Mane is ground up Lions Mane.\u201d The Reishi product is a 4:1 extract and is scored above."),
    ("Toniiq", "Publishes the best single document in this whole survey, a one-click COA with a Megazyme "
     "beta-glucan assay, but the product page calls it whole mushroom powder and states no extraction method, "
     "so it cannot be scored as an extract."),
    ("Sun Potion", "Their own spec table: \u201cFull-spectrum mushroom powder (not an extract)\u201d, despite "
     "publishing 52.2% beta-glucans on a recent Lion\u2019s Mane lot."),
    ("Four Sigmatic", "No single-species Lion\u2019s Mane or Reishi extract. Every mushroom product is a blend, "
     "coffee, cocoa or elixir packet."),
    ("NOW Rei-Shi", "A reishi and shiitake blend, not a single-species reishi extract. NOW\u2019s Lion\u2019s Mane "
     "is a single-species extract and is scored above."),
    ("Gummies, coffees and drink mixes", "Excluded as a format across every brand in the survey."),
]

PENDING_BRANDS = [
    "Naturealm / Sacred 7 (the brand site is a parked page and sacred7.com redirects away, "
    "so nothing the brand publishes can be read)",
]


def _coa_cell(kind, text):
    cls = {"yes": "yes", "part": "unk", "off": "unk", "no": "no"}[kind]
    label = {"yes": "Published", "part": "On request",
             "off": "Published off-page", "no": "Not available"}[kind]
    return f'<span class="{cls}">{label}</span><br><span class="scoreno">{html.escape(text)}</span>'


def _comparison_table(rows):
    head = "".join(f"<th>{html.escape(c)}</th>" for c in COMPARISON_COLUMNS)
    body = ""
    for r in rows:
        stars = "★" * r["stars"] + "☆" * (5 - r["stars"])
        body += (
            "<tr>"
            f'<td class="brandcell"><a href="{r["url"]}" target="_blank" rel="noopener nofollow">'
            f'{html.escape(r["brand"])}</a><span>{html.escape(r["product"])}</span></td>'
            f'<td>{html.escape(r["part"])}</td>'
            f'<td>{html.escape(r["extraction"])}</td>'
            f'<td>{html.escape(r["actives"])}</td>'
            f"<td>{_coa_cell(*r['coa'])}</td>"
            f'<td>{html.escape(r["format"])}</td>'
            f'<td><span class="stars">{stars}</span>'
            f'<span class="scoreno">{html.escape(r["why"])}</span></td>'
            "</tr>"
        )
    return (f'<div class="tscroll"><table class="ctable"><thead><tr>{head}</tr></thead>'
            f"<tbody>{body}</tbody></table></div>")


def comparison_html():
    excluded = "".join(
        f"<li><strong>{html.escape(n)}</strong> &mdash; {t}</li>"
        for n, t in EXCLUDED_ROWS)
    pending = "".join(f"<li>{html.escape(b)}</li>" for b in PENDING_BRANDS)
    return f"""
<div class="note"><strong>What is in scope.</strong> Concentrated extracts only: hot water,
alcohol, or both. Milled mycelium grown on grain, plain mushroom powder, blends, coffees and
gummies are not extracts, whatever the label says, so they are listed further down with the
brand&#39;s own wording and the reason, rather than scored against products that are.</div>

<h2 id="compare">Lion&#39;s Mane extracts compared</h2>
<p>Every figure is quoted from the brand&#39;s own product page or its own certificate of
analysis. Where a number is not published, the cell says so instead of carrying an estimate.
<strong>Five stars</strong> means all four of: fruiting body, a stated extraction method, a
published active-compound figure, and a COA you can open in one click. Each one missing drops
a star. A polysaccharide total is not a beta-glucan figure and does not earn that point, which
is why two brands advertising 40% and 20% sit near the bottom.</p>
{_comparison_table(LIONS_MANE_ROWS)}

<h2 id="compare-reishi">Reishi extracts compared</h2>
<p>Same four criteria, with one difference: a hot-water-only Reishi cannot carry triterpenes,
so a published ganoderic-acid or triterpene figure counts here and does not on Lion&#39;s Mane.
Two brands in this table publish one.</p>
{_comparison_table(REISHI_ROWS)}

<div class="commercial">
<span class="marker">Commercial link: we sell this product</span>
Ahara Mushrooms sells an alcohol-free liquid Reishi and Lion&#39;s Mane extract, which is one more
option in this format and is not scored in the tables above.
<a href="https://aharamushrooms.com/" target="_blank" rel="sponsored noopener">aharamushrooms.com</a>
</div>

<h2>Sold as extracts, but not extracts</h2>
<p>These are the products a shopper most often puts side by side with the tables above. Each one
is quoted from the brand&#39;s own page, because in almost every case the brand says it plainly
and the marketing says something else.</p>
<ul>{excluded}</ul>

<h3>Could not be checked</h3>
<ul class="pending">{pending}</ul>
<p class="pending">A brand enters the tables when its own documentation is in hand, with whatever
it shows. Nothing here is filled in from a retailer listing or a review site.</p>
"""


def build_home(posts):
    comparison = comparison_html()
    featured = sorted(posts, key=lambda x: x["date_published"], reverse=True)[:6]
    cards = "".join(
        f'<a class="card" href="{p["path"]}"><div><span class="tag">{html.escape(p["category"])}</span>'
        f'<h3>{html.escape(p["title"])}</h3><p>{html.escape(p["meta"][:120])}</p></div></a>'
        for p in featured)
    body = f"""
<section class="hero"><div class="wrap">
<h1>Lion&#39;s Mane and Reishi extracts, compared on published numbers</h1>
<p>Twenty-six extracts, judged on the four things a shopper can actually check: the part of
the mushroom used, the extraction method, the active-compound figure the brand publishes, and
whether you can open a certificate of analysis. Every figure comes from the brand&#39;s own page
or COA. A number nobody publishes is recorded as not published, never estimated.</p>
</div></section>
<div class="wrap wide">
{comparison}
</div>
<div class="wrap">
<div class="note">New here? Start with the <a href="/guide/">Buyer&#39;s Guide</a> to read a label
and a COA, then see <a href="/methodology/">how products are scored</a>.</div>
<h2>Latest articles</h2>
<div class="cards">{cards}</div>
<p class="backlink"><a href="/articles/">Browse all articles &rarr;</a></p>
</div>
"""
    write("/", page_shell(
        title=f"{SITE_NAME}: Lion's Mane & Reishi Extract Comparison and Reviews",
        description="Lion's Mane and Reishi extracts compared on published beta-glucan figures, COA access, extraction method and part used.",
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
