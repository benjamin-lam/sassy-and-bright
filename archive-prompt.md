# Archiv-Prompt fuer neue Paletten

Nutze diesen Prompt, wenn eine KI eine neue Palette-Datei fuer VibeVault erzeugen soll.

```text
Du erzeugst eine einzelne JSON-Datei fuer das Archiv VibeVault.

Ziel:
Erstelle keine dekorative Farbspielerei, sondern eine belastbare Set-Card fuer Webprojekte. Die Daten muessen Webentwicklern, Designern und Projektverantwortlichen helfen, eine Farbpalette fachlich zu begruenden.

Arbeitsregeln:
- Ausgabe nur als gueltiges JSON.
- Deutsch, aber nur ASCII-Zeichen.
- Keine Erklaerungen ausserhalb des JSON.
- Keine Felder ausserhalb des vorgegebenen Schemas.
- Fokus auf Web, UX, Conversion, Lesbarkeit, Markenwirkung und Argumentation.
- Risiken, Gegenargumente und unpassende Einsatzfaelle immer benennen.
- SEO-Fragen so formulieren, dass daraus spaeter echte Landingpage- oder FAQ-Inhalte werden koennen.
- `html_preview` als kleines, statisches HTML-Snippet ausgeben.

Pflichtschema:
{
  "title": "Kurzer Name der Palette",
  "slug": "kebab-case-slug",
  "vibe": "Emotionales Kurzlabel",
  "summary": "1 bis 2 Saetze zu Wirkung, Ziel und Kontext",
  "keywords": ["..."],
  "seo": {
    "meta_title": "...",
    "meta_description": "...",
    "focus_keyword": "...",
    "questions": ["...", "...", "..."]
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
    "note": "Wie die Palette nach dem 60-30-10 Prinzip eingesetzt wird"
  },
  "accessibility": {
    "text_on_primary": 4.5,
    "text_on_secondary": 7.0,
    "text_on_bg": 12.0,
    "text_on_card": 12.0
  },
  "cognitive_load": 3,
  "industry_match": ["..."],
  "audiences": ["..."],
  "brand_traits": ["..."],
  "color_psychology": {
    "primary": {
      "name": "...",
      "psychology": "...",
      "best_for": "...",
      "risk": "..."
    },
    "secondary": {
      "name": "...",
      "psychology": "...",
      "best_for": "...",
      "risk": "..."
    },
    "accent": {
      "name": "...",
      "psychology": "...",
      "best_for": "...",
      "risk": "..."
    }
  },
  "decision_support": {
    "best_for": ["..."],
    "avoid_for": ["..."],
    "argumentation": [
      {
        "claim": "...",
        "reason": "..."
      }
    ],
    "faq": [
      {
        "question": "...",
        "answer": "..."
      }
    ]
  },
  "html_preview": "<button class='btn btn-cta' type='button'>Demo</button>"
}

Inhaltliche Anforderungen:
- Die Palette muss fuer eine konkrete Branche oder Projektsituation sinnvoll sein.
- Die Farben muessen funktional unterschiedliche Rollen haben.
- `summary` und `argumentation` muessen zeigen, warum diese Palette besser passt als eine beliebige neutrale Standardpalette.
- Mindestens eine FAQ-Frage soll das Thema "Warum ist Grau fuer E-Commerce oft zu schwach?" oder eine eng verwandte Frage beantworten, wenn der Kontext E-Commerce, D2C oder Conversion ist.
- `best_for` und `avoid_for` duerfen sich nicht widersprechen.
- `meta_title`, `meta_description` und `focus_keyword` muessen inhaltlich zusammenpassen.

Kontext fuer diese konkrete Ausgabe:
- Branche / Projekt:
- Zielgruppe:
- Markencharakter:
- Gewuenschte Wirkung:
- No-Go-Signale:
- Optional vorhandene Hausfarben:
```
