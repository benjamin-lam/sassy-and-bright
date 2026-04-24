(function () {
  var STORAGE_KEY = "vibevault-mode";
  var aliasMap = {
    primary: "p",
    secondary: "s",
    accent: "a",
    bg: "bg",
    text: "t",
    card: "c"
  };
  var themeVarKeys = ["primary", "secondary", "accent", "bg", "text", "card"];

  function escapeHtml(value) {
    return String(value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function hexToRgb(hex) {
    var normalized = hex.replace("#", "");
    return {
      r: parseInt(normalized.slice(0, 2), 16) / 255,
      g: parseInt(normalized.slice(2, 4), 16) / 255,
      b: parseInt(normalized.slice(4, 6), 16) / 255
    };
  }

  function channelLuminance(channel) {
    return channel <= 0.03928
      ? channel / 12.92
      : Math.pow((channel + 0.055) / (1.055), 2.4);
  }

  function luminance(hex) {
    var rgb = hexToRgb(hex);
    return (
      0.2126 * channelLuminance(rgb.r) +
      0.7152 * channelLuminance(rgb.g) +
      0.0722 * channelLuminance(rgb.b)
    );
  }

  function contrastRatio(first, second) {
    var lumA = luminance(first);
    var lumB = luminance(second);
    var lighter = Math.max(lumA, lumB);
    var darker = Math.min(lumA, lumB);
    return (lighter + 0.05) / (darker + 0.05);
  }

  function preferredForeground(colors) {
    return contrastRatio(colors.primary, colors.bg) >= contrastRatio(colors.primary, colors.text)
      ? colors.bg
      : colors.text;
  }

  function injectTheme(colors) {
    if (!colors) {
      return;
    }

    Object.keys(colors).forEach(function (key) {
      var value = colors[key];
      document.documentElement.style.setProperty("--color-" + key, value);

      if (aliasMap[key]) {
        document.documentElement.style.setProperty("--" + aliasMap[key], value);
      }
    });

    document.documentElement.style.setProperty("--cta-fg", preferredForeground(colors));

    var themeMeta = document.querySelector('meta[name="theme-color"]');
    if (themeMeta && colors.primary) {
      themeMeta.setAttribute("content", colors.primary);
    }
  }

  function captureDefaultTheme() {
    var computed = window.getComputedStyle(document.documentElement);
    var snapshot = {
      themeColor: null
    };

    themeVarKeys.forEach(function (key) {
      snapshot["--color-" + key] = computed.getPropertyValue("--color-" + key).trim();
    });

    Object.keys(aliasMap).forEach(function (key) {
      snapshot["--" + aliasMap[key]] = computed.getPropertyValue("--" + aliasMap[key]).trim();
    });

    snapshot["--cta-fg"] = computed.getPropertyValue("--cta-fg").trim();

    var themeMeta = document.querySelector('meta[name="theme-color"]');
    if (themeMeta) {
      snapshot.themeColor = themeMeta.getAttribute("content") || "";
    }

    return snapshot;
  }

  function restoreTheme(snapshot) {
    if (!snapshot) {
      return;
    }

    Object.keys(snapshot).forEach(function (key) {
      if (key === "themeColor") {
        return;
      }

      if (snapshot[key]) {
        document.documentElement.style.setProperty(key, snapshot[key]);
      } else {
        document.documentElement.style.removeProperty(key);
      }
    });

    var themeMeta = document.querySelector('meta[name="theme-color"]');
    if (themeMeta) {
      if (snapshot.themeColor) {
        themeMeta.setAttribute("content", snapshot.themeColor);
      } else {
        themeMeta.removeAttribute("content");
      }
    }
  }

  function cssBlock(colors) {
    var lines = [":root {"];

    Object.keys(colors).forEach(function (key) {
      lines.push("  --color-" + key + ": " + colors[key] + ";");
    });

    Object.keys(aliasMap).forEach(function (key) {
      lines.push("  --" + aliasMap[key] + ": " + colors[key] + ";");
    });

    lines.push("  --cta-fg: " + preferredForeground(colors) + ";");
    lines.push("}");
    return lines.join("\n");
  }

  function updateCssPreview(colors) {
    var block = document.querySelector("[data-css-preview]");
    if (block) {
      block.textContent = cssBlock(colors);
    }
  }

  function updateContrastHint(colors) {
    var notice = document.getElementById("contrast-note");
    if (!notice || !colors) {
      return;
    }

    var pairs = [
      { label: "Text auf Background", ratio: contrastRatio(colors.text, colors.bg) },
      { label: "Text auf Card", ratio: contrastRatio(colors.text, colors.card) },
      { label: "Text auf Primary", ratio: contrastRatio(colors.text, colors.primary) },
      { label: "Text auf Secondary", ratio: contrastRatio(colors.text, colors.secondary) }
    ];

    var failing = pairs.filter(function (pair) {
      return pair.ratio < 4.5;
    });

    if (failing.length > 0) {
      notice.className = "notice notice-warning";
      notice.innerHTML =
        "<strong>Kontrast-Check:</strong> " +
        failing
          .map(function (pair) {
            return escapeHtml(pair.label + " " + pair.ratio.toFixed(2) + ":1");
          })
          .join(" | ") +
        ". Für Fließtext sollten mindestens 4.5:1 erreicht werden.";
      return;
    }

    notice.className = "notice notice-success";
    notice.innerHTML =
      "<strong>Kontrast-Check:</strong> Alle Kernpaare liegen aktuell über 4.5:1.";
  }

  function copyCss(colors) {
    var output = cssBlock(colors);
    if (navigator.clipboard && navigator.clipboard.writeText) {
      return navigator.clipboard.writeText(output);
    }

    return new Promise(function (resolve, reject) {
      var input = document.createElement("textarea");
      input.value = output;
      input.setAttribute("readonly", "");
      input.style.position = "absolute";
      input.style.left = "-9999px";
      document.body.appendChild(input);
      input.select();

      try {
        document.execCommand("copy");
        document.body.removeChild(input);
        resolve();
      } catch (error) {
        document.body.removeChild(input);
        reject(error);
      }
    });
  }

  function readEmbeddedJSON(node) {
    if (!node) {
      return null;
    }

    try {
      return JSON.parse(node.textContent || "{}");
    } catch (error) {
      return null;
    }
  }

  function readStoredMode() {
    try {
      return window.localStorage.getItem(STORAGE_KEY) || "reading";
    } catch (error) {
      return "reading";
    }
  }

  function storeMode(mode) {
    try {
      window.localStorage.setItem(STORAGE_KEY, mode);
    } catch (error) {
      return;
    }
  }

  function setMode(mode, toggle, description, colors, defaultTheme) {
    document.body.setAttribute("data-mode", mode);

    if (toggle) {
      toggle.checked = mode === "lab";
    }

    if (description) {
      description.textContent =
        mode === "lab" ? description.dataset.labCopy : description.dataset.readingCopy;
    }

    if (mode === "lab") {
      injectTheme(colors);
    } else {
      restoreTheme(defaultTheme);
    }

    storeMode(mode);
  }

  function bindModeToggle(toggle, description, colors, defaultTheme) {
    if (!toggle) {
      return;
    }

    setMode(readStoredMode(), toggle, description, colors, defaultTheme);
    toggle.addEventListener("change", function () {
      setMode(toggle.checked ? "lab" : "reading", toggle, description, colors, defaultTheme);
    });
  }

  function applyPaletteFromJSON(json) {
    if (!json || !json.colors) {
      return;
    }

    injectTheme(json.colors);
    updateCssPreview(json.colors);
    updateContrastHint(json.colors);
  }

  var dataNode = document.getElementById("article-data");
  var data = readEmbeddedJSON(dataNode);

  if (!data) {
    window.injectTheme = injectTheme;
    window.applyPaletteFromJSON = applyPaletteFromJSON;
    return;
  }

  var modeToggle = document.getElementById("mode-toggle");
  var modeDescription = document.getElementById("mode-description");
  var copyButton = document.querySelector("[data-copy-css]");
  var copyStatus = document.getElementById("copy-status");
  var defaultTheme = captureDefaultTheme();

  updateCssPreview(data.colors);
  updateContrastHint(data.colors);
  bindModeToggle(modeToggle, modeDescription, data.colors, defaultTheme);

  if (copyButton) {
    copyButton.addEventListener("click", function () {
      copyCss(data.colors)
        .then(function () {
          if (copyStatus) {
            copyStatus.textContent = "CSS-Variablen in die Zwischenablage kopiert.";
          }
        })
        .catch(function () {
          if (copyStatus) {
            copyStatus.textContent = "Kopieren fehlgeschlagen. Nutze den Download-Link.";
          }
        });
    });
  }

  window.injectTheme = injectTheme;
  window.applyPaletteFromJSON = applyPaletteFromJSON;
})();
