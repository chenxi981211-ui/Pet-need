#!/usr/bin/env python3
"""
Pet Needs — static site generator (Nederlands + English).

Leest data/site.json en scripts/i18n.py en schrijft platte HTML:
    /                 Nederlandse site  (index.html, assortiment.html, …)
    /en/              Engelse site      (en/index.html, en/assortiment.html, …)

Gebruik:  python3 scripts/build.py
"""

import html
import json
import os
import shutil
import sys
from urllib.parse import quote

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from icons import icon  # noqa: E402
from i18n import TEXT, LANGS, LANG_LABEL, LANG_NAME, HTML_LANG, DAYS, PET_LABELS, SITE_TEXT  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = json.load(open(os.path.join(ROOT, "data", "site.json"), encoding="utf-8"))
SITE = DATA["site"]
CATS = DATA["categories"]
PRODUCTS = DATA["products"]
PETS = DATA["pets"]
IMG = SITE["images"]

CAT_BY_SLUG = {c["slug"]: c for c in CATS}
WA = "https://wa.me/" + SITE["whatsapp"].lstrip("+")
BASE_URL = "https://www.petneeds.nl"


def asset_version(*paths):
    """Korte hash van de asset-bestanden, als cache-buster in de URL."""
    import hashlib
    h = hashlib.md5()
    for rel in paths:
        full = os.path.join(ROOT, rel)
        if os.path.exists(full):
            with open(full, "rb") as fh:
                h.update(fh.read())
    return h.hexdigest()[:8]


VERSION = asset_version("assets/css/site.css", "assets/js/site.js", "assets/js/cart.js")


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------
def e(s):
    return html.escape(str(s or ""), quote=True)


def t(lang, key, **fmt):
    value = TEXT[lang].get(key, TEXT["nl"].get(key, key))
    return value.format(**fmt) if fmt else value


def money(value):
    if value is None:
        return ""
    return "€ " + ("%.2f" % value).replace(".", ",")


def wa_link(text):
    return WA + "?text=" + quote(text)


def plural(lang, n):
    return "%d %s" % (n, t(lang, "product_one" if n == 1 else "product_many"))


def write(path, content):
    full = os.path.join(ROOT, path)
    os.makedirs(os.path.dirname(full) or ".", exist_ok=True)
    with open(full, "w", encoding="utf-8") as fh:
        fh.write(content)
    return path


def out_path(lang, rel):
    return rel if lang == "nl" else "en/" + rel


def lang_base(lang, rel):
    """Relatief pad terug naar de site-root vanaf de gegenereerde pagina (voor assets)."""
    return "../" * out_path(lang, rel).count("/")


def link_base(lang, rel):
    """Basis voor links naar andere pagina's — blijft binnen dezelfde taal."""
    return lang_base(lang, rel) + ("" if lang == "nl" else "en/")


# --- taalgevoelige data-accessors ----------------------------------------
def cat_name(c, lang):
    return c["name_en"] if lang == "en" and c.get("name_en") else c["name"]


def cat_intro(c, lang):
    return c["intro_en"] if lang == "en" and c.get("intro_en") else c["intro"]


def prod_desc(p, lang):
    return (p.get("description_en") or "") if lang == "en" else (p.get("description") or "")


def pet_label(slug, lang):
    return PET_LABELS[lang].get(slug, slug)


def site_text(lang, key):
    return SITE_TEXT[lang][key]


def hours_rows(lang):
    return [(DAYS[lang].get(d, d), DAYS[lang].get(v, v)) for d, v in SITE["hours"]]


def img_alt(key, lang):
    if lang == "en" and IMG.get(key + "_en"):
        return IMG[key + "_en"]
    return IMG.get(key, "")


def products_of(slug):
    return [p for p in PRODUCTS if p["category"] == slug]


def pets_of(cat):
    return cat.get("pets") or [cat["pet"]]


def count_for_pet(pet_slug):
    return sum(1 for p in PRODUCTS if pet_slug in pets_of(CAT_BY_SLUG[p["category"]]))


def delivery_area(lang):
    joiner = " and " if lang == "en" else " en "
    return ", ".join(SITE["delivery_area"][:-1]) + joiner + SITE["delivery_area"][-1]


def has_img(rel_path):
    return bool(rel_path) and os.path.exists(os.path.join(ROOT, rel_path))


# --------------------------------------------------------------------------
# chrome
# --------------------------------------------------------------------------
NAV = [
    ("index.html", "nav_home"),
    ("assortiment.html", "nav_shop"),
    ("dierenarts.html", "nav_vet"),
    ("over-ons.html", "nav_about"),
    ("contact.html", "nav_contact"),
]


def lang_switch(lang, rel, base, other_rel=None):
    links = []
    for code in LANGS:
        target = rel if code == lang else (other_rel or rel)
        href = base + ("" if code == "nl" else "en/") + target
        current = code == lang
        links.append(
            '<a class="lang__link{cur}" href="{href}" hreflang="{code}" lang="{code}" '
            'title="{name}"{aria}>{label}</a>'.format(
                cur=" is-active" if current else "", href=href, code=HTML_LANG[code],
                name=e(LANG_NAME[code]), label=LANG_LABEL[code],
                aria=' aria-current="true"' if current else "")
        )
    return '<div class="lang" role="group" aria-label="{lbl}">{links}</div>'.format(
        lbl=t(lang, "lang_switch"), links="".join(links))


def header(lang, rel, base, other_rel=None):
    lbase = link_base(lang, rel)
    links = "".join(
        '<li><a class="nav__link" href="{L}{href}"{cur}>{label}</a></li>'.format(
            L=lbase, href=href, label=t(lang, key),
            cur=' aria-current="page"' if href == rel else "")
        for href, key in NAV
    )
    return """
<a class="skip-link" href="#main">{skip}</a>
<div class="topbar">
  <div class="wrap topbar__inner">
    <span>{truck} {delivery}</span>
    <span>{clock} {advice}&nbsp;<a href="{wa}">{phone}</a></span>
  </div>
</div>
<header class="site-header">
  <div class="wrap header__inner">
    <a class="brand" href="{L}index.html">
      <span class="brand__mark">{logo}</span>
      <span>Pet Needs<small>{sub}</small></span>
    </a>
    <nav class="nav" data-nav aria-label="{menu_label}">
      <ul class="nav__list">{links}
        <li class="nav__item--mobile"><a class="nav__link" href="{L}bestellen.html">{order_mobile}</a></li>
        <li class="nav__item--lang">{lang_switch}</li>
      </ul>
    </nav>
    <div class="header__actions">
      {lang_switch}
      <a class="btn btn--primary btn--sm hide-sm" href="{L}bestellen.html">{bag} {order}</a>
      <button class="icon-btn cart-btn" data-cart-open aria-label="{cart_open}">
        {bag}<span class="cart-btn__count" data-cart-count hidden>0</span>
      </button>
      <button class="icon-btn nav-toggle" data-nav-toggle aria-expanded="false" aria-label="{menu_open}">{menu_icon}</button>
    </div>
  </div>
</header>
""".format(
        skip=t(lang, "skip"), truck=icon("truck"), clock=icon("clock"),
        delivery=t(lang, "topbar_delivery", days=e(site_text(lang, "delivery_days"))),
        advice=t(lang, "topbar_advice"), wa=wa_link(t(lang, "wa_question")),
        phone=e(SITE["whatsapp_display"]), b=base, L=lbase, logo=icon("logo"),
        sub=t(lang, "brand_sub"), menu_label=t(lang, "nav_home"), links=links,
        order_mobile=t(lang, "nav_order_mobile"), lang_switch=lang_switch(lang, rel, base, other_rel),
        bag=icon("bag"), order=t(lang, "btn_order"), cart_open=t(lang, "cart_open"),
        menu_open=t(lang, "menu_open"), menu_icon=icon("menu"),
    )


def footer(lang, base, lbase):
    cat_links = "".join(
        '<li><a href="{L}categorie/{s}.html">{n}</a></li>'.format(
            L=lbase, s=c["slug"], n=e(cat_name(c, lang)))
        for c in CATS[:7]
    )
    hours = "".join("<li><span>{d}</span><span>{v}</span></li>".format(d=e(d), v=e(v))
                    for d, v in hours_rows(lang))
    styleguide = ('<li><a href="{L}styleguide.html">{label}</a></li>'.format(
        L=lbase, label=t(lang, "footer_styleguide")) if lang == "nl" else "")
    return """
<footer class="site-footer">
  <div class="wrap">
    <div class="footer__grid">
      <div>
        <a class="brand" href="{L}index.html">
          <span class="brand__mark">{logo}</span>
          <span>Pet Needs<small>{sub}</small></span>
        </a>
        <p style="margin-top:1rem;max-width:22rem">{tagline}</p>
        <a class="btn btn--wa btn--sm" href="{wa}">{whatsapp} {phone}</a>
      </div>
      <div>
        <h4>{col_shop}</h4>
        <ul class="footer__list">{cat_links}
          <li><a href="{L}assortiment.html">{all_products}</a></li>
        </ul>
      </div>
      <div>
        <h4>{col_store}</h4>
        <ul class="footer__list">
          <li><a href="{L}over-ons.html">{about}</a></li>
          <li><a href="{L}dierenarts.html">{vet}</a></li>
          <li><a href="{L}contact.html">{hours_route}</a></li>
          <li><a href="{L}privacy.html">{privacy}</a></li>
          {styleguide}
        </ul>
      </div>
      <div>
        <h4>{col_visit}</h4>
        <p style="margin-bottom:.75rem">{street}<br>{zip} {city}</p>
        <ul class="hours">{hours}</ul>
      </div>
    </div>
    <div class="footer__bottom">
      <span>&copy; <span data-year>2026</span> {rights}</span>
      <span>{price_note}</span>
    </div>
  </div>
</footer>
""".format(
        b=base, L=lbase, logo=icon("logo"), sub=t(lang, "brand_sub_footer", since=SITE["since"]),
        tagline=t(lang, "footer_tagline"), wa=wa_link(t(lang, "wa_question")),
        whatsapp=icon("whatsapp"), phone=e(SITE["whatsapp_display"]),
        col_shop=t(lang, "footer_shop"), cat_links=cat_links,
        all_products=t(lang, "footer_all_products"), col_store=t(lang, "footer_store"),
        about=t(lang, "nav_about"), vet=t(lang, "nav_vet"),
        hours_route=t(lang, "footer_hours_route"), privacy=t(lang, "footer_privacy"),
        styleguide=styleguide, col_visit=t(lang, "footer_visit"),
        street=e(SITE["address"]["street"]), zip=e(SITE["address"]["zip"]),
        city=e(SITE["address"]["city"]), hours=hours, rights=t(lang, "footer_rights"),
        price_note=t(lang, "footer_price_note"),
    )


def cart_drawer(lang, base, lbase):
    return """
<div class="cart-backdrop" data-cart-backdrop hidden></div>
<aside class="cart" data-cart-panel aria-label="{title}" aria-hidden="true" hidden>
  <div class="cart__head">
    <h2>{title}</h2>
    <button class="icon-btn" data-cart-close aria-label="{close}">{close_icon}</button>
  </div>
  <div class="cart__body" data-cart-items></div>
  <div class="cart__foot" data-cart-foot hidden>
    <div class="cart__total"><span>{subtotal}</span><strong data-cart-total>€ 0,00</strong></div>
    <p class="cart__note">{note}</p>
    <a class="btn btn--primary btn--block" href="{L}bestellen.html">{checkout} {arrow}</a>
    <button class="cart__clear" data-cart-clear>{clear}</button>
  </div>
</aside>
<div class="toast" data-toast hidden role="status" aria-live="polite"></div>
""".format(
        title=t(lang, "cart_title"), close=t(lang, "cart_close"), close_icon=icon("close"),
        subtotal=t(lang, "cart_subtotal"), note=t(lang, "cart_note"), L=lbase,
        checkout=t(lang, "cart_checkout"), arrow=icon("arrow"), clear=t(lang, "cart_clear"),
    )


def js_strings(lang, base, lbase):
    payload = {k[3:]: v for k, v in TEXT[lang].items() if k.startswith("js_")}
    payload["base"] = base
    payload["lang"] = HTML_LANG[lang]
    payload["shopUrl"] = lbase + "assortiment.html"
    payload["linkBase"] = lbase
    return json.dumps(payload, ensure_ascii=False)


FONTS = ("https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700"
         "&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap")


def layout(lang, rel, title, description, body, extra_head="", other_rel=None):
    base = lang_base(lang, rel)
    lbase = link_base(lang, rel)
    alternates = "" if other_rel else "".join(
        '<link rel="alternate" hreflang="{code}" href="{url}">'.format(
            code=HTML_LANG[code],
            url=BASE_URL + "/" + ("" if code == "nl" else "en/") + rel)
        for code in LANGS)
    return """<!doctype html>
<html lang="{htmllang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:type" content="website">
<meta name="theme-color" content="#14523a">
{alternates}
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>&#128062;</text></svg>">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="{fonts}" rel="stylesheet">
<link rel="stylesheet" href="{b}assets/css/site.css?v={v}">
{extra_head}
</head>
<body data-base="{b}" data-link-base="{L}" data-lang="{htmllang}">
{header}
<main id="main">
{body}
</main>
{footer}
{cart}
<script>window.PN_I18N = {i18n};</script>
<script src="{b}assets/js/site.js?v={v}" defer></script>
<script src="{b}assets/js/cart.js?v={v}" defer></script>
</body>
</html>
""".format(
        htmllang=HTML_LANG[lang], title=e(title), desc=e(description), alternates=alternates,
        fonts=FONTS, b=base, L=lbase, v=VERSION, extra_head=extra_head,
        header=header(lang, rel, base, other_rel), body=body, footer=footer(lang, base, lbase),
        cart=cart_drawer(lang, base, lbase), i18n=js_strings(lang, base, lbase),
    )


# --------------------------------------------------------------------------
# components
# --------------------------------------------------------------------------
def cart_data(p):
    return ('data-add-to-cart data-sku="{sku}" data-name="{name}" data-price="{price}" '
            'data-image="{img}" data-url="product/{slug}.html"').format(
        sku=e(p["sku"]), name=e(p["name"]),
        price=("%.2f" % p["price"]) if p["price"] else "",
        img=e(p["image"]), slug=p["slug"])


def product_card(p, lang, base="", lbase=None):
    lbase = base if lbase is None else lbase
    cat = CAT_BY_SLUG[p["category"]]
    media = ('<img src="{b}{img}" alt="{alt}" loading="lazy" width="600" height="600">'.format(
        b=base, img=p["image"], alt=e(p["name"]))
        if p["image"] else '<span class="product__ph {tint}">{paw}</span>'.format(
            tint=cat["tint"], paw=icon("paw")))
    price = ('<span class="price">{}</span>'.format(money(p["price"])) if p["price"]
             else '<span class="price--ask">{}</span>'.format(t(lang, "price_ask")))
    search = "{} {} {}".format(p["name"], cat_name(cat, lang), prod_desc(p, lang))
    return """
<article class="product reveal" data-product data-category="{cat}" data-pet="{pet}" data-search="{search}">
  <div class="product__media">{media}</div>
  <div class="product__body">
    <span class="product__cat">{catname}</span>
    <h3 class="product__title"><a href="{L}product/{slug}.html">{name}</a></h3>
    <div class="product__foot">{price}
      <button class="product__add" type="button" {data} aria-label="{aria}">{bag}<span>{add}</span></button>
    </div>
  </div>
</article>""".format(
        cat=cat["slug"], pet=" ".join(pets_of(cat)), search=e(search), media=media,
        catname=e(cat_name(cat, lang)), L=lbase, b=base, slug=p["slug"], name=e(p["name"]), price=price,
        data=cart_data(p), bag=icon("bag"), add=t(lang, "add_short"),
        aria=t(lang, "add_to_cart_label", name=e(p["name"])))


def category_card(c, lang, base="", lbase=None):
    lbase = base if lbase is None else lbase
    media = ('<img src="{b}{img}" alt="{alt}" loading="lazy" width="600" height="450">'.format(
        b=base, img=c["image"], alt=e(cat_name(c, lang)))
        if c["image"] else "<span>{}</span>".format(icon("paw")))
    return """
<article class="card reveal">
  <div class="card__media {tint}">{media}</div>
  <div class="card__body">
    <h3 class="card__title"><a class="card__link" href="{L}categorie/{slug}.html">{name}</a></h3>
    <p class="card__meta">{count}</p>
  </div>
</article>""".format(
        tint=c["tint"], media=media, b=base, L=lbase, slug=c["slug"], name=e(cat_name(c, lang)),
        count=plural(lang, c["count"]))


def cta_band(lang, base="", lbase=None):
    lbase = base if lbase is None else lbase
    return """
<section class="section">
  <div class="wrap">
    <div class="cta paw-bg reveal">
      <span class="eyebrow">{paw} {eyebrow}</span>
      <h2>{title}</h2>
      <p>{body}</p>
      <div class="cta__actions">
        <a class="btn btn--primary btn--lg" href="{wa}">{whatsapp} {app}</a>
        <a class="btn btn--light btn--lg" href="{L}contact.html">{pin} {visit}</a>
      </div>
    </div>
  </div>
</section>""".format(
        paw=icon("paw"), eyebrow=t(lang, "cta_eyebrow"), title=t(lang, "cta_title"),
        body=t(lang, "cta_body"), wa=wa_link(t(lang, "wa_pet_question")), whatsapp=icon("whatsapp"),
        app=t(lang, "cta_app", phone=e(SITE["whatsapp_display"])), L=lbase, pin=icon("pin"),
        visit=t(lang, "cta_visit"))


def shop_cat_section(lang, base=""):
    if not has_img(IMG.get("cat")):
        return ""
    second = ""
    if has_img(IMG.get("cat2")):
        second = """
      <div class="cat-stack__small frame">
        <img src="{b}{img}" alt="{alt}" loading="lazy" width="800" height="800">
      </div>""".format(b=base, img=e(IMG["cat2"]), alt=e(img_alt("cat2_alt", lang)))
    return """
<section class="section section--sand">
  <div class="wrap split">
    <div class="cat-stack reveal">
      <div class="frame frame--3x4">
        <img src="{b}{img}" alt="{alt}" loading="lazy" width="900" height="1200">
      </div>{second}
      <span class="sticker cat-stack__sticker">{paw} {sticker}</span>
    </div>
    <div>
      <span class="eyebrow eyebrow--sun">{heart} {eyebrow}</span>
      <h2>{title}</h2>
      <p class="lede">{intro}</p>
    </div>
  </div>
</section>""".format(
        b=base, img=e(IMG["cat"]), alt=e(img_alt("cat_alt", lang)), second=second, paw=icon("paw"),
        sticker=e(site_text(lang, "cat_sticker")), heart=icon("heart"),
        eyebrow=e(site_text(lang, "cat_eyebrow")), title=e(site_text(lang, "cat_title")),
        intro=e(site_text(lang, "cat_intro")))


def hero_slides(lang, base=""):
    out = []
    for index, slide in enumerate(SITE["hero_slides"]):
        alt = slide.get("alt_en") if lang == "en" and slide.get("alt_en") else slide["alt"]
        out.append('<img class="hero__slide{active}" src="{b}{src}" alt="{alt}" width="1100" '
                   'height="1100" {loading} data-slide="{i}">'.format(
                       active=" is-active" if index == 0 else "", b=base, src=e(slide["image"]),
                       alt=e(alt), i=index,
                       loading='fetchpriority="high"' if index == 0 else 'loading="lazy"'))
    return "".join(out)


def hero_dots(lang):
    out = []
    for index, slide in enumerate(SITE["hero_slides"]):
        label = slide.get("label_en") if lang == "en" and slide.get("label_en") else slide["label"]
        out.append('<button type="button" class="hero__dot{active}" data-hero-dot="{i}" '
                   'aria-label="{aria}" aria-selected="{sel}"></button>'.format(
                       active=" is-active" if index == 0 else "", i=index,
                       aria=t(lang, "hero_photo_of", label=e(label)),
                       sel="true" if index == 0 else "false"))
    return "".join(out)


def crumbs(lang, base, trail, lbase=None):
    lbase = base if lbase is None else lbase
    parts = ['<a href="{L}index.html">{home}</a>'.format(L=lbase, home=t(lang, "crumb_home"))]
    for label, href in trail:
        parts.append("<span>/</span>")
        parts.append('<a href="{L}{href}">{label}</a>'.format(L=lbase, href=href, label=label)
                     if href else "<span>%s</span>" % label)
    return '<div class="wrap"><nav class="crumbs" aria-label="Breadcrumb">%s</nav></div>' % " ".join(parts)


# --------------------------------------------------------------------------
# pages
# --------------------------------------------------------------------------
def page_home(lang):
    rel = "index.html"
    base = lang_base(lang, rel)
    lbase = link_base(lang, rel)
    days = site_text(lang, "delivery_days")
    area = delivery_area(lang)

    pets = "".join(
        """<a class="pet reveal" href="{L}assortiment.html?dier={slug}">
        <span class="pet__ring {tint}"><img src="{b}{img}" alt="{label}" loading="lazy" width="300" height="300"></span>
        <span class="pet__label">{label}</span>
        <span class="pet__count">{count}</span>
      </a>""".format(
            b=base, L=lbase, slug=p["slug"], tint=p.get("tint", "tint-mint"), img=e(p["image"]),
            label=e(pet_label(p["slug"], lang)), count=plural(lang, count_for_pet(p["slug"])))
        for p in PETS)

    featured, used = [], set()
    for c in CATS:
        pick = next((p for p in products_of(c["slug"]) if p["image"] and p["price"]), None)
        if pick and pick["slug"] not in used:
            featured.append(pick)
            used.add(pick["slug"])
    featured_html = "".join(product_card(p, lang, base, lbase) for p in featured[:8])
    cats_html = "".join(category_card(c, lang, base, lbase) for c in CATS[:8])

    strip_items = [t(lang, "strip_1", since=SITE["since"]), t(lang, "strip_2"),
                   t(lang, "strip_3"), t(lang, "strip_4"), t(lang, "strip_5")]
    strip = "".join("<span>{paw} {txt}</span>".format(paw=icon("paw"), txt=txt)
                    for txt in strip_items) * 2

    body = """
<section class="hero">
  <div class="wrap">
    <div class="hero__panel paw-bg">
      <div class="hero__grid">
        <div>
          <span class="eyebrow">{paw} {hero_eyebrow}</span>
          <h1>{hero_title}</h1>
          <p class="hero__lede">{hero_lede}</p>
          <div class="hero__actions">
            <a class="btn btn--primary btn--lg" href="{L}assortiment.html">{cta_shop} {arrow}</a>
            <a class="btn btn--light btn--lg" href="{wa}">{whatsapp} {cta_app}</a>
          </div>
          <ul class="hero__trust">
            <li>{check} {trust1}</li>
            <li>{check} {trust2}</li>
            <li>{check} {trust3}</li>
          </ul>
        </div>
        <div class="hero__media reveal">
          <span class="sticker hero__sticker hero__sticker--tl">{heart} {sticker_since}</span>
          <span class="sticker sticker--carrot hero__sticker hero__sticker--br">{stet} {sticker_vet}</span>
          <div class="hero__photo" data-hero-slider>
            {slides}
            <div class="hero__dots" role="group">{dots}</div>
            <div class="hero__progress" data-hero-progress></div>
          </div>
          <div class="hero__card">
            <span class="dot">{paw}</span>
            <span><strong>{card_title}</strong><span>{card_sub}</span></span>
          </div>
        </div>
      </div>
    </div>
  </div>
</section>

<div class="strip" aria-hidden="true"><div class="strip__track">{strip}</div></div>

<section class="section">
  <div class="wrap">
    <div class="section-head section-head--center">
      <span class="eyebrow eyebrow--carrot">{paw} {pets_eyebrow}</span>
      <h2>{pets_title}</h2>
      <p>{pets_lede}</p>
    </div>
    <div class="pets">{pets}</div>
  </div>
</section>

{storefront_block}
<section class="section section--sand">
  <div class="wrap">
    <div class="section-head">
      <span class="eyebrow">{cats_eyebrow}</span>
      <h2>{cats_title}</h2>
      <p>{cats_lede}</p>
    </div>
    <div class="cards">{cats}</div>
    <p class="mt-lg"><a class="btn btn--outline" href="{L}assortiment.html">{cats_cta} {arrow}</a></p>
  </div>
</section>

<section class="section">
  <div class="wrap split">
    <div class="reveal" style="position:relative">
      <div class="frame frame--squircle frame--1x1">
        <img src="{b}{advice_img}" alt="{advice_alt}" loading="lazy" width="1000" height="1000">
      </div>
      <span class="sticker sticker--white" style="position:absolute;right:.5rem;bottom:1.5rem;z-index:2">{leaf} {advice_sticker}</span>
    </div>
    <div>
      <span class="eyebrow eyebrow--sun">{heart} {advice_eyebrow}</span>
      <h2>{advice_title}</h2>
      <div class="quote" style="margin-bottom:1.5rem">
        <span class="quote__mark">{quote}</span>
        <p>{advice_quote}</p>
        <cite>{advice_cite}</cite>
      </div>
      <p>{advice_body}</p>
      <a class="btn btn--primary" href="{wa}">{whatsapp} {advice_cta}</a>
    </div>
  </div>
</section>

<section class="section section--sand">
  <div class="wrap split split--reverse">
    <div>
      <span class="eyebrow">{paw} {animals_eyebrow}</span>
      <h2>{animals_title}</h2>
      <p>{animals_p1}</p>
      <p>{animals_p2}</p>
      <div class="grid-auto mt-lg">
        <div class="feature"><span class="feature__icon">{heart}</span><div><h3>{a_f1_t}</h3><p>{a_f1_b}</p></div></div>
        <div class="feature"><span class="feature__icon">{leaf}</span><div><h3>{a_f2_t}</h3><p>{a_f2_b}</p></div></div>
      </div>
    </div>
    <div class="reveal">
      <div class="frame frame--circle">
        <img src="{b}assets/img/products/baby-cavia-s.jpg" alt="{animals_alt}" loading="lazy" width="900" height="900">
      </div>
    </div>
  </div>
</section>

<section class="section">
  <div class="wrap">
    <div class="section-head section-head--center">
      <span class="eyebrow eyebrow--carrot">{popular_eyebrow}</span>
      <h2>{popular_title}</h2>
      <p>{popular_lede}</p>
    </div>
    <div class="products">{featured}</div>
    <p class="center mt-lg"><a class="btn btn--outline" href="{L}assortiment.html">{popular_cta} {arrow}</a></p>
  </div>
</section>

<section class="section section--forest paw-bg">
  <div class="wrap split">
    <div class="reveal">
      <div class="frame frame--4x3">
        <img src="{b}{vet_img}" alt="{vet_alt}" loading="lazy" width="1200" height="900">
      </div>
    </div>
    <div>
      <span class="eyebrow">{stet} {vet_eyebrow}</span>
      <h2>{vet_title}</h2>
      <p>{vet_body}</p>
      <div class="grid-auto" style="margin:1.5rem 0">
        <div class="feature"><span class="feature__icon">{clock}</span><div><h3>{vet_hours_title}</h3><p>{vet_hours}</p></div></div>
        <div class="feature"><span class="feature__icon">{check}</span><div><h3>{vet_free_title}</h3><p>{vet_free_body}</p></div></div>
      </div>
      <a class="btn btn--light" href="{L}dierenarts.html">{vet_cta} {arrow}</a>
    </div>
  </div>
</section>

<section class="section">
  <div class="wrap">
    <div class="section-head section-head--center">
      <span class="eyebrow">{truck} {steps_eyebrow}</span>
      <h2>{steps_title}</h2>
      <p>{steps_lede}</p>
    </div>
    <div class="steps">
      <div class="step reveal"><div class="step__num"></div><h3>{s1t}</h3><p>{s1b}</p></div>
      <div class="step reveal"><div class="step__num"></div><h3>{s2t}</h3><p>{s2b}</p></div>
      <div class="step reveal"><div class="step__num"></div><h3>{s3t}</h3><p>{s3b}</p></div>
    </div>
    <p class="center mt-lg"><a class="btn btn--primary" href="{L}assortiment.html">{steps_cta} {arrow}</a></p>
  </div>
</section>

{shop_cat}
<section class="section section--tight">
  <div class="wrap">
    <div class="grid-auto">
      <div class="stat reveal"><strong>{since}</strong><span>{stat1}</span></div>
      <div class="stat reveal"><strong>{count}</strong><span>{stat2}</span></div>
      <div class="stat reveal"><strong>2&times;</strong><span>{stat3}</span></div>
      <div class="stat reveal"><strong>1</strong><span>{stat4}</span></div>
    </div>
  </div>
</section>
{cta}
""".format(
        b=base, paw=icon("paw"), arrow=icon("arrow"), whatsapp=icon("whatsapp"), L=lbase,
        check=icon("check"), heart=icon("heart"), stet=icon("stethoscope"), leaf=icon("leaf"),
        quote=icon("quote"), clock=icon("clock"), truck=icon("truck"), pin=icon("pin"),
        hero_eyebrow=t(lang, "hero_eyebrow", since=SITE["since"]), hero_title=t(lang, "hero_title"),
        hero_lede=t(lang, "hero_lede"), cta_shop=t(lang, "hero_cta_shop"),
        wa=wa_link(t(lang, "wa_pet_question")),
        cta_app=t(lang, "hero_cta_app", phone=e(SITE["whatsapp_display"])),
        trust1=t(lang, "hero_trust_1"), trust2=t(lang, "hero_trust_2"),
        trust3=t(lang, "hero_trust_3", days=e(days)),
        sticker_since=t(lang, "hero_sticker_since", since=SITE["since"]),
        sticker_vet=t(lang, "hero_sticker_vet"), slides=hero_slides(lang, base), dots=hero_dots(lang),
        card_title=t(lang, "hero_card_title", count=len(PRODUCTS)),
        card_sub=t(lang, "hero_card_sub"), strip=strip,
        pets_eyebrow=t(lang, "pets_eyebrow"), pets_title=t(lang, "pets_title"),
        pets_lede=t(lang, "pets_lede"), pets=pets, cats_eyebrow=t(lang, "cats_eyebrow"),
        cats_title=t(lang, "cats_title"), cats_lede=t(lang, "cats_lede"), cats=cats_html,
        cats_cta=t(lang, "cats_cta", count=len(PRODUCTS)), advice_img=e(IMG["advice"]),
        advice_alt=e(img_alt("advice_alt", lang)), advice_sticker=t(lang, "advice_sticker"),
        advice_eyebrow=t(lang, "advice_eyebrow"), advice_title=t(lang, "advice_title"),
        advice_quote=t(lang, "advice_quote"), advice_cite=t(lang, "advice_cite"),
        advice_body=t(lang, "advice_body"), advice_cta=t(lang, "advice_cta"),
        animals_eyebrow=t(lang, "animals_eyebrow"), animals_title=t(lang, "animals_title"),
        animals_p1=t(lang, "animals_p1"), animals_p2=t(lang, "animals_p2"),
        a_f1_t=t(lang, "animals_f1_title"), a_f1_b=t(lang, "animals_f1_body"),
        a_f2_t=t(lang, "animals_f2_title"), a_f2_b=t(lang, "animals_f2_body"),
        animals_alt=t(lang, "animals_alt"), popular_eyebrow=t(lang, "popular_eyebrow"),
        popular_title=t(lang, "popular_title"), popular_lede=t(lang, "popular_lede"),
        featured=featured_html, popular_cta=t(lang, "popular_cta"), vet_img=e(IMG["vet"]),
        vet_alt=e(img_alt("vet_alt", lang)), vet_eyebrow=t(lang, "vet_eyebrow"),
        vet_title=t(lang, "vet_title"), vet_body=t(lang, "vet_body"),
        vet_hours_title=t(lang, "vet_hours_title"), vet_hours=e(site_text(lang, "vet_hours")),
        vet_free_title=t(lang, "vet_free_title"), vet_free_body=t(lang, "vet_free_body"),
        vet_cta=t(lang, "vet_cta"), steps_eyebrow=t(lang, "steps_eyebrow"),
        steps_title=t(lang, "steps_title"), steps_lede=t(lang, "steps_lede"),
        s1t=t(lang, "step1_title"), s1b=t(lang, "step1_body"), s2t=t(lang, "step2_title"),
        s2b=t(lang, "step2_body"), s3t=t(lang, "step3_title"),
        s3b=t(lang, "step3_body", days=e(days), area=e(area)), steps_cta=t(lang, "steps_cta"),
        storefront_block="""<section class="section storefront">
  <div class="wrap">
    <div class="section-head section-head--center">
      <span class="eyebrow eyebrow--carrot">{pin} {visit_eyebrow}</span>
      <h2>{visit_title}</h2>
      <p>{visit_body}</p>
    </div>
  </div>
  <div class="storefront__media reveal">
    <img src="{b}{shop_wide}" alt="{visit_alt}" loading="lazy" width="1800" height="1013">
    <span class="sticker storefront__sticker">{paw} {sticker_since}</span>
  </div>
  <div class="wrap">
    <div class="storefront__card reveal">
      <div>
        <h3>{store} {visit_card_hours}</h3>
        <ul class="hours">{hours}</ul>
      </div>
      <div>
        <h3>{pin} {visit_card_address}</h3>
        <p class="lede" style="margin-bottom:.5rem">{street}<br>{zip} {city}</p>
        <p class="muted" style="font-size:var(--step--1)">{parking}</p>
        <div class="hero__actions" style="margin-top:1rem">
          <a class="btn btn--forest" href="{L}contact.html">{visit_cta} {arrow}</a>
          <a class="btn btn--outline" href="{maps}" target="_blank" rel="noopener">{maps_label}</a>
        </div>
      </div>
    </div>
  </div>
</section>""".format(
            b=base, L=lbase, shop_wide=e(IMG["shop_wide"]), visit_alt=t(lang, "visit_alt"),
            pin=icon("pin"), paw=icon("paw"), store=icon("store"), arrow=icon("arrow"),
            sticker_since=t(lang, "hero_sticker_since", since=SITE["since"]),
            visit_eyebrow=t(lang, "visit_eyebrow"), visit_title=t(lang, "visit_title"),
            visit_body=t(lang, "visit_body", since=SITE["since"]),
            visit_card_hours=t(lang, "contact_hours"), visit_card_address=t(lang, "contact_address"),
            street=e(SITE["address"]["street"]), zip=e(SITE["address"]["zip"]),
            city=e(SITE["address"]["city"]), parking=e(site_text(lang, "parking")),
            visit_cta=t(lang, "visit_cta"), maps=e(SITE["maps"]),
            maps_label=t(lang, "contact_maps"),
            hours="".join("<li><span>{}</span><span>{}</span></li>".format(e(d), e(v))
                          for d, v in hours_rows(lang))),
        shop_cat=shop_cat_section(lang, base), since=SITE["since"], count=len(PRODUCTS),
        stat1=t(lang, "stat_1"), stat2=t(lang, "stat_2"), stat3=t(lang, "stat_3"),
        stat4=t(lang, "stat_4"), cta=cta_band(lang, base, lbase))
    return write(out_path(lang, rel), layout(
        lang, rel, t(lang, "meta_home_title"), site_text(lang, "description"), body))


def page_catalog(lang):
    rel = "assortiment.html"
    base = lang_base(lang, rel)
    lbase = link_base(lang, rel)
    chips = ['<button class="chip" data-filter="all" aria-pressed="true">%s</button>'
             % t(lang, "shop_all")]
    for c in CATS:
        chips.append('<button class="chip" data-filter="{s}" aria-pressed="false">{n}</button>'.format(
            s=c["slug"], n=e(cat_name(c, lang))))
    grid = "".join(product_card(p, lang, base, lbase) for p in PRODUCTS)
    body = """
{crumbs}
<section class="section" style="padding-top:1.5rem">
  <div class="wrap">
    <div class="section-head">
      <span class="eyebrow">{paw} {count}</span>
      <h1 data-catalog-title>{title}</h1>
      <p>{lede}</p>
    </div>
    <div class="toolbar">
      <div class="chips" role="group" aria-label="{filter_label}">{chips}</div>
      <label class="search">{search}<span class="sr-only">{search_label}</span>
        <input type="search" placeholder="{search_ph}" data-catalog-search autocomplete="off">
      </label>
    </div>
    <p class="muted" data-count>{count}</p>
    <div class="products" data-catalog>{grid}</div>
    <div class="hide center" data-empty style="padding:3rem 0">
      <h3>{empty_title}</h3>
      <p class="lede">{empty_lede}</p>
      <a class="btn btn--wa" href="{wa}">{whatsapp} {empty_cta}</a>
    </div>
  </div>
</section>
{cta}
""".format(
        crumbs=crumbs(lang, base, lbase=lbase, trail=[(t(lang, "nav_shop"), None)]), paw=icon("paw"), L=lbase,
        count=plural(lang, len(PRODUCTS)), title=t(lang, "shop_title"), lede=t(lang, "shop_lede"),
        filter_label=t(lang, "shop_filter_label"), chips="".join(chips), search=icon("search"),
        search_label=t(lang, "shop_search_label"), search_ph=t(lang, "shop_search_placeholder"),
        grid=grid, empty_title=t(lang, "shop_empty_title"), empty_lede=t(lang, "shop_empty_lede"),
        wa=wa_link(t(lang, "wa_missing_product")), whatsapp=icon("whatsapp"),
        empty_cta=t(lang, "shop_empty_cta"), cta=cta_band(lang, base, lbase))
    return write(out_path(lang, rel), layout(
        lang, rel, t(lang, "meta_shop_title"), t(lang, "meta_shop_desc"), body))


def page_category(c, lang):
    rel = "categorie/%s.html" % c["slug"]
    base = lang_base(lang, rel)
    lbase = link_base(lang, rel)
    lbase = link_base(lang, rel)
    items = products_of(c["slug"])
    grid = "".join(product_card(p, lang, base, lbase) for p in items)
    others = "".join('<a class="chip" href="{s}.html">{n}</a>'.format(
        s=o["slug"], n=e(cat_name(o, lang))) for o in CATS if o["slug"] != c["slug"])
    body = """
{crumbs}
<section class="section" style="padding-top:1.5rem">
  <div class="wrap">
    <div class="section-head">
      <span class="eyebrow">{paw} {count}</span>
      <h1>{name}</h1>
      <p>{intro}</p>
    </div>
    <div class="products">{grid}</div>
  </div>
</section>
<section class="section section--sand">
  <div class="wrap">
    <div class="section-head"><h2>{others_title}</h2></div>
    <div class="chips">{others}</div>
  </div>
</section>
{cta}
""".format(
        crumbs=crumbs(lang, base, lbase=lbase, trail=[(t(lang, "nav_shop"), "assortiment.html"),
                                   (e(cat_name(c, lang)), None)]),
        paw=icon("paw"), count=plural(lang, len(items)), name=e(cat_name(c, lang)), L=lbase,
        intro=e(cat_intro(c, lang)), grid=grid, others_title=t(lang, "cat_others_title"),
        others=others, cta=cta_band(lang, base, lbase))
    return write(out_path(lang, rel), layout(
        lang, rel, "%s — Pet Needs Delft" % cat_name(c, lang), cat_intro(c, lang), body))


def page_product(p, lang):
    rel = "product/%s.html" % p["slug"]
    base = lang_base(lang, rel)
    lbase = link_base(lang, rel)
    lbase = link_base(lang, rel)
    c = CAT_BY_SLUG[p["category"]]
    related = [o for o in products_of(c["slug"]) if o["slug"] != p["slug"]][:4]
    related_html = "".join(product_card(o, lang, base, lbase) for o in related)
    media = ('<img src="{b}{img}" alt="{alt}" width="900" height="900">'.format(
        b=base, img=p["image"], alt=e(p["name"]))
        if p["image"] else '<span class="product__ph {tint}">{paw}</span>'.format(
            tint=c["tint"], paw=icon("paw")))
    price = money(p["price"]) if p["price"] else t(lang, "price_ask")
    desc = prod_desc(p, lang) or t(lang, "pdp_desc_fallback")
    order_text = t(lang, "wa_order_single", name=p["name"], sku=p["sku"],
                   price=(" — " + money(p["price"])) if p["price"] else "")
    offer = {}
    if p["price"]:
        offer = {"offers": {"@type": "Offer", "price": "%.2f" % p["price"], "priceCurrency": "EUR",
                            "availability": "https://schema.org/InStock",
                            "seller": {"@type": "Store", "name": "Pet Needs"}}}
    jsonld = json.dumps(dict({"@context": "https://schema.org", "@type": "Product",
                              "name": p["name"], "sku": p["sku"], "category": cat_name(c, lang),
                              "description": desc,
                              "brand": {"@type": "Brand", "name": "Pet Needs"}}, **offer),
                        ensure_ascii=False)
    related_block = ("""
<section class="section section--sand">
  <div class="wrap">
    <div class="section-head"><h2>%s</h2></div>
    <div class="products">%s</div>
  </div>
</section>""" % (t(lang, "pdp_related"), related_html)) if related else ""
    body = """
{crumbs}
<section class="section" style="padding-top:1.5rem">
  <div class="wrap pdp">
    <div class="pdp__media reveal">{media}</div>
    <div>
      <span class="eyebrow">{catname}</span>
      <h1>{name}</h1>
      <p class="pdp__price">{price}</p>
      <p class="lede">{desc}</p>
      <div class="pdp__actions">
        <div class="qty" data-qty>
          <button type="button" class="qty__btn" data-qty-minus aria-label="{qty_less}">{minus}</button>
          <input class="qty__input" type="number" inputmode="numeric" min="1" max="99" value="1" data-qty-input aria-label="{qty_label}">
          <button type="button" class="qty__btn" data-qty-plus aria-label="{qty_more}">{plus}</button>
        </div>
        <button class="btn btn--primary btn--lg" type="button" {data}>{bag} {add}</button>
      </div>
      <div class="pdp__actions" style="margin-top:-.4rem">
        <a class="btn btn--outline btn--sm" href="{wa}">{whatsapp} {direct}</a>
        <a class="btn btn--outline btn--sm" href="{L}contact.html">{store} {pickup}</a>
      </div>
      <ul class="pdp__list">
        <li>{check} {b1}</li>
        <li>{check} {b2}</li>
        <li>{check} {b3}</li>
      </ul>
      <p class="muted" style="margin-top:1.5rem;font-size:.85rem">{sku_note}</p>
    </div>
  </div>
</section>
{related_block}
{cta}
<script type="application/ld+json">{jsonld}</script>
""".format(
        crumbs=crumbs(lang, base, lbase=lbase, trail=[(t(lang, "nav_shop"), "assortiment.html"),
                                   (e(cat_name(c, lang)), "categorie/%s.html" % c["slug"]),
                                   (e(p["name"]), None)]),
        media=media, catname=e(cat_name(c, lang)), name=e(p["name"]), price=e(price), desc=e(desc), L=lbase,
        qty_less=t(lang, "pdp_qty_less"), minus=icon("minus"), qty_label=t(lang, "pdp_qty_label"),
        qty_more=t(lang, "pdp_qty_more"), plus=icon("plus"), data=cart_data(p), bag=icon("bag"),
        add=t(lang, "pdp_add"), wa=wa_link(order_text), whatsapp=icon("whatsapp"),
        direct=t(lang, "pdp_direct_wa"), b=base, store=icon("store"), pickup=t(lang, "pdp_pickup"),
        check=icon("check"),
        b1=t(lang, "pdp_bullet_1", days=e(site_text(lang, "delivery_days")),
             area=e(", ".join(SITE["delivery_area"]))),
        b2=t(lang, "pdp_bullet_2"), b3=t(lang, "pdp_bullet_3"),
        sku_note=t(lang, "pdp_sku", sku=e(p["sku"])), related_block=related_block,
        cta=cta_band(lang, base, lbase), jsonld=jsonld)
    return write(out_path(lang, rel), layout(
        lang, rel, "%s — Pet Needs Delft" % p["name"],
        (prod_desc(p, lang) or t(lang, "meta_product_desc", name=p["name"]))[:155], body))


def page_about(lang):
    rel = "over-ons.html"
    base = lang_base(lang, rel)
    lbase = link_base(lang, rel)
    body = """
{crumbs}
<section class="section" style="padding-top:1.5rem">
  <div class="wrap split">
    <div>
      <span class="eyebrow">{paw} {eyebrow}</span>
      <h1>{title}</h1>
      <p class="lede">{lede}</p>
      <p>{p1}</p>
      <p>{p2}</p>
    </div>
    <div class="reveal" style="position:relative">
      <div class="frame frame--4x3">
        <img src="{b}{shop_img}" alt="{alt}" width="1400" height="1050">
      </div>
      <span class="sticker" style="position:absolute;left:-.5rem;top:-.7rem;z-index:2">{heart} {sticker}</span>
    </div>
  </div>
</section>

<section class="section section--sand">
  <div class="wrap">
    <div class="section-head"><h2>{values}</h2></div>
    <div class="grid-auto">
      <div class="info reveal"><h3>{heart} {v1t}</h3><p>{v1b}</p></div>
      <div class="info reveal"><h3>{leaf} {v2t}</h3><p>{v2b}</p></div>
      <div class="info reveal"><h3>{truck} {v3t}</h3><p>{v3b}</p></div>
      <div class="info reveal"><h3>{paw} {v4t}</h3><p>{v4b}</p></div>
    </div>
  </div>
</section>
{shop_cat}
{cta}
""".format(
        crumbs=crumbs(lang, base, lbase=lbase, trail=[(t(lang, "nav_about"), None)]), paw=icon("paw"), L=lbase,
        eyebrow=t(lang, "about_eyebrow", since=SITE["since"]), title=t(lang, "about_title"),
        lede=t(lang, "about_lede", since=SITE["since"]), p1=t(lang, "about_p1"),
        p2=t(lang, "about_p2", licg=e(SITE["licg"])), b=base, shop_img=e(IMG["shop"]),
        alt=t(lang, "visit_alt"), heart=icon("heart"),
        sticker=t(lang, "hero_sticker_since", since=SITE["since"]), values=t(lang, "about_values"),
        v1t=t(lang, "about_v1_title"), v1b=t(lang, "about_v1_body"), leaf=icon("leaf"),
        v2t=t(lang, "about_v2_title"), v2b=t(lang, "about_v2_body"), truck=icon("truck"),
        v3t=t(lang, "about_v3_title"),
        v3b=t(lang, "about_v3_body", days=e(site_text(lang, "delivery_days")),
              area=e(delivery_area(lang))),
        v4t=t(lang, "about_v4_title"), v4b=t(lang, "about_v4_body"),
        shop_cat=shop_cat_section(lang, base), cta=cta_band(lang, base, lbase))
    return write(out_path(lang, rel), layout(
        lang, rel, t(lang, "meta_about_title"), t(lang, "meta_about_desc"), body))


def page_vet(lang):
    rel = "dierenarts.html"
    base = lang_base(lang, rel)
    lbase = link_base(lang, rel)
    body = """
{crumbs}
<section class="section" style="padding-top:1.5rem">
  <div class="wrap split">
    <div>
      <span class="eyebrow">{stet} {eyebrow}</span>
      <h1>{title}</h1>
      <p class="lede">{lede}</p>
      <p>{p1}</p>
      <p>{p2}</p>
      <div class="hero__actions">
        <a class="btn btn--primary" href="{wa}">{whatsapp} {cta_label}</a>
      </div>
      <div class="grid-auto" style="margin-top:2rem">
        <div class="feature"><span class="feature__icon">{clock}</span><div><h3>{hours_title}</h3><p>{hours}</p></div></div>
        <div class="feature"><span class="feature__icon">{pin}</span><div><h3>{where}</h3><p>{street}, {zip} {city}</p></div></div>
        <div class="feature"><span class="feature__icon">{paw}</span><div><h3>{what}</h3><p>{what_body}</p></div></div>
      </div>
    </div>
    <div class="reveal" style="position:relative">
      <div class="frame frame--squircle frame--1x1">
        <img src="{b}{vet_img}" alt="{vet_alt}" width="1200" height="900">
      </div>
      <span class="sticker sticker--carrot" style="position:absolute;right:0;top:-.5rem;z-index:2">{stet} {sticker}</span>
    </div>
  </div>
</section>
{cta}
""".format(
        crumbs=crumbs(lang, base, lbase=lbase, trail=[(t(lang, "nav_vet"), None)]), stet=icon("stethoscope"), L=lbase,
        eyebrow=t(lang, "vet_page_eyebrow"), title=t(lang, "vet_page_title"),
        lede=t(lang, "vet_page_lede"), p1=t(lang, "vet_page_p1"), p2=t(lang, "vet_page_p2"),
        wa=wa_link(t(lang, "wa_vet_question")), whatsapp=icon("whatsapp"),
        cta_label=t(lang, "vet_page_cta"), clock=icon("clock"),
        hours_title=t(lang, "vet_hours_title"), hours=e(site_text(lang, "vet_hours")),
        pin=icon("pin"), where=t(lang, "vet_where"), street=e(SITE["address"]["street"]),
        zip=e(SITE["address"]["zip"]), city=e(SITE["address"]["city"]), paw=icon("paw"),
        what=t(lang, "vet_what"), what_body=t(lang, "vet_what_body"), b=base,
        vet_img=e(IMG["vet"]), vet_alt=e(img_alt("vet_alt", lang)), sticker=t(lang, "vet_sticker"),
        cta=cta_band(lang, base, lbase))
    return write(out_path(lang, rel), layout(
        lang, rel, t(lang, "meta_vet_title"),
        t(lang, "meta_vet_desc", hours=site_text(lang, "vet_hours")), body))


def page_contact(lang):
    rel = "contact.html"
    base = lang_base(lang, rel)
    lbase = link_base(lang, rel)
    hours = "".join("<li><span>{}</span><span>{}</span></li>".format(e(d), e(v))
                    for d, v in hours_rows(lang))
    body = """
{crumbs}
<section class="section" style="padding-top:1.5rem">
  <div class="wrap">
    <div class="section-head">
      <span class="eyebrow eyebrow--carrot">{pin} Choorstraat 49, Delft</span>
      <h1>{title}</h1>
      <p>{lede}</p>
    </div>
    <div class="grid-auto">
      <div class="info reveal">
        <h3>{clock} {hours_title}</h3>
        <ul class="hours">{hours}</ul>
      </div>
      <div class="info reveal">
        <h3>{pin} {address_title}</h3>
        <p>{street}<br>{zip} {city}</p>
        <p>{parking}</p>
        <a class="btn btn--outline btn--sm" style="margin-top:1rem" href="{maps}" target="_blank" rel="noopener">{maps_label}</a>
      </div>
      <div class="info reveal">
        <h3>{whatsapp} {order_title}</h3>
        <p>{order_body}</p>
        <a class="btn btn--wa btn--sm" style="margin-top:1rem" href="{wa}">{app}</a>
      </div>
      <div class="info reveal">
        <h3>{truck} {delivery_title}</h3>
        <p>{delivery_body}</p>
      </div>
    </div>
  </div>
</section>
<section class="section section--sand">
  <div class="wrap split">
    <div class="reveal">
      <div class="frame frame--4x3">
        <img src="{b}{shop_img}" alt="{alt}" loading="lazy" width="1400" height="1050">
      </div>
    </div>
    <div>
      <h2>{find_title}</h2>
      <p>{find_p1}</p>
      <p>{find_p2}</p>
    </div>
  </div>
</section>
""".format(
        crumbs=crumbs(lang, base, lbase=lbase, trail=[(t(lang, "nav_contact"), None)]), pin=icon("pin"), L=lbase,
        title=t(lang, "contact_title"), lede=t(lang, "contact_lede"), clock=icon("clock"),
        hours_title=t(lang, "contact_hours"), hours=hours,
        address_title=t(lang, "contact_address"), street=e(SITE["address"]["street"]),
        zip=e(SITE["address"]["zip"]), city=e(SITE["address"]["city"]),
        parking=e(site_text(lang, "parking")), maps=e(SITE["maps"]),
        maps_label=t(lang, "contact_maps"), whatsapp=icon("whatsapp"),
        order_title=t(lang, "contact_order_title"),
        order_body=t(lang, "contact_order_body", phone=e(SITE["whatsapp_display"])),
        wa=wa_link(t(lang, "wa_question")), app=t(lang, "btn_app_us"), truck=icon("truck"),
        delivery_title=t(lang, "contact_delivery"),
        delivery_body=t(lang, "contact_delivery_body", days=e(site_text(lang, "delivery_days")),
                        area=e(delivery_area(lang))),
        b=base, shop_img=e(IMG["shop"]), alt=t(lang, "visit_alt"),
        find_title=t(lang, "contact_find_title"),
        find_p1=t(lang, "contact_find_p1", parking=e(site_text(lang, "parking"))),
        find_p2=t(lang, "contact_find_p2"))
    return write(out_path(lang, rel), layout(
        lang, rel, t(lang, "meta_contact_title"),
        t(lang, "meta_contact_desc", phone=SITE["whatsapp_display"]), body))


def page_privacy(lang):
    rel = "privacy.html"
    base = lang_base(lang, rel)
    lbase = link_base(lang, rel)
    body = """
{crumbs}
<section class="section" style="padding-top:1.5rem">
  <div class="wrap" style="max-width:44rem">
    <h1>{title}</h1>
    <p class="lede">{lede}</p>
    <p>{p1}</p>
    <p>{p2}</p>
    <p class="muted">{p3}</p>
  </div>
</section>
""".format(
        crumbs=crumbs(lang, base, lbase=lbase, trail=[(t(lang, "privacy_title"), None)]),
        title=t(lang, "privacy_title"), lede=t(lang, "privacy_lede"), p1=t(lang, "privacy_p1"),
        p2=t(lang, "privacy_p2", phone=e(SITE["whatsapp_display"])),
        p3=t(lang, "privacy_p3", street=e(SITE["address"]["street"]),
             zip=e(SITE["address"]["zip"]), city=e(SITE["address"]["city"])))
    return write(out_path(lang, rel), layout(
        lang, rel, t(lang, "meta_privacy_title"), t(lang, "meta_privacy_desc"), body))


def page_checkout(lang):
    rel = "bestellen.html"
    base = lang_base(lang, rel)
    lbase = link_base(lang, rel)
    days = site_text(lang, "delivery_days")
    area = delivery_area(lang)
    body = """
{crumbs}
<section class="section" style="padding-top:1.5rem">
  <div class="wrap">
    <div class="section-head">
      <span class="eyebrow eyebrow--carrot">{bag} {eyebrow}</span>
      <h1>{title}</h1>
      <p>{lede}</p>
    </div>

    <div class="checkout">
      <div>
        <h2 class="checkout__title">{products}</h2>
        <div data-checkout-items></div>

        <div class="checkout__empty" data-checkout-empty hidden>
          <span class="checkout__empty-icon">{bag}</span>
          <h3>{empty_title}</h3>
          <p class="lede">{empty_lede}</p>
          <a class="btn btn--primary" href="{L}assortiment.html">{empty_cta} {arrow}</a>
        </div>

        <form class="checkout__form" data-checkout-form novalidate>
          <h2 class="checkout__title">{details}</h2>
          <div class="field-grid">
            <label class="field">
              <span class="field__label">{f_name} <em>*</em></span>
              <input type="text" name="naam" autocomplete="name" required>
              <span class="field__error" data-error></span>
            </label>
            <label class="field">
              <span class="field__label">{f_phone} <em>*</em></span>
              <input type="tel" name="telefoon" autocomplete="tel" required placeholder="06 12 34 56 78">
              <span class="field__error" data-error></span>
            </label>
            <label class="field field--wide">
              <span class="field__label">{f_email}</span>
              <input type="email" name="email" autocomplete="email" placeholder="{f_email_hint}">
              <span class="field__error" data-error></span>
            </label>
          </div>

          <h2 class="checkout__title">{delivery_title}</h2>
          <div class="choice-grid">
            <label class="choice">
              <input type="radio" name="levering" value="ophalen" checked>
              <span class="choice__body">
                <span class="choice__icon">{store}</span>
                <strong>{pickup_title}</strong>
                <span>{pickup_body}</span>
              </span>
            </label>
            <label class="choice">
              <input type="radio" name="levering" value="bezorgen">
              <span class="choice__body">
                <span class="choice__icon">{truck}</span>
                <strong>{delivery_choice_title}</strong>
                <span>{delivery_choice_body}</span>
              </span>
            </label>
          </div>

          <div class="delivery-fields" data-delivery-fields hidden>
            <div class="field-grid">
              <label class="field field--wide">
                <span class="field__label">{f_street} <em>*</em></span>
                <input type="text" name="adres" autocomplete="street-address">
                <span class="field__error" data-error></span>
              </label>
              <label class="field">
                <span class="field__label">{f_zip} <em>*</em></span>
                <input type="text" name="postcode" autocomplete="postal-code" placeholder="2611 JE">
                <span class="field__error" data-error></span>
              </label>
              <label class="field">
                <span class="field__label">{f_city} <em>*</em></span>
                <input type="text" name="plaats" autocomplete="address-level2" placeholder="Delft">
                <span class="field__error" data-error></span>
              </label>
              <label class="field field--wide">
                <span class="field__label">{f_day}</span>
                <select name="dag">
                  <option value="{day_any}">{day_any}</option>
                  <option value="{day_tue}">{day_tue}</option>
                  <option value="{day_fri}">{day_fri}</option>
                </select>
              </label>
            </div>
            <p class="muted" style="font-size:var(--step--1);margin:0">{delivery_note}</p>
          </div>

          <label class="field field--wide" style="margin-top:1.25rem">
            <span class="field__label">{f_notes}</span>
            <textarea name="opmerking" rows="3" placeholder="{f_notes_ph}"></textarea>
          </label>

          <div class="checkout__submit">
            <button type="submit" class="btn btn--wa btn--lg">{whatsapp} {submit}</button>
            <button type="button" class="btn btn--outline" data-copy-order>{copy}</button>
          </div>
          <p class="muted" style="font-size:var(--step--1)">{note}</p>
        </form>

        <div class="checkout__sent" data-checkout-sent hidden>
          <span class="checkout__empty-icon">{check}</span>
          <h3>{sent_title}</h3>
          <p class="lede">{sent_body}</p>
          <div class="checkout__submit">
            <button type="button" class="btn btn--primary" data-clear-after-send>{sent_clear}</button>
            <button type="button" class="btn btn--outline" data-back-to-form>{sent_back}</button>
          </div>
        </div>
      </div>

      <aside class="summary" data-summary hidden>
        <h2 class="summary__title">{summary_title}</h2>
        <ul class="summary__lines" data-summary-lines></ul>
        <div class="summary__total"><span>{subtotal}</span><strong data-summary-total>€ 0,00</strong></div>
        <p class="summary__note" data-summary-note hidden></p>
        <ul class="pdp__list" style="margin-top:1rem">
          <li>{check} {s1}</li>
          <li>{check} {s2}</li>
          <li>{check} {s3}</li>
        </ul>
      </aside>
    </div>
  </div>
</section>
""".format(
        crumbs=crumbs(lang, base, lbase=lbase, trail=[(t(lang, "btn_order"), None)]), bag=icon("bag"), L=lbase,
        eyebrow=t(lang, "checkout_eyebrow"), title=t(lang, "checkout_title"),
        lede=t(lang, "checkout_lede"), products=t(lang, "checkout_products"),
        empty_title=t(lang, "checkout_empty_title"), empty_lede=t(lang, "checkout_empty_lede"),
        b=base, empty_cta=t(lang, "checkout_empty_cta"), arrow=icon("arrow"),
        details=t(lang, "checkout_details"), f_name=t(lang, "field_name"),
        f_phone=t(lang, "field_phone"), f_email=t(lang, "field_email"),
        f_email_hint=t(lang, "field_email_hint"), delivery_title=t(lang, "checkout_delivery"),
        store=icon("store"), pickup_title=t(lang, "choice_pickup_title"),
        pickup_body=t(lang, "choice_pickup_body"), truck=icon("truck"),
        delivery_choice_title=t(lang, "choice_delivery_title"),
        delivery_choice_body=t(lang, "choice_delivery_body", days=e(days), area=e(area)),
        f_street=t(lang, "field_street"), f_zip=t(lang, "field_zip"), f_city=t(lang, "field_city"),
        f_day=t(lang, "field_day"), day_any=t(lang, "day_any"), day_tue=t(lang, "day_tue"),
        day_fri=t(lang, "day_fri"), delivery_note=t(lang, "delivery_note", area=e(area)),
        f_notes=t(lang, "field_notes"), f_notes_ph=t(lang, "field_notes_ph"),
        whatsapp=icon("whatsapp"), submit=t(lang, "checkout_submit"), copy=t(lang, "checkout_copy"),
        note=t(lang, "checkout_note", phone=e(SITE["whatsapp_display"])), check=icon("check"),
        sent_title=t(lang, "checkout_sent_title"), sent_body=t(lang, "checkout_sent_body"),
        sent_clear=t(lang, "checkout_sent_clear"), sent_back=t(lang, "checkout_sent_back"),
        summary_title=t(lang, "summary_title"), subtotal=t(lang, "cart_subtotal"),
        s1=t(lang, "summary_1"), s2=t(lang, "summary_2", days=e(days)), s3=t(lang, "summary_3"))
    return write(out_path(lang, rel), layout(
        lang, rel, t(lang, "meta_checkout_title"), t(lang, "meta_checkout_desc", days=days), body))


# --------------------------------------------------------------------------
# stijlgids (Nederlands — interne documentatie)
# --------------------------------------------------------------------------
def swatch(var, name, hexv):
    return ('<div><div style="background:var(--{v});height:74px;border-radius:var(--r-md);'
            'border:1px solid var(--line)"></div>'
            '<p style="margin:.5rem 0 0;font-size:.8rem"><strong>{n}</strong><br>'
            '<span class="muted">--{v} · {h}</span></p></div>').format(v=var, n=name, h=hexv)


def page_styleguide():
    lang, rel = "nl", "styleguide.html"
    base = lang_base(lang, rel)
    lbase = link_base(lang, rel)
    colors = "".join([
        swatch("forest", "Forest", "#14523a"), swatch("forest-deep", "Forest deep", "#0e3b29"),
        swatch("forest-soft", "Forest soft", "#dfeee4"), swatch("carrot", "Carrot", "#ff6f2c"),
        swatch("carrot-soft", "Carrot soft", "#ffe7d8"), swatch("sun", "Sun", "#ffcf4d"),
        swatch("cream", "Cream", "#fdf8f0"), swatch("sand", "Sand", "#f7eddf"),
        swatch("ink", "Ink", "#16211c"), swatch("ink-soft", "Ink soft", "#4c5a53"),
        swatch("tint-mint", "Tint mint", "#dff0e4"), swatch("tint-sky", "Tint sky", "#dcecf8"),
        swatch("tint-blush", "Tint blush", "#ffe2d6"), swatch("tint-lilac", "Tint lilac", "#e9e3f9"),
        swatch("tint-butter", "Tint butter", "#fdf0c4"), swatch("tint-sage", "Tint sage", "#e4ecdc"),
    ])
    icon_names = ["logo", "paw", "check", "truck", "clock", "heart", "pin", "phone", "whatsapp",
                  "search", "menu", "arrow", "stethoscope", "leaf", "star", "quote", "bag",
                  "close", "plus", "minus", "trash", "store"]
    icons_html = "".join(
        '<div class="center" style="background:#fff;border:1px solid var(--line);border-radius:var(--r-md);padding:1rem">'
        '<span style="display:grid;place-items:center;color:var(--forest)">{ic}</span>'
        '<p class="muted" style="margin:.5rem 0 0;font-size:.75rem">{n}</p></div>'.format(
            ic=icon(name).replace("<svg ", '<svg style="width:26px;height:26px" '), n=name)
        for name in icon_names)
    demo = [p for p in PRODUCTS if p["image"] and p["price"]][:2]
    demo_cat = CATS[0]
    body = """
{crumbs}
<section class="section" style="padding-top:1.5rem">
  <div class="wrap">
    <div class="section-head">
      <span class="eyebrow">{paw} Design system</span>
      <h1>Stijlgids</h1>
      <p>Alle bouwstenen van de site op één pagina. Gebruik deze tokens en componenten, dan blijft het geheel consistent. Bron: <code>assets/css/site.css</code>, <code>scripts/build.py</code> en <code>scripts/i18n.py</code>.</p>
    </div>

    <h2>1. Kleur</h2>
    <div class="grid-auto" style="grid-template-columns:repeat(auto-fit,minmax(150px,1fr))">{colors}</div>

    <h2 class="mt-lg">2. Typografie</h2>
    <div class="info">
      <p class="muted" style="margin-bottom:1rem">Display: <strong>Outfit</strong> · Body: <strong>Plus Jakarta Sans</strong></p>
      <h1 style="margin-bottom:.2em">Heading 1 — step-4</h1>
      <h2 style="margin-bottom:.2em">Heading 2 — step-3</h2>
      <h3 style="margin-bottom:.2em">Heading 3 — step-1</h3>
      <p class="lede">Lede — step-1, voor introducties onder een kop.</p>
      <p>Body — step-0, de basisregel voor lopende tekst.</p>
      <p class="muted" style="font-size:var(--step--1)">Small — step--1, voor meta-informatie.</p>
    </div>

    <h2 class="mt-lg">3. Iconen</h2>
    <div class="grid-auto" style="grid-template-columns:repeat(auto-fit,minmax(96px,1fr))">{icons}</div>

    <h2 class="mt-lg">4. Knoppen</h2>
    <div class="info" style="display:flex;flex-wrap:wrap;gap:.75rem;align-items:center">
      <a class="btn btn--primary" href="#main">Primary</a>
      <a class="btn btn--forest" href="#main">Forest</a>
      <a class="btn btn--outline" href="#main">Outline</a>
      <a class="btn btn--light" href="#main">Light</a>
      <a class="btn btn--wa" href="#main">{whatsapp} WhatsApp</a>
      <a class="btn btn--primary btn--sm" href="#main">Small</a>
      <a class="btn btn--primary btn--lg" href="#main">Large</a>
    </div>

    <h2 class="mt-lg">5. Labels &amp; stickers</h2>
    <div class="info" style="display:flex;flex-wrap:wrap;gap:1rem 1.5rem;align-items:center">
      <span class="eyebrow" style="margin:0">{paw} Eyebrow</span>
      <span class="eyebrow eyebrow--carrot" style="margin:0">Eyebrow carrot</span>
      <span class="eyebrow eyebrow--sun" style="margin:0">Eyebrow sun</span>
      <span class="sticker">{heart} Sticker</span>
      <span class="sticker sticker--carrot">{stet} Sticker carrot</span>
      <span class="sticker sticker--white">{leaf} Sticker wit</span>
    </div>

    <h2 class="mt-lg">6. Chips &amp; zoeken</h2>
    <div class="info">
      <div class="toolbar" style="margin:0">
        <div class="chips">
          <button class="chip is-active">Alles</button>
          <button class="chip">Hond</button>
          <button class="chip">Kat</button>
          <button class="chip">Knaagdier</button>
        </div>
        <label class="search">{search}<input type="search" placeholder="Zoek een product…"></label>
      </div>
    </div>

    <h2 class="mt-lg">7. Kaarten</h2>
    <div class="products" style="margin-bottom:var(--gap)">
      {demo1}{demo2}
      <article class="card">
        <div class="card__media {cat_tint}"><img src="{cat_img}" alt="" loading="lazy"></div>
        <div class="card__body"><h3 class="card__title">Categoriekaart</h3><p class="card__meta">12 producten</p></div>
      </article>
      <div class="pet">
        <span class="pet__ring {pet_tint}"><img src="{pet_img}" alt="" loading="lazy"></span>
        <span class="pet__label">Dierkaart</span><span class="pet__count">24 producten</span>
      </div>
    </div>
    <div class="grid-auto">
      <div class="info"><h3>{clock} Info-kaart</h3><p>Voor openingstijden, adres en losse blokjes uitleg.</p></div>
      <div class="step"><div class="step__num"></div><h3>Stap-kaart</h3><p>Genummerde stappen, telt automatisch door.</p></div>
      <div class="stat"><strong>1992</strong><span>Stat-kaart</span></div>
      <div class="info"><div class="feature"><span class="feature__icon">{heart}</span><div><h3>Feature-rij</h3><p>Icoon plus korte uitleg.</p></div></div></div>
    </div>

    <h2 class="mt-lg">8. Citaat</h2>
    <div class="quote">
      <span class="quote__mark">{quote}</span>
      <p>Bij het advies dat u krijgt staat uw huisdier centraal.</p>
      <cite>— Pet Needs, Choorstraat 49</cite>
    </div>

    <h2 class="mt-lg">9. Fotolijsten</h2>
    <div class="grid-auto">
      <div><div class="frame frame--4x3"><img src="{cat_img}" alt="" loading="lazy"></div><p class="muted" style="margin-top:.5rem;font-size:.8rem">frame--4x3</p></div>
      <div><div class="frame frame--circle"><img src="{pet_img}" alt="" loading="lazy"></div><p class="muted" style="margin-top:.5rem;font-size:.8rem">frame--circle</p></div>
      <div><div class="frame frame--squircle frame--1x1"><img src="{pet_img2}" alt="" loading="lazy"></div><p class="muted" style="margin-top:.5rem;font-size:.8rem">frame--squircle</p></div>
    </div>

    <h2 class="mt-lg">10. Bestellen</h2>
    <div class="grid-auto">
      <div class="info">
        <h3>{bag} Winkelwagenregel</h3>
        <ul class="cart-lines" style="margin-top:.75rem">
          <li class="cart-line">
            <span class="cart-line__media"><img src="{cart_img}" alt=""></span>
            <div class="cart-line__body">
              <span class="cart-line__name">Productnaam</span>
              <div class="cart-line__row">
                <div class="qty qty--sm">
                  <button type="button" class="qty__btn">&minus;</button>
                  <span class="qty__value">2</span>
                  <button type="button" class="qty__btn">+</button>
                </div>
                <span class="cart-line__price">€ 7,98</span>
              </div>
            </div>
            <button type="button" class="cart-line__remove" aria-label="Verwijderen">&times;</button>
          </li>
        </ul>
      </div>
      <div class="info">
        <h3>{plus} Aantalkiezer &amp; toevoegen</h3>
        <div style="display:flex;flex-wrap:wrap;gap:.75rem;align-items:center;margin-top:.75rem">
          <div class="qty">
            <button type="button" class="qty__btn">{minus}</button>
            <input class="qty__input" type="number" value="1" aria-label="Aantal">
            <button type="button" class="qty__btn">{plus}</button>
          </div>
          <button type="button" class="product__add">{bag}<span>Toevoegen</span></button>
        </div>
      </div>
      <div class="info">
        <h3>{store} Keuzekaart</h3>
        <label class="choice" style="margin-top:.75rem">
          <input type="radio" name="sg-choice" checked>
          <span class="choice__body">
            <span class="choice__icon">{store}</span>
            <strong>Ophalen in de winkel</strong>
            <span>Geselecteerde staat van .choice</span>
          </span>
        </label>
      </div>
      <div class="info">
        <h3>{check} Formulierveld</h3>
        <label class="field" style="margin-top:.75rem">
          <span class="field__label">Telefoon <em>*</em></span>
          <input type="tel" placeholder="06 12 34 56 78">
          <span class="field__error">Foutmelding verschijnt hier</span>
        </label>
      </div>
    </div>

    <h2 class="mt-lg">11. Secties</h2>
    <div class="stack">
      <div class="section--sand" style="padding:1.5rem;border-radius:var(--r-lg)"><strong>.section--sand</strong> — zandkleurige band voor afwisseling.</div>
      <div class="section--forest paw-bg" style="padding:1.5rem;border-radius:var(--r-lg)"><strong>.section--forest + .paw-bg</strong> — groene band met pootjespatroon.</div>
      <div class="strip" style="border-radius:var(--r-lg)"><div class="strip__track">{strip}</div></div>
    </div>

    <h2 class="mt-lg">12. Taal</h2>
    <div class="info">
      <p>De site wordt in twee talen gebouwd: Nederlands in de root, Engels onder <code>/en/</code>. Alle interfaceteksten staan in <code>scripts/i18n.py</code>; teksten die bij de data horen (categorieën, productomschrijvingen) hebben een <code>_en</code>-variant in <code>data/site.json</code>. De schakelaar rechtsboven wijst altijd naar dezelfde pagina in de andere taal.</p>
      <div style="margin-top:1rem">{lang_demo}</div>
    </div>
  </div>
</section>
""".format(
        crumbs=crumbs(lang, base, lbase=lbase, trail=[("Stijlgids", None)]), paw=icon("paw"), colors=colors, L=lbase,
        icons=icons_html, whatsapp=icon("whatsapp"), heart=icon("heart"), stet=icon("stethoscope"),
        leaf=icon("leaf"), search=icon("search"), clock=icon("clock"), quote=icon("quote"),
        demo1=product_card(demo[0], lang), demo2=product_card(demo[1], lang),
        cat_tint=demo_cat["tint"], cat_img=e(demo_cat["image"]),
        pet_tint=PETS[0].get("tint", "tint-mint"), pet_img=e(PETS[0]["image"]),
        pet_img2=e(PETS[1]["image"]), bag=icon("bag"), plus=icon("plus"), minus=icon("minus"),
        store=icon("store"), check=icon("check"), cart_img=e(demo[0]["image"]),
        strip="".join("<span>{p} Design system</span>".format(p=icon("paw")) for _ in range(8)),
        lang_demo=lang_switch(lang, rel, base, "index.html"))
    return write(out_path(lang, rel), layout(
        lang, rel, "Stijlgids — Pet Needs",
        "Het design system van de Pet Needs website: kleuren, typografie, iconen en componenten.",
        body, other_rel="index.html"))


# --------------------------------------------------------------------------
def page_sitemap():
    rels = ["index.html", "assortiment.html", "bestellen.html", "over-ons.html",
            "dierenarts.html", "contact.html", "privacy.html"]
    rels += ["categorie/%s.html" % c["slug"] for c in CATS]
    rels += ["product/%s.html" % p["slug"] for p in PRODUCTS]
    lines = []
    for rel in rels:
        alts = "".join('<xhtml:link rel="alternate" hreflang="%s" href="%s"/>' % (
            HTML_LANG[code], BASE_URL + "/" + ("" if code == "nl" else "en/") + rel)
            for code in LANGS)
        for lang in LANGS:
            url = BASE_URL + "/" + ("" if lang == "nl" else "en/") + rel
            lines.append("  <url><loc>%s</loc>%s</url>" % (url, alts))
    return write("sitemap.xml",
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
                 'xmlns:xhtml="http://www.w3.org/1999/xhtml">\n%s\n</urlset>\n' % "\n".join(lines))


def page_robots():
    return write("robots.txt", "User-agent: *\nAllow: /\nSitemap: %s/sitemap.xml\n" % BASE_URL)


def main():
    for folder in ("categorie", "product", "en"):
        target = os.path.join(ROOT, folder)
        if os.path.isdir(target):
            shutil.rmtree(target)

    written = []
    for lang in LANGS:
        written += [page_home(lang), page_catalog(lang), page_checkout(lang), page_about(lang),
                    page_vet(lang), page_contact(lang), page_privacy(lang)]
        written += [page_category(c, lang) for c in CATS]
        written += [page_product(p, lang) for p in PRODUCTS]
    written += [page_styleguide(), page_sitemap(), page_robots()]

    print("Gegenereerd: %d bestanden — %s (%d producten, %d categorieën)" % (
        len(written), " + ".join(LANG_LABEL[l] for l in LANGS), len(PRODUCTS), len(CATS)))
    for key, note in (("cat", "winkelkat-blok"), ("cat2", "tweede winkelkatfoto")):
        if not has_img(IMG.get(key)):
            print("  · overgeslagen: %s — zet de foto op %s en build opnieuw" % (note, IMG.get(key)))


if __name__ == "__main__":
    main()
