#!/usr/bin/env python3
"""Static site generator for gaspecancer.org (repo: com-gcfn).

Run from the repo root:  python3 tools/build.py
Edit CONFIG below (Zeffy links, email, room number) and rebuild.
All links are relative, so the site works both on the custom domain and on
the <user>.github.io/com-gcfn/ project URL.
"""
import html, os, pathlib, datetime, re

ROOT = pathlib.Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------
# CONFIG — fill these in once the Zeffy account and mailbox exist.
# Zeffy links: paste the campaign URL with {lang} where the language goes,
# e.g. "https://www.zeffy.com/{lang}/donation-form/gaspe-cancer-foundation-donations"
# {lang} becomes "fr-CA" on French pages and "en-CA" on English pages.
# Leave a value as None and the site shows an offline fallback instead.
# ---------------------------------------------------------------------------
CONFIG = {
    "zeffy_donate": None,        # Zeffy donation form (one-time, monthly, in memoriam)
    "zeffy_membership": None,    # Zeffy membership form (Individual $15 / Couple $25)
    "contact_form": None,        # Optional: Zoho Forms (or other) contact form URL
    "email": None,               # e.g. "info@gaspecancer.org" — org-owned mailbox only
    "office_room": None,         # e.g. "413" — CONFIRM: site says 413 and 143, old PDF says 243
    "charity_no": "875354300RR0001",
    "site_url": "https://gaspecancer.org",
}

ORG_FR = "Fondation du cancer de Gaspé"
ORG_EN = "Gaspé Cancer Foundation"
YEAR = datetime.date.today().year

# Page registry: key -> (fr_path, en_path)
PAGES = {
    "home":       ("index.html",                "en/about/index.html"),
    "assistance": ("fr/demande/index.html",     "en/assistance/index.html"),
    "resources":  ("fr/ressources/index.html",  "en/resources/index.html"),
    "donate":     ("fr/donner/index.html",      "en/donate/index.html"),
    "membership": ("fr/adhesion/index.html",    "en/membership/index.html"),
    "contact":    ("fr/coordonnees/index.html", "en/contact/index.html"),
}
NAV = ["home", "assistance", "resources", "membership", "contact"]
LABELS = {
    "fr": {"home": "À propos", "assistance": "Demander de l’aide", "resources": "Ressources",
           "donate": "Faire un don", "membership": "Devenir membre", "contact": "Nous joindre"},
    "en": {"home": "About", "assistance": "Request Assistance", "resources": "Resources",
           "donate": "Donate", "membership": "Become a Member", "contact": "Contact Us"},
}
# Old WordPress URLs that must keep working -> new page (lang, key)
REDIRECTS = {
    "fr/index.html": ("fr", "home"),
    "fr/organisation/index.html": ("fr", "home"),
    "fr/membriat/index.html": ("fr", "membership"),
    "fr/nouvelles/index.html": ("fr", "home"),
    "en/index.html": ("en", "home"),
    "en/news/index.html": ("en", "home"),
}

def e(s):
    return html.escape(s, quote=True)

def rel(from_path, to_path):
    """Relative URL from one output file to another (directory-style URLs)."""
    src_dir = os.path.dirname(from_path) or "."
    target = to_path[:-len("index.html")] if to_path.endswith("index.html") else to_path
    r = os.path.relpath(target or ".", src_dir)
    if r == ".":
        return "./"
    return r + ("/" if target.endswith("/") or target == "" else "")

def url(lang, key, cur):
    return rel(cur, PAGES[key][0 if lang == "fr" else 1])

def asset(cur, name):
    return os.path.relpath(f"assets/{name}", os.path.dirname(cur) or ".")

def doc(cur, name):
    return os.path.relpath(f"docs/{name}", os.path.dirname(cur) or ".")

def zeffy(kind, lang):
    u = CONFIG.get(kind)
    return u.replace("{lang}", "fr-CA" if lang == "fr" else "en-CA") if u else None

def zbutton(kind, lang, label, cls="btn"):
    u = zeffy(kind, lang)
    if u:
        return f'<a class="{cls}" href="{e(u)}" rel="noopener">{e(label)}</a>'
    soon = "En ligne bientôt" if lang == "fr" else "Online soon"
    return f'<span class="btn disabled" aria-disabled="true" title="{soon}">{e(label)} · {soon}</span>'

def office(lang):
    room = CONFIG["office_room"]
    if lang == "fr":
        r = f", local {room}" if room else ""
        return f"Hôpital Hôtel-Dieu de Gaspé{r}<br>215, boulevard de York Ouest<br>Gaspé (Québec) G4X 2W2"
    r = f", Room {room}" if room else ""
    return f"Hôtel-Dieu de Gaspé Hospital{r}<br>215 York Boulevard West<br>Gaspé, Quebec G4X 2W2"

MAIL_FR = f"{ORG_FR}<br>C.P. 6078<br>Gaspé (Québec) G4X 2R6"
MAIL_EN = f"{ORG_EN}<br>P.O. Box 6078<br>Gaspé, Quebec G4X 2R6"

def email_line(lang):
    em = CONFIG["email"]
    if not em:
        return ""
    lbl = "Courriel" if lang == "fr" else "Email"
    return f'<dt>{lbl}</dt><dd><a href="mailto:{e(em)}">{e(em)}</a></dd>'

# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------
CUR = ' aria-current="page"'

def layout(lang, key, cur, title, desc, body):
    other = "en" if lang == "fr" else "fr"
    L = LABELS[lang]
    fr_url = CONFIG["site_url"] + "/" + PAGES[key][0].replace("index.html", "")
    en_url = CONFIG["site_url"] + "/" + PAGES[key][1].replace("index.html", "")
    nav = "".join(
        f'<a href="{url(lang, k, cur)}"{CUR if k == key else ""}>{e(L[k])}</a>'
        for k in NAV)
    lang_label = "English" if lang == "fr" else "Français"
    donate_lbl = L["donate"]
    menu = "Menu"
    org1, org2 = (ORG_FR, ORG_EN) if lang == "fr" else (ORG_EN, ORG_FR)
    f = FOOT[lang]
    footer_links = "".join(f'<li><a href="{url(lang, k, cur)}">{e(L[k])}</a></li>' for k in
                           ["home", "assistance", "resources", "donate", "membership", "contact"])
    return f"""<!doctype html>
<html lang="{'fr-CA' if lang == 'fr' else 'en-CA'}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)} | {e(org1)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{fr_url if lang == 'fr' else en_url}">
<link rel="alternate" hreflang="fr-CA" href="{fr_url}">
<link rel="alternate" hreflang="en-CA" href="{en_url}">
<link rel="alternate" hreflang="x-default" href="{fr_url}">
<meta property="og:title" content="{e(title)} | {e(org1)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:image" content="{CONFIG['site_url']}/assets/care.jpg">
<meta property="og:locale" content="{'fr_CA' if lang == 'fr' else 'en_CA'}">
<link rel="icon" type="image/png" href="{asset(cur, 'favicon.png')}">
<link rel="apple-touch-icon" href="{asset(cur, 'apple-touch-icon.png')}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Source+Sans+3:wght@400;600;700&family=Source+Serif+4:wght@600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{asset(cur, 'site.css')}">
</head>
<body>
<a class="skip" href="#main">{'Aller au contenu' if lang == 'fr' else 'Skip to content'}</a>
<header class="site-header">
 <div class="wrap">
  <a class="brand" href="{url(lang, 'home', cur)}">
   <img src="{asset(cur, 'emblem.png')}" alt="" width="52" height="47">
   <span><span class="n1">{e(org1)}</span><span class="n2">{e(org2)}</span></span>
  </a>
  <button class="menu-toggle" aria-expanded="false" aria-controls="nav">{menu}</button>
  <nav class="nav" id="nav" aria-label="{'Navigation principale' if lang == 'fr' else 'Main navigation'}">
   {nav}
   <a class="lang" href="{url(other, key, cur)}" lang="{other}" hreflang="{other}">{lang_label}</a>
   <a class="btn" href="{url(lang, 'donate', cur)}">{e(donate_lbl)}</a>
  </nav>
 </div>
</header>
<main id="main">
{body}
</main>
<footer class="site-footer">
 <div class="wrap">
  <div class="cols">
   <div>
    <h4>{e(org1)}</h4>
    <p>{f['blurb']}</p>
    <p>{f['charity']} {CONFIG['charity_no']}</p>
   </div>
   <div>
    <h4>{f['mail']}</h4>
    <p>{MAIL_FR if lang == 'fr' else MAIL_EN}</p>
    <h4>{f['office']}</h4>
    <p>{office(lang)}<br>{f['hours']}</p>
   </div>
   <div>
    <h4>{f['links']}</h4>
    <ul>{footer_links}<li><a href="https://www.facebook.com/gaspecancer" rel="noopener">Facebook</a></li></ul>
   </div>
  </div>
  <div class="legal">© {YEAR} {e(org1)}. {f['legal']}</div>
 </div>
</footer>
<script>
(function(){{var b=document.querySelector('.menu-toggle'),n=document.getElementById('nav');
if(b)b.addEventListener('click',function(){{var o=n.classList.toggle('open');b.setAttribute('aria-expanded',o)}});}})();
</script>
</body>
</html>
"""

FOOT = {
    "fr": {"blurb": "Organisme de bienfaisance entièrement bénévole qui aide financièrement les personnes atteintes de cancer devant se déplacer hors de la région pour leurs traitements.",
           "charity": "N° d’enregistrement d’organisme de bienfaisance :",
           "mail": "Adresse postale", "office": "Bureau", "hours": "Ouvert le vendredi, de 13 h à 15 h",
           "links": "Liens", "legal": "Ne pas confondre avec l’Association du cancer de l’Est du Québec ni avec la Société canadienne du cancer."},
    "en": {"blurb": "An all-volunteer registered charity providing financial aid to people with cancer who must travel outside the region for treatment.",
           "charity": "Charitable registration number:",
           "mail": "Mailing address", "office": "Office", "hours": "Open Fridays, 1 p.m. to 3 p.m.",
           "links": "Links", "legal": "Not affiliated with the Association du cancer de l’Est du Québec or the Canadian Cancer Society."},
}

def head(title, lead):
    return f'<div class="page-head"><div class="wrap"><h1>{title}</h1><p>{lead}</p></div></div>'

# ---------------------------------------------------------------------------
# Content
# ---------------------------------------------------------------------------
STATS = [  # (value, fr, en) — "donations received" removed: EN said 385,000, FR said 900,000.
    ("1 282", "1,282", "Membres", "Members"),
    ("124", "124", "Bénévoles", "Volunteers"),
    ("10 896", "10,896", "Heures de bénévolat", "Volunteer hours"),
    ("255", "255", "Membres aidés", "Members helped"),
    ("274 006 $", "$274,006", "Versés en aide", "Paid out in aid"),
]

CANNOT = {
    "fr": ["Il ne peut pas briser l’amour", "Il ne peut pas anéantir l’espoir", "Il ne peut pas affaiblir la foi",
           "Il ne peut pas détruire la paix", "Il ne peut pas mettre fin à l’amitié", "Il ne peut pas effacer les souvenirs",
           "Il ne peut pas réduire le courage au silence", "Il ne peut pas envahir l’âme",
           "Il ne peut pas voler la vie éternelle", "Il ne peut pas vaincre l’esprit"],
    "en": ["It cannot cripple love", "It cannot shatter hope", "It cannot corrode faith", "It cannot destroy peace",
           "It cannot kill friendship", "It cannot suppress memories", "It cannot silence courage",
           "It cannot invade the soul", "It cannot steal eternal life", "It cannot conquer the spirit"],
}

def page_home(lang, cur):
    fr = lang == "fr"
    stats = "".join(f'<div class="stat"><b>{s[0] if fr else s[1]}</b><span>{s[2] if fr else s[3]}</span></div>' for s in STATS)
    cannot = "".join(f"<li>{x}</li>" for x in CANNOT[lang])
    if fr:
        return f"""
<div class="hero" style="background-image:url('{asset(cur, 'care.jpg')}')"><div class="wrap">
 <h1>Personne ne devrait renoncer à un traitement à cause de la distance.</h1>
 <p class="lead">Depuis 2003, la {ORG_FR} aide financièrement les personnes atteintes de cancer qui doivent quitter la région pour se faire soigner.</p>
 <div class="btns"><a class="btn" href="{url(lang, 'donate', cur)}">Faire un don</a><a class="btn secondary" href="{url(lang, 'membership', cur)}">Devenir membre</a><a class="btn secondary" href="{url(lang, 'assistance', cur)}">Demander de l’aide</a></div>
</div></div>
<section><div class="wrap grid g2">
 <div class="card feature"><h2 style="margin-top:0">Notre mission</h2>
  <p>Offrir une aide financière aux personnes atteintes de cancer qui doivent se déplacer hors de la région pour recevoir leurs traitements.</p>
  <p>Agir comme centre d’information bilingue pour notre région.</p></div>
 <div class="card feature"><h2 style="margin-top:0">Notre vision</h2>
  <p>Mettre en place une équipe de soutien active qui offre encouragement, appui émotionnel et information aux personnes atteintes de cancer.</p></div>
</div></section>
<section class="alt"><div class="wrap">
 <h2 style="margin-top:0">Un impact réel depuis 2003</h2>
 <div class="stats">{stats}</div>
</div></section>
<section><div class="wrap split">
 <div class="prose">
  <h2 style="margin-top:0">Notre histoire</h2>
  <p>La {ORG_FR} est née du rêve de Noreen Hackett. Lors d’un symposium pour femmes, elle a découvert la Fondation Linda LeMore-Brown, créée pour répondre aux besoins financiers des personnes atteintes de cancer dans le district de Bonaventure. Elle a reconnu le même besoin dans la région de Gaspé.</p>
  <p>La Fondation a été fondée en juillet 2003 et enregistrée comme organisme de bienfaisance la même année. Elle est gérée à 100 % par des bénévoles et sert les résidents de Grande-Vallée à Coin-du-Banc, y compris Murdochville.</p>
  <p>Elle offre une aide financière aux personnes qui doivent se rendre à Chandler, Sainte-Anne-des-Monts, Rimouski, Rivière-du-Loup, Québec, Montréal ou Sherbrooke pour leurs traitements.</p>
  <p class="note">La Fondation n’est affiliée ni à l’Association du cancer de l’Est du Québec ni à la Société canadienne du cancer.</p>
 </div>
 <div class="media"><img src="{asset(cur, 'patient.webp')}" alt="Une femme portant un foulard regarde au loin, sereine." width="465" height="698" loading="lazy"></div>
</div></section>
<section class="alt"><div class="wrap grid g2">
 <blockquote>« La {ORG_FR} a été une lumière durant l’une des périodes les plus difficiles de ma vie. Leur attention, leur compassion et leur dévouement m’ont donné force et espoir au moment où j’en avais le plus besoin. »<footer>— Nancy Briand</footer></blockquote>
 <div><h2 style="margin-top:0">Ce que le cancer ne peut pas faire</h2>
  <p>Nous offrons à nos membres des ressources, de l’inspiration et la force de faire face au cancer. Car si le cancer est puissant, il a aussi ses limites :</p>
  <ul class="cannot">{cannot}</ul></div>
</div></section>
<section><div class="wrap" style="text-align:center">
 <h2 style="margin-top:0">Chaque don garde quelqu’un sur la route des soins.</h2>
 <div class="btns" style="justify-content:center"><a class="btn" href="{url(lang, 'donate', cur)}">Faire un don</a><a class="btn secondary" href="{url(lang, 'membership', cur)}">Devenir membre</a></div>
</div></section>"""
    return f"""
<div class="hero" style="background-image:url('{asset(cur, 'care.jpg')}')"><div class="wrap">
 <h1>No one should give up treatment because of distance.</h1>
 <p class="lead">Since 2003, the {ORG_EN} has provided financial aid to people with cancer who must leave the region for care.</p>
 <div class="btns"><a class="btn" href="{url(lang, 'donate', cur)}">Donate</a><a class="btn secondary" href="{url(lang, 'membership', cur)}">Become a Member</a><a class="btn secondary" href="{url(lang, 'assistance', cur)}">Request Assistance</a></div>
</div></div>
<section><div class="wrap grid g2">
 <div class="card feature"><h2 style="margin-top:0">Our mission</h2>
  <p>To provide financial aid to people with cancer who must travel outside the region for treatment.</p>
  <p>To act as a bilingual information centre for our region.</p></div>
 <div class="card feature"><h2 style="margin-top:0">Our vision</h2>
  <p>To build an active support team that offers encouragement, emotional support and information to people living with cancer.</p></div>
</div></section>
<section class="alt"><div class="wrap">
 <h2 style="margin-top:0">Real impact since 2003</h2>
 <div class="stats">{stats}</div>
</div></section>
<section><div class="wrap split">
 <div class="prose">
  <h2 style="margin-top:0">Our story</h2>
  <p>The {ORG_EN} grew out of Noreen Hackett’s dream. At a women’s symposium she learned about the Linda LeMore-Brown Foundation, created to meet the financial needs of cancer patients in the Bonaventure district. She saw the same need in the Gaspé area.</p>
  <p>The Foundation was established in July 2003 and registered as a charity that same year. It is run 100% by volunteers and serves residents from Grande-Vallée to Coin-du-Banc (Corner-of-the-Beach), including Murdochville.</p>
  <p>It provides financial aid to people who must travel to Chandler, Sainte-Anne-des-Monts, Rimouski, Rivière-du-Loup, Quebec City, Montreal or Sherbrooke for treatment.</p>
  <p class="note">The Foundation is not affiliated with the Association du cancer de l’Est du Québec or the Canadian Cancer Society.</p>
 </div>
 <div class="media"><img src="{asset(cur, 'patient.webp')}" alt="A woman wearing a headscarf looks into the distance, calm." width="465" height="698" loading="lazy"></div>
</div></section>
<section class="alt"><div class="wrap grid g2">
 <blockquote>“The {ORG_EN} was a guiding light during one of the hardest times of my life. Their care, compassion and dedication gave me strength and hope when I needed it most.”<footer>— Nancy Briand</footer></blockquote>
 <div><h2 style="margin-top:0">What cancer cannot do</h2>
  <p>We give our members resources, inspiration and the strength to face cancer. Because as powerful as cancer is, it has its limits:</p>
  <ul class="cannot">{cannot}</ul></div>
</div></section>
<section><div class="wrap" style="text-align:center">
 <h2 style="margin-top:0">Every gift keeps someone on the road to care.</h2>
 <div class="btns" style="justify-content:center"><a class="btn" href="{url(lang, 'donate', cur)}">Donate</a><a class="btn secondary" href="{url(lang, 'membership', cur)}">Become a Member</a></div>
</div></section>"""

def page_assistance(lang, cur):
    em = CONFIG["email"]
    if lang == "fr":
        send = f"par la poste, en personne au bureau le vendredi" + (f", ou par courriel à <a href=\"mailto:{em}\">{em}</a>" if em else "")
        return head("Demander de l’aide", "Une aide financière pour les membres qui doivent se déplacer hors de la région pour leurs traitements contre le cancer.") + f"""
<section><div class="wrap split">
 <div class="prose">
  <h2 style="margin-top:0">Admissibilité</h2>
  <p>Seuls les <a href="{url(lang, 'membership', cur)}">membres de la Fondation</a> peuvent demander de l’aide. La demande doit être appuyée par un professionnel de la santé qui vous a dirigé vers un établissement hors de la région.</p>
  <h2>Comment présenter une demande</h2>
  <ol class="steps">
   <li><strong>Vérifiez votre adhésion.</strong> Votre adhésion doit être en vigueur pour l’année en cours.</li>
   <li><strong>Téléchargez le formulaire de recommandation</strong> et imprimez-le.</li>
   <li><strong>Faites remplir la première partie par votre médecin</strong> (recommandation) et la seconde par l’établissement où vous êtes traité (attestation de présence).</li>
   <li><strong>Envoyez-nous le formulaire</strong> {send}.</li>
  </ol>
  <div class="btns"><a class="btn blue" href="{doc(cur, 'referral-form.pdf')}">Télécharger le formulaire de recommandation (PDF)</a></div>
  <p class="callout info">Des questions sur votre demande? Appelez l’un de nos bénévoles — leurs numéros sont sur la page <a href="{url(lang, 'contact', cur)}">Nous joindre</a>.</p>
 </div>
 <div><a href="{doc(cur, 'referral-form.pdf')}"><img src="{asset(cur, 'referral-thumb.png')}" alt="Aperçu du formulaire de recommandation" width="518" height="800" loading="lazy" style="border:1px solid var(--line);border-radius:8px"></a></div>
</div></section>"""
    send = "by mail, in person at the office on Fridays" + (f", or by email to <a href=\"mailto:{em}\">{em}</a>" if em else "")
    return head("Request Assistance", "Financial aid for members who must travel outside the region for cancer treatment.") + f"""
<section><div class="wrap split">
 <div class="prose">
  <h2 style="margin-top:0">Eligibility</h2>
  <p>Only <a href="{url(lang, 'membership', cur)}">members of the Foundation</a> can request assistance. Requests must be supported by a health professional who referred you to a facility outside the region.</p>
  <h2>How to apply</h2>
  <ol class="steps">
   <li><strong>Check your membership.</strong> It must be in good standing for the current year.</li>
   <li><strong>Download the referral form</strong> and print it.</li>
   <li><strong>Have your physician complete the first part</strong> (referral) and the treating facility complete the second part (proof of attendance).</li>
   <li><strong>Send us the form</strong> {send}.</li>
  </ol>
  <div class="btns"><a class="btn blue" href="{doc(cur, 'referral-form.pdf')}">Download the referral form (PDF)</a></div>
  <p class="callout info">Questions about your request? Call one of our volunteers — their numbers are on the <a href="{url(lang, 'contact', cur)}">Contact Us</a> page.</p>
 </div>
 <div><a href="{doc(cur, 'referral-form.pdf')}"><img src="{asset(cur, 'referral-thumb.png')}" alt="Preview of the referral form" width="518" height="800" loading="lazy" style="border:1px solid var(--line);border-radius:8px"></a></div>
</div></section>"""

# Resources directory: (city_fr, city_en, type, name, address, phones)
# type: H hospital, L lodging, R resource
RES = [
    ("Québec", "Quebec City", "R", "Centre Holland", "1270, chemin Sainte-Foy, bureau 1124", "418 684-5333, poste 1580<br>1 888 984-5333<br>info@hollandcentre.ca"),
    ("Québec", "Quebec City", "H", "CHUL — Centre hospitalier de l’Université Laval", "2705, boulevard Laurier", "418 654-2705"),
    ("Québec", "Quebec City", "H", "Hôtel-Dieu de Québec", "11, côte du Palais", "418 525-4444"),
    ("Québec", "Quebec City", "H", "IUCPQ (anciennement Hôpital Laval)", "2725, chemin Sainte-Foy", "418 656-8711"),
    ("Québec", "Quebec City", "L", "Manoir Ronald McDonald", "2747, boulevard Laurier", "418 651-1771"),
    ("Québec", "Quebec City", "L", "La Maison Leclerc", "2613, rue Lapointe, Sainte-Foy", "418 653-8936"),
    ("Québec", "Quebec City", "L", "Au Pignon Vert", "2631, rue Jean-Brillant, Sainte-Foy", "418 651-8487"),
    ("Québec", "Quebec City", "L", "Hôtellerie hospitalière (cancer) — à l’Hôtel-Dieu", "1, rue de l’Hôtel-Dieu", "418 691-5242"),
    ("Montréal", "Montreal", "H", "Institut thoracique de Montréal — site Glen", "1001, boulevard Décarie", "514 934-1934"),
    ("Montréal", "Montreal", "H", "Hôpital de Montréal pour enfants — site Glen", "1001, boulevard Décarie", "514 412-4400"),
    ("Montréal", "Montreal", "H", "Hôpital général de Montréal", "1650, avenue Cedar", "514 934-1934"),
    ("Montréal", "Montreal", "H", "Institut-hôpital neurologique de Montréal", "3801, rue University", "514 398-6644"),
    ("Montréal", "Montreal", "H", "Hôpital Royal Victoria — site Glen", "1001, boulevard Décarie", "514 934-1934"),
    ("Montréal", "Montreal", "H", "Hôpital Shriners pour enfants — site Glen", "1003, boulevard Décarie", "514 842-4464<br>1 800 361-7256"),
    ("Montréal", "Montreal", "H", "Institut de cardiologie de Montréal", "5000, rue Bélanger", "514 376-3330"),
    ("Montréal", "Montreal", "H", "CHU Sainte-Justine", "3175, chemin de la Côte-Sainte-Catherine", "514 345-4931"),
    ("Montréal", "Montreal", "L", "Mona’s Bed and Breakfast", "1230, avenue du Docteur-Penfield, app. 905", "1 877 427-6966"),
    ("Montréal", "Montreal", "L", "Résidence Marie-de-la-Ferre", "225, avenue des Pins Ouest", "514 844-1022"),
    ("Montréal", "Montreal", "L", "À la Bonne Étoile", "5193, rue de Bordeaux", "514 525-1698"),
    ("Montréal", "Montreal", "L", "Manoir Ronald McDonald", "3201, chemin de la Côte-Sainte-Catherine", "514 731-2871"),
    ("Montréal", "Montreal", "L", "Hôtellerie de la Fondation québécoise du cancer", "2075, rue de Champlain", "514 527-2194<br>1 877 336-4443"),
    ("Rimouski", "Rimouski", "H", "Hôpital régional de Rimouski", "150, avenue Rouleau", "418 723-3000"),
    ("Rimouski", "Rimouski", "L", "Hôtellerie Omer-Brazeau (personnes atteintes de cancer)", "151, rue Saint-Louis", "1 800 463-0806"),
    ("Rimouski", "Rimouski", "L", "Gîte Victoria", "77, rue Saint-Pierre", "418 723-4483"),
    ("Rimouski", "Rimouski", "L", "Gîte la Maison Bérubé", "1216, boulevard Saint-Germain Ouest", "418 723-1578"),
    ("Rimouski", "Rimouski", "L", "Résidence Domaine La Marguerite (aînés en perte d’autonomie)", "214, rue Saint-Edmond", "418 724-2696"),
    ("Rivière-du-Loup", "Rivière-du-Loup", "H", "Centre hospitalier régional du Grand-Portage", "75, rue Saint-Henri", "418 868-1000<br>Rendez-vous : 418 868-1020"),
    ("Rivière-du-Loup", "Rivière-du-Loup", "L", "Hôtellerie Marc-Bélanger", "75, rue Saint-Henri, pavillon Alphonse-Couturier, 6<sup>e</sup> étage", "418 868-1000, poste 2237<br>fondation@fondationchrgp.qc.ca"),
    ("Rivière-du-Loup", "Rivière-du-Loup", "L", "Auberge la Sabline", "343, rue Fraser Ouest", "418 867-4890<br>1 800 470-4890"),
    ("Rivière-du-Loup", "Rivière-du-Loup", "L", "Gîte La Suite Fraser", "150-A, rue Fraser", "418 862-9832"),
]
NAME_EN = {
    "Centre Holland": "Holland Centre",
    "CHUL — Centre hospitalier de l’Université Laval": "CHUL (Centre hospitalier de l’Université Laval)",
    "IUCPQ (anciennement Hôpital Laval)": "IUCPQ (formerly Hôpital Laval)",
    "Manoir Ronald McDonald": "Ronald McDonald House",
    "Hôtellerie hospitalière (cancer) — à l’Hôtel-Dieu": "Hôtellerie hospitalière (cancer) — at the Hôtel-Dieu",
    "Institut thoracique de Montréal — site Glen": "Montreal Chest Institute — Glen site",
    "Hôpital de Montréal pour enfants — site Glen": "Montreal Children’s Hospital — Glen site",
    "Hôpital général de Montréal": "Montreal General Hospital",
    "Institut-hôpital neurologique de Montréal": "Montreal Neurological Institute-Hospital",
    "Hôpital Royal Victoria — site Glen": "Royal Victoria Hospital — Glen site",
    "Hôpital Shriners pour enfants — site Glen": "Shriners Hospital for Children — Glen site",
    "Institut de cardiologie de Montréal": "Montreal Heart Institute",
    "Hôtellerie de la Fondation québécoise du cancer": "Fondation québécoise du cancer lodging (Hôtellerie)",
    "Hôtellerie Omer-Brazeau (personnes atteintes de cancer)": "Hôtellerie Omer-Brazeau (for cancer patients)",
    "Résidence Domaine La Marguerite (aînés en perte d’autonomie)": "Résidence Domaine La Marguerite (for seniors with reduced autonomy)",
}
ADDR_EN = [("6<sup>e</sup> étage", "6th floor"), ("app. ", "apt. "), ("bureau ", "office ")]

TYPE = {"fr": {"H": "Hôpital", "L": "Hébergement", "R": "Ressource"},
        "en": {"H": "Hospital", "L": "Lodging", "R": "Resource"}}
TCLS = {"H": "", "L": "lodging", "R": "resource"}

def en_addr(a):
    for x, y in ADDR_EN:
        a = a.replace(x, y)
    return a

def page_resources(lang, cur):
    fr = lang == "fr"
    blocks = ""
    cities = []
    for r in RES:
        c = r[0] if fr else r[1]
        if c not in cities:
            cities.append(c)
    for c in cities:
        rows = "".join(
            f'<tr><td><span class="tag {TCLS[r[2]]}">{TYPE[lang][r[2]]}</span></td><td><strong>{r[3] if fr else NAME_EN.get(r[3], r[3])}</strong></td><td>{r[4] if fr else en_addr(r[4])}</td><td>{(r[5] if fr else re.sub(r"(?<![\d-])1 (\d{3})-", r"1-\1-", re.sub(r"\b(\d{3}) (\d{3}-\d{4})", r"\1-\2", r[5]))).replace("poste", "poste" if fr else "ext.").replace("Rendez-vous", "Rendez-vous" if fr else "Appointments")}</td></tr>'
            for r in RES if (r[0] if fr else r[1]) == c)
        th = ("Type", "Nom", "Adresse", "Téléphone / courriel") if fr else ("Type", "Name", "Address", "Phone / email")
        blocks += f'<h2 id="{e(c.lower().replace(" ", "-"))}">{c}</h2><div class="table-wrap"><table><thead><tr>' + "".join(f"<th>{t}</th>" for t in th) + f"</tr></thead><tbody>{rows}</tbody></table></div>"
    jump = " · ".join(f'<a href="#{e(c.lower().replace(" ", "-"))}">{c}</a>' for c in cities)
    if fr:
        return head("Ressources", "Hôpitaux et hébergement hors région, et aide pour obtenir des services en anglais.") + f"""
<section><div class="wrap">
 <div class="prose">
  <h2 style="margin-top:0">Services d’interprétation et d’accompagnement</h2>
  <p>Si vous êtes traité dans un hôpital principalement francophone, comme à Rimouski, et que vous avez besoin de services en anglais, demandez-le au professionnel de la santé qui vous a dirigé, ou appelez l’hôpital ou le CASA (Committee for Anglophone Social Action) au <a href="tel:+18777525995">1 877 752-5995</a> à l’avance pour obtenir un interprète ou de l’aide pour l’hébergement.</p>
  <p class="callout">Les coordonnées ci-dessous sont fournies à titre indicatif. Confirmez toujours l’adresse et la disponibilité auprès de l’établissement avant de partir.</p>
 </div>
 <p><strong>Aller à :</strong> {jump}</p>
 {blocks}
</div></section>"""
    return head("Resources", "Out-of-region hospitals and lodging, and help getting services in English.") + f"""
<section><div class="wrap">
 <div class="prose">
  <h2 style="margin-top:0">Interpretation and support services</h2>
  <p>If you are treated at a predominantly French-speaking hospital, such as in Rimouski, and need services in English, ask the health professional who referred you, or call the hospital or CASA (Committee for Anglophone Social Action) at <a href="tel:+18777525995">1-877-752-5995</a> in advance to arrange an interpreter or help with lodging.</p>
  <p class="callout">The listings below are provided for convenience. Always confirm the address and availability with the facility before you travel.</p>
 </div>
 <p><strong>Jump to:</strong> {jump}</p>
 {blocks}
</div></section>"""

def page_donate(lang, cur):
    fr = lang == "fr"
    cn = CONFIG["charity_no"]
    if fr:
        return head("Faire un don", "Votre don paie l’essence, l’hébergement et les repas de personnes qui doivent quitter la région pour se faire soigner.") + f"""
<section><div class="wrap grid g3">
 <div class="card feature"><h3>Don unique</h3><p>Un don, du montant de votre choix.</p></div>
 <div class="card feature"><h3>Don mensuel</h3><p>Un appui régulier, mensuel, trimestriel ou annuel. Vous pouvez l’arrêter en tout temps.</p></div>
 <div class="card feature"><h3>Don in memoriam</h3><p>Honorez la mémoire d’un proche. Nous pouvons aviser la famille de votre geste (sans en mentionner le montant).</p></div>
</div>
<div class="wrap cta">{zbutton('zeffy_donate', lang, 'Donner en ligne')}</div></section>
<section class="alt"><div class="wrap prose">
 <h2 style="margin-top:0">Pourquoi en ligne avec Zeffy?</h2>
 <p>Nos dons en ligne passent par <strong>Zeffy</strong>, une plateforme gratuite pour les organismes : la Fondation reçoit <strong>100 % de votre don</strong>, sans frais de plateforme ni de transaction. Au moment de payer, Zeffy vous propose une contribution volontaire à son fonctionnement — vous pouvez la ramener à 0 $.</p>
 <p>Votre reçu officiel pour fins d’impôt est envoyé par courriel automatiquement. Les donateurs mensuels reçoivent un reçu annuel cumulatif en janvier.</p>
</div></section>
<section><div class="wrap">
 <h2 style="margin-top:0">Autres façons de donner</h2>
 <div class="grid g2">
  <div class="card"><h3>Par chèque</h3><p>À l’ordre de la <strong>{ORG_FR}</strong>, envoyé à :</p><p>{MAIL_FR}</p><p>Pour un don in memoriam, joignez le <a href="{doc(cur, 'in-memoriam-form.pdf')}">formulaire in memoriam (PDF)</a> ou une note indiquant le nom de la personne honorée et la personne à aviser.</p></div>
  <div class="card"><h3>En personne</h3><p>Au bureau, le vendredi de 13 h à 15 h :</p><p>{office(lang)}</p></div>
 </div>
 <p class="note" style="margin-top:1.5em">{ORG_FR} — organisme de bienfaisance enregistré, n° {cn}. Des reçus officiels sont délivrés pour les dons admissibles, conformément aux règles de l’Agence du revenu du Canada. Les cotisations de membre ne donnent pas droit à un reçu.</p>
</div></section>"""
    return head("Donate", "Your gift pays for fuel, lodging and meals for people who must leave the region for treatment.") + f"""
<section><div class="wrap grid g3">
 <div class="card feature"><h3>One-time gift</h3><p>A single gift of any amount.</p></div>
 <div class="card feature"><h3>Monthly giving</h3><p>Steady support, monthly, quarterly or yearly. Stop at any time.</p></div>
 <div class="card feature"><h3>In memoriam</h3><p>Honour the memory of a loved one. We can let the family know of your gift (without the amount).</p></div>
</div>
<div class="wrap cta">{zbutton('zeffy_donate', lang, 'Give online')}</div></section>
<section class="alt"><div class="wrap prose">
 <h2 style="margin-top:0">Why we use Zeffy</h2>
 <p>Online gifts are processed by <strong>Zeffy</strong>, a free platform for non-profits: the Foundation receives <strong>100% of your gift</strong>, with no platform or transaction fees. At checkout, Zeffy suggests an optional contribution to its own operations — you can set it to $0.</p>
 <p>Your official tax receipt is emailed automatically. Monthly donors receive one cumulative receipt in January.</p>
</div></section>
<section><div class="wrap">
 <h2 style="margin-top:0">Other ways to give</h2>
 <div class="grid g2">
  <div class="card"><h3>By cheque</h3><p>Payable to the <strong>{ORG_EN}</strong>, mailed to:</p><p>{MAIL_EN}</p><p>For an in-memoriam gift, include the <a href="{doc(cur, 'in-memoriam-form.pdf')}">in-memoriam form (PDF)</a> or a note with the name of the person honoured and who should be notified.</p></div>
  <div class="card"><h3>In person</h3><p>At the office, Fridays from 1 p.m. to 3 p.m.:</p><p>{office(lang)}</p></div>
 </div>
 <p class="note" style="margin-top:1.5em">{ORG_EN} — registered charity no. {cn}. Official receipts are issued for eligible gifts in accordance with Canada Revenue Agency rules. Membership fees are not receipted.</p>
</div></section>"""

def page_membership(lang, cur):
    if lang == "fr":
        return head("Devenir membre", "L’adhésion vous donne accès à l’aide financière de la Fondation et vous permet de voter à l’assemblée générale annuelle.") + f"""
<section><div class="wrap grid g2">
 <div class="card feature"><h3>Individuelle</h3><p class="price">15 $ <small>/ année</small></p><p>Une personne.</p></div>
 <div class="card feature"><h3>Couple</h3><p class="price">25 $ <small>/ année</small></p><p>Deux personnes à la même adresse.</p></div>
</div>
<div class="wrap cta">{zbutton('zeffy_membership', lang, 'Adhérer ou renouveler en ligne')}</div></section>
<section class="alt"><div class="wrap prose">
 <h2 style="margin-top:0">Ce que comprend l’adhésion</h2>
 <ul>
  <li>L’admissibilité à l’<a href="{url(lang, 'assistance', cur)}">aide financière</a> pour les déplacements liés aux traitements;</li>
  <li>Les nouvelles de la Fondation;</li>
  <li>Le droit de vote à l’assemblée générale annuelle.</li>
 </ul>
 <h2>Période d’adhésion</h2>
 <p>L’adhésion est valide du 1<sup>er</sup> janvier au 31 décembre. Le renouvellement est dû le 1<sup>er</sup> janvier de chaque année. Une adhésion non renouvelée au plus tard le dernier jour de février prend fin.</p>
 <h2>Adhérer autrement</h2>
 <p>Par chèque à l’ordre de la {ORG_FR}, envoyé au {MAIL_FR.replace('<br>', ', ')}, avec votre nom, adresse, téléphone et courriel — ou en personne au bureau le vendredi de 13 h à 15 h.</p>
</div></section>"""
    return head("Become a Member", "Membership gives you access to the Foundation’s financial aid and a vote at the annual general meeting.") + f"""
<section><div class="wrap grid g2">
 <div class="card feature"><h3>Individual</h3><p class="price">$15 <small>/ year</small></p><p>One person.</p></div>
 <div class="card feature"><h3>Couple</h3><p class="price">$25 <small>/ year</small></p><p>Two people at the same address.</p></div>
</div>
<div class="wrap cta">{zbutton('zeffy_membership', lang, 'Join or renew online')}</div></section>
<section class="alt"><div class="wrap prose">
 <h2 style="margin-top:0">What membership includes</h2>
 <ul>
  <li>Eligibility for <a href="{url(lang, 'assistance', cur)}">financial aid</a> for treatment-related travel;</li>
  <li>News from the Foundation;</li>
  <li>A vote at the annual general meeting.</li>
 </ul>
 <h2>Membership period</h2>
 <p>Membership runs from January 1 to December 31. Renewal is due on January 1 each year. A membership not renewed by the last day of February lapses.</p>
 <h2>Other ways to join</h2>
 <p>By cheque payable to the {ORG_EN}, mailed to {MAIL_EN.replace('<br>', ', ')}, with your name, address, phone and email — or in person at the office on Fridays from 1 p.m. to 3 p.m.</p>
</div></section>"""

PEOPLE = [("Tony C. Patterson", "418 368-3276", "418-368-3276"),
          ("Beatrice Coffin", "418 368-1566", "418-368-1566"),
          ("Theresa Joseph", "418 368-2361", "418-368-2361"),
          ("Patricia Ste-Croix", "418 645-3779", "418-645-3779")]

def page_contact(lang, cur):
    fr = lang == "fr"
    ppl = "".join(f'<li><span>{n}</span><a href="tel:+1{t.replace("-", "")}">{a if fr else t}</a></li>' for n, a, t in PEOPLE)
    form = ""
    if CONFIG["contact_form"]:
        lbl = "Écrivez-nous" if fr else "Write to us"
        form = f'<div class="btns"><a class="btn blue" href="{e(CONFIG["contact_form"])}" rel="noopener">{lbl}</a></div>'
    if fr:
        return head("Nous joindre", "Nos bénévoles sont là pour répondre à vos questions.") + f"""
<section><div class="wrap grid g2">
 <div class="card"><h2 style="margin-top:0">Coordonnées</h2>
  <dl class="contact">
   <dt>Adresse postale</dt><dd>{MAIL_FR}</dd>
   <dt>Bureau</dt><dd>{office(lang)}</dd>
   <dt>Heures</dt><dd>Le vendredi, de 13 h à 15 h</dd>
   {email_line(lang)}
   <dt>Facebook</dt><dd><a href="https://www.facebook.com/gaspecancer" rel="noopener">facebook.com/gaspecancer</a></dd>
  </dl>{form}</div>
 <div class="card"><h2 style="margin-top:0">Par téléphone</h2><p>Joignez directement l’un de nos bénévoles :</p><ul class="people">{ppl}</ul></div>
</div></section>"""
    return head("Contact Us", "Our volunteers are here to answer your questions.") + f"""
<section><div class="wrap grid g2">
 <div class="card"><h2 style="margin-top:0">Contact information</h2>
  <dl class="contact">
   <dt>Mailing address</dt><dd>{MAIL_EN}</dd>
   <dt>Office</dt><dd>{office(lang)}</dd>
   <dt>Hours</dt><dd>Fridays, 1 p.m. to 3 p.m.</dd>
   {email_line(lang)}
   <dt>Facebook</dt><dd><a href="https://www.facebook.com/gaspecancer" rel="noopener">facebook.com/gaspecancer</a></dd>
  </dl>{form}</div>
 <div class="card"><h2 style="margin-top:0">By phone</h2><p>Reach one of our volunteers directly:</p><ul class="people">{ppl}</ul></div>
</div></section>"""

META = {
    "home": (("Accueil", "Aide financière aux personnes atteintes de cancer de la région de Gaspé qui doivent se déplacer pour leurs traitements."),
             ("About Us", "Financial aid for people with cancer in the Gaspé area who must travel for treatment.")),
    "assistance": (("Demander de l’aide", "Comment les membres peuvent demander une aide financière pour les déplacements liés aux traitements contre le cancer."),
                   ("Request Assistance", "How members can request financial aid for cancer treatment travel.")),
    "resources": (("Ressources", "Hôpitaux, hébergement et services d’interprétation hors région."),
                  ("Resources", "Out-of-region hospitals, lodging and interpretation services.")),
    "donate": (("Faire un don", "Faites un don à la Fondation du cancer de Gaspé. 100 % de votre don va à la Fondation."),
               ("Donate", "Give to the Gaspé Cancer Foundation. 100% of your gift reaches the Foundation.")),
    "membership": (("Devenir membre", "Adhésion annuelle individuelle (15 $) ou couple (25 $)."),
                   ("Become a Member", "Annual membership: individual ($15) or couple ($25).")),
    "contact": (("Nous joindre", "Coordonnées et bénévoles de la Fondation du cancer de Gaspé."),
                ("Contact Us", "Contact information and volunteers of the Gaspé Cancer Foundation.")),
}
BUILDERS = {"home": page_home, "assistance": page_assistance, "resources": page_resources,
            "donate": page_donate, "membership": page_membership, "contact": page_contact}

def redirect_page(cur, lang, key):
    target = url(lang, key, cur)
    return f"""<!doctype html><html lang="{lang}"><head><meta charset="utf-8"><title>…</title>
<meta name="robots" content="noindex"><meta http-equiv="refresh" content="0; url={target}">
<link rel="canonical" href="{target}"></head><body><p><a href="{target}">{'Continuer' if lang == 'fr' else 'Continue'}</a></p></body></html>
"""

def page_404():
    cur = "404.html"
    # GitHub Pages serves 404.html from any path, so use root-absolute links here.
    return f"""<!doctype html><html lang="fr-CA"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Page introuvable / Page not found</title><link rel="icon" href="/assets/favicon.png"><link rel="stylesheet" href="/assets/site.css"></head>
<body><header class="site-header"><div class="wrap"><a class="brand" href="/"><img src="/assets/emblem.png" alt="" width="52"><span><span class="n1">{ORG_FR}</span><span class="n2">{ORG_EN}</span></span></a></div></header>
<main id="main"><section><div class="wrap grid g2">
<div><h1>Page introuvable</h1><p>La page demandée n’existe pas ou a été déplacée.</p><p><a class="btn" href="/">Retour à l’accueil</a></p></div>
<div lang="en"><h1>Page not found</h1><p>The page you requested does not exist or has moved.</p><p><a class="btn secondary" href="/en/about/">Go to the English home page</a></p></div>
</div></section></main></body></html>
"""

def main():
    written = []
    for key, (frp, enp) in PAGES.items():
        for lang, path in (("fr", frp), ("en", enp)):
            title, desc = META[key][0 if lang == "fr" else 1]
            body = BUILDERS[key](lang, path)
            out = ROOT / path
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(layout(lang, key, path, title, desc, body), encoding="utf-8")
            written.append(path)
    for path, (lang, key) in REDIRECTS.items():
        out = ROOT / path
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(redirect_page(path, lang, key), encoding="utf-8")
        written.append(path)
    (ROOT / "404.html").write_text(page_404(), encoding="utf-8")
    # sitemap
    urls = "".join(f"<url><loc>{CONFIG['site_url']}/{p.replace('index.html', '')}</loc></url>"
                   for k in PAGES for p in PAGES[k])
    (ROOT / "sitemap.xml").write_text(f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>\n', encoding="utf-8")
    (ROOT / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {CONFIG['site_url']}/sitemap.xml\n", encoding="utf-8")
    print(f"Built {len(written) + 1} pages.")

if __name__ == "__main__":
    main()
