# com-gcfn — gaspecancer.org

Static bilingual site for the **Fondation du cancer de Gaspé / Gaspé Cancer Foundation**
(registered charity 875354300RR0001), migrated from WordPress on 2026-10-10.
Hosted on GitHub Pages. French is at the root (Charter of the French Language); English under `/en/`.

## Structure

| French | English |
|---|---|
| `/` (À propos) | `/en/about/` |
| `/fr/demande/` | `/en/assistance/` |
| `/fr/ressources/` | `/en/resources/` |
| `/fr/donner/` | `/en/donate/` |
| `/fr/adhesion/` | `/en/membership/` |
| `/fr/coordonnees/` | `/en/contact/` |

Old WordPress URLs redirect: `/fr/`, `/fr/organisation/`, `/fr/membriat/`, `/fr/nouvelles/`, `/en/`, `/en/news/`.
Dropped: demo blog posts (lorem ipsum), WooCommerce pages (cart, checkout, account).

- `tools/build.py` — generator. **All pages are generated; edit the script, not the HTML.**
- `assets/` — CSS, images, favicon. `docs/` — referral form and in-memoriam form (PDF).

## Editing

1. Open `tools/build.py`, edit `CONFIG` or page content.
2. Run `python3 tools/build.py` from the repo root (Python 3.8+, no dependencies).
3. Commit everything, including the regenerated HTML.

### Turning on Zeffy (after the account is verified)

In `CONFIG`, paste each campaign URL with `{lang}` in place of the language segment:

```python
"zeffy_donate": "https://www.zeffy.com/{lang}/donation-form/<slug>",
"zeffy_membership": "https://www.zeffy.com/{lang}/ticketing/<slug>",   # copy exact path from Zeffy "Share"
```

`{lang}` becomes `fr-CA` on French pages and `en-CA` on English pages. Until set, buttons show "Online soon".
We link out rather than embed: embedded Zeffy forms drop Apple Pay / Google Pay and the campaign description.

Also set `email` (an org-owned mailbox, e.g. info@gaspecancer.org) and `office_room` once confirmed.

## Deploy (Pages first, DNS second)

1. Push to `main` of `com-gcfn`. Settings → Pages → Deploy from branch → `main` / root.
2. Settings → Pages → Custom domain: `gaspecancer.org` (the `CNAME` file is already here). Wait for the DNS check.
3. At the DNS host for gaspecancer.org, **only** replace web records:
   - Apex `@` A: `185.199.108.153`, `185.199.109.153`, `185.199.110.153`, `185.199.111.153`
   - Apex `@` AAAA (optional): `2606:50c0:8000::153`, `2606:50c0:8001::153`, `2606:50c0:8002::153`, `2606:50c0:8003::153`
   - `www` CNAME → `<github-user>.github.io`
   - Remove the old A/CNAME records pointing to the WordPress host. **Do not touch MX, TXT (SPF/DKIM/DMARC) or other mail records.**
4. When the certificate is issued, tick **Enforce HTTPS**.
5. Keep the WordPress site reachable (e.g. on its ceegim.com host) for 30 days, then retire it.

Before DNS, the site previews at `https://<github-user>.github.io/com-gcfn/` (links are relative; only the 404 page assumes the root domain).

## Open items (client to confirm)

See the migration notes delivered with this repo. Key ones: office room number, territory served,
membership lapse rule, Interac e-Transfer policy, outdated resource listings, an org-owned email.
