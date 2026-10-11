#!/usr/bin/env python3
"""Static site generator for gaspecancer.org (repo: com-gcfn).

Run from the repo root:  python3 tools/build.py
Edit CONFIG below (Zeffy links, email, room number) and rebuild.
All links are relative, so the site works both on the custom domain and on
the <user>.github.io/com-gcfn/ project URL.

Page structure mirrors the original WordPress (WoodMart + Elementor) site:
navy promo bar, header over a bright-blue page banner,
"subtitle over title" section headings, counters band, "Take Action" footer
and the mobile sticky toolbar (Donate / Become a Member / Get Financial Support).
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
    "promo": True,               # top bar: annual fundraising campaign
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
# Same menu as the original site: About / Travel Assistance / Resources / Contact
NAV = ["home", "assistance", "resources", "contact"]
LABELS = {
    "fr": {"home": "À propos", "assistance": "Aide aux déplacements", "resources": "Ressources",
           "donate": "Faire un don", "membership": "Devenir membre", "contact": "Nous joindre",
           "crumb_home": "Accueil"},
    "en": {"home": "About Us", "assistance": "Travel Assistance", "resources": "Resources",
           "donate": "Donate", "membership": "Become a Member", "contact": "Contact Us",
           "crumb_home": "Home"},
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
FACEBOOK = "https://www.facebook.com/gaspecancer"

# ---------------------------------------------------------------------------
# Building blocks
# ---------------------------------------------------------------------------
CUR = ' aria-current="page"'

def logo(lang, cur, cls="logo"):
    """EN: the original logo file. FR: emblem + French name set in type
    (no French logo file was recovered from the old site)."""
    if lang == "en":
        return (f'<a class="{cls}" href="{url(lang, "home", cur)}">'
                f'<img src="{asset(cur, "logo-en.png")}" alt="{ORG_EN}" width="369" height="123"></a>')
    return (f'<a class="{cls} logo-text" href="{url(lang, "home", cur)}" aria-label="{ORG_FR}">'
            f'<img src="{asset(cur, "emblem.png")}" alt="" width="137" height="123">'
            f'<span>Fondation<br>du cancer<br>de Gaspé</span></a>')

def title(sub, main, center=False, sep=False, right=False):
    c = " center" if center else (" right" if right else "")
    s = '<span class="sep"></span>' if sep else ""
    sub_html = f'<span class="sub">{sub}</span>' if sub else ""
    return f'<div class="title{c}">{sub_html}<h2>{main}</h2>{s}</div>'

def page_title(lang, key, cur, h1):
    return f'<div class="page-title"><div class="wrap"><h1>{h1}</h1></div></div>'

PROMO = {
    "fr": "Notre campagne annuelle de financement est en cours! Devenez membre ou faites un don dès aujourd’hui.",
    "en": "Our annual fundraising campaign is underway! Become a member or donate today.",
}
TOOLBAR = {
    "fr": ("Faire un don", "Devenir membre", "Obtenir de l’aide"),
    "en": ("Donate Now", "Become a Member", "Get Financial Support"),
}
FOOT = {
    "fr": {"blurb": "Organisme de bienfaisance entièrement bénévole qui aide financièrement les personnes atteintes de cancer devant se déplacer hors de la région pour leurs traitements.",
           "charity": "N° d’organisme de bienfaisance", "act": "Passez à l’action",
           "renew": "Renouveler l’adhésion", "reach": "Nous joindre",
           "hours": "Bureau ouvert le vendredi, de 13 h à 15 h",
           "legal": "Ne pas confondre avec l’Association du cancer de l’Est du Québec ni avec la Société canadienne du cancer."},
    "en": {"blurb": "An all-volunteer registered charity providing financial aid to people with cancer who must travel outside the region for treatment.",
           "charity": "Charitable registration no.", "act": "Take Action",
           "renew": "Renew Membership", "reach": "Reach Us",
           "hours": "Office open Fridays, 1 p.m. to 3 p.m.",
           "legal": "Not affiliated with the Association du cancer de l’Est du Québec or the Canadian Cancer Society."},
}

def layout(lang, key, cur, title_txt, desc, body):
    other = "en" if lang == "fr" else "fr"
    L = LABELS[lang]
    F = FOOT[lang]
    org = ORG_FR if lang == "fr" else ORG_EN
    fr_url = CONFIG["site_url"] + "/" + PAGES[key][0].replace("index.html", "")
    en_url = CONFIG["site_url"] + "/" + PAGES[key][1].replace("index.html", "")
    nav = "".join(f'<a href="{url(lang, k, cur)}"{CUR if k == key else ""}>{e(L[k])}</a>' for k in NAV)
    lang_label = "English" if lang == "fr" else "Français"
    promo = (f'<div class="promo"><a href="{url(lang, "donate", cur)}">🏠 {PROMO[lang]}</a></div>') if CONFIG["promo"] else ""
    t = TOOLBAR[lang]
    return f"""<!doctype html>
<html lang="{'fr-CA' if lang == 'fr' else 'en-CA'}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title_txt)} | {e(org)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{fr_url if lang == 'fr' else en_url}">
<link rel="alternate" hreflang="fr-CA" href="{fr_url}">
<link rel="alternate" hreflang="en-CA" href="{en_url}">
<link rel="alternate" hreflang="x-default" href="{fr_url}">
<meta property="og:title" content="{e(title_txt)} | {e(org)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:image" content="{CONFIG['site_url']}/assets/care.jpg">
<meta property="og:locale" content="{'fr_CA' if lang == 'fr' else 'en_CA'}">
<link rel="icon" type="image/png" href="{asset(cur, 'favicon.png')}">
<link rel="apple-touch-icon" href="{asset(cur, 'apple-touch-icon.png')}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600&family=Roboto:wght@400;500;700;900&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{asset(cur, 'site.css')}">
</head>
<body>
<a class="skip" href="#main">{'Aller au contenu' if lang == 'fr' else 'Skip to content'}</a>
<div class="masthead">
{promo}
<header class="site-header">
 <div class="wrap">
  {logo(lang, cur)}
  <button class="menu-toggle" aria-expanded="false" aria-controls="nav">Menu</button>
  <nav class="nav" id="nav" aria-label="{'Navigation principale' if lang == 'fr' else 'Main navigation'}">
   <a class="lang" href="{url(other, key, cur)}" lang="{other}" hreflang="{other}">{lang_label}</a>
   {nav}
  </nav>
  <div class="hbtns">
   <a class="btn yellow" href="{url(lang, 'donate', cur)}">{e(L['donate'])}</a>
   <a class="btn" href="{url(lang, 'membership', cur)}">{e(L['membership'])}</a>
  </div>
 </div>
</header>
</div>
<main id="main">
{body}
</main>
<footer class="site-footer">
 <div class="wrap">
  <div>
   {logo(lang, cur)}
   <p>{F['blurb']}</p>
   <p>{F['charity']} {CONFIG['charity_no']}</p>
  </div>
  <div>
   <h4>{F['act']}</h4>
   <ul>
    <li><a href="{url(lang, 'assistance', cur)}">{'Demander de l’aide' if lang == 'fr' else 'Request Assistance'}</a></li>
    <li><a href="{url(lang, 'donate', cur)}">{e(L['donate'])}</a></li>
    <li><a href="{url(lang, 'membership', cur)}">{e(L['membership'])}</a></li>
    <li><a href="{url(lang, 'membership', cur)}">{F['renew']}</a></li>
    <li><a href="{url(lang, 'resources', cur)}">{e(L['resources'])}</a></li>
   </ul>
  </div>
  <div>
   <h4>{F['reach']}</h4>
   <p>{MAIL_FR if lang == 'fr' else MAIL_EN}</p>
   <p>{F['hours']}</p>
   <p><a href="{url(lang, 'contact', cur)}">{e(L['contact'])}</a> · <a href="{FACEBOOK}" rel="noopener">Facebook</a></p>
  </div>
 </div>
 <div class="copy">© {YEAR} {e(org)}. {F['legal']}</div>
</footer>
<nav class="toolbar" aria-label="{'Actions rapides' if lang == 'fr' else 'Quick actions'}">
 <a href="{url(lang, 'donate', cur)}">{t[0]}</a>
 <a href="{url(lang, 'membership', cur)}">{t[1]}</a>
 <a href="{url(lang, 'assistance', cur)}">{t[2]}</a>
</nav>
<script>
(function(){{var b=document.querySelector('.menu-toggle'),n=document.getElementById('nav');
if(b)b.addEventListener('click',function(){{var o=n.classList.toggle('open');b.setAttribute('aria-expanded',o)}});}})();
</script>
</body>
</html>
"""

# ---------------------------------------------------------------------------
# About (home)
# ---------------------------------------------------------------------------
STATS = [  # "donations received" removed: EN said 385,000, FR said 900,000.
    ("1 282", "1,282", "Membres", "Members"),
    ("124", "124", "Bénévoles", "Volunteers"),
    ("10 896", "10,896", "Heures de bénévolat", "Hours volunteered"),
    ("255", "255", "Membres aidés", "Members helped"),
    ("274 006 $", "$274,006", "Versés en aide", "Dollars given"),
    ("2003", "2003", "Année de fondation", "Year founded"),
]

CANNOT = {
    "fr": ["Il ne peut pas briser l’amour", "Il ne peut pas anéantir l’espoir", "Il ne peut pas affaiblir la foi",
           "Il ne peut pas détruire la paix", "Il ne peut pas mettre fin à l’amitié", "Il ne peut pas effacer les souvenirs",
           "Il ne peut pas réduire le courage au silence", "Il ne peut pas envahir l’âme",
           "Il ne peut pas voler la vie éternelle", "Il ne peut pas vaincre l’esprit"],
    "en": ["It cannot cripple love", "It cannot shatter hope", "It cannot weaken faith", "It cannot destroy peace",
           "It cannot end friendship", "It cannot suppress memories", "It cannot silence courage",
           "It cannot invade the soul", "It cannot steal eternal life", "It cannot conquer the spirit"],
}

def page_home(lang, cur):
    fr = lang == "fr"
    L = LABELS[lang]
    counters = "".join(f'<div class="counter"><b>{s[0] if fr else s[1]}</b><span>{s[2] if fr else s[3]}</span></div>' for s in STATS)
    cannot = "".join(f"<li>{x}</li>" for x in CANNOT[lang])
    d, m, a = url(lang, 'donate', cur), url(lang, 'membership', cur), url(lang, 'assistance', cur)
    if fr:
        T = dict(
            h1="À propos",
            mis_sub="Notre mission en deux volets", mis="Notre mission",
            mis_txt="<p>Offrir une aide financière aux personnes atteintes de cancer qui doivent se déplacer hors de la région pour recevoir leurs traitements.</p><p>Agir comme centre d’information bilingue pour notre région.</p>",
            vis_sub="Notre vision à long terme", vis="Notre vision",
            vis_txt="<p>La Fondation souhaite mettre en place une équipe de soutien active, capable d’offrir encouragement et appui émotionnel aux personnes qui combattent le cancer, et de leur fournir l’information dont elles ont besoin.</p>",
            quote="La Fondation du cancer de Gaspé a été une lumière durant l’une des périodes les plus difficiles de ma vie. Leur attention, leur compassion et leur dévouement m’ont donné force et espoir au moment où j’en avais le plus besoin.",
            imp="Un impact réel.", imp_sub="Depuis notre fondation en 2003",
            imp_txt="<p>Nous offrons à nos membres des ressources, de l’inspiration et la force de lutter contre le cancer et d’en limiter l’emprise. Car si le cancer est puissant à bien des égards, il a aussi ses limites. Voici quelques-unes des choses qu’il ne peut pas faire :</p>",
            img_alt="Une femme portant un foulard regarde au loin, sereine.",
            care_alt="Une infirmière prend soin d’une dame âgée.",
            his_sub="L’histoire de notre fondation", his="Notre histoire",
            his_txt=f"""<p>La {ORG_FR} est née du rêve de Noreen Hackett. Lors d’un symposium pour femmes, elle a découvert la Fondation Linda LeMore-Brown, créée pour répondre aux besoins financiers des personnes atteintes de cancer dans le district de Bonaventure. Elle a reconnu le même besoin dans la région de Gaspé.</p>
<p>La Fondation a vu le jour en juillet 2003 et a obtenu à ce moment son statut d’organisme de bienfaisance. Elle est gérée à 100 % par des bénévoles et sert les résidents de Grande-Vallée à Coin-du-Banc, y compris Murdochville.</p>
<p>Elle agit comme centre d’information bilingue et offre une aide financière aux personnes qui doivent se rendre à Chandler, Sainte-Anne-des-Monts, Rimouski, Rivière-du-Loup, Québec, Montréal ou Sherbrooke pour leurs traitements.</p>
<p class="note">La Fondation n’est affiliée ni à l’Association du cancer de l’Est du Québec ni à la Société canadienne du cancer.</p>""",
            b_don="Faire un don", b_mem="Devenir membre", b_ass="Demander de l’aide",
        )
    else:
        T = dict(
            h1="About Us",
            mis_sub="Our two-part mission statement", mis="Our Mission",
            mis_txt="<p>To provide financial aid to individuals with cancer who need to travel outside our region for treatment.</p><p>To act as a bilingual information centre for our region.</p>",
            vis_sub="Our long-term vision statement", vis="Our Vision",
            vis_txt="<p>The Foundation would like to have an active support team in place, able to offer encouragement and emotional support to people battling cancer and to provide them with the information they need.</p>",
            quote="The Gaspé Cancer Foundation was a guiding light during one of the hardest times of my life. Their care, compassion and dedication gave me strength and hope when I needed it most.",
            imp="Real Impact.", imp_sub="Since our founding in 2003",
            imp_txt="<p>We provide members with resources, inspiration and the strength to fight cancer and limit its power. Because while cancer is very powerful in many ways, it is also very limited. Here are a few of the things cancer cannot do:</p>",
            img_alt="A woman wearing a headscarf looks into the distance, calm.",
            care_alt="A nurse caring for an older woman.",
            his_sub="The story of our founding", his="Our History",
            his_txt=f"""<p>The {ORG_EN} grew out of Noreen Hackett’s dream after she attended a women’s symposium where she learned of the Linda LeMore-Brown Foundation, formed to help meet the financial needs of cancer patients in the Bonaventure district. Noreen saw the same need in the Gaspé area.</p>
<p>The Foundation was formed in July 2003 and registered as a charity at that time. It is a non-profit run entirely by volunteers, serving residents from Grande-Vallée to Coin-du-Banc (Corner-of-the-Beach), including Murdochville.</p>
<p>The Foundation acts as a bilingual information centre and provides financial aid to people who must travel to Chandler, Sainte-Anne-des-Monts, Rimouski, Rivière-du-Loup, Quebec City, Montreal or Sherbrooke for treatment.</p>
<p class="note">We are not affiliated with the Association du cancer de l’Est du Québec or the Canadian Cancer Society.</p>""",
            b_don="Make a Donation", b_mem="Become a Member", b_ass="Request Assistance",
        )
    return page_title(lang, "home", cur, T["h1"]) + f"""
<section class="sec"><div class="wrap about-top">
 <div>
  {title(T['mis_sub'], T['mis'])}
  <ul class="lead-list">{T['mis_txt'].replace('<p>', '<li>').replace('</p>', '</li>')}</ul>
  <hr class="rule">
  {title(T['vis_sub'], T['vis'], right=True)}
  <div style="text-align:right">{T['vis_txt']}</div>
 </div>
 <div class="mosaic">
  <div class="stack">
   <img class="a" src="{asset(cur, 'care.jpg')}" alt="{T['care_alt']}" width="1600" height="1058" loading="lazy">
   <img class="b" src="{asset(cur, 'patient.webp')}" alt="{T['img_alt']}" width="465" height="698" loading="lazy">
  </div>
  <div class="stack" style="margin-top:0">
   <figure class="quote-card" style="margin:0"><blockquote>{T['quote']}</blockquote><figcaption><cite>Nancy Briand</cite></figcaption></figure>
   <img class="d" src="{asset(cur, 'cairn.jpg')}" alt="" width="1600" height="1067" loading="lazy">
  </div>
 </div>
</div></section>
<section class="impact"><div class="wrap">
 <div class="cgrid">{counters}</div>
 <div>
  <h2>{T['imp']}</h2><span class="since">{T['imp_sub']}</span>
  {T['imp_txt']}
  <ul class="plain">{cannot}</ul>
  <div class="btns"><a class="btn white" href="{d}">{T['b_don']}</a><a class="btn ghost" href="{m}">{T['b_mem']}</a></div>
 </div>
</div></section>
<section class="sec"><div class="wrap history">
 <span class="sub">{T['his_sub']}</span>
 <h2>{T['his']}</h2>
 <div class="two-col">{T['his_txt']}</div>
 <div class="btns"><a class="btn" href="{m}">{T['b_mem']}</a><a class="btn yellow" href="{d}">{T['b_don']}</a><a class="btn outline" href="{a}">{T['b_ass']}</a></div>
</div></section>"""

# ---------------------------------------------------------------------------
# Travel assistance
# ---------------------------------------------------------------------------
def page_assistance(lang, cur):
    em = CONFIG["email"]
    ref = doc(cur, 'referral-form.pdf')
    thumb = f'<a href="{ref}" class="photo"><img src="{asset(cur, "referral-thumb.png")}" alt="{"Aperçu du formulaire de recommandation" if lang == "fr" else "Preview of the referral form"}" width="518" height="800" loading="lazy" style="border:1px solid var(--line)"></a>'
    phones = f'<a href="{url(lang, "contact", cur)}">{"Nous joindre" if lang == "fr" else "Contact Us"}</a>'
    if lang == "fr":
        send = "par la poste ou en personne au bureau le vendredi" + (f", ou par courriel à <a href=\"mailto:{em}\">{em}</a>" if em else "")
        return page_title(lang, "assistance", cur, "Demander de l’aide") + f"""
<section class="sec"><div class="wrap cols c7-5">
 <div>
  {title("", "Admissibilité", sep=True)}
  <p>Seuls les <a href="{url(lang, 'membership', cur)}">membres de la {ORG_FR}</a> peuvent demander de l’aide. L’adhésion doit être en vigueur pour l’année en cours.</p>
  <div style="height:24px"></div>
  {title("", "Recommandation", sep=True)}
  <p>Pour présenter une demande, le membre doit avoir été dirigé vers un établissement hors de la région par un professionnel de la santé.</p>
  <p>Téléchargez et imprimez notre formulaire de recommandation. Faites remplir la première partie par votre médecin et la seconde par l’établissement où vous êtes traité, puis envoyez-le-nous {send}.</p>
  <div class="btns"><a class="btn" href="{ref}">Télécharger le formulaire de recommandation</a></div>
  <p class="callout" style="margin-top:28px">Des questions sur votre demande? Appelez l’un de nos bénévoles. Leurs numéros sont sur la page {phones}.</p>
 </div>
 <div>{thumb}</div>
</div></section>"""
    send = "by mail or in person at the office on a Friday" + (f", or by email to <a href=\"mailto:{em}\">{em}</a>" if em else "")
    return page_title(lang, "assistance", cur, "Request Assistance") + f"""
<section class="sec"><div class="wrap cols c7-5">
 <div>
  {title("", "Eligibility", sep=True)}
  <p>Only <a href="{url(lang, 'membership', cur)}">members of the {ORG_EN}</a> can request assistance. Membership must be in good standing for the current year.</p>
  <div style="height:24px"></div>
  {title("", "Referral", sep=True)}
  <p>To make a claim, a member must have been referred to a facility outside the region by a health professional.</p>
  <p>Download and print our referral form. Have your doctor complete the first part and the treating facility complete the second, then send it to us {send}.</p>
  <div class="btns"><a class="btn" href="{ref}">Download Referral Form</a></div>
  <p class="callout" style="margin-top:28px">Questions about your request? Call one of our volunteers. Their numbers are on the {phones} page.</p>
 </div>
 <div>{thumb}</div>
</div></section>"""

# ---------------------------------------------------------------------------
# Resources
# ---------------------------------------------------------------------------
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

def en_addr(a):
    for x, y in ADDR_EN:
        a = a.replace(x, y)
    return a

def fmt_phone(s, fr):
    if not fr:
        s = re.sub(r"(?<![\d-])1 (\d{3})-", r"1-\1-", re.sub(r"\b(\d{3}) (\d{3}-\d{4})", r"\1-\2", s))
        s = s.replace("poste", "ext.").replace("Rendez-vous", "Appointments")
    return s

def page_resources(lang, cur):
    fr = lang == "fr"
    rows = "".join(
        f'<tr><td class="city">{r[0] if fr else r[1]}</td><td>{TYPE[lang][r[2]]}</td>'
        f'<td><strong>{r[3] if fr else NAME_EN.get(r[3], r[3])}</strong></td>'
        f'<td>{r[4] if fr else en_addr(r[4])}</td><td>{fmt_phone(r[5], fr)}</td></tr>'
        for r in RES)
    th = ("Ville", "Type", "Nom", "Adresse", "Téléphone / courriel") if fr else ("City", "Type", "Name", "Address", "Telephone / Email")
    table = '<div class="table-wrap"><table><thead><tr>' + "".join(f"<th>{t}</th>" for t in th) + f"</tr></thead><tbody>{rows}</tbody></table></div>"
    if fr:
        return page_title(lang, "resources", cur, "Ressources") + f"""
<section class="sec tight"><div class="wrap" style="max-width:900px">
 {title("", "Services de traduction et d’interprétation", sep=True)}
 <p>Si vous devez vous loger à l’extérieur de l’hôpital, des options d’hébergement sont indiquées pour les établissements ci-dessous.</p>
 <p>Si vous êtes traité dans un hôpital principalement francophone, comme à Rimouski, et que vous avez besoin de services en anglais, adressez-vous au professionnel de la santé qui vous a dirigé, ou appelez à l’avance l’hôpital ou le CASA (Committee for Anglophone Social Action) au <a href="tel:+18777525995">1 877 752-5995</a> pour obtenir un interprète ou de l’aide pour l’hébergement.</p>
</div></section>
<section class="sec light tight"><div class="wrap">
 {title("", "Services médicaux et hébergement hors région", sep=True)}
 {table}
 <p class="note">Coordonnées fournies à titre indicatif. Confirmez l’adresse et la disponibilité auprès de l’établissement avant de partir.</p>
</div></section>"""
    return page_title(lang, "resources", cur, "Resources") + f"""
<section class="sec tight"><div class="wrap" style="max-width:900px">
 {title("", "Translation and Interpretation Services", sep=True)}
 <p>If you need accommodation outside the hospital, lodging is listed for the institutions below.</p>
 <p>If you are travelling to a predominantly French-speaking hospital, such as in Rimouski, and need services in English, ask the health professional who referred you, or call the hospital or CASA (Committee for Anglophone Social Action) at <a href="tel:+18777525995">1-877-752-5995</a> in advance to arrange for an interpreter or help with accommodation.</p>
</div></section>
<section class="sec light tight"><div class="wrap">
 {title("", "Out-of-Region Medical Services and Lodging", sep=True)}
 {table}
 <p class="note">Listings are provided for convenience. Always confirm the address and availability with the facility before you travel.</p>
</div></section>"""

# ---------------------------------------------------------------------------
# Donate
# ---------------------------------------------------------------------------
def page_donate(lang, cur):
    fr = lang == "fr"
    cn = CONFIG["charity_no"]
    imf = doc(cur, 'in-memoriam-form.pdf')
    if fr:
        return page_title(lang, "donate", cur, "Faire un don") + f"""
<section class="sec"><div class="wrap">
 {title("Votre don paie l’essence, l’hébergement et les repas de personnes qui doivent quitter la région pour se faire soigner.", "Trois façons de donner", center=True, sep=True)}
 <p class="center" style="max-width:760px;margin:0 auto 36px">Vous pouvez donner en ligne par carte de crédit ou de débit, ou hors ligne par chèque ou en argent comptant. Tous les détails ci-dessous.</p>
 <div class="cols c3">
  <div class="box top"><h3>Don unique</h3><p>Un don unique offre un soutien immédiat aux personnes atteintes de cancer du territoire que nous desservons. Il aide à payer les frais de déplacement, d’hébergement et de repas des patients durant une période difficile.</p><div class="btns">{zbutton('zeffy_donate', lang, 'Donner un montant unique')}</div></div>
  <div class="box top"><h3>Don récurrent</h3><p>Devenez un partenaire fidèle dans la lutte contre le cancer. Un don mensuel, trimestriel ou annuel nous donne un financement stable, qui nous permet de planifier et d’offrir un soutien continu. Vous pouvez l’arrêter en tout temps.</p><div class="btns">{zbutton('zeffy_donate', lang, 'Donner un montant récurrent')}</div></div>
  <div class="box top"><h3>Don in memoriam</h3><p>Honorez la mémoire d’un ami ou d’un proche emporté par le cancer. Nous informons la famille de votre geste, sans en mentionner le montant, et vous recevez un reçu aux fins de l’impôt.</p><div class="btns">{zbutton('zeffy_donate', lang, 'Faire un don in memoriam')}</div></div>
 </div>
</div></section>
<section class="sec light"><div class="wrap cols c2">
 <div>{title("Donnez en toute sécurité, soutenez directement", "Faire un don en ligne", sep=True)}</div>
 <div>
  <p>Nos dons en ligne passent par <strong>Zeffy</strong>, une plateforme gratuite pour les organismes de bienfaisance. La Fondation reçoit <strong>100 % de votre don</strong> : aucuns frais de plateforme ni de transaction.</p>
  <p>Au moment de payer, Zeffy vous propose une contribution volontaire à son propre fonctionnement. Elle est facultative et vous pouvez la ramener à 0 $.</p>
  <p>Votre reçu officiel aux fins de l’impôt est envoyé par courriel dès que le paiement est confirmé. Les donateurs mensuels reçoivent un reçu annuel cumulatif en janvier.</p>
  <div class="btns">{zbutton('zeffy_donate', lang, 'Donner en ligne')}</div>
 </div>
</div></section>
<section class="sec"><div class="wrap">
 {title("Autres façons de donner", "Paiements hors ligne", center=True, sep=True)}
 <p class="center" style="max-width:760px;margin:0 auto 40px">Si vous préférez ne pas donner en ligne, suivez les étapes ci-dessous.</p>
 <div class="steps">
  <div class="step"><h3>Téléchargez le formulaire</h3><p>Vous pouvez envoyer un don par la poste sans formulaire, sauf pour un don in memoriam ou si vous désirez un reçu aux fins de l’impôt. Dans ce cas, joignez une note avec votre nom et votre adresse, ou le formulaire ci-dessous.</p><ul class="links"><li><a href="{imf}">Formulaire de don in memoriam (PDF)</a></li></ul></div>
  <div class="step"><h3>Préparez votre paiement</h3><p>Nous acceptons les chèques et l’argent comptant. Les chèques sont libellés à l’ordre de la <strong>{ORG_FR}</strong>. Pour un don récurrent, des chèques postdatés sont recommandés.</p></div>
  <div class="step"><h3>Envoyez ou apportez votre paiement</h3><p>Chèques, par la poste :</p><address>{MAIL_FR}</address><p>Pour des raisons de sécurité, n’envoyez pas d’argent comptant par la poste. Remettez-le en personne au bureau, le vendredi de 13 h à 15 h :</p><address>{office(lang)}</address></div>
 </div>
 <p class="note center" style="margin-top:30px">{ORG_FR}, organisme de bienfaisance enregistré n° {cn}. Des reçus officiels sont délivrés pour les dons admissibles selon les règles de l’Agence du revenu du Canada. Les cotisations de membre ne donnent pas droit à un reçu.</p>
</div></section>"""
    return page_title(lang, "donate", cur, "Donate") + f"""
<section class="sec"><div class="wrap">
 {title("Your gift pays for fuel, lodging and meals for people who must leave the region for treatment.", "Three Ways to Give", center=True, sep=True)}
 <p class="center" style="max-width:760px;margin:0 auto 36px">You can give online by credit or debit card, or offline by cheque or cash. Read below for details.</p>
 <div class="cols c3">
  <div class="box top"><h3>One-Time Donation</h3><p>A one-time donation provides immediate support to people facing cancer in the territory we serve. It helps cover travel, lodging and meals for patients during a time of great need.</p><div class="btns">{zbutton('zeffy_donate', lang, 'Donate a Lump Sum')}</div></div>
  <div class="box top"><h3>Recurring Donation</h3><p>Become a sustaining partner in the fight against cancer. A monthly, quarterly or yearly gift gives the Foundation reliable funding, so we can plan ahead and offer consistent support. Stop at any time.</p><div class="btns">{zbutton('zeffy_donate', lang, 'Donate a Recurring Amount')}</div></div>
  <div class="box top"><h3>In Memoriam Donation</h3><p>Honour the memory of a friend or loved one lost to cancer. We let the family know of your gift, without the amount, and you receive an income tax receipt.</p><div class="btns">{zbutton('zeffy_donate', lang, 'Donate In Memoriam')}</div></div>
 </div>
</div></section>
<section class="sec light"><div class="wrap cols c2">
 <div>{title("Donate Securely, Support Directly", "Donate Online", sep=True)}</div>
 <div>
  <p>Online gifts are processed by <strong>Zeffy</strong>, a free platform for charities. The Foundation receives <strong>100% of your gift</strong>: no platform or transaction fees.</p>
  <p>At checkout, Zeffy suggests an optional contribution to its own operations. It is voluntary and you can set it to $0.</p>
  <p>Your official tax receipt is emailed as soon as payment is confirmed. Monthly donors receive one cumulative receipt in January.</p>
  <div class="btns">{zbutton('zeffy_donate', lang, 'Donate Online')}</div>
 </div>
</div></section>
<section class="sec"><div class="wrap">
 {title("Other Methods to Give", "Offline Payments", center=True, sep=True)}
 <p class="center" style="max-width:760px;margin:0 auto 40px">If you prefer not to give online, follow the steps below.</p>
 <div class="steps">
  <div class="step"><h3>Download and Print the Form</h3><p>You may mail a donation without a form, except for an in-memoriam gift or if you want an income tax receipt. In that case, include a note with your name and address, or the form below.</p><ul class="links"><li><a href="{imf}">In Memoriam Donation Form (PDF)</a></li></ul></div>
  <div class="step"><h3>Prepare Your Payment</h3><p>We accept cheques and cash. Cheques are payable to the <strong>{ORG_EN}</strong>. For recurring donations, post-dated cheques are recommended.</p></div>
  <div class="step"><h3>Send or Deliver Payment</h3><p>Cheques, by mail:</p><address>{MAIL_EN}</address><p>For security reasons, do not mail cash. Deliver it in person at our office on Fridays between 1 p.m. and 3 p.m.:</p><address>{office(lang)}</address></div>
 </div>
 <p class="note center" style="margin-top:30px">{ORG_EN}, registered charity no. {cn}. Official receipts are issued for eligible gifts under Canada Revenue Agency rules. Membership fees are not receipted.</p>
</div></section>"""

# ---------------------------------------------------------------------------
# Membership
# ---------------------------------------------------------------------------
def page_membership(lang, cur):
    if lang == "fr":
        return page_title(lang, "membership", cur, "Adhésion") + f"""
<section class="sec"><div class="wrap cols c2">
 <div>
  {title("", "Adhésion", sep=True)}
  <p>La {ORG_FR} est un organisme communautaire voué au soutien des personnes touchées par le cancer dans notre région. En devenant membre, vous contribuez directement à notre capacité d’offrir des services essentiels et une aide financière aux patients en traitement.</p>
  <p>Nous offrons une seule catégorie d’adhésion, pour une personne ou un couple :</p>
  <div class="prices"><div class="price"><b>15 $</b><span>Individuelle / an</span></div><div class="price"><b>25 $</b><span>Couple / an</span></div></div>
  <h3>Avantages</h3>
  <ul>
   <li>L’admissibilité à l’<a href="{url(lang, 'assistance', cur)}">aide aux déplacements</a> pour vos traitements;</li>
   <li>Des nouvelles régulières de nos programmes et initiatives;</li>
   <li>Le droit de vote à l’assemblée générale annuelle et à toute assemblée extraordinaire des membres.</li>
  </ul>
  <p>L’adhésion est valide du 1<sup>er</sup> janvier au 31 décembre de l’année où vous adhérez. Une adhésion non renouvelée au plus tard le dernier jour de février prend fin.</p>
 </div>
 <div class="box top">
  {title("Adhérer ou renouveler", "Devenir membre", sep=True)}
  <p>Remplissez le formulaire en ligne pour devenir membre ou renouveler votre adhésion. Le paiement est sécurisé et la Fondation reçoit 100 % de votre cotisation.</p>
  <div class="btns">{zbutton('zeffy_membership', lang, 'Adhérer ou renouveler')}</div>
  <p style="margin-top:24px"><strong>Par la poste ou en personne :</strong> envoyez un chèque à l’ordre de la {ORG_FR} au {MAIL_FR.replace('<br>', ', ')}, avec votre nom, adresse, téléphone et courriel, ou passez au bureau le vendredi de 13 h à 15 h.</p>
 </div>
</div></section>"""
    return page_title(lang, "membership", cur, "Membership") + f"""
<section class="sec"><div class="wrap cols c2">
 <div>
  {title("", "Membership", sep=True)}
  <p>The {ORG_EN} is a community-based organization dedicated to supporting people affected by cancer in our region. By becoming a member, you directly contribute to our ability to offer essential services and financial assistance to patients undergoing treatment.</p>
  <p>We offer one class of membership, for individuals or couples:</p>
  <div class="prices"><div class="price"><b>$15</b><span>Individual / year</span></div><div class="price"><b>$25</b><span>Couple / year</span></div></div>
  <h3>Membership benefits</h3>
  <ul>
   <li>Eligibility for <a href="{url(lang, 'assistance', cur)}">travel assistance</a> for your treatments;</li>
   <li>Regular updates on our programs and initiatives;</li>
   <li>Voting rights at the Annual General Meeting and any special members’ meeting.</li>
  </ul>
  <p>Membership is valid from January 1 to December 31 of the year you join. A membership not renewed by the last day of February lapses.</p>
 </div>
 <div class="box top">
  {title("Join or Renew Today!", "Become a Member", sep=True)}
  <p>Fill out the online form to become a new member or renew your membership. Payment is secure and the Foundation receives 100% of your fee.</p>
  <div class="btns">{zbutton('zeffy_membership', lang, 'Join or Renew')}</div>
  <p style="margin-top:24px"><strong>By mail or in person:</strong> send a cheque payable to the {ORG_EN} to {MAIL_EN.replace('<br>', ', ')}, with your name, address, phone and email, or drop by the office on a Friday between 1 p.m. and 3 p.m.</p>
 </div>
</div></section>"""

# ---------------------------------------------------------------------------
# Contact
# ---------------------------------------------------------------------------
PEOPLE = [("Tony C. Patterson", "418 368-3276", "418-368-3276"),
          ("Beatrice Coffin", "418 368-1566", "418-368-1566"),
          ("Theresa Joseph", "418 368-2361", "418-368-2361"),
          ("Patricia Ste-Croix", "418 645-3779", "418-645-3779")]

def page_contact(lang, cur):
    fr = lang == "fr"
    ppl = "".join(f'<li><span>{n}</span><a href="tel:+1{t.replace("-", "")}">{a if fr else t}</a></li>' for n, a, t in PEOPLE)
    write = ""
    if CONFIG["email"] or CONFIG["contact_form"]:
        bits = []
        if CONFIG["email"]:
            bits.append(f'<a href="mailto:{e(CONFIG["email"])}">{e(CONFIG["email"])}</a>')
        if CONFIG["contact_form"]:
            bits.append(f'<a class="btn" href="{e(CONFIG["contact_form"])}" rel="noopener">{"Écrivez-nous" if fr else "Write to us"}</a>')
        write = f'<div class="info"><h3>{"Courriel" if fr else "Email"}</h3><p>{"<br>".join(bits)}</p></div>'
    if fr:
        return page_title(lang, "contact", cur, "Nous joindre") + f"""
<section class="sec"><div class="wrap">
 {title("Par la poste, en personne ou par téléphone", "Nous joindre", center=True, sep=True)}
 <div class="cols c3">
  <div class="box info"><h3>Poste</h3><address>{MAIL_FR}</address></div>
  <div class="box info"><h3>Bureau</h3><address>{office(lang)}</address><p style="margin-top:1em">Rendez-nous visite au bureau tous les vendredis, de 13 h à 15 h.</p></div>
  <div class="box info"><h3>Téléphone</h3><ul class="people">{ppl}</ul></div>
 </div>
</div></section>
<section class="sec light tight"><div class="wrap cols c2">
 <div class="info"><h3>Réseaux sociaux</h3><p>Suivez notre page officielle : <a href="{FACEBOOK}" rel="noopener">Facebook</a></p></div>
 {write}
</div></section>"""
    return page_title(lang, "contact", cur, "Contact Us") + f"""
<section class="sec"><div class="wrap">
 {title("Reach out to us by mail, in person or by phone", "Contact Us", center=True, sep=True)}
 <div class="cols c3">
  <div class="box info"><h3>Post Mail</h3><address>{MAIL_EN}</address></div>
  <div class="box info"><h3>Office</h3><address>{office(lang)}</address><p style="margin-top:1em">Visit us at our office any Friday from 1 p.m. to 3 p.m.</p></div>
  <div class="box info"><h3>Phone</h3><ul class="people">{ppl}</ul></div>
 </div>
</div></section>
<section class="sec light tight"><div class="wrap cols c2">
 <div class="info"><h3>Follow Us</h3><p>Find and follow our official page: <a href="{FACEBOOK}" rel="noopener">Facebook</a></p></div>
 {write}
</div></section>"""

META = {
    "home": (("À propos", "Aide financière aux personnes atteintes de cancer de la région de Gaspé qui doivent se déplacer pour leurs traitements."),
             ("About Us", "Financial aid for people with cancer in the Gaspé area who must travel for treatment.")),
    "assistance": (("Demander de l’aide", "Comment les membres peuvent demander une aide financière pour les déplacements liés aux traitements contre le cancer."),
                   ("Request Assistance", "How members can request financial aid for cancer treatment travel.")),
    "resources": (("Ressources", "Hôpitaux, hébergement et services d’interprétation hors région."),
                  ("Resources", "Out-of-region hospitals, lodging and interpretation services.")),
    "donate": (("Faire un don", "Faites un don à la Fondation du cancer de Gaspé. 100 % de votre don va à la Fondation."),
               ("Donate", "Give to the Gaspé Cancer Foundation. 100% of your gift reaches the Foundation.")),
    "membership": (("Adhésion", "Adhésion annuelle individuelle (15 $) ou couple (25 $)."),
                   ("Membership", "Annual membership: individual ($15) or couple ($25).")),
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
    # GitHub Pages serves 404.html from any path, so use root-absolute links here.
    return f"""<!doctype html><html lang="fr-CA"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Page introuvable / Page not found</title><link rel="icon" href="/assets/favicon.png">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600&family=Roboto:wght@400;500;700;900&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/assets/site.css"></head>
<body><div class="masthead solid"><header class="site-header"><div class="wrap"><a class="logo logo-text" href="/"><img src="/assets/emblem.png" alt="" width="137" height="123"><span>Fondation<br>du cancer<br>de Gaspé</span></a></div></header></div>
<main id="main"><section class="sec"><div class="wrap cols c2">
<div><h1>Page introuvable</h1><p>La page demandée n’existe pas ou a été déplacée.</p><p><a class="btn" href="/">Retour à l’accueil</a></p></div>
<div lang="en"><h1>Page not found</h1><p>The page you requested does not exist or has moved.</p><p><a class="btn outline" href="/en/about/">English home page</a></p></div>
</div></section></main></body></html>
"""

def main():
    written = []
    for key, (frp, enp) in PAGES.items():
        for lang, path in (("fr", frp), ("en", enp)):
            title_txt, desc = META[key][0 if lang == "fr" else 1]
            body = BUILDERS[key](lang, path)
            out = ROOT / path
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(layout(lang, key, path, title_txt, desc, body), encoding="utf-8")
            written.append(path)
    for path, (lang, key) in REDIRECTS.items():
        out = ROOT / path
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(redirect_page(path, lang, key), encoding="utf-8")
        written.append(path)
    (ROOT / "404.html").write_text(page_404(), encoding="utf-8")
    urls = "".join(f"<url><loc>{CONFIG['site_url']}/{p.replace('index.html', '')}</loc></url>"
                   for k in PAGES for p in PAGES[k])
    (ROOT / "sitemap.xml").write_text(f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>\n', encoding="utf-8")
    (ROOT / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {CONFIG['site_url']}/sitemap.xml\n", encoding="utf-8")
    print(f"Built {len(written) + 1} pages.")

if __name__ == "__main__":
    main()
