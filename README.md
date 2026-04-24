# VibeVault

VibeVault ist ein statisches Showcase fuer Farbpaletten. Jede Palette wird aus einer JSON-Datei in eine einheitliche Set-Card ueberfuehrt: mit Farbpsychologie, Zielgruppenfit, Accessibility, SEO-Fragen, FAQ, HTML-Demo, CSS-Download und separater Suchseite.

## Ziele

- Farbpaletten nicht nur zeigen, sondern fachlich begruenden.
- Webentwicklern, Designern und Projektverantwortlichen eine belastbare Entscheidungsgrundlage geben.
- Farbpsychologie, SEO und Accessibility in denselben Datensatz legen.
- CSS Variablen direkt nutzbar machen und parallel als KI-Referenz bereitstellen.

## Projektstruktur

```text
/
|-- .ai-blueprint.md
|-- .github/workflows/build.yml
|-- archive-prompt.md
|-- build.py
|-- src/
|   |-- articles/
|   |   `-- example-palette.json
|   |-- templates/
|   |   |-- article.html
|   |   |-- index.html
|   |   `-- search.html
|   `-- assets/
|       |-- css/
|       |   `-- style.css
|       `-- js/
|           |-- search.js
|           `-- theme-engine.js
`-- docs/
```

## Neue Palette hinzufuegen

1. Lege eine neue JSON-Datei in `src/articles/` an.
2. Verwende einen eindeutigen `slug` in `kebab-case`.
3. Fuelle Farben, SEO-Metadaten, Zielgruppen, Farbpsychologie und Entscheidungslogik aus.
4. Fuehre `python3 build.py` aus.

Danach entstehen automatisch:

- `docs/{slug}/index.html` fuer die Detailseite
- `docs/assets/css/palettes/{slug}.css` als Download
- `docs/data/{slug}.json` als Maschinen- und KI-Referenz
- `docs/index.html` als Uebersicht
- `docs/search/index.html` als Filterseite
- `docs/palette-index.json`, `sitemap.xml`, `robots.txt`

## Erweitertes JSON-Schema

Die Daten sind absichtlich fachlich reichhaltiger als ein reines Farbschema. Eine Palette soll nicht nur huebsch sein, sondern argumentierbar.

```json
{
  "title": "Name der Palette",
  "slug": "kebab-case-slug",
  "vibe": "Kurzlabel fuer die emotionale Richtung",
  "summary": "1 bis 2 Saetze zur Wirkung und zum Einsatz",
  "keywords": [
    "Farbpalette E-Commerce",
    "Farbpsychologie Rosa"
  ],
  "seo": {
    "meta_title": "SEO Title",
    "meta_description": "SEO Description",
    "focus_keyword": "Hauptkeyword",
    "questions": [
      "Welche Farben passen zu ...?",
      "Warum ist ...?"
    ]
  },
  "colors": {
    "primary": "#000000",
    "secondary": "#000000",
    "accent": "#000000",
    "bg": "#000000",
    "text": "#000000",
    "card": "#000000"
  },
  "usage_ratio": {
    "dominant": "bg",
    "supporting": "secondary",
    "accent": "accent",
    "note": "Wie die Palette im 60-30-10 Prinzip eingesetzt wird"
  },
  "accessibility": {
    "text_on_primary": 4.5,
    "text_on_secondary": 7.0,
    "text_on_bg": 12.0,
    "text_on_card": 12.0
  },
  "cognitive_load": 3,
  "industry_match": [
    "E-Commerce",
    "SaaS"
  ],
  "audiences": [
    "Markenentscheider",
    "Webteams"
  ],
  "brand_traits": [
    "nahbar",
    "klar"
  ],
  "color_psychology": {
    "primary": {
      "name": "Name der Leitfarbe",
      "psychology": "Welche Wirkung sie ausloest",
      "best_for": "Wofuer sie gut ist",
      "risk": "Worauf man achten muss"
    },
    "secondary": {
      "name": "Name der Sekundaerfarbe",
      "psychology": "Wirkung",
      "best_for": "Einsatz",
      "risk": "Risiko"
    },
    "accent": {
      "name": "Name der Akzentfarbe",
      "psychology": "Wirkung",
      "best_for": "Einsatz",
      "risk": "Risiko"
    }
  },
  "decision_support": {
    "best_for": [
      "Passende Projektkontexte"
    ],
    "avoid_for": [
      "Weniger passende Kontexte"
    ],
    "argumentation": [
      {
        "claim": "Behauptung, die du im Pitch nutzen kannst",
        "reason": "Begruendung mit Design- oder Businesslogik"
      }
    ],
    "faq": [
      {
        "question": "SEO- oder Stakeholder-Frage",
        "answer": "Praezise Antwort"
      }
    ]
  },
  "html_preview": "<button class='btn btn-cta' type='button'>Demo</button>"
}
```

Die Referenzdatei liegt in [src/articles/example-palette.json](/home/benjamin/PhpstormProjects/sassy-and-bright/src/articles/example-palette.json:1).

## Build und lokale Nutzung

```bash
python3 build.py
```

Optional explizit mit GitHub-Pages-URL:

```bash
SITE_URL="https://benjamin-lam.github.io/sassy-and-bright/" python3 build.py
```

Der Build:

- validiert alle JSON-Dateien
- erzeugt Detailseiten aus Templates
- kopiert CSS und JS nach `docs/assets/`
- erstellt Uebersicht, Suchseite, Sitemap und Robots-Datei

## Deployment

Bei einem Push auf `main` baut GitHub Actions die Seite und deployt `docs/` nach `gh-pages`.

Workflow: [.github/workflows/build.yml](/home/benjamin/PhpstormProjects/sassy-and-bright/.github/workflows/build.yml:1)

## SEO-Definition

Die Seite ist auf Suchanfragen rund um Farbpalette, Farbpsychologie und Begruendung von Farbentscheidungen ausgerichtet. Priorisierte Query-Typen:

- Welche Farben passen zu Branche X?
- Welche Farbpalette passt zu einer Marke oder Zielgruppe?
- Warum ist eine neutrale graue Palette fuer E-Commerce oft zu schwach?
- Welche Farben erzeugen Vertrauen, Kaufimpuls oder Klarheit?
- Wie argumentiert man Farbentscheidungen in Projekten?

SEO wird ueber drei Ebenen abgebildet:

- `seo.meta_title` und `seo.meta_description` pro Palette
- `seo.questions` fuer Informationsintention und FAQ-Logik
- JSON-LD, Canonicals, Sitemap und Robots im Build

## KI-Workflow

- Regeln fuer konsistente Inhaltsgenerierung stehen in [.ai-blueprint.md](/home/benjamin/PhpstormProjects/sassy-and-bright/.ai-blueprint.md:1)
- Ein direkt nutzbarer Archiv-Prompt steht in [archive-prompt.md](/home/benjamin/PhpstormProjects/sassy-and-bright/archive-prompt.md:1)

## Hinweise

- `html_preview` wird bewusst als vertrauenswuerdiger, statischer HTML-Snippet behandelt und nicht sanitisiert.
- Ziel ist ein statischer, sehr leichter Output, optimiert fuer starke Werte in SEO, Accessibility und Performance.
