# Decision Log

## 2026-04-23

- Reading und Mockup wurden als zwei getrennte Seiten pro Palette umgesetzt. Die Analyse bleibt dadurch redaktionell ruhig, das UI-Mockup kann dieselben Farbvariablen isoliert testen.
- Jede Palette lädt ihr generiertes Stylesheet direkt per `<link rel="stylesheet">`. JavaScript ergänzt nur Copy-CSS, Kontrast-Hinweis und die Navigation zwischen Reading und Mockup.
- Palette-spezifische SEO-Fragen und Keywords wurden aus dem sichtbaren HTML entfernt. Sie liegen jetzt als `meta keywords`, `article:tag`, JSON-LD und zusätzlicher GEO-JSON-Kontext für KI-Systeme vor.
- Die frühere eingebettete Live-Demo/Lab-Ansicht ist damit obsolet und wurde aus der HTML-Ausgabe entfernt.
- Für die UI-Demo gibt es eine separate Mockup-Seite unter `/{slug}/mockup/`, damit dieselben Variablen ohne Analyse-Content auf Navigation, Hero, Karten und Status-Footer angewendet werden.
- Die CSS-Ausgabe enthält neben `--color-*` auch Kurzvariablen `--p`, `--s`, `--a`, `--bg`, `--t` und `--c`, damit generierte Mockups und KI-Referenzen dieselbe Benennung verwenden.
- Der Abstand zwischen Mini-Swatches und Tag-Listen wurde vergrößert, damit sich beide Elemente in den Set-Cards nicht mehr visuell berühren.
- Die IDE-Hinweise zu angeblich fehlerhaftem JSON stammten aus Template-Platzhaltern innerhalb von `<script>`-Tags. Die Templates rendern diese Blöcke jetzt als vollständige Platzhalter-Tags, sodass kein echtes JSON-Parsing-Problem mehr im HTML-Template entsteht.
