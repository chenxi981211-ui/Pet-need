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

  /* ---------- Catalog search + category filter ---------- */
  var grid = document.querySelector("[data-catalog]");
  if (grid) {
    var items = Array.prototype.slice.call(grid.querySelectorAll("[data-product]"));
    var input = document.querySelector("[data-catalog-search]");
    var chips = Array.prototype.slice.call(document.querySelectorAll("[data-filter]"));
    var counter = document.querySelector("[data-count]");
    var empty = document.querySelector("[data-empty]");
    var activeCat = "all";
    var activePet = "all";
    var term = "";

    function norm(s) {
      return (s || "").toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "");
    }

    function apply() {
      var shown = 0;
      items.forEach(function (el) {
        var matchesCat = activeCat === "all" || el.dataset.category === activeCat;
        var matchesPet = activePet === "all" || (" " + el.dataset.pet + " ").indexOf(" " + activePet + " ") !== -1;
        var matchesTerm = !term || norm(el.dataset.search).indexOf(term) !== -1;
        var visible = matchesCat && matchesPet && matchesTerm;
        el.classList.toggle("hide", !visible);
        if (visible) shown++;
      });
      if (counter) counter.textContent = shown + (shown === 1 ? " product" : " producten");
      if (empty) empty.classList.toggle("hide", shown !== 0);
    }

    if (input) {
      input.addEventListener("input", function () {
        term = norm(input.value.trim());
        apply();
      });
    }

    chips.forEach(function (chip) {
      chip.addEventListener("click", function () {
        activeCat = chip.dataset.filter;
        activePet = "all";
        chips.forEach(function (c) { c.setAttribute("aria-pressed", String(c === chip)); });
        if (heading) heading.textContent = chip.dataset.filter === "all" ? "Het hele assortiment" : chip.textContent;
        apply();
      });
    });

    // Deep links: ?categorie=<slug> (category chip) and ?dier=<hond|kat|knaagdier|vogel>
    var params = new URLSearchParams(window.location.search);
    var catParam = params.get("categorie");
    var petParam = params.get("dier");
    var heading = document.querySelector("[data-catalog-title]");

    if (catParam) {
      var match = chips.filter(function (c) { return c.dataset.filter === catParam; })[0];
      if (match) match.click();
      else apply();
    } else if (petParam) {
      activePet = petParam;
      if (heading) {
        var labels = { hond: "Voor de hond", kat: "Voor de kat", knaagdier: "Voor knaagdieren", vogel: "Voor vogels" };
        heading.textContent = labels[petParam] || heading.textContent;
      }
      apply();
    } else {
      apply();
    }
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
  var DELAY = 5200;

  function show(next) {
    index = (next + slides.length) % slides.length;
    slides.forEach(function (slide, i) { slide.classList.toggle("is-active", i === index); });
    dots.forEach(function (dot, i) {
      dot.classList.toggle("is-active", i === index);
      dot.setAttribute("aria-selected", String(i === index));
    });
  }

  function start() {
    if (timer) return;
    timer = setInterval(function () { show(index + 1); }, DELAY);
  }

  function stop() {
    clearInterval(timer);
    timer = null;
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
