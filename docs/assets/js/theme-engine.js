(function () {
  function escapeHtml(value) {
    return String(value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function injectTheme(colors) {
    if (!colors) {
      return;
    }

    Object.entries(colors).forEach(function (entry) {
      var key = entry[0];
      var value = entry[1];
      document.documentElement.style.setProperty("--color-" + key, value);
    });
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
      : Math.pow((channel + 0.055) / 1.055, 2.4);
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

  function cssBlock(colors) {
    var lines = [":root {"];
    Object.keys(colors).forEach(function (key) {
      lines.push("  --color-" + key + ": " + colors[key] + ";");
    });
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
        "<strong>Kontrast check:</strong> " +
        failing
          .map(function (pair) {
            return escapeHtml(pair.label + " " + pair.ratio.toFixed(2) + ":1");
          })
          .join(" | ") +
        ". Fuer Fliesstext sollten mindestens 4.5:1 erreicht werden.";
      return;
    }

    notice.className = "notice notice-success";
    notice.innerHTML =
      "<strong>Kontrast check:</strong> Alle Kernpaare liegen aktuell ueber 4.5:1.";
  }

  function buildLabMode(data) {
    var bestFit = (data.decision_support && data.decision_support.best_for && data.decision_support.best_for[0]) || "Passender Einsatzbereich";
    var question = (data.seo && data.seo.questions && data.seo.questions[0]) || "Welche Farben passen zum Projekt?";
    return [
      '<div class="lab-shell">',
      '  <section class="hero-card bg-60">',
      '    <span class="badge bg-10">Hero</span>',
      "    <h3>" + escapeHtml(data.title) + "</h3>",
      "    <p>" + escapeHtml(data.summary) + "</p>",
      '    <button class="btn btn-cta" type="button">Palette in UI testen</button>',
      "    <p class=\"micro-copy\">" + escapeHtml(question) + "</p>",
      "  </section>",
      '  <section class="contact-card">',
      '    <span class="badge bg-10">Kontaktformular</span>',
      "    <p>Nutze denselben Farbkanon fuer Lead-Formulare und Support-Kontakt.</p>",
      '    <form>',
      '      <label class="field"><span>Name</span><input type="text" placeholder="Jane Example"></label>',
      '      <label class="field"><span>E-Mail</span><input type="email" placeholder="jane@example.com"></label>',
      '      <label class="field"><span>Projektziel</span><textarea placeholder="Welche Wirkung soll die Palette ausloesen?"></textarea></label>',
      '      <button class="btn" type="button">Analyse senden</button>',
      "    </form>",
      "  </section>",
      '  <section class="dashboard-card bg-30">',
      '    <span class="badge bg-10">Dashboard</span>',
      "    <p><strong>Best Fit:</strong> " + escapeHtml(bestFit) + "</p>",
      '    <div class="dashboard-metrics">',
      "      <span><strong>Load</strong><small>" + escapeHtml(String(data.cognitive_load)) + " / 5</small></span>",
      "      <span><strong>Vibe</strong><small>" + escapeHtml(data.vibe) + "</small></span>",
      "      <span><strong>Branche</strong><small>" + escapeHtml(data.industry_match[0] || "Allgemein") + "</small></span>",
      "      <span><strong>Accent</strong><small>" + escapeHtml(data.colors.accent) + "</small></span>",
      "    </div>",
      "    " + data.html_preview,
      "  </section>",
      "</div>"
    ].join("");
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

  function applyPaletteFromJSON(json) {
    if (!json || !json.colors) {
      return;
    }
    injectTheme(json.colors);
    updateCssPreview(json.colors);
    updateContrastHint(json.colors);
  }

  var dataNode = document.getElementById("article-data");
  if (!dataNode) {
    window.injectTheme = injectTheme;
    window.applyPaletteFromJSON = applyPaletteFromJSON;
    return;
  }

  var data = JSON.parse(dataNode.textContent || "{}");
  var modeToggle = document.getElementById("mode-toggle");
  var labStage = document.getElementById("lab-mode");
  var copyButton = document.querySelector("[data-copy-css]");
  var copyStatus = document.getElementById("copy-status");

  function setMode(isLab) {
    document.body.setAttribute("data-mode", isLab ? "lab" : "reading");
    if (!labStage) {
      return;
    }

    if (isLab) {
      labStage.hidden = false;
      labStage.innerHTML = buildLabMode(data);
      return;
    }

    labStage.hidden = true;
    labStage.innerHTML = "";
  }

  applyPaletteFromJSON(data);
  setMode(false);

  if (modeToggle) {
    modeToggle.addEventListener("change", function (event) {
      setMode(Boolean(event.target.checked));
    });
  }

  if (copyButton) {
    copyButton.addEventListener("click", function () {
      copyCss(data.colors)
        .then(function () {
          if (copyStatus) {
            copyStatus.textContent = "CSS Variablen in die Zwischenablage kopiert.";
          }
        })
        .catch(function () {
          if (copyStatus) {
            copyStatus.textContent = "Copy fehlgeschlagen. Nutze den Download-Link.";
          }
        });
    });
  }

  window.injectTheme = injectTheme;
  window.applyPaletteFromJSON = applyPaletteFromJSON;
})();
