/* Superiso Studio — shared behaviour: mobile nav, work filters, gallery lightbox. */
(function () {
  'use strict';

  /* --- Mobile navigation ------------------------------------------------ */
  var toggle = document.querySelector('.mobile-toggle');
  var menu = document.querySelector('.mobile-nav');

  if (toggle && menu) {
    var setMenu = function (open) {
      toggle.setAttribute('aria-expanded', String(open));
      menu.classList.toggle('is-open', open);
      menu.inert = !open;
      toggle.innerHTML = open
        ? 'Close <span aria-hidden="true">&times;</span>'
        : 'Menu <span aria-hidden="true">&#9776;</span>';
    };
    toggle.addEventListener('click', function () {
      setMenu(toggle.getAttribute('aria-expanded') !== 'true');
    });
    menu.querySelectorAll('a').forEach(function (a) {
      a.addEventListener('click', function () { setMenu(false); });
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && toggle.getAttribute('aria-expanded') === 'true') {
        setMenu(false);
        toggle.focus();
      }
    });
    window.matchMedia('(min-width:701px)').addEventListener('change', function () {
      setMenu(false);
    });
  }

  /* --- Work index filters ----------------------------------------------- */
  var filterBar = document.querySelector('.filters');

  if (filterBar) {
    var items = Array.prototype.slice.call(document.querySelectorAll('.index-item'));
    var counter = document.querySelector('.filter-count');
    var empty = document.querySelector('.no-results');

    var apply = function (key) {
      var shown = 0;
      items.forEach(function (item) {
        var tags = (item.dataset.scope || '').split(' ');
        var match = key === 'all' || tags.indexOf(key) !== -1;
        item.hidden = !match;
        if (match) shown++;
      });
      if (counter) {
        counter.textContent = shown + (shown === 1 ? ' project' : ' projects');
      }
      if (empty) empty.hidden = shown !== 0;
      // Reflect the filter in the URL so a filtered view can be linked or reloaded.
      var url = new URL(window.location.href);
      if (key === 'all') url.searchParams.delete('filter');
      else url.searchParams.set('filter', key);
      history.replaceState(null, '', url);
    };

    filterBar.addEventListener('click', function (e) {
      var btn = e.target.closest('.filter-btn');
      if (!btn) return;
      filterBar.querySelectorAll('.filter-btn').forEach(function (b) {
        b.setAttribute('aria-pressed', String(b === btn));
      });
      apply(btn.dataset.filter);
    });

    // Restore a filter passed in the URL on load.
    var initial = new URL(window.location.href).searchParams.get('filter');
    if (initial) {
      var target = filterBar.querySelector('.filter-btn[data-filter="' + CSS.escape(initial) + '"]');
      if (target) target.click();
    }
  }

  /* --- Gallery lightbox -------------------------------------------------- */
  var gallery = document.querySelector('.gallery');
  var box = document.querySelector('.lightbox');

  if (gallery && box) {
    var shots = Array.prototype.slice.call(gallery.querySelectorAll('.shot button'));
    var boxImg = box.querySelector('img');
    var boxCap = box.querySelector('figcaption');
    var boxCount = box.querySelector('.lb-count');
    var index = 0;
    var lastFocus = null;

    var show = function (i) {
      index = (i + shots.length) % shots.length;
      var source = shots[index].querySelector('img');
      // Prefer the largest rendition the <img> offers, falling back to its src.
      var srcset = source.getAttribute('srcset');
      var best = source.currentSrc || source.src;
      if (srcset) {
        var candidates = srcset.split(',').map(function (part) {
          var bits = part.trim().split(/\s+/);
          return { url: bits[0], w: parseInt(bits[1], 10) || 0 };
        });
        candidates.sort(function (a, b) { return b.w - a.w; });
        if (candidates.length) best = candidates[0].url;
      }
      boxImg.src = best;
      boxImg.hidden = false;
      boxImg.alt = source.alt;
      boxCap.textContent = source.alt;
      boxCount.textContent = (index + 1) + ' / ' + shots.length;
      box.classList.toggle('is-flat', shots[index].closest('.shot').classList.contains('is-flat'));
    };

    var open = function (i) {
      lastFocus = document.activeElement;
      show(i);
      box.hidden = false;
      document.body.style.overflow = 'hidden';
      box.querySelector('.lb-close').focus();
    };

    var close = function () {
      box.hidden = true;
      document.body.style.overflow = '';
      if (lastFocus) lastFocus.focus();
    };

    shots.forEach(function (btn, i) {
      btn.addEventListener('click', function () { open(i); });
    });

    box.querySelector('.lb-close').addEventListener('click', close);
    box.querySelector('.lb-prev').addEventListener('click', function () { show(index - 1); });
    box.querySelector('.lb-next').addEventListener('click', function () { show(index + 1); });
    box.addEventListener('click', function (e) {
      if (e.target === box) close();
    });

    document.addEventListener('keydown', function (e) {
      if (box.hidden) return;
      if (e.key === 'Escape') close();
      else if (e.key === 'ArrowLeft') show(index - 1);
      else if (e.key === 'ArrowRight') show(index + 1);
      else if (e.key === 'Tab') {
        // Keep focus inside the lightbox while it is open.
        var focusable = box.querySelectorAll('button');
        var first = focusable[0];
        var last = focusable[focusable.length - 1];
        if (e.shiftKey && document.activeElement === first) {
          e.preventDefault(); last.focus();
        } else if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault(); first.focus();
        }
      }
    });
  }
})();
