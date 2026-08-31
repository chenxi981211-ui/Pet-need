# Pet Needs — nieuwe website

Statische website voor dierenspeciaalzaak **Pet Needs**, Choorstraat 49, Delft.
De inhoud komt van de bestaande site (petneeds.nl, gebouwd met ShopFactory) en is
opnieuw vormgegeven: fris, jong en mobiel-eerst, zonder frameworks of build-tools.

## Pagina's

| Pagina | Bestand |
| --- | --- |
| Home | `index.html` |
| Assortiment (zoeken + filteren) | `assortiment.html` |
| Bestellen (winkelwagen + formulier) | `bestellen.html` |
| Categorie (15×) | `categorie/<slug>.html` |
| Product (116×) | `product/<slug>.html` |
| Over ons | `over-ons.html` |
| Dierenarts | `dierenarts.html` |
| Bezoek & contact | `contact.html` |
| Privacy | `privacy.html` |
| **Stijlgids (design system)** | `styleguide.html` |

Alle HTML wordt **gegenereerd** uit `data/site.json`. Pas dus nooit de HTML in de
root aan — die wordt bij de volgende build overschreven.

## Design system

Alles staat in één bestand: `assets/css/site.css`, opgedeeld in zes lagen —
tokens, base, layout, graphics, componenten, utilities. De stijlgids op
`styleguide.html` toont elk onderdeel live; gebruik die als referentie voordat je
nieuwe HTML schrijft.

**Tokens (CSS-variabelen)**

- Kleur: `--forest #14523a` (merk), `--carrot #ff6f2c` (actie), `--sun #ffcf4d`
  (accent), `--cream`/`--sand` (achtergronden), `--ink`-serie (tekst) en zes
  pasteltinten (`--tint-mint`, `-sky`, `-blush`, `-lilac`, `-butter`, `-sage`)
  voor kaarten en dier-cirkels.
- Typografie: **Outfit** voor koppen, **Plus Jakarta Sans** voor lopende tekst.
  Groottes lopen via een schaal `--step--1` t/m `--step-4` (alles `clamp()`, dus
  vloeiend responsive).
- Verder: `--space-*`, `--r-*` (radius), `--shadow-*`, `--ease`/`--fast`/`--base`/`--slow`.

**Componenten**: `.btn` (primary / forest / outline / light / wa, + `--sm`/`--lg`),
`.eyebrow`, `.sticker`, `.badge`, `.card`, `.product`, `.pet`, `.stat`, `.step`,
`.info`, `.quote`, `.feature`, `.chip`, `.search`, `.crumbs`, `.hero`, `.strip`,
`.cta`, `.pdp`, `.hours`, header en footer.

**Grafische elementen**: `.paw-bg` (pootjespatroon over groene vlakken),
`.frame--squircle` / `--circle` / `--4x3` (fotolijsten), `.sticker` (schuine label),
`.strip` (gele marquee).

## Online bestellen

De site heeft een volwaardige winkelwagen zonder server:

- **Toevoegen** kan vanaf elke productkaart en vanaf de productpagina (met aantalkiezer).
- De winkelwagen leeft in `localStorage` (`petneeds.cart.v1`), blijft dus staan als de
  bezoeker verder klikt of later terugkomt, en synchroniseert tussen tabbladen.
- Een **lade** schuift open vanaf rechts met regels, aantallen en subtotaal; het
  winkelwagen-icoon in de header toont het aantal.
- **`bestellen.html`** toont het overzicht plus een formulier: naam, telefoon, e-mail,
  ophalen óf bezorgen (met adres, postcode, plaats en voorkeursdag) en opmerkingen.
  Validatie gebeurt inline in het Nederlands.
- Verzenden opent **WhatsApp** met een net opgemaakte bestelling (regels, aantallen,
  subtotaal, gegevens). Werkt WhatsApp niet? Dan kopieert de knop "Bestelling kopiëren"
  dezelfde tekst naar het klembord.
- Producten zonder prijs kunnen gewoon in de winkelwagen; die tellen niet mee in het
  subtotaal en worden gemarkeerd als "op aanvraag".

**Let op — er wordt niet online betaald.** De bestelling komt als bericht binnen; de
winkel bevestigt voorraad, prijs en bezorgkosten en stemt de betaling af. Wil je wél
online afrekenen (iDEAL), dan is daar een backend of webshopplatform voor nodig
(Mollie + een klein serverdeel, of Shopify/WooCommerce). Zeg het als je die kant op wilt.

De code staat in `assets/js/cart.js`; het WhatsApp-nummer staat bovenin dat bestand
(`WA_NUMBER`) én in `data/site.json`.

## Bewerken

```bash
python3 scripts/build.py
```

- **Teksten, prijzen, producten, openingstijden, foto-paden** → `data/site.json`
- **Stijl** → `assets/css/site.css`
- **Gedrag** (menu, zoeken, filters, scroll-reveals) → `assets/js/site.js`
- **Winkelwagen en bestelformulier** → `assets/js/cart.js`
- **Paginasjablonen** → `scripts/build.py`, iconen in `scripts/icons.py`
- **Foto's** → `assets/img/products/`, `assets/img/pets/`, `assets/img/site/`

Na elke wijziging in `data/` of `scripts/` opnieuw builden.

## Lokaal bekijken

```bash
cd "/Users/chenxi/Pet need" && python3 -m http.server 4173
```

Daarna http://localhost:4173 openen.

## Beeld

- **Productfoto's** (115×) komen van de oude site. De vogel- en cavia-foto's zijn
  wit-gebalanceerd omdat ze een zware paarse zweem hadden van de winkelverlichting.
- **Sfeerfoto's** (hero, advies, dierenarts) en de vier dier-cirkels zijn
  **CC0/publiek domein** stockfoto's — vrij te gebruiken, geen naamsvermelding
  verplicht. De herkomst staat in `data/image-credits.json`.
- **Winkelfoto**: `assets/img/site/winkel.jpg` — vervang door de daglichtfoto van de pui.
- **Winkelkat**: zodra `assets/img/site/winkelkat.jpg` bestaat, verschijnt het blok
  "Onze winkelkat" op home en Over ons; met `winkelkat-2.jpg` erbij komt er een
  tweede, kleinere foto overheen. Zonder die bestanden slaat de build het blok
  netjes over.

Foto's toevoegen gaat het makkelijkst met het hulpscript — dat snijdt en
comprimeert meteen goed:

```bash
python3 scripts/add-photo.py ~/Downloads/IMG_1234.jpg winkelkat
python3 scripts/build.py
```

Bestemmingen: `winkel`, `winkelkat`, `winkelkat-2`, `hero`.

## Nog te doen / aandachtspunten

- **Betaling**: bestellingen komen binnen via WhatsApp; er wordt niets online betaald.
  Bevestig hoe klanten betalen (in de winkel, bij bezorging, of via een betaalverzoek)
  zodat we die tekst op de bestelpagina kunnen zetten.
- **Prijzen** komen uit de oude site (2021–2023) en moeten gecontroleerd worden.
  Overal staat "prijs onder voorbehoud".
- **Telefoonnummer**: alleen het WhatsApp-nummer 06 10 83 75 12 uit de oude site is
  overgenomen. Een vast nummer kan in `data/site.json` bij `site.whatsapp*` erbij.
- **Twee producten missen een foto** (Hope Farms Cavia Super trio, Selective +4);
  die tonen een pootje-placeholder.
