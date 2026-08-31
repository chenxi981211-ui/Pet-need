/* ==========================================================================
   Pet Needs — winkelwagen
   Bewaart de bestelling in localStorage, vult de lade in de header en
   bouwt op bestellen.html het overzicht + het WhatsApp-bericht.
   Geen backend: de klant verstuurt zijn bestelling zelf via WhatsApp.
   ========================================================================== */
(function () {
  "use strict";

  var KEY = "petneeds.cart.v1";
  var WA_NUMBER = "31610837512";
  var BASE = document.body.getAttribute("data-base") || "";           // root, voor afbeeldingen
  var LINK = document.body.getAttribute("data-link-base") || BASE;    // taalmap, voor paginalinks
  var I18N = window.PN_I18N || {};

  function s(key, vars) {
    var value = I18N[key] || key;
    if (vars) {
      Object.keys(vars).forEach(function (name) {
        value = value.replace("{" + name + "}", vars[name]);
      });
    }
    return value;
  }

  /* ---------------- state ---------------- */
  function read() {
    try {
      var raw = localStorage.getItem(KEY);
      var items = raw ? JSON.parse(raw) : [];
      return Array.isArray(items) ? items.filter(validItem) : [];
    } catch (err) {
      return [];
    }
  }

  function validItem(i) {
    return i && typeof i.sku === "string" && typeof i.name === "string" && i.qty > 0;
  }

  function save(items) {
    try {
      localStorage.setItem(KEY, JSON.stringify(items));
    } catch (err) {
      /* private mode / vol geheugen: de winkelwagen leeft dan alleen in deze pagina */
    }
    state = items;
    render();
  }

  var state = read();

  /* ---------------- helpers ---------------- */
  function money(value) {
    return "€ " + value.toFixed(2).replace(".", ",");
  }

  function subtotal() {
    return state.reduce(function (sum, i) {
      return sum + (i.price ? i.price * i.qty : 0);
    }, 0);
  }

  function askCount() {
    return state.filter(function (i) { return !i.price; }).length;
  }

  function totalQty() {
    return state.reduce(function (sum, i) { return sum + i.qty; }, 0);
  }

  function add(item, qty) {
    var existing = state.filter(function (i) { return i.sku === item.sku; })[0];
    if (existing) {
      existing.qty = Math.min(99, existing.qty + qty);
    } else {
      state.push({
        sku: item.sku, name: item.name, price: item.price,
        image: item.image, url: item.url, qty: qty,
      });
    }
    save(state.slice());
  }

  function setQty(sku, qty) {
    state = state.filter(function (i) {
      if (i.sku !== sku) return true;
      i.qty = qty;
      return qty > 0;
    });
    save(state.slice());
  }

  function clear() { save([]); }

  /* ---------------- toast ---------------- */
  var toastEl = document.querySelector("[data-toast]");
  var toastTimer;
  function toast(message) {
    if (!toastEl) return;
    toastEl.textContent = message;
    toastEl.hidden = false;
    requestAnimationFrame(function () { toastEl.classList.add("is-visible"); });
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function () {
      toastEl.classList.remove("is-visible");
      setTimeout(function () { toastEl.hidden = true; }, 250);
    }, 2600);
  }

  /* ---------------- drawer ---------------- */
  var panel = document.querySelector("[data-cart-panel]");
  var backdrop = document.querySelector("[data-cart-backdrop]");
  var lastFocused = null;

  function openCart() {
    if (!panel) return;
    lastFocused = document.activeElement;
    panel.hidden = false;
    backdrop.hidden = false;
    requestAnimationFrame(function () {
      document.body.classList.add("cart-open");
      panel.setAttribute("aria-hidden", "false");
    });
    var close = panel.querySelector("[data-cart-close]");
    if (close) close.focus();
  }

  function closeCart() {
    if (!panel) return;
    document.body.classList.remove("cart-open");
    panel.setAttribute("aria-hidden", "true");
    setTimeout(function () {
      panel.hidden = true;
      backdrop.hidden = true;
    }, 280);
    if (lastFocused && lastFocused.focus) lastFocused.focus();
  }

  /* ---------------- rendering ---------------- */
  function p_ask() {
    return '<span class="price--ask">' + s("ask") + "</span>";
  }

  function lineMarkup(item) {
    var img = item.image
      ? '<img src="' + BASE + item.image + '" alt="" width="80" height="80" loading="lazy">'
      : '<span class="cart-line__ph"></span>';
    var price = item.price
      ? money(item.price * item.qty)
      : p_ask();
    return '' +
      '<li class="cart-line" data-line="' + item.sku + '">' +
        '<a class="cart-line__media" href="' + LINK + item.url + '">' + img + '</a>' +
        '<div class="cart-line__body">' +
          '<a class="cart-line__name" href="' + LINK + item.url + '">' + item.name + '</a>' +
          '<div class="cart-line__row">' +
            '<div class="qty qty--sm">' +
              '<button type="button" class="qty__btn" data-line-minus aria-label="' + s("qty_less") + '">&minus;</button>' +
              '<span class="qty__value" aria-live="polite">' + item.qty + '</span>' +
              '<button type="button" class="qty__btn" data-line-plus aria-label="' + s("qty_more") + '">+</button>' +
            '</div>' +
            '<span class="cart-line__price">' + price + '</span>' +
          '</div>' +
        '</div>' +
        '<button type="button" class="cart-line__remove" data-line-remove aria-label="' + s("remove", {name: item.name}) + '">&times;</button>' +
      '</li>';
  }

  function render() {
    var count = totalQty();

    // header badge
    Array.prototype.forEach.call(document.querySelectorAll("[data-cart-count]"), function (el) {
      el.textContent = String(count);
      el.hidden = count === 0;
    });

    // drawer
    var listHost = document.querySelector("[data-cart-items]");
    if (listHost) {
      if (!state.length) {
        listHost.innerHTML =
          '<div class="cart__empty">' +
            '<p><strong>' + s("empty_title") + '</strong></p>' +
            '<p class="muted">' + s("empty_body") + '</p>' +
            '<a class="btn btn--outline btn--sm" href="' + LINK + 'assortiment.html">' + s("empty_cta") + '</a>' +
          '</div>';
      } else {
        listHost.innerHTML = '<ul class="cart-lines">' + state.map(lineMarkup).join("") + '</ul>';
      }
      var foot = document.querySelector("[data-cart-foot]");
      if (foot) foot.hidden = !state.length;
      var totalEl = document.querySelector("[data-cart-total]");
      if (totalEl) totalEl.textContent = money(subtotal());
    }

    renderCheckout();
  }

  /* ---------------- checkout page ---------------- */
  function renderCheckout() {
    var host = document.querySelector("[data-checkout-items]");
    if (!host) return;

    var form = document.querySelector("[data-checkout-form]");
    var empty = document.querySelector("[data-checkout-empty]");
    var summary = document.querySelector("[data-summary]");
    var sent = document.querySelector("[data-checkout-sent]");
    var hasItems = state.length > 0;
    var sending = sent && !sent.hidden;

    host.innerHTML = hasItems ? '<ul class="cart-lines cart-lines--wide">' + state.map(lineMarkup).join("") + "</ul>" : "";
    if (empty) empty.hidden = hasItems;
    if (form) form.hidden = !hasItems || sending;
    if (summary) summary.hidden = !hasItems;

    var lines = document.querySelector("[data-summary-lines]");
    if (lines) {
      lines.innerHTML = state.map(function (i) {
        return '<li><span>' + i.qty + '× ' + i.name + "</span><span>" +
          (i.price ? money(i.price * i.qty) : s("ask")) + "</span></li>";
      }).join("");
    }
    var totalEl = document.querySelector("[data-summary-total]");
    if (totalEl) totalEl.textContent = money(subtotal());

    var note = document.querySelector("[data-summary-note]");
    if (note) {
      var ask = askCount();
      note.hidden = ask === 0;
      note.textContent = ask === 1 ? s("one_ask") : s("more_ask", { count: ask });
    }
  }

  /* ---------------- order message ---------------- */
  function orderText(data) {
    var lines = [s("order_intro"), ""];
    state.forEach(function (i) {
      lines.push("• " + i.qty + "× " + i.name + " (" + i.sku + ") — " +
        (i.price ? money(i.price * i.qty) : s("ask_price")));
    });
    lines.push("");
    lines.push(s("order_subtotal") + ": " + money(subtotal()) + (askCount() ? " " + s("order_excl") : ""));
    lines.push("");
    lines.push(s("order_name") + ": " + data.naam);
    lines.push(s("order_phone") + ": " + data.telefoon);
    if (data.email) lines.push(s("order_email") + ": " + data.email);
    if (data.levering === "bezorgen") {
      lines.push(s("order_delivery") + ": " + data.adres + ", " + data.postcode + " " + data.plaats);
      lines.push(s("order_day") + ": " + data.dag);
    } else {
      lines.push(s("order_pickup"));
    }
    if (data.opmerking) {
      lines.push("");
      lines.push(s("order_note") + ": " + data.opmerking);
    }
    return lines.join("\n");
  }

  /* ---------------- events ---------------- */
  document.addEventListener("click", function (event) {
    var addBtn = event.target.closest("[data-add-to-cart]");
    if (addBtn) {
      var qtyInput = document.querySelector("[data-qty-input]");
      var qty = addBtn.closest(".pdp__actions") && qtyInput ? Math.max(1, parseInt(qtyInput.value, 10) || 1) : 1;
      var priceRaw = addBtn.getAttribute("data-price");
      add({
        sku: addBtn.getAttribute("data-sku"),
        name: addBtn.getAttribute("data-name"),
        price: priceRaw ? parseFloat(priceRaw) : null,
        image: addBtn.getAttribute("data-image") || "",
        url: addBtn.getAttribute("data-url"),
      }, qty);
      toast(s("added", { qty: qty, name: addBtn.getAttribute("data-name") }));
      addBtn.classList.add("is-added");
      setTimeout(function () { addBtn.classList.remove("is-added"); }, 900);
      if (!document.querySelector("[data-checkout-items]")) openCart();
      return;
    }

    if (event.target.closest("[data-cart-open]")) { openCart(); return; }
    if (event.target.closest("[data-cart-close]") || event.target.closest("[data-cart-backdrop]")) { closeCart(); return; }
    if (event.target.closest("[data-cart-clear]")) { clear(); toast(s("cleared")); return; }

    var line = event.target.closest("[data-line]");
    if (line) {
      var sku = line.getAttribute("data-line");
      var item = state.filter(function (i) { return i.sku === sku; })[0];
      if (!item) return;
      if (event.target.closest("[data-line-plus]")) setQty(sku, Math.min(99, item.qty + 1));
      else if (event.target.closest("[data-line-minus]")) setQty(sku, item.qty - 1);
      else if (event.target.closest("[data-line-remove]")) { setQty(sku, 0); toast(s("removed", { name: item.name })); }
      return;
    }

    if (event.target.closest("[data-clear-after-send]")) {
      clear();
      var sent = document.querySelector("[data-checkout-sent]");
      if (sent) sent.hidden = true;
      renderCheckout();
      toast(s("thanks"));
      return;
    }
    if (event.target.closest("[data-back-to-form]")) {
      var sentPanel = document.querySelector("[data-checkout-sent]");
      if (sentPanel) sentPanel.hidden = true;
      renderCheckout();
      return;
    }
  });

  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape" && document.body.classList.contains("cart-open")) closeCart();
  });

  /* quantity stepper on the product page */
  var qtyWrap = document.querySelector("[data-qty]");
  if (qtyWrap) {
    var input = qtyWrap.querySelector("[data-qty-input]");
    qtyWrap.addEventListener("click", function (event) {
      var step = event.target.closest("[data-qty-plus]") ? 1 : (event.target.closest("[data-qty-minus]") ? -1 : 0);
      if (!step) return;
      var next = Math.min(99, Math.max(1, (parseInt(input.value, 10) || 1) + step));
      input.value = next;
    });
  }

  /* checkout form */
  var form = document.querySelector("[data-checkout-form]");
  if (form) {
    var deliveryFields = document.querySelector("[data-delivery-fields]");

    form.addEventListener("change", function (event) {
      if (event.target.name === "levering") {
        deliveryFields.hidden = event.target.value !== "bezorgen";
      }
    });

    function collect() {
      var fd = new FormData(form);
      var data = {};
      fd.forEach(function (value, key) { data[key] = String(value).trim(); });
      return data;
    }

    function validate(data) {
      var errors = {};
      if (!data.naam) errors.naam = s("err_name");
      if (!data.telefoon) errors.telefoon = s("err_phone");
      else if (data.telefoon.replace(/\D/g, "").length < 8) errors.telefoon = s("err_phone_short");
      if (data.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(data.email)) errors.email = s("err_email");
      if (data.levering === "bezorgen") {
        if (!data.adres) errors.adres = s("err_street");
        if (!data.postcode) errors.postcode = s("err_zip");
        if (!data.plaats) errors.plaats = s("err_city");
      }
      return errors;
    }

    function showErrors(errors) {
      Array.prototype.forEach.call(form.querySelectorAll("[data-error]"), function (el) {
        el.textContent = "";
        el.closest(".field").classList.remove("field--invalid");
      });
      var first = null;
      Object.keys(errors).forEach(function (name) {
        var input = form.querySelector('[name="' + name + '"]');
        if (!input) return;
        var field = input.closest(".field");
        field.classList.add("field--invalid");
        var msg = field.querySelector("[data-error]");
        if (msg) msg.textContent = errors[name];
        if (!first) first = input;
      });
      if (first) first.focus();
    }

    form.addEventListener("submit", function (event) {
      event.preventDefault();
      if (!state.length) return;
      var data = collect();
      var errors = validate(data);
      if (Object.keys(errors).length) { showErrors(errors); return; }
      showErrors({});
      window.open("https://wa.me/" + WA_NUMBER + "?text=" + encodeURIComponent(orderText(data)), "_blank", "noopener");
      var sent = document.querySelector("[data-checkout-sent]");
      if (sent) sent.hidden = false;
      form.hidden = true;
    });

    var copyBtn = document.querySelector("[data-copy-order]");
    if (copyBtn) {
      copyBtn.addEventListener("click", function () {
        var data = collect();
        var text = orderText(data);
        if (navigator.clipboard && navigator.clipboard.writeText) {
          navigator.clipboard.writeText(text).then(
            function () { toast(s("copied")); },
            function () { window.prompt(s("copy_prompt"), text); }
          );
        } else {
          window.prompt(s("copy_prompt"), text);
        }
      });
    }
  }

  /* andere tabbladen houden dezelfde winkelwagen aan */
  window.addEventListener("storage", function (event) {
    if (event.key === KEY) { state = read(); render(); }
  });

  render();
})();
