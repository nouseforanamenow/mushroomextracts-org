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
    ("/compare/", "Compare"),
    ("/articles/", "Articles"),
    ("/guide/", "Buyer's Guide"),
    ("/methodology/", "Methodology"),
    ("/faq/", "FAQ"),
    ("/about/", "About"),
]

INDEXNOW_KEY = "501abdd9daa95113e6a2935e66c20175"

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
.rank{font-weight:800;color:var(--dark);font-size:1.05rem;text-align:center;width:38px}
.score{text-align:center;font-weight:700;color:var(--dark);white-space:nowrap}
.toppick{display:inline-block;background:var(--amber);color:#3a2a00;font-size:.63rem;font-weight:700;
text-transform:uppercase;letter-spacing:.05em;padding:2px 7px;border-radius:20px;margin-left:6px;vertical-align:middle}
.inline-marker{display:block;margin-top:6px;font-size:.7rem;font-weight:600;text-transform:uppercase;
letter-spacing:.04em;color:#92400e}
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
            "Lion&#39;s Mane and Reishi extracts, compared on published numbers.</p>"
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

CRITERIA = [
    ("Extraction depth and compound completeness", 25,
     "Is this a concentrated extract, and how completely does the maker disclose what is in it? "
     "Full compound mapping scores highest, a single standardized percentage scores in the middle, "
     "and an undisclosed extraction scores lowest."),
    ("Bioavailability and delivery format", 20,
     "How is the product built to be absorbed? Liquid sublingual delivery scores highest, "
     "capsules and powders in the middle, and anything diluted with its growing medium lowest."),
    ("Third-party testing and COA access", 20,
     "Is there current, accessible, independent testing? A per-lot certificate you can open in "
     "one click scores highest, a COA on request in the middle, a testing claim with no document lowest."),
    ("Source material", 15,
     "Fruiting body against mycelium on grain, the species named in full, and organic sourcing."),
    ("Label and sourcing transparency", 10,
     "Extraction method and ratio stated, no proprietary blends hiding the quantities, clear origin."),
    ("Value against verified quality", 10,
     "Price measured against what is actually proven to be inside, not the lowest sticker price."),
]
CRITERIA_KEYS = ["extraction", "bioavailability", "testing", "source", "transparency", "value"]

COMPARISON_COLUMNS = [
    "Brand / product", "Part used", "Extraction", "Published actives", "COA access", "Format",
]

# SCOPE: concentrated extracts only. A product is listed only where the brand's own page calls
# it an extract or states an extraction method or ratio. Mycelium grown on grain, plain mushroom
# powder, blends and gummies are not extracts and are listed under EXCLUDED_ROWS instead.
# Every cell is quoted from the brand's own page or its own COA; sources in
# Content/11_Microsite_Overhaul/mushroomextracts/brand_coa_scan.md.

LIONS_MANE_ROWS = [
    {
        "brand": "AHARA", "product": "Organic Lion\u2019s Mane Elixir", "commercial": True,
        "url": "https://aharamushrooms.com/products/ahara-organic-lions-mane-elixir-alcohol-free",
        "part": "Whole mushroom", "extraction": "Water, alcohol-free. No ethanol, no organic solvents",
        "actives": "Over 2,000 metabolites mapped, published in full rather than a single marker",
        "coa": ("yes", "One click: heavy metals, microbials and residual solvents, by Altitude Consulting, ILAC-MRA and PJLA accredited"),
        "format": "Alcohol-free liquid extract, sublingual dropper, 2 oz",
        "scores": {"extraction": 10, "bioavailability": 10, "testing": 9, "source": 8,
                   "transparency": 9, "value": 7},
        "verdict": "The only product here that publishes its whole compound profile instead of one "
                   "number, in the format that needs no capsule to dissolve first.",
    },
    {
        "brand": "Eversio Wellness", "product": "Lion\u2019s Mane capsules",
        "url": "https://www.eversiowellness.com/products/lions-mane-capsules",
        "part": "Fruiting body, grown outdoors on hardwood",
        "extraction": "Dual, hot water and alcohol (8:1)",
        "actives": "Beta-glucan 35%, standardized; 350 mg per 1,000 mg serving",
        "coa": ("yes", "One click, assayed by SGS"),
        "format": "Capsules",
        "scores": {"extraction": 8, "bioavailability": 6, "testing": 10, "source": 10,
                   "transparency": 9, "value": 7},
        "verdict": "The only brand in the survey with an outside lab standing behind its own "
                   "beta-glucan percentage.",
    },
    {
        "brand": "Nootropics Depot", "product": "Lion\u2019s Mane 1:1 fruiting body",
        "url": "https://nootropicsdepot.com/lions-mane-mushroom-extract-capsules/",
        "part": "Whole fruiting body, explicitly not mycelium-on-grain",
        "extraction": "Hot water (1:1)",
        "actives": "Beta-glucan 25%, standardized",
        "coa": ("yes", "10 per-lot COA PDFs, with heavy-metal and microbial panels"),
        "format": "Capsules, powder",
        "scores": {"extraction": 7, "bioavailability": 6, "testing": 10, "source": 10,
                   "transparency": 9, "value": 8},
        "verdict": "Ten per-lot certificates and a standardized figure on the label. Hot water only, "
                   "so one compound class.",
    },
    {
        "brand": "Mushroom Revival", "product": "Focus Lion\u2019s Mane capsules",
        "url": "https://www.mushroomrevival.com/products/focus-lions-mane-capsules",
        "part": "Fruiting body, no mycelium on grain",
        "extraction": "Dual; no ratio published",
        "actives": "Beta-glucan 37.1%, printed on the product page",
        "coa": ("yes", "One click from the product page"),
        "format": "Capsules",
        "scores": {"extraction": 8, "bioavailability": 6, "testing": 9, "source": 10,
                   "transparency": 8, "value": 8},
        "verdict": "Highest published beta-glucan of any Lion\u2019s Mane here, with the certificate "
                   "beside it. No ratio stated.",
    },
    {
        "brand": "Oriveda", "product": "Lion\u2019s Mane extract",
        "url": "https://oriveda.com/coa.php",
        "part": "Fruiting body", "extraction": "Hot water (1:1)",
        "actives": "Beta-glucan published per lot",
        "coa": ("yes", "Full COAs published"),
        "format": "Capsules",
        "scores": {"extraction": 8, "bioavailability": 6, "testing": 10, "source": 10,
                   "transparency": 8, "value": 6},
        "verdict": "Publishes complete certificates including glucan figures. Capsules only, and "
                   "imported, which costs it on value.",
    },
    {
        "brand": "Real Mushrooms", "product": "Lion\u2019s Mane extract",
        "url": "https://realmushrooms.com/product/lions-mane-mushroom-powder/",
        "part": "Fruiting body", "extraction": "Hot water",
        "actives": "Beta-glucan \u201cover 30%\u201d guaranteed",
        "coa": ("part", "Third-party tested, COA on request rather than one click"),
        "format": "Powder, capsules",
        "scores": {"extraction": 7, "bioavailability": 6, "testing": 7, "source": 10,
                   "transparency": 8, "value": 8},
        "verdict": "A real published guarantee held behind a request form, which is where it loses "
                   "ground to the brands above.",
    },
    {
        "brand": "Hifas da Terra", "product": "Mico Leo",
        "url": "https://hifasdaterra.co.uk/products/mico-leo-extract-vitamin-c",
        "part": "Fruiting body only",
        "extraction": "Concentrated extract; solvent not published",
        "actives": "Beta-(1,3)(1,6)-D-glucans 200 mg per 2 capsules; 52.34% in the COA",
        "coa": ("yes", "Six PDFs on the product page; the glucan assay is their own lab"),
        "format": "Capsules",
        "scores": {"extraction": 8, "bioavailability": 6, "testing": 8, "source": 10,
                   "transparency": 6, "value": 5},
        "verdict": "Unusually complete paperwork, assayed in-house, at the highest price per "
                   "capsule in the table.",
    },
    {
        "brand": "Birch Boys", "product": "Organic Lion\u2019s Mane tincture",
        "url": "https://birchboys.com/products/lions-mane-tincture",
        "part": "Fruiting body only, hardwood-grown",
        "extraction": "Double: water at 178\u00b0F for 72 hours, plus 95% organic cane alcohol",
        "actives": "None for the bottled tincture; the 6% beta-glucan figure describes a reference powder",
        "coa": ("off", "One Medallion Labs PDF, on the process page rather than the product page"),
        "format": "Tincture",
        "scores": {"extraction": 6, "bioavailability": 8, "testing": 6, "source": 9,
                   "transparency": 8, "value": 8},
        "verdict": "The clearest description of an extraction process anywhere in this survey, "
                   "attached to a number that describes a different product.",
    },
    {
        "brand": "FreshCap", "product": "Organic Lion\u2019s Mane",
        "url": "https://freshcap.com/products/lions-mane-capsules",
        "part": "Fruiting body", "extraction": "Dual (14:1)",
        "actives": "Beta-glucan 31% or higher, standardized",
        "coa": ("no", "No COA on the site; a blog post describes the testing"),
        "format": "Capsules, powder, stick packs",
        "scores": {"extraction": 8, "bioavailability": 6, "testing": 4, "source": 10,
                   "transparency": 8, "value": 8},
        "verdict": "A strong ratio and a strong number with nothing published to check either against.",
    },
    {
        "brand": "Gaia Herbs", "product": "Lion\u2019s Mane Mushroom",
        "url": "https://www.gaiaherbs.com/products/lions-mane-mushroom",
        "part": "Fruiting body, no mycelium, grain or growing medium",
        "extraction": "Extract; method not stated. 450 mg equals 2.5 g dried",
        "actives": "Beta-glucans 83 mg or more per serving",
        "coa": ("yes", "On-site results table, ISO/IEC 17025 accreditation 107080"),
        "format": "Capsules",
        "scores": {"extraction": 6, "bioavailability": 6, "testing": 8, "source": 10,
                   "transparency": 6, "value": 7},
        "verdict": "A verified minimum per serving from an accredited lab, on a product that never "
                   "says how it was extracted.",
    },
]

REISHI_ROWS = [
    {
        "brand": "AHARA", "product": "Organic Reishi Elixir", "commercial": True,
        "url": "https://aharamushrooms.com/products/ahara-organic-reishi-elixir-alcohol-free",
        "part": "Whole mushroom", "extraction": "Water, alcohol-free. No ethanol, no organic solvents",
        "actives": "Over 2,000 metabolites mapped, published in full rather than a single marker",
        "coa": ("yes", "One click: heavy metals, microbials and residual solvents, by Altitude Consulting, ILAC-MRA and PJLA accredited"),
        "format": "Alcohol-free liquid extract, sublingual dropper, 2 oz",
        "scores": {"extraction": 10, "bioavailability": 10, "testing": 9, "source": 8,
                   "transparency": 9, "value": 7},
        "verdict": "Publishes the whole compound profile rather than one marker, and is alcohol-free "
                   "without giving up the compounds alcohol is usually needed for.",
    },
    {
        "brand": "Eversio Wellness", "product": "Reishi capsules",
        "url": "https://www.eversiowellness.com/products/reishi-mushroom-supplement",
        "part": "Fruiting body, 100%", "extraction": "Dual, hot water and alcohol (15:1)",
        "actives": "Beta-glucan 45%, standardized; triterpenes 25 mg per 500 mg serving",
        "coa": ("yes", "One click, assayed by SGS"),
        "format": "Capsules",
        "scores": {"extraction": 9, "bioavailability": 6, "testing": 10, "source": 10,
                   "transparency": 9, "value": 7},
        "verdict": "The highest standardized beta-glucan in the survey, on an outside lab\u2019s "
                   "certificate, with triterpenes declared as well.",
    },
    {
        "brand": "Oriveda", "product": "Reishi Primo",
        "url": "https://oriveda.com/coa.php",
        "part": "Fruiting body", "extraction": "Dual, alcohol-free",
        "actives": "Ganoderic acids 6% or higher",
        "coa": ("yes", "Full COAs published"),
        "format": "Capsules",
        "scores": {"extraction": 9, "bioavailability": 6, "testing": 10, "source": 10,
                   "transparency": 8, "value": 6},
        "verdict": "One of only two capsule products here publishing a triterpene figure and the "
                   "certificate behind it.",
    },
    {
        "brand": "Nootropics Depot", "product": "Red Reishi 8:1 / 1:1",
        "url": "https://nootropicsdepot.com/reishi-mushroom-extract-capsules/",
        "part": "Whole fruiting body", "extraction": "Hot water (8:1 and 1:1 lines)",
        "actives": "Beta-glucan 35% minimum, guaranteed; triterpenes not published as a percentage",
        "coa": ("yes", "Per-lot COA PDFs"),
        "format": "Capsules, powder",
        "scores": {"extraction": 7, "bioavailability": 6, "testing": 10, "source": 10,
                   "transparency": 9, "value": 8},
        "verdict": "Hot water cannot carry triterpenes and the label does not pretend otherwise, "
                   "which is worth more than a number that cannot be true.",
    },
    {
        "brand": "Mushroom Revival", "product": "Calm Reishi capsules",
        "url": "https://www.mushroomrevival.com/products/calm-reishi-mushroom-capsules",
        "part": "Fruiting body", "extraction": "Dual; no ratio published",
        "actives": "Beta-glucan 27.8%, printed on the product page",
        "coa": ("yes", "One click from the product page"),
        "format": "Capsules",
        "scores": {"extraction": 8, "bioavailability": 6, "testing": 9, "source": 10,
                   "transparency": 8, "value": 8},
        "verdict": "Number on the page, certificate beside it, no ratio and no triterpene figure.",
    },
    {
        "brand": "Hifas da Terra", "product": "Mico Rei",
        "url": "https://hifasdaterra.co.uk/products/mico-rei-pure-eco-extract-of-reishi",
        "part": "Fruiting body only",
        "extraction": "Concentrated extract; solvent and ratio not published",
        "actives": "Beta-glucans 248 mg and triterpenoids 50 mg per 2 capsules; 58% polysaccharides",
        "coa": ("yes", "Six PDFs on the product page; the glucan assay is their own lab"),
        "format": "Capsules",
        "scores": {"extraction": 8, "bioavailability": 6, "testing": 8, "source": 10,
                   "transparency": 6, "value": 5},
        "verdict": "Milligrams for both compound classes, assayed in-house, at the top of the price range.",
    },
    {
        "brand": "Real Mushrooms", "product": "Reishi extract",
        "url": "https://realmushrooms.com/product/reishi-mushroom-powder/",
        "part": "Fruiting body", "extraction": "Hot water",
        "actives": "Beta-glucan guaranteed across the line; the Reishi-specific figure is unverified",
        "coa": ("part", "Third-party tested, COA on request rather than one click"),
        "format": "Powder, capsules",
        "scores": {"extraction": 6, "bioavailability": 6, "testing": 7, "source": 10,
                   "transparency": 8, "value": 8},
        "verdict": "The line guarantee is real, the figure for this particular product is not published.",
    },
    {
        "brand": "Gaia Herbs", "product": "Reishi Mushroom",
        "url": "https://www.gaiaherbs.com/products/reishi-mushroom",
        "part": "Fruiting body, no fillers, starch, grain or mycelium",
        "extraction": "Extract; method not stated. 450 mg equals 2.5 g dried",
        "actives": "Beta-glucans 113 mg or more per serving; no triterpene figure",
        "coa": ("yes", "On-site results table, ISO/IEC 17025 accreditation 107080"),
        "format": "Capsules",
        "scores": {"extraction": 6, "bioavailability": 6, "testing": 8, "source": 10,
                   "transparency": 6, "value": 7},
        "verdict": "An accredited minimum per serving, on a product that never says how it was extracted.",
    },
    {
        "brand": "FreshCap", "product": "Organic Reishi",
        "url": "https://freshcap.com/products/reishi-capsules",
        "part": "Fruiting body on the panel; the FAQ on the same page says fruiting body and spore",
        "extraction": "Dual (14:1)",
        "actives": "Beta-glucan 27% and triterpenes 1.4%, both standardized",
        "coa": ("no", "No COA on the site; a blog post describes the testing"),
        "format": "Capsules, powder",
        "scores": {"extraction": 9, "bioavailability": 6, "testing": 4, "source": 8,
                   "transparency": 7, "value": 8},
        "verdict": "Declares both compound classes, publishes nothing to check them, and contradicts "
                   "itself on what part of the mushroom is in the bottle.",
    },
    {
        "brand": "Birch Boys", "product": "Organic Reishi tincture",
        "url": "https://birchboys.com/products/reishi-tincture",
        "part": "Fruiting body only, wild-harvested. The species is Ganoderma tsugae, not G. lucidum",
        "extraction": "Double: water at 178\u00b0F for 72 hours, plus 95% organic cane alcohol",
        "actives": "None for the bottled tincture; the 4% beta-glucan figure describes a reference powder",
        "coa": ("off", "One Medallion Labs PDF, on the process page rather than the product page"),
        "format": "Tincture",
        "scores": {"extraction": 6, "bioavailability": 8, "testing": 6, "source": 7,
                   "transparency": 8, "value": 8},
        "verdict": "A different species from every other row, which the brand discloses and most "
                   "shoppers will not notice.",
    },
]

EXCLUDED_ROWS = [
    ("Host Defense", "Mycelium grown on fermented brown rice, milled rather than extracted. Their own FAQ: "
     "\u201cwe don\u2019t isolate or concentrate any particular compounds in our powdered products.\u201d "
     "The \u201cover 55% polysaccharides\u201d guarantee is a polysaccharide total on a rice matrix, not a "
     "beta-glucan figure."),
    ("Om Mushrooms", "Mycelial biomass and fruit body cultured on whole oats, with the oats included in the "
     "2 g serving. Their own FAQ: \u201cNo. We don\u2019t use hot water or alcohol extraction.\u201d"),
    ("Genius Mushrooms", "Mycelium on oats, and extract-free by design: \u201cMade with 100% extract-free, "
     "100% organic mushrooms.\u201d"),
    ("Solaray", "Fermented mycelium cultured on whole oats or brown rice. No extraction method and no ratio published."),
    ("Nutricost", "Labelled mushroom powder, not an extract. No method, no ratio, no actives figure."),
    ("NOW Foods", "The Lion\u2019s Mane is sold as \u201cextract powder\u201d with no method, no ratio, no actives "
     "figure and no COA, so there is nothing to score; the Rei-Shi product is a reishi and shiitake blend."),
    ("Swanson", "Full Spectrum is \u201cwhole reishi mushroom rather than a concentrated extract\u201d in their own "
     "words. The standardized products publish a polysaccharide total, which includes grain starch, and no method."),
    ("Micro Ingredients", "\u201cFreeze-dried extract\u201d is a drying step, not an extraction. The Reishi powder "
     "claims a 100:1 ratio and does not state what part of the mushroom is in it."),
    ("Terrasoul Superfoods", "A genuine 4:1 water extract from log-grown fruiting bodies, but no actives figure "
     "and no COA, so there is nothing to score it on."),
    ("Double Wood", "The Lion\u2019s Mane is not an extract in the brand\u2019s own words. The Reishi is a 4:1 "
     "extract whose published COA assays identity, metals and microbials, but no actives."),
    ("Toniiq", "Publishes the best single document in the survey, a one-click COA with a Megazyme beta-glucan "
     "assay, but the product page calls it whole mushroom powder and states no extraction method."),
    ("Sun Potion", "Their own spec table: \u201cFull-spectrum mushroom powder (not an extract)\u201d, despite "
     "publishing 52.2% beta-glucans on a recent Lion\u2019s Mane lot."),
    ("Four Sigmatic", "No single-species Lion\u2019s Mane or Reishi extract. Every mushroom product is a blend, "
     "coffee, cocoa or elixir packet."),
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


def _total(row):
    return round(sum(row["scores"][k] * w / 100 for (_, w, _), k
                     in zip(CRITERIA, CRITERIA_KEYS)), 1)


def _ranked(rows):
    body = ""
    for i, r in enumerate(rows, start=1):
        tag = ' <span class="toppick">Top pick</span>' if i == 1 else ""
        mark = ('<span class="inline-marker">Commercial link: we sell this product</span>'
                if r.get("commercial") else "")
        body += (
            "<tr>"
            f'<td class="rank">{i}</td>'
            f'<td class="brandcell"><a href="{r["url"]}" target="_blank" rel="{"sponsored noopener" if r.get("commercial") else "noopener nofollow"}">'
            f'{html.escape(r["brand"])}</a>{tag}<span>{html.escape(r["product"])}</span>{mark}</td>'
            f'<td>{html.escape(r["format"])}</td>'
            f'<td class="score">{_total(r):.1f}</td>'
            f'<td>{html.escape(r["verdict"])}</td>'
            "</tr>")
    return ('<div class="tscroll"><table class="ctable"><thead><tr>'
            "<th>#</th><th>Brand and product</th><th>Format</th><th>Score</th>"
            "<th>One-line verdict</th></tr></thead>"
            f"<tbody>{body}</tbody></table></div>")


def _criteria_table():
    rows = "".join(
        f"<tr><td><strong>{html.escape(n)}</strong></td><td class=\"score\">{w}%</td>"
        f"<td>{html.escape(d)}</td></tr>" for n, w, d in CRITERIA)
    return ('<div class="tscroll"><table class="ctable"><thead><tr><th>Criterion</th>'
            "<th>Weight</th><th>What we look for</th></tr></thead>"
            f"<tbody>{rows}</tbody></table></div>")


def _score_table(rows):
    head = "".join(f'<th>{html.escape(n.split(" and ")[0].split(" against ")[0])} ({w})</th>'
                   for n, w, _ in CRITERIA)
    body = ""
    for r in rows:
        cells = "".join(f'<td class="score">{r["scores"][k]}</td>' for k in CRITERIA_KEYS)
        body += (f'<tr><td class="brandcell">{html.escape(r["brand"])}</td>{cells}'
                 f'<td class="score"><strong>{_total(r):.1f}</strong></td></tr>')
    return ('<div class="tscroll"><table class="ctable"><thead><tr><th>Brand</th>'
            f"{head}<th>Total</th></tr></thead><tbody>{body}</tbody></table></div>")


def _evidence_table(rows):
    head = "".join(f"<th>{html.escape(c)}</th>" for c in COMPARISON_COLUMNS)
    body = ""
    for r in rows:
        body += (
            "<tr>"
            f'<td class="brandcell">{html.escape(r["brand"])}<span>{html.escape(r["product"])}</span></td>'
            f'<td>{html.escape(r["part"])}</td>'
            f'<td>{html.escape(r["extraction"])}</td>'
            f'<td>{html.escape(r["actives"])}</td>'
            f"<td>{_coa_cell(*r['coa'])}</td>"
            f'<td>{html.escape(r["format"])}</td>'
            "</tr>")
    return ('<div class="tscroll"><table class="ctable"><thead><tr>'
            f"{head}</tr></thead><tbody>{body}</tbody></table></div>")


SCOPE_NOTE = """<div class="note"><strong>What is in scope.</strong> Concentrated extracts only:
hot water, alcohol, or both. A product is ranked only where the brand\u2019s own page calls it an
extract or states an extraction method or ratio. Mycelium grown on grain, plain mushroom powder,
blends, coffees and gummies are not extracts, whatever the label says, and are listed separately
with the brand\u2019s own wording and the reason.</div>"""


def _species_block(title, anchor, rows, intro):
    return f"""
<h2 id="{anchor}">{title}</h2>
<p>{intro}</p>
{_ranked(rows)}
<h3>Scores by criterion</h3>
{_score_table(rows)}
<h3>The evidence behind each score</h3>
<p>Every figure below is quoted from the brand\u2019s own product page or its own certificate of
analysis. Where a number is not published, the cell says so instead of carrying an estimate.</p>
{_evidence_table(rows)}
"""


def comparison_tables():
    return SCOPE_NOTE + _species_block(
        "Lion\u2019s Mane extracts ranked", "compare", LIONS_MANE_ROWS,
        "Ten concentrated Lion\u2019s Mane extracts, scored against the weighted criteria below.")+ _species_block(
        "Reishi extracts ranked", "compare-reishi", REISHI_ROWS,
        "Ten concentrated Reishi extracts, scored the same way, with one difference: a hot-water-only "
        "Reishi cannot carry triterpenes, so a published triterpene or ganoderic-acid figure counts "
        "here and does not on Lion\u2019s Mane.") + f"""
<h2 id="criteria">How the scores are built</h2>
<p>Six weighted criteria, applied identically to every product in both tables.</p>
{_criteria_table()}
"""


def comparison_home():
    return comparison_tables() + """
<p class="backlink"><a href="/compare/">Full comparison: how every cell was checked, the brands
that do not sell an extract at all, and the source for each figure &rarr;</a></p>
"""


def _source_list():
    seen, items = set(), []
    for r in LIONS_MANE_ROWS + REISHI_ROWS:
        if r["url"] in seen:
            continue
        seen.add(r["url"])
        items.append(f'<li>{html.escape(r["brand"])}, {html.escape(r["product"])} &mdash; '
                     f'<a href="{r["url"]}" target="_blank" rel="{"sponsored noopener" if r.get("commercial") else "noopener nofollow"}">'
                     f'{html.escape(r["url"])}</a></li>')
    return "".join(items)


def comparison_full():
    excluded = "".join(
        f"<li><strong>{html.escape(n)}</strong> &mdash; {t}</li>"
        for n, t in EXCLUDED_ROWS)
    pending = "".join(f"<li>{html.escape(b)}</li>" for b in PENDING_BRANDS)
    return comparison_tables() + f"""
<h2 id="not-extracts">Sold as extracts, but not extracts</h2>
<p>These are the products a shopper most often puts beside the tables above. Each is quoted from
the brand\u2019s own page, because in almost every case the brand says it plainly and the marketing
says something else.</p>
<ul>{excluded}</ul>

<h2 id="method">How each cell was checked</h2>
<p>One pass, against each brand\u2019s own pages and its own COA documents. No retailer listing,
no review site and no affiliate roundup was used as a source for any figure.</p>
<ul>
<li><strong>Part used</strong> comes from the Supplement Facts panel where one exists. On several
brands that panel is an image rather than text, so the wording was read off the label image on the
brand\u2019s own page.</li>
<li><strong>Extraction</strong> counts only where the brand states a method or a ratio.
&ldquo;Freeze-dried extract&rdquo; is a drying step, not an extraction.</li>
<li><strong>Published actives</strong> separates beta-glucan from polysaccharides on purpose. A
polysaccharide total on a grain-grown product includes the starch from the grain, so the two are
not comparable and are never merged into one cell.</li>
<li><strong>COA access</strong> is Published only where a reader can open the document in one click.
A testing claim in body copy, or a blog post about testing, is recorded as Not available.</li>
</ul>

<h2 id="pending">Could not be checked</h2>
<ul class="pending">{pending}</ul>

<h2 id="sources">Sources</h2>
<p class="pending">Every ranked product, with the page its figures were read from.</p>
<ul class="pending">{_source_list()}</ul>
"""


def comparison_jsonld():
    items = []
    for i, r in enumerate(LIONS_MANE_ROWS + REISHI_ROWS, start=1):
        items.append({
            "@type": "ListItem", "position": i,
            "name": f'{r["brand"]} {r["product"]}', "url": r["url"],
        })
    return json.dumps({
        "@context": "https://schema.org", "@type": "ItemList",
        "name": "Lion's Mane and Reishi extracts ranked",
        "description": ("Twenty Lion's Mane and Reishi extracts ranked on extraction depth, "
                        "delivery format, COA access, source material, transparency and value."),
        "numberOfItems": len(items), "itemListElement": items,
    }, separators=(",", ":"))


def build_compare_page():
    body = f'''
<section class="hero"><div class="wrap">
<h1>Lion&#39;s Mane and Reishi extracts, ranked</h1>
<p>Twenty concentrated extracts scored against six weighted criteria, every figure checked against
the brand&#39;s own product page or its own certificate of analysis, and fourteen brands found to be
selling something that is not an extract at all.</p>
</div></section>
<div class="wrap wide">
{comparison_full()}
<p class="backlink"><a href="/">&larr; Home</a></p>
</div>
'''
    write("/compare/", page_shell(
        title=f"Lion's Mane & Reishi Extracts Ranked: 20 Extracts, 6 Criteria | {SITE_NAME}",
        description=("Twenty Lion's Mane and Reishi extracts ranked on extraction depth, delivery "
                     "format, COA access, source material and transparency. Every figure from the "
                     "brand's own page or COA."),
        canonical=f"{BASE_URL}/compare/", body=body, active_path="/compare/",
        jsonld=comparison_jsonld()))


def build_home(posts):
    comparison = comparison_home()
    featured = sorted(posts, key=lambda x: x["date_published"], reverse=True)[:6]
    cards = "".join(
        f'<a class="card" href="{p["path"]}"><div><span class="tag">{html.escape(p["category"])}</span>'
        f'<h3>{html.escape(p["title"])}</h3><p>{html.escape(p["meta"][:120])}</p></div></a>'
        for p in featured)
    body = f"""
<section class="hero"><div class="wrap">
<h1>The 20 Lion&#39;s Mane and Reishi extracts, ranked</h1>
<p>Concentrated extracts only, scored against six weighted criteria: extraction depth and how
completely the maker discloses what is inside, delivery format, certificate of analysis access,
source material, label transparency and value. Every figure comes from the brand&#39;s own page or
its own COA. A number nobody publishes is recorded as not published, never estimated.</p>
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
    # IndexNow key file. Bing, Yandex and Seznam fetch this to prove we own the host
    # before accepting a submission, so it must survive every rebuild.
    (OUT / "501abdd9daa95113e6a2935e66c20175.txt").write_text("501abdd9daa95113e6a2935e66c20175", encoding="utf-8")

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
    build_compare_page()
    build_articles_index(posts)

    (OUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {BASE_URL}/sitemap.xml\n", encoding="utf-8")

    urls = [{"path": "/", "lastmod": TODAY}, {"path": "/compare/", "lastmod": TODAY},
            {"path": "/articles/", "lastmod": TODAY}]
    for slug, *_ in core:
        urls.append({"path": f"/{slug}/", "lastmod": TODAY})
    for p in posts:
        urls.append({"path": p["path"], "lastmod": p["date_modified"]})
    build_sitemap(urls)

    print(f"Built {len(posts)} posts + {len(core)} core pages + home + compare + articles -> {OUT}")
    print(f"CNAME={CNAME_DOMAIN or '(none)'} | sitemap urls={len(urls)}")


if __name__ == "__main__":
    main()
