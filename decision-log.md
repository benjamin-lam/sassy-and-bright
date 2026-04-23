# Decision Log

## 2026-04-23

- Das Archiv wurde von einer Einzelbeispiel-Struktur auf ein vollständigeres Portfolio mit 131 Paletten ausgebaut. Die Anzahl folgt den definierten Clustern und Varianten über alle sechs Sektoren hinweg.
- Jede Palette bleibt datengetrieben. Die JSON-Dateien enthalten Taxonomie, SEO-Metadaten, Zielgruppen, Branchenfit, Farbpsychologie, Entscheidungsargumente und die Style-Guide-Übertragung in einem Datensatz.
- Die Detailseite ist jetzt die eigentliche Trägerseite der Palette. Das generierte Paletten-Stylesheet wird direkt auf die Analyse-Seite geladen, statt eine separate Mockup-Seite zu erzeugen.
- Der Modusschalter bleibt erhalten, aber nur noch innerhalb derselben Seite: `Reading` priorisiert Analyse und Argumentation, `Lab` verschiebt dieselbe Oberfläche visuell in eine UI-nähere Gewichtung.
- SEO-Fragen und Keywords werden nicht mehr sichtbar im HTML ausgegeben. Sie liegen als klassische Metadaten, OpenGraph, JSON-LD und zusätzlicher maschinenlesbarer GEO-Kontext im Head.
- Die Startseite wurde von Prompt-/Anleitungs-Texten bereinigt. Stattdessen beschreibt sie jetzt das Portfolio, die Suchlogik und wie VibeVault-Daten in einen Style Guide oder ein Design-System übertragen werden.
- Die Suche bleibt als eigene Seite erhalten und wurde um Sektor- und Clusterfilter erweitert. Dadurch bleibt die Startseite redaktionell fokussiert und die Suche skaliert sauber mit dem größeren Portfolio.
- Ein separates Impressum wurde ergänzt und in die Hauptnavigation der zentralen Einstiegsseiten aufgenommen.
- Die bisherige generische Umlaut-Konvertierung war zu aggressiv und hat englische Variantennamen wie `Blue` beschädigt. Die Ausgabe verwendet jetzt gezieltere Schutz- und Korrekturregeln.
- Alte Mockup-spezifische CSS- und Variablennamen wurden entfernt, damit die Codebasis die aktuelle Ein-Seiten-Architektur konsistent abbildet.
