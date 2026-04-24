(function () {
  var dataNode = document.getElementById("search-data");
  if (!dataNode) {
    return;
  }

  var palettes = JSON.parse(dataNode.textContent || "[]");
  var input = document.getElementById("search-input");
  var sectorFilter = document.getElementById("sector-filter");
  var clusterFilter = document.getElementById("cluster-filter");
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

  function syncQueryString() {
    var url = new URL(window.location.href);

    if (sectorFilter && sectorFilter.value) {
      url.searchParams.set("sector", sectorFilter.value);
    } else {
      url.searchParams.delete("sector");
    }

    if (clusterFilter && clusterFilter.value) {
      url.searchParams.set("cluster", clusterFilter.value);
    } else {
      url.searchParams.delete("cluster");
    }

    if (vibeFilter && vibeFilter.value) {
      url.searchParams.set("vibe", vibeFilter.value);
    } else {
      url.searchParams.delete("vibe");
    }

    if (industryFilter && industryFilter.value) {
      url.searchParams.set("industry", industryFilter.value);
    } else {
      url.searchParams.delete("industry");
    }

    if (input && input.value.trim()) {
      url.searchParams.set("q", input.value.trim());
    } else {
      url.searchParams.delete("q");
    }

    window.history.replaceState({}, "", url.toString());
  }

  function filterCards() {
    var query = (input && input.value ? input.value : "").trim().toLowerCase();
    var sector = sectorFilter ? sectorFilter.value : "";
    var cluster = clusterFilter ? clusterFilter.value : "";
    var vibe = vibeFilter ? vibeFilter.value : "";
    var industry = industryFilter ? industryFilter.value : "";
    var visible = 0;

    cards.forEach(function (card) {
      var searchBlob = card.dataset.search || "";
      var cardSector = card.dataset.sector || "";
      var cardCluster = card.dataset.cluster || "";
      var cardVibe = card.dataset.vibe || "";
      var cardIndustries = card.dataset.industries || "";
      var queryMatch = !query || searchBlob.indexOf(query) !== -1;
      var sectorMatch = !sector || cardSector === sector;
      var clusterMatch = !cluster || cardCluster === cluster;
      var vibeMatch = !vibe || cardVibe === vibe;
      var industryMatch = matchesIndustry(cardIndustries, industry);
      var show = queryMatch && sectorMatch && clusterMatch && vibeMatch && industryMatch;
      card.hidden = !show;
      if (show) {
        visible += 1;
      }
    });

    updateCount(visible);
    syncQueryString();
  }

  function applyFiltersFromURL() {
    var params = new URLSearchParams(window.location.search);

    if (input && params.get("q")) {
      input.value = params.get("q");
    }
    if (sectorFilter && params.get("sector")) {
      sectorFilter.value = params.get("sector");
    }
    if (clusterFilter && params.get("cluster")) {
      clusterFilter.value = params.get("cluster");
    }
    if (vibeFilter && params.get("vibe")) {
      vibeFilter.value = params.get("vibe");
    }
    if (industryFilter && params.get("industry")) {
      industryFilter.value = params.get("industry");
    }
  }

  if (input) {
    input.addEventListener("input", filterCards);
  }
  if (sectorFilter) {
    sectorFilter.addEventListener("change", filterCards);
  }
  if (clusterFilter) {
    clusterFilter.addEventListener("change", filterCards);
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
      if (sectorFilter) {
        sectorFilter.value = "";
      }
      if (clusterFilter) {
        clusterFilter.value = "";
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

  applyFiltersFromURL();
  updateCount(palettes.length);
  filterCards();
})();
