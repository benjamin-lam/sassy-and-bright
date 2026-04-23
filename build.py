#!/usr/bin/env python3

from __future__ import annotations

import html
import json
import os
import re
import shutil
from datetime import date
from pathlib import Path
from urllib.parse import urljoin

ROOT = Path(__file__).resolve().parent
SRC_DIR = ROOT / "src"
ARTICLES_DIR = SRC_DIR / "articles"
TEMPLATES_DIR = SRC_DIR / "templates"
ASSETS_DIR = SRC_DIR / "assets"
DOCS_DIR = ROOT / "docs"

SITE_NAME = "VibeVault"
DEFAULT_SITE_URL = "https://example.com/"
SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
HEX_PATTERN = re.compile(r"^#[0-9a-fA-F]{6}$")


def ensure_trailing_slash(value: str) -> str:
    return value if value.endswith("/") else f"{value}/"


SITE_URL = ensure_trailing_slash(os.environ.get("SITE_URL", DEFAULT_SITE_URL))
BUILD_DATE = date.today().isoformat()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def read_template(name: str) -> str:
    return (TEMPLATES_DIR / name).read_text(encoding="utf-8")


def render_template(name: str, mapping: dict[str, str]) -> str:
    content = read_template(name)
    for key, value in mapping.items():
        content = content.replace(f"{{{{{key}}}}}", value)

    leftovers = sorted(set(re.findall(r"\{\{([a-zA-Z0-9_]+)\}\}", content)))
    if leftovers:
        missing = ", ".join(leftovers)
        raise ValueError(f"Unresolved placeholders in {name}: {missing}")
    return content


def html_text(value: str) -> str:
    return html.escape(value, quote=True)


def script_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2).replace("</", "<\\/")


def require_string(data: dict, key: str, path: str, errors: list[str]) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{path}.{key} must be a non-empty string")
        return ""
    return value.strip()


def require_number(data: dict, key: str, path: str, errors: list[str]) -> float:
    value = data.get(key)
    if not isinstance(value, (int, float)):
        errors.append(f"{path}.{key} must be a number")
        return 0.0
    return float(value)


def require_string_list(data: dict, key: str, path: str, errors: list[str]) -> list[str]:
    value = data.get(key)
    if not isinstance(value, list) or not value:
        errors.append(f"{path}.{key} must be a non-empty list of strings")
        return []

    normalized: list[str] = []
    for index, item in enumerate(value):
        if not isinstance(item, str) or not item.strip():
            errors.append(f"{path}.{key}[{index}] must be a non-empty string")
            continue
        normalized.append(item.strip())
    return normalized


def require_object(data: dict, key: str, path: str, errors: list[str]) -> dict:
    value = data.get(key)
    if not isinstance(value, dict):
        errors.append(f"{path}.{key} must be an object")
        return {}
    return value


def validate_colors(colors: dict, errors: list[str]) -> dict[str, str]:
    normalized: dict[str, str] = {}
    for key in ("primary", "secondary", "accent", "bg", "text", "card"):
        value = colors.get(key)
        if not isinstance(value, str) or not HEX_PATTERN.match(value):
            errors.append(f"colors.{key} must be a 6-digit hex color")
            continue
        normalized[key] = value.lower()
    return normalized


def validate_accessibility(data: dict, errors: list[str]) -> dict[str, float]:
    normalized: dict[str, float] = {}
    for key in ("text_on_primary", "text_on_secondary", "text_on_bg", "text_on_card"):
        value = data.get(key)
        if not isinstance(value, (int, float)):
            errors.append(f"accessibility.{key} must be a number")
            continue
        normalized[key] = float(value)
    return normalized


def validate_psychology(data: dict, errors: list[str]) -> dict[str, dict[str, str]]:
    normalized: dict[str, dict[str, str]] = {}
    for key in ("primary", "secondary", "accent"):
        entry = data.get(key)
        if not isinstance(entry, dict):
            errors.append(f"color_psychology.{key} must be an object")
            continue
        normalized[key] = {
            "name": require_string(entry, "name", f"color_psychology.{key}", errors),
            "psychology": require_string(entry, "psychology", f"color_psychology.{key}", errors),
            "best_for": require_string(entry, "best_for", f"color_psychology.{key}", errors),
            "risk": require_string(entry, "risk", f"color_psychology.{key}", errors),
        }
    return normalized


def validate_argumentation(items: object, errors: list[str]) -> list[dict[str, str]]:
    if not isinstance(items, list) or not items:
        errors.append("decision_support.argumentation must be a non-empty list")
        return []

    normalized: list[dict[str, str]] = []
    for index, item in enumerate(items):
        path = f"decision_support.argumentation[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{path} must be an object")
            continue
        normalized.append(
            {
                "claim": require_string(item, "claim", path, errors),
                "reason": require_string(item, "reason", path, errors),
            }
        )
    return normalized


def validate_faq(items: object, errors: list[str]) -> list[dict[str, str]]:
    if not isinstance(items, list) or not items:
        errors.append("decision_support.faq must be a non-empty list")
        return []

    normalized: list[dict[str, str]] = []
    for index, item in enumerate(items):
        path = f"decision_support.faq[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{path} must be an object")
            continue
        normalized.append(
            {
                "question": require_string(item, "question", path, errors),
                "answer": require_string(item, "answer", path, errors),
            }
        )
    return normalized


def validate_palette(raw: dict, source_path: Path) -> dict:
    if not isinstance(raw, dict):
        raise ValueError(f"{source_path.name} must contain a JSON object at the root")

    errors: list[str] = []
    title = require_string(raw, "title", "root", errors)
    slug = require_string(raw, "slug", "root", errors)
    vibe = require_string(raw, "vibe", "root", errors)
    summary = require_string(raw, "summary", "root", errors)
    keywords = require_string_list(raw, "keywords", "root", errors)

    seo = require_object(raw, "seo", "root", errors)
    colors = require_object(raw, "colors", "root", errors)
    usage_ratio = require_object(raw, "usage_ratio", "root", errors)
    accessibility = require_object(raw, "accessibility", "root", errors)
    color_psychology = require_object(raw, "color_psychology", "root", errors)
    decision_support = require_object(raw, "decision_support", "root", errors)

    if slug and not SLUG_PATTERN.match(slug):
        errors.append("root.slug must use kebab-case")

    normalized = {
        "title": title,
        "slug": slug,
        "vibe": vibe,
        "summary": summary,
        "keywords": keywords,
        "seo": {
            "meta_title": require_string(seo, "meta_title", "seo", errors),
            "meta_description": require_string(seo, "meta_description", "seo", errors),
            "focus_keyword": require_string(seo, "focus_keyword", "seo", errors),
            "questions": require_string_list(seo, "questions", "seo", errors),
        },
        "colors": validate_colors(colors, errors),
        "usage_ratio": {
            "dominant": require_string(usage_ratio, "dominant", "usage_ratio", errors),
            "supporting": require_string(usage_ratio, "supporting", "usage_ratio", errors),
            "accent": require_string(usage_ratio, "accent", "usage_ratio", errors),
            "note": require_string(usage_ratio, "note", "usage_ratio", errors),
        },
        "accessibility": validate_accessibility(accessibility, errors),
        "cognitive_load": int(require_number(raw, "cognitive_load", "root", errors)),
        "industry_match": require_string_list(raw, "industry_match", "root", errors),
        "audiences": require_string_list(raw, "audiences", "root", errors),
        "brand_traits": require_string_list(raw, "brand_traits", "root", errors),
        "color_psychology": validate_psychology(color_psychology, errors),
        "decision_support": {
            "best_for": require_string_list(decision_support, "best_for", "decision_support", errors),
            "avoid_for": require_string_list(decision_support, "avoid_for", "decision_support", errors),
            "argumentation": validate_argumentation(decision_support.get("argumentation"), errors),
            "faq": validate_faq(decision_support.get("faq"), errors),
        },
        "html_preview": require_string(raw, "html_preview", "root", errors),
    }

    if normalized["cognitive_load"] < 1 or normalized["cognitive_load"] > 5:
        errors.append("root.cognitive_load must be between 1 and 5")

    color_keys = set(normalized["colors"])
    for key in ("dominant", "supporting", "accent"):
        usage_value = normalized["usage_ratio"][key]
        if usage_value and usage_value not in color_keys:
            errors.append(f"usage_ratio.{key} must reference one of the color keys")

    if errors:
        joined = "\n".join(f"- {error}" for error in errors)
        raise ValueError(f"Schema validation failed for {source_path.name}:\n{joined}")

    return normalized


def color_var_block(colors: dict[str, str]) -> str:
    lines = [":root {"]
    for key, value in colors.items():
        lines.append(f"  --color-{key}: {value};")
    lines.append("}")
    return "\n".join(lines)


def palette_css(colors: dict[str, str]) -> str:
    return "\n".join(
        [
            ":root {",
            *(f"  --color-{key}: {value};" for key, value in colors.items()),
            "}",
            "",
        ]
    )


def list_items(items: list[str], class_name: str = "bullet-list") -> str:
    rendered = "".join(f"<li>{html_text(item)}</li>" for item in items)
    return f'<ul class="{class_name}">{rendered}</ul>'


def tag_list(items: list[str], tone: str = "") -> str:
    classes = "tag"
    if tone:
        classes += f" {tone}"
    return "".join(f'<li class="{classes}">{html_text(item)}</li>' for item in items)


def palette_swatches(colors: dict[str, str], usage_ratio: dict[str, str]) -> str:
    role_map = {
        usage_ratio["dominant"]: "60%",
        usage_ratio["supporting"]: "30%",
        usage_ratio["accent"]: "10%",
    }
    cards: list[str] = []
    for key in ("primary", "secondary", "accent", "bg", "text", "card"):
        color = colors[key]
        role = role_map.get(key, "Support")
        cards.append(
            "\n".join(
                [
                    '<article class="swatch-card">',
                    f'  <div class="swatch-chip" style="background:{html_text(color)}"></div>',
                    '  <div class="swatch-meta">',
                    f"    <h3>{html_text(key.title())}</h3>",
                    f'    <p class="swatch-hex">{html_text(color)}</p>',
                    f'    <p class="swatch-role">{html_text(role)}</p>',
                    "  </div>",
                    "</article>",
                ]
            )
        )
    return "\n".join(cards)


def accessibility_rows(accessibility: dict[str, float]) -> str:
    labels = {
        "text_on_primary": "Text auf Primary",
        "text_on_secondary": "Text auf Secondary",
        "text_on_bg": "Text auf Background",
        "text_on_card": "Text auf Card",
    }
    rows: list[str] = []
    for key in ("text_on_primary", "text_on_secondary", "text_on_bg", "text_on_card"):
        ratio = accessibility[key]
        state = "Pass" if ratio >= 4.5 else "Check"
        rows.append(
            "<tr>"
            f"<th scope=\"row\">{html_text(labels[key])}</th>"
            f"<td>{ratio:.2f}:1</td>"
            f"<td>{state}</td>"
            "</tr>"
        )
    return "\n".join(rows)


def psychology_cards(psychology: dict[str, dict[str, str]]) -> str:
    cards: list[str] = []
    for key in ("primary", "secondary", "accent"):
        entry = psychology[key]
        cards.append(
            "\n".join(
                [
                    '<article class="insight-card">',
                    f"  <p class=\"eyebrow\">{html_text(key.title())}</p>",
                    f"  <h3>{html_text(entry['name'])}</h3>",
                    f"  <p>{html_text(entry['psychology'])}</p>",
                    f"  <p><strong>Gut fuer:</strong> {html_text(entry['best_for'])}</p>",
                    f"  <p><strong>Risiko:</strong> {html_text(entry['risk'])}</p>",
                    "</article>",
                ]
            )
        )
    return "\n".join(cards)


def argument_cards(items: list[dict[str, str]]) -> str:
    rendered: list[str] = []
    for item in items:
        rendered.append(
            "\n".join(
                [
                    '<article class="argument-card">',
                    f"  <h3>{html_text(item['claim'])}</h3>",
                    f"  <p>{html_text(item['reason'])}</p>",
                    "</article>",
                ]
            )
        )
    return "\n".join(rendered)


def faq_items(items: list[dict[str, str]]) -> str:
    rendered: list[str] = []
    for item in items:
        rendered.append(
            "\n".join(
                [
                    '<details class="faq-item">',
                    f"  <summary>{html_text(item['question'])}</summary>",
                    f"  <p>{html_text(item['answer'])}</p>",
                    "</details>",
                ]
            )
        )
    return "\n".join(rendered)


def question_cards(items: list[str]) -> str:
    return "\n".join(f"<li>{html_text(item)}</li>" for item in items)


def cognitive_label(score: int) -> str:
    labels = {
        1: "Sehr ruhig",
        2: "Ruhig",
        3: "Ausgewogen",
        4: "Aktivierend",
        5: "Sehr aktivierend",
    }
    return labels.get(score, "Nicht bewertet")


def palette_card(palette: dict, asset_prefix: str = "", show_link: bool = True) -> str:
    detail_href = f"{asset_prefix}{palette['slug']}/"
    link_markup = (
        f'<a class="text-link" href="{html_text(detail_href)}">Set-Card ansehen</a>'
        if show_link
        else ""
    )
    swatches = "".join(
        f'<span class="mini-swatch" style="background:{html_text(palette["colors"][key])}"></span>'
        for key in ("primary", "secondary", "accent", "bg")
    )
    meta = " / ".join(
        [
            html_text(palette["vibe"]),
            html_text(palette["seo"]["focus_keyword"]),
            html_text(", ".join(palette["industry_match"][:2])),
        ]
    )
    return "\n".join(
        [
            '<article class="palette-card reveal">',
            '  <div class="palette-card-top">',
            f"    <p class=\"eyebrow\">{html_text(meta)}</p>",
            f"    <h2>{html_text(palette['title'])}</h2>",
            f"    <p>{html_text(palette['summary'])}</p>",
            "  </div>",
            f'  <div class="mini-swatches" aria-label="Farben">{swatches}</div>',
            '  <ul class="tag-list">',
            f"{tag_list(palette['brand_traits'][:3])}",
            "  </ul>",
            f"  {link_markup}",
            "</article>",
        ]
    )


def palette_search_card(palette: dict) -> str:
    search_terms = [
        palette["title"],
        palette["vibe"],
        palette["summary"],
        palette["seo"]["focus_keyword"],
        *palette["keywords"],
        *palette["industry_match"],
        *palette["audiences"],
        *palette["brand_traits"],
        *palette["seo"]["questions"],
    ]
    payload = " ".join(term.lower() for term in search_terms)
    industries = ",".join(palette["industry_match"])
    return "\n".join(
        [
            (
                f'<article class="palette-card search-card reveal" '
                f'data-search="{html_text(payload)}" '
                f'data-vibe="{html_text(palette["vibe"].lower())}" '
                f'data-industries="{html_text(industries.lower())}">'
            ),
            '  <div class="palette-card-top">',
            f"    <p class=\"eyebrow\">{html_text(palette['seo']['focus_keyword'])}</p>",
            f"    <h2>{html_text(palette['title'])}</h2>",
            f"    <p>{html_text(palette['summary'])}</p>",
            "  </div>",
            '  <ul class="tag-list">',
            f"{tag_list(palette['industry_match'][:3], 'tag-soft')}",
            "  </ul>",
            f'  <a class="text-link" href="../{html_text(palette["slug"])}/">Zur Palette</a>',
            "</article>",
        ]
    )


def to_absolute_url(path: str) -> str:
    return urljoin(SITE_URL, path)


def article_json_ld(palette: dict, canonical_url: str) -> str:
    faq_entities = [
        {
            "@type": "Question",
            "name": entry["question"],
            "acceptedAnswer": {"@type": "Answer", "text": entry["answer"]},
        }
        for entry in palette["decision_support"]["faq"]
    ]
    data = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "WebPage",
                "@id": canonical_url,
                "url": canonical_url,
                "name": palette["seo"]["meta_title"],
                "description": palette["seo"]["meta_description"],
                "inLanguage": "de",
                "isPartOf": {"@id": to_absolute_url("#website")},
            },
            {
                "@type": "Article",
                "@id": f"{canonical_url}#article",
                "headline": palette["title"],
                "description": palette["summary"],
                "keywords": palette["keywords"],
                "articleSection": palette["industry_match"],
                "about": [
                    palette["seo"]["focus_keyword"],
                    "Farbpsychologie",
                    "Design-System",
                ],
                "mainEntityOfPage": {"@id": canonical_url},
                "dateModified": BUILD_DATE,
                "inLanguage": "de",
            },
            {
                "@type": "FAQPage",
                "@id": f"{canonical_url}#faq",
                "mainEntity": faq_entities,
            },
        ],
    }
    return script_json(data)


def collection_json_ld(title: str, description: str, canonical_url: str, items: list[dict]) -> str:
    item_list = [
        {
            "@type": "ListItem",
            "position": index + 1,
            "url": to_absolute_url(f"{item['slug']}/"),
            "name": item["title"],
        }
        for index, item in enumerate(items)
    ]
    data = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "WebSite",
                "@id": to_absolute_url("#website"),
                "url": SITE_URL,
                "name": SITE_NAME,
                "inLanguage": "de",
            },
            {
                "@type": "CollectionPage",
                "@id": canonical_url,
                "url": canonical_url,
                "name": title,
                "description": description,
                "inLanguage": "de",
                "isPartOf": {"@id": to_absolute_url("#website")},
            },
            {
                "@type": "ItemList",
                "@id": f"{canonical_url}#itemlist",
                "itemListElement": item_list,
            },
        ],
    }
    return script_json(data)


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def copy_assets() -> None:
    shutil.copytree(ASSETS_DIR, DOCS_DIR / "assets", dirs_exist_ok=True)


def build_article_page(palette: dict) -> None:
    slug = palette["slug"]
    canonical_url = to_absolute_url(f"{slug}/")
    css_href = f"../assets/css/palettes/{slug}.css"
    json_href = f"../data/{slug}.json"
    content = render_template(
        "article.html",
        {
            "meta_title": html_text(palette["seo"]["meta_title"]),
            "meta_description": html_text(palette["seo"]["meta_description"]),
            "canonical_url": html_text(canonical_url),
            "theme_color": html_text(palette["colors"]["primary"]),
            "json_ld": article_json_ld(palette, canonical_url),
            "title": html_text(palette["title"]),
            "slug": html_text(slug),
            "vibe": html_text(palette["vibe"]),
            "summary": html_text(palette["summary"]),
            "focus_keyword": html_text(palette["seo"]["focus_keyword"]),
            "color_vars": html_text(color_var_block(palette["colors"])),
            "article_json": script_json(palette),
            "html_preview": palette["html_preview"],
            "usage_note": html_text(palette["usage_ratio"]["note"]),
            "palette_swatches": palette_swatches(palette["colors"], palette["usage_ratio"]),
            "accessibility_rows": accessibility_rows(palette["accessibility"]),
            "cognitive_load": str(palette["cognitive_load"]),
            "cognitive_label": html_text(cognitive_label(palette["cognitive_load"])),
            "industry_tags": tag_list(palette["industry_match"]),
            "audience_tags": tag_list(palette["audiences"], "tag-soft"),
            "brand_tags": tag_list(palette["brand_traits"], "tag-soft"),
            "keyword_tags": tag_list(palette["keywords"], "tag-soft"),
            "psychology_cards": psychology_cards(palette["color_psychology"]),
            "best_for_list": list_items(palette["decision_support"]["best_for"]),
            "avoid_for_list": list_items(palette["decision_support"]["avoid_for"]),
            "argument_cards": argument_cards(palette["decision_support"]["argumentation"]),
            "faq_items": faq_items(palette["decision_support"]["faq"]),
            "seo_question_cards": question_cards(palette["seo"]["questions"]),
            "css_download_href": html_text(css_href),
            "json_download_href": html_text(json_href),
            "home_href": "../",
            "search_href": "../search/",
            "year": BUILD_DATE[:4],
        },
    )
    write_file(DOCS_DIR / slug / "index.html", content)
    write_file(DOCS_DIR / "assets" / "css" / "palettes" / f"{slug}.css", palette_css(palette["colors"]))
    write_file(DOCS_DIR / "data" / f"{slug}.json", script_json(palette) + "\n")


def build_index_page(palettes: list[dict]) -> None:
    title = "Farbpaletten fuer Webprojekte mit Farbpsychologie und SEO-Fokus"
    description = (
        "VibeVault zeigt Farbpaletten als Set-Cards mit Farbpsychologie, Zielgruppenfit, "
        "Accessibility und argumentierbaren Empfehlungen fuer Webprojekte."
    )
    content = render_template(
        "index.html",
        {
            "meta_title": html_text(title),
            "meta_description": html_text(description),
            "canonical_url": html_text(SITE_URL),
            "theme_color": html_text("#e68298"),
            "json_ld": collection_json_ld(title, description, SITE_URL, palettes),
            "palette_count": str(len(palettes)),
            "palette_cards": "\n".join(palette_card(palette) for palette in palettes),
            "featured_questions": question_cards(
                [
                    "Welche Farben passen zu welcher Branche?",
                    "Welche Farbpalette ist fuer ein neues Produkt glaubwuerdig?",
                    "Warum sind neutrale Grautoene im E-Commerce oft nicht genug?",
                ]
            ),
            "search_href": "search/",
            "year": BUILD_DATE[:4],
        },
    )
    write_file(DOCS_DIR / "index.html", content)


def build_search_page(palettes: list[dict]) -> None:
    title = "Suche: passende Farbpalette nach Zielgruppe, Branche und Wirkung"
    description = (
        "Filtere Farbpaletten nach Vibe, Branche, Keywords und Entscheidungsfragen. "
        "So findest du schneller eine argumentierbare Farbpalette fuer dein Webprojekt."
    )
    palette_index = [
        {
            "title": palette["title"],
            "slug": palette["slug"],
            "vibe": palette["vibe"],
            "summary": palette["summary"],
            "keywords": palette["keywords"],
            "industry_match": palette["industry_match"],
            "audiences": palette["audiences"],
            "brand_traits": palette["brand_traits"],
            "focus_keyword": palette["seo"]["focus_keyword"],
            "questions": palette["seo"]["questions"],
            "colors": palette["colors"],
        }
        for palette in palettes
    ]

    vibes = sorted({palette["vibe"] for palette in palettes})
    industries = sorted({item for palette in palettes for item in palette["industry_match"]})
    vibe_options = "\n".join(
        f'<option value="{html_text(vibe.lower())}">{html_text(vibe)}</option>' for vibe in vibes
    )
    industry_options = "\n".join(
        f'<option value="{html_text(industry.lower())}">{html_text(industry)}</option>'
        for industry in industries
    )

    content = render_template(
        "search.html",
        {
            "meta_title": html_text(title),
            "meta_description": html_text(description),
            "canonical_url": html_text(to_absolute_url("search/")),
            "theme_color": html_text("#36b7a7"),
            "json_ld": collection_json_ld(title, description, to_absolute_url("search/"), palettes),
            "search_cards": "\n".join(palette_search_card(palette) for palette in palettes),
            "palette_index_json": script_json(palette_index),
            "vibe_options": vibe_options,
            "industry_options": industry_options,
            "home_href": "../",
            "year": BUILD_DATE[:4],
        },
    )
    write_file(DOCS_DIR / "search" / "index.html", content)
    write_file(DOCS_DIR / "palette-index.json", script_json(palette_index) + "\n")


def build_support_files(palettes: list[dict]) -> None:
    urls = [SITE_URL, to_absolute_url("search/"), *(to_absolute_url(f"{item['slug']}/") for item in palettes)]
    sitemap_lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for url in urls:
        sitemap_lines.extend(
            [
                "  <url>",
                f"    <loc>{html_text(url)}</loc>",
                f"    <lastmod>{BUILD_DATE}</lastmod>",
                "  </url>",
            ]
        )
    sitemap_lines.append("</urlset>")
    write_file(DOCS_DIR / "sitemap.xml", "\n".join(sitemap_lines) + "\n")

    robots = "\n".join(
        [
            "User-agent: *",
            "Allow: /",
            f"Sitemap: {to_absolute_url('sitemap.xml')}",
            "",
        ]
    )
    write_file(DOCS_DIR / "robots.txt", robots)
    write_file(DOCS_DIR / ".nojekyll", "\n")


def reset_docs_dir() -> None:
    if DOCS_DIR.exists():
        shutil.rmtree(DOCS_DIR)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)


def main() -> None:
    article_paths = sorted(ARTICLES_DIR.glob("*.json"))
    if not article_paths:
        raise SystemExit("No JSON files found in src/articles/")

    palettes = [validate_palette(load_json(path), path) for path in article_paths]
    reset_docs_dir()
    copy_assets()
    for palette in palettes:
        build_article_page(palette)
    build_index_page(palettes)
    build_search_page(palettes)
    build_support_files(palettes)
    print(f"Built {len(palettes)} palette page(s) into {DOCS_DIR}")


if __name__ == "__main__":
    main()
