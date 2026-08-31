/* Pet Needs — site behaviour: mobile nav, scroll reveals, catalog search/filter */
(function () {
  "use strict";

  /* ---------- Mobile navigation ---------- */
  var toggle = document.querySelector("[data-nav-toggle]");
  var nav = document.querySelector("[data-nav]");
  if (toggle && nav) {
    toggle.addEventListener("click", function () {
      var open = document.body.classList.toggle("nav-open");
      toggle.setAttribute("aria-expanded", String(open));
    });
    nav.addEventListener("click", function (e) {
      if (e.target.closest("a")) {
        document.body.classList.remove("nav-open");
        toggle.setAttribute("aria-expanded", "false");
      }
    });
    document.addEventListener("click", function (e) {
      if (!document.body.classList.contains("nav-open")) return;
      if (nav.contains(e.target) || toggle.contains(e.target)) return;
      document.body.classList.remove("nav-open");
      toggle.setAttribute("aria-expanded", "false");
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && document.body.classList.contains("nav-open")) {
        document.body.classList.remove("nav-open");
        toggle.setAttribute("aria-expanded", "false");
        toggle.focus();
      }
    });
  }

  /* ---------- Reveal on scroll ---------- */
  var revealables = document.querySelectorAll(".reveal");
  if (revealables.length) {
    if (!("IntersectionObserver" in window)) {
      revealables.forEach(function (el) { el.classList.add("is-visible"); });
    } else {
      var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-visible");
            io.unobserve(entry.target);
          }
        });
      }, { rootMargin: "0px 0px -8% 0px", threshold: 0.05 });
      revealables.forEach(function (el) { io.observe(el); });
    }
  }

  /* ---------- Catalog: dier-tabs, categoriechips, zoeken ---------- */
  var grid = document.querySelector("[data-catalog]");
  if (grid) {
    var STR = window.PN_I18N || {};
    var items = Array.prototype.slice.call(grid.querySelectorAll("[data-product]"));
    var tabs = Array.prototype.slice.call(document.querySelectorAll("[data-pet-tab]"));
    var chips = Array.prototype.slice.call(document.querySelectorAll("[data-filter]"));
    var input = document.querySelector("[data-catalog-search]");
    var counter = document.querySelector("[data-count]");
    var heading = document.querySelector("[data-catalog-title]");
    var empty = document.querySelector("[data-empty]");
    var clearBtn = document.querySelector("[data-clear-filters]");

    var state = { pet: "all", cat: "all", term: "" };

    function norm(value) {
      return (value || "").toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
    }

    function matches(el) {
      var okPet = state.pet === "all" || (" " + el.dataset.pet + " ").indexOf(" " + state.pet + " ") !== -1;
      var okCat = state.cat === "all" || el.dataset.category === state.cat;
      var okTerm = !state.term || norm(el.dataset.search).indexOf(state.term) !== -1;
      return okPet && okCat && okTerm;
    }

    function label(count) {
      var word = count === 1 ? (STR.product_one || "product") : (STR.product_many || "producten");
      return count + " " + word;
    }

    function syncChips() {
      // laat alleen categorieën zien die bij het gekozen dier horen
      chips.forEach(function (chip) {
        var pets = chip.dataset.pets || "";
        var relevant = state.pet === "all" || chip.dataset.filter === "all" ||
          (" " + pets + " ").indexOf(" " + state.pet + " ") !== -1;
        chip.classList.toggle("hide", !relevant);
        chip.setAttribute("aria-pressed", String(chip.dataset.filter === state.cat));
      });
      tabs.forEach(function (tab) {
        var active = tab.dataset.petTab === state.pet;
        tab.classList.toggle("is-active", active);
        tab.setAttribute("aria-pressed", String(active));
        if (active && tab.parentNode.scrollWidth > tab.parentNode.clientWidth) {
          // op smalle schermen schuift de actieve tab in beeld
          tab.parentNode.scrollTo({
            left: Math.max(0, tab.offsetLeft - 16),
            behavior: "smooth",
          });
        }
      });
    }

    function syncUrl() {
      if (!window.history || !history.replaceState) return;
      var params = new URLSearchParams();
      if (state.pet !== "all") params.set("dier", state.pet);
      if (state.cat !== "all") params.set("categorie", state.cat);
      var query = params.toString();
      history.replaceState(null, "", query ? "?" + query : location.pathname);
    }

    function syncHeading() {
      if (!heading) return;
      if (state.cat !== "all") {
        var chip = chips.filter(function (c) { return c.dataset.filter === state.cat; })[0];
        if (chip) heading.textContent = chip.childNodes[0].textContent.trim();
        return;
      }
      var tab = tabs.filter(function (tb) { return tb.dataset.petTab === state.pet; })[0];
      heading.textContent = tab ? tab.dataset.title : (STR.all_products || heading.textContent);
    }

    function apply() {
      var shown = 0;
      items.forEach(function (el) {
        var visible = matches(el);
        el.classList.toggle("hide", !visible);
        if (visible) shown++;
      });
      if (counter) counter.textContent = label(shown);
      if (empty) empty.classList.toggle("hide", shown !== 0);
      if (clearBtn) {
        var filtering = state.pet !== "all" || state.cat !== "all" || state.term !== "";
        clearBtn.classList.toggle("hide", !filtering);
      }
      syncChips();
      syncHeading();
    }

    tabs.forEach(function (tab) {
      tab.addEventListener("click", function () {
        state.pet = tab.dataset.petTab;
        // categorie loslaten als die niet bij het gekozen dier hoort
        var chip = chips.filter(function (c) { return c.dataset.filter === state.cat; })[0];
        if (chip && state.pet !== "all" &&
            (" " + (chip.dataset.pets || "") + " ").indexOf(" " + state.pet + " ") === -1) {
          state.cat = "all";
        }
        apply();
        syncUrl();
      });
    });

    chips.forEach(function (chip) {
      chip.addEventListener("click", function () {
        state.cat = chip.dataset.filter;
        apply();
        syncUrl();
      });
    });

    if (input) {
      input.addEventListener("input", function () {
        state.term = norm(input.value.trim());
        apply();
      });
    }

    if (clearBtn) {
      clearBtn.addEventListener("click", function () {
        state = { pet: "all", cat: "all", term: "" };
        if (input) input.value = "";
        apply();
        syncUrl();
      });
    }

    // beginstand uit de URL: ?dier=hond en/of ?categorie=slug
    var params = new URLSearchParams(window.location.search);
    var petParam = params.get("dier");
    var catParam = params.get("categorie");
    if (petParam && tabs.some(function (tb) { return tb.dataset.petTab === petParam; })) state.pet = petParam;
    if (catParam && chips.some(function (c) { return c.dataset.filter === catParam; })) state.cat = catParam;
    apply();
  }

  /* ---------- Header shadow on scroll ---------- */
  var header = document.querySelector(".site-header");
  if (header) {
    var onScroll = function () {
      header.style.boxShadow = window.scrollY > 8 ? "0 6px 24px rgba(35,32,29,.08)" : "none";
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    onScroll();
  }

  /* ---------- Current year in footer ---------- */
  var year = document.querySelector("[data-year]");
  if (year) year.textContent = String(new Date().getFullYear());
})();

/* ---------- Hero slideshow (rabbit → guinea pig → dog → cat) ---------- */
(function () {
  "use strict";
  var slider = document.querySelector("[data-hero-slider]");
  if (!slider) return;

  var slides = Array.prototype.slice.call(slider.querySelectorAll(".hero__slide"));
  var dots = Array.prototype.slice.call(slider.querySelectorAll("[data-hero-dot]"));
  if (slides.length < 2) return;

  var index = 0;
  var timer = null;
  var DELAY = 3000;
  var progress = slider.querySelector("[data-hero-progress]");
  if (progress) progress.style.setProperty("--hero-delay", DELAY + "ms");

  function show(next) {
    index = (next + slides.length) % slides.length;
    slides.forEach(function (slide, i) { slide.classList.toggle("is-active", i === index); });
    dots.forEach(function (dot, i) {
      dot.classList.toggle("is-active", i === index);
      dot.setAttribute("aria-selected", String(i === index));
    });
    restartProgress();
  }

  function restartProgress() {
    if (!progress) return;
    progress.classList.remove("is-running");
    void progress.offsetWidth;          // forceer een reflow zodat de animatie opnieuw start
    if (timer) progress.classList.add("is-running");
  }

  function start() {
    if (timer) return;
    timer = setInterval(function () { show(index + 1); }, DELAY);
    restartProgress();
  }

  function stop() {
    clearInterval(timer);
    timer = null;
    if (progress) progress.classList.remove("is-running");
  }

  dots.forEach(function (dot, i) {
    dot.addEventListener("click", function () {
      show(i);
      stop();
      start();
    });
  });

  slider.addEventListener("mouseenter", stop);
  slider.addEventListener("mouseleave", start);
  document.addEventListener("visibilitychange", function () {
    if (document.hidden) stop(); else start();
  });

  start();
})();
