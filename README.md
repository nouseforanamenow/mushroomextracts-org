# mushroomextracts.org

Independent, criteria-based reviews of Lion's Mane and Reishi mushroom extracts.
Static site hosted on GitHub Pages (deploy from branch `main`, path `/docs`).

## How it works
- Source content lives in `content/`:
  - `content/posts/*.md` — published articles (light markdown + front matter).
  - `content/scheduled/*.md` — future-dated queue. A post whose front-matter `date`
    is on or before today is promoted into `content/posts/` and published.
  - `content/pages/*.html` — the corrected core-page bodies (guide, methodology, faq, about).
- `_build/generate.py` renders everything into `docs/` (the served root): posts at
  root `/<slug>/`, core pages at `/<slug>/`, a homepage, an `/articles/` index,
  `sitemap.xml`, `robots.txt`, GA4, canonical tags, and the `CNAME`.
- `.github/workflows/publish-scheduled.yml` runs `generate.py` on a daily cron and
  commits any changes, so future-dated posts go live on their date (this replaces
  the retired WordPress future-dating mechanism). Pages serves `docs/` on push.

## Rebuild locally
    python3 _build/generate.py      # writes docs/

## Voice and safety
Independent reviewer (Consumer-Reports style). Structure/function only, no disease
claims. Never fabricate a lab/COA number or a study result. No links to other owned
sites.
