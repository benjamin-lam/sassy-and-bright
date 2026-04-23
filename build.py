#!/usr/bin/env python3

from __future__ import annotations

import html
import json
import os
import re
import shutil
from copy import deepcopy
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
PALETTE_ALIAS_MAP = {
    "primary": "p",
    "secondary": "s",
    "accent": "a",
    "bg": "bg",
    "text": "t",
    "card": "c",
}


def ensure_trailing_slash(value: str) -> str:
    return value if value.endswith("/") else f"{value}/"


SITE_URL = ensure_trailing_slash(os.environ.get("SITE_URL", DEFAULT_SITE_URL))
BUILD_DATE = date.today().isoformat()
UMLAUT_PROTECTIONS = {
    "Blue-Chip": "__P0__",
    "True Crime": "__P1__",
    "Aerospace": "__P2__",
}


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


def dedupe_strings(items: list[str]) -> list[str]:
    return list(dict.fromkeys(item for item in items if item))


def canonical_link_tag(url: str) -> str:
    return f'<link rel="canonical" href="{html_text(url)}">'


def stylesheet_link_tag(href: str) -> str:
    return f'<link rel="stylesheet" href="{html_text(href)}">'


def json_ld_script_tag(content: str) -> str:
    return f'<script type="application/ld+json">{content}</script>'


def json_data_script_tag(element_id: str, payload: object) -> str:
    return f'<script id="{html_text(element_id)}" type="application/json">{script_json(payload)}</script>'


def with_umlauts(value: str) -> str:
    if not isinstance(value, str):
        return value

    for original, placeholder in UMLAUT_PROTECTIONS.items():
        value = value.replace(original, placeholder)

    value = value.replace("AE", "Ä").replace("OE", "Ö").replace("UE", "Ü")
    value = re.sub(r"(?<![A-Za-zÄÖÜäöü])Ae", "Ä", value)
    value = re.sub(r"(?<![A-Za-zÄÖÜäöü])Oe", "Ö", value)
    value = re.sub(r"(?<![A-Za-zÄÖÜäöü])Ue", "Ü", value)
    value = re.sub(r"(?<![AÄEIOUÖÜaäeiouöü])ae", "ä", value)
    value = re.sub(r"(?<![AÄEIOUÖÜaäeiouöü])oe", "ö", value)
    value = re.sub(r"(?<![AÄEIOUÖÜaäeiouöü])ue", "ü", value)
    value = (
        value.replace("visüll", "visuell")
        .replace("Trü-Crime", "True-Crime")
        .replace("serioes", "seriös")
        .replace("Serioes", "Seriös")
        .replace("Qü", "Que")
        .replace("qü", "que")
        .replace("Zustande", "Zustände")
        .replace("zustande", "zustände")
    )

    for original, placeholder in UMLAUT_PROTECTIONS.items():
        value = value.replace(placeholder, original)
    return value


def humanize_palette(palette: dict) -> dict:
    display = deepcopy(palette)
    display["title"] = with_umlauts(display["title"])
    display["vibe"] = with_umlauts(display["vibe"])
    display["summary"] = with_umlauts(display["summary"])
    display["keywords"] = [with_umlauts(item) for item in display["keywords"]]
    display["seo"]["meta_title"] = with_umlauts(display["seo"]["meta_title"])
    display["seo"]["meta_description"] = with_umlauts(display["seo"]["meta_description"])
    display["seo"]["focus_keyword"] = with_umlauts(display["seo"]["focus_keyword"])
    display["seo"]["questions"] = [with_umlauts(item) for item in display["seo"]["questions"]]
    display["usage_ratio"]["note"] = with_umlauts(display["usage_ratio"]["note"])
    display["industry_match"] = [with_umlauts(item) for item in display["industry_match"]]
    display["audiences"] = [with_umlauts(item) for item in display["audiences"]]
    display["brand_traits"] = [with_umlauts(item) for item in display["brand_traits"]]
    display["html_preview"] = with_umlauts(display["html_preview"])

    for key in ("primary", "secondary", "accent"):
        entry = display["color_psychology"][key]
        entry["name"] = with_umlauts(entry["name"])
        entry["psychology"] = with_umlauts(entry["psychology"])
        entry["best_for"] = with_umlauts(entry["best_for"])
        entry["risk"] = with_umlauts(entry["risk"])

    display["decision_support"]["best_for"] = [
        with_umlauts(item) for item in display["decision_support"]["best_for"]
    ]
    display["decision_support"]["avoid_for"] = [
        with_umlauts(item) for item in display["decision_support"]["avoid_for"]
    ]
    display["decision_support"]["argumentation"] = [
        {
            "claim": with_umlauts(item["claim"]),
            "reason": with_umlauts(item["reason"]),
        }
        for item in display["decision_support"]["argumentation"]
    ]
    display["decision_support"]["faq"] = [
        {
            "question": with_umlauts(item["question"]),
            "answer": with_umlauts(item["answer"]),
        }
        for item in display["decision_support"]["faq"]
    ]
    return display


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


def hex_to_rgb(hex_color: str) -> tuple[float, float, float]:
    normalized = hex_color.lstrip("#")
    return tuple(int(normalized[index : index + 2], 16) / 255 for index in (0, 2, 4))


def channel_luminance(channel: float) -> float:
    if channel <= 0.03928:
        return channel / 12.92
    return ((channel + 0.055) / 1.055) ** 2.4


def contrast_ratio(first: str, second: str) -> float:
    rgb_a = hex_to_rgb(first)
    rgb_b = hex_to_rgb(second)
    lum_a = (
        0.2126 * channel_luminance(rgb_a[0])
        + 0.7152 * channel_luminance(rgb_a[1])
        + 0.0722 * channel_luminance(rgb_a[2])
    )
    lum_b = (
        0.2126 * channel_luminance(rgb_b[0])
        + 0.7152 * channel_luminance(rgb_b[1])
        + 0.0722 * channel_luminance(rgb_b[2])
    )
    lighter = max(lum_a, lum_b)
    darker = min(lum_a, lum_b)
    return (lighter + 0.05) / (darker + 0.05)


def best_foreground(background: str, *options: str) -> str:
    return max(options, key=lambda option: contrast_ratio(background, option))


def theme_var_lines(colors: dict[str, str]) -> list[str]:
    lines = [f"  --color-{key}: {value};" for key, value in colors.items()]
    for key, alias in PALETTE_ALIAS_MAP.items():
        lines.append(f"  --{alias}: {colors[key]};")
    lines.append(
        f"  --mockup-cta-fg: {best_foreground(colors['primary'], colors['text'], colors['bg'])};"
    )
    return lines


def color_var_block(colors: dict[str, str]) -> str:
    return "\n".join([":root {", *theme_var_lines(colors), "}"])


def palette_css(colors: dict[str, str]) -> str:
    return color_var_block(colors) + "\n"


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
                    f"  <p><strong>Gut für:</strong> {html_text(entry['best_for'])}</p>",
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


def wcag_status(accessibility: dict[str, float]) -> str:
    ratios = list(accessibility.values())
    if ratios and all(ratio >= 7.0 for ratio in ratios):
        return "WCAG AAA"
    if ratios and all(ratio >= 4.5 for ratio in ratios):
        return "WCAG AA"
    return "Kontrast prüfen"


def meta_keywords(palette: dict) -> str:
    terms = dedupe_strings(
        [
            palette["seo"]["focus_keyword"],
            *palette["keywords"],
            *palette["industry_match"],
            *palette["brand_traits"],
            *palette["audiences"],
        ]
    )
    return ", ".join(terms)


def article_tag_meta(palette: dict) -> str:
    tags = dedupe_strings(
        [
            palette["seo"]["focus_keyword"],
            *palette["keywords"][:6],
            *palette["industry_match"][:3],
        ]
    )
    return "\n".join(
        f'<meta property="article:tag" content="{html_text(tag)}">' for tag in tags
    )


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


def geo_context_payload(palette: dict, canonical_url: str) -> dict:
    return {
        "type": "palette-knowledge-card",
        "site": SITE_NAME,
        "language": "de",
        "url": canonical_url,
        "title": palette["title"],
        "slug": palette["slug"],
        "summary": palette["summary"],
        "focus_keyword": palette["seo"]["focus_keyword"],
        "keywords": dedupe_strings([palette["seo"]["focus_keyword"], *palette["keywords"]]),
        "seo_questions": palette["seo"]["questions"],
        "industry_match": palette["industry_match"],
        "audiences": palette["audiences"],
        "brand_traits": palette["brand_traits"],
        "decision_support": palette["decision_support"],
        "accessibility": palette["accessibility"],
        "recommended_ai_output": [
            "Kurzbegründung für die Palette",
            "Farbpsychologie pro Leitfarbe",
            "geeignete Einsatzbereiche",
            "Hinweise zu Kontrast und Risiken",
        ],
    }


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
    reading_href = "./"
    mockup_href = "mockup/"
    content = render_template(
        "article.html",
        {
            "meta_title": html_text(palette["seo"]["meta_title"]),
            "meta_description": html_text(palette["seo"]["meta_description"]),
            "meta_keywords": html_text(meta_keywords(palette)),
            "canonical_url": html_text(canonical_url),
            "theme_color": html_text(palette["colors"]["primary"]),
            "canonical_link": canonical_link_tag(canonical_url),
            "article_tag_meta": article_tag_meta(palette),
            "palette_stylesheet_link": stylesheet_link_tag(css_href),
            "json_ld_script": json_ld_script_tag(article_json_ld(palette, canonical_url)),
            "geo_context_script": json_data_script_tag(
                "geo-context", geo_context_payload(palette, canonical_url)
            ),
            "title": html_text(palette["title"]),
            "slug": html_text(slug),
            "vibe": html_text(palette["vibe"]),
            "summary": html_text(palette["summary"]),
            "focus_keyword": html_text(palette["seo"]["focus_keyword"]),
            "color_vars": html_text(color_var_block(palette["colors"])),
            "article_data_script": json_data_script_tag("article-data", palette),
            "usage_note": html_text(palette["usage_ratio"]["note"]),
            "palette_swatches": palette_swatches(palette["colors"], palette["usage_ratio"]),
            "accessibility_rows": accessibility_rows(palette["accessibility"]),
            "cognitive_load": str(palette["cognitive_load"]),
            "cognitive_label": html_text(cognitive_label(palette["cognitive_load"])),
            "industry_tags": tag_list(palette["industry_match"]),
            "audience_tags": tag_list(palette["audiences"], "tag-soft"),
            "brand_tags": tag_list(palette["brand_traits"], "tag-soft"),
            "psychology_cards": psychology_cards(palette["color_psychology"]),
            "best_for_list": list_items(palette["decision_support"]["best_for"]),
            "avoid_for_list": list_items(palette["decision_support"]["avoid_for"]),
            "argument_cards": argument_cards(palette["decision_support"]["argumentation"]),
            "faq_items": faq_items(palette["decision_support"]["faq"]),
            "css_download_href": html_text(css_href),
            "json_download_href": html_text(json_href),
            "reading_href": reading_href,
            "mockup_href": mockup_href,
            "home_href": "../",
            "search_href": "../search/",
            "year": BUILD_DATE[:4],
        },
    )
    write_file(DOCS_DIR / slug / "index.html", content)
    write_file(DOCS_DIR / "assets" / "css" / "palettes" / f"{slug}.css", palette_css(palette["colors"]))
    write_file(DOCS_DIR / "data" / f"{slug}.json", script_json(palette) + "\n")


def build_mockup_page(palette: dict) -> None:
    slug = palette["slug"]
    canonical_url = to_absolute_url(f"{slug}/")
    content = render_template(
        "mockup.html",
        {
            "meta_title": html_text(f"{palette['title']} UI-Mockup | {SITE_NAME}"),
            "meta_description": html_text(
                f"{palette['summary']} Als eigenständiges UI-Mockup mit denselben CSS-Variablen."
            ),
            "canonical_url": html_text(canonical_url),
            "theme_color": html_text(palette["colors"]["primary"]),
            "canonical_link": canonical_link_tag(canonical_url),
            "palette_stylesheet_link": stylesheet_link_tag(
                f"../../assets/css/palettes/{slug}.css"
            ),
            "title": html_text(palette["title"]),
            "vibe": html_text(palette["vibe"]),
            "wcag_status": html_text(wcag_status(palette["accessibility"])),
            "css_download_href": html_text(f"../../assets/css/palettes/{slug}.css"),
            "json_download_href": html_text(f"../../data/{slug}.json"),
            "reading_href": "../",
            "mockup_href": "./",
            "home_href": "../../",
            "search_href": "../../search/",
            "article_data_script": json_data_script_tag("article-data", palette),
            "year": BUILD_DATE[:4],
        },
    )
    write_file(DOCS_DIR / slug / "mockup" / "index.html", content)


def build_index_page(palettes: list[dict]) -> None:
    title = "Farbpaletten für Webprojekte mit Farbpsychologie und SEO-Fokus"
    description = (
        "VibeVault zeigt Farbpaletten als Set-Cards mit Farbpsychologie, Zielgruppenfit, "
        "Accessibility und argumentierbaren Empfehlungen für Webprojekte."
    )
    content = render_template(
        "index.html",
        {
            "meta_title": html_text(title),
            "meta_description": html_text(description),
            "canonical_url": html_text(SITE_URL),
            "theme_color": html_text("#e68298"),
            "canonical_link": canonical_link_tag(SITE_URL),
            "json_ld_script": json_ld_script_tag(collection_json_ld(title, description, SITE_URL, palettes)),
            "palette_count": str(len(palettes)),
            "palette_cards": "\n".join(palette_card(palette) for palette in palettes),
            "featured_questions": question_cards(
                [
                    "Welche Farben passen zu welcher Branche?",
                    "Welche Farbpalette ist für ein neues Produkt glaubwürdig?",
                    "Warum sind neutrale Grautöne im E-Commerce oft nicht genug?",
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
        "So findest du schneller eine argumentierbare Farbpalette für dein Webprojekt."
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
            "canonical_link": canonical_link_tag(to_absolute_url("search/")),
            "json_ld_script": json_ld_script_tag(
                collection_json_ld(title, description, to_absolute_url("search/"), palettes)
            ),
            "search_cards": "\n".join(palette_search_card(palette) for palette in palettes),
            "search_data_script": json_data_script_tag("search-data", palette_index),
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

    palettes = [humanize_palette(validate_palette(load_json(path), path)) for path in article_paths]
    reset_docs_dir()
    copy_assets()
    for palette in palettes:
        build_article_page(palette)
        build_mockup_page(palette)
    build_index_page(palettes)
    build_search_page(palettes)
    build_support_files(palettes)
    print(f"Built {len(palettes)} palette page(s) into {DOCS_DIR}")


if __name__ == "__main__":
    main()
