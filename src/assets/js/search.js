(function () {
  var dataNode = document.getElementById("search-data");
  if (!dataNode) {
    return;
  }

  var palettes = JSON.parse(dataNode.textContent || "[]");
  var input = document.getElementById("search-input");
  var vibeFilter = document.getElementById("vibe-filter");
  var industryFilter = document.getElementById("industry-filter");
  var resetButton = document.getElementById("reset-search");
  var cards = Array.prototype.slice.call(document.querySelectorAll(".search-card"));
  var resultCount = document.getElementById("result-count");
  var totalCount = document.getElementById("total-count");
  var emptyState = document.getElementById("empty-state");

  function updateCount(visible) {
    if (resultCount) {
      resultCount.textContent = String(visible);
    }
    if (totalCount) {
      totalCount.textContent = String(palettes.length);
    }
    if (emptyState) {
      emptyState.hidden = visible !== 0;
    }
  }

  function matchesIndustry(cardIndustries, activeIndustry) {
    if (!activeIndustry) {
      return true;
    }
    return cardIndustries.split(",").indexOf(activeIndustry) !== -1;
  }

  function filterCards() {
    var query = (input && input.value ? input.value : "").trim().toLowerCase();
    var vibe = vibeFilter ? vibeFilter.value : "";
    var industry = industryFilter ? industryFilter.value : "";
    var visible = 0;

    cards.forEach(function (card) {
      var searchBlob = card.dataset.search || "";
      var cardVibe = card.dataset.vibe || "";
      var cardIndustries = card.dataset.industries || "";
      var queryMatch = !query || searchBlob.indexOf(query) !== -1;
      var vibeMatch = !vibe || cardVibe === vibe;
      var industryMatch = matchesIndustry(cardIndustries, industry);
      var show = queryMatch && vibeMatch && industryMatch;
      card.hidden = !show;
      if (show) {
        visible += 1;
      }
    });

    updateCount(visible);
  }

  if (input) {
    input.addEventListener("input", filterCards);
  }

  if (vibeFilter) {
    vibeFilter.addEventListener("change", filterCards);
  }

  if (industryFilter) {
    industryFilter.addEventListener("change", filterCards);
  }

  if (resetButton) {
    resetButton.addEventListener("click", function () {
      if (input) {
        input.value = "";
      }
      if (vibeFilter) {
        vibeFilter.value = "";
      }
      if (industryFilter) {
        industryFilter.value = "";
      }
      filterCards();
    });
  }

  updateCount(palettes.length);
  filterCards();
})();
