(function() {
  'use strict';

  /* ════════════════════════════════════════════════════════
     CHRONOCHROM — Tiroler Tageszeit-Farbmotor V1
     7 Phasen, interpoliert via Gaußsche Gewichtung.
     Setzt data-tod + interpolierte CSS-Vars auf :root.
     Alle 10 Minuten Re-Evaluierung.
     3-State Button: auto → Tag → Nacht → auto
     ════════════════════════════════════════════════════════ */

  /* ─── 1. PHASEN-DEFINITIONEN ─── */
  // peak = Uhrzeit des stärksten Einflusses (0-24)
  // Hex-Farben + rgba Opazitäten für 15 interpoliere Variablen
  var PHASES = [
    { id: 'deepnight', peak: 2.0,
      bg:'#05050A', bg2:'#0A0A14', text:'#B8B8C8', text2:'rgba(184,184,200,.45)', text3:'rgba(184,184,200,.20)',
      pink:'#CC1175', pinkDark:'#A00E5E', pinkGlow:'rgba(255,20,147,.08)',
      gold:'#B89600', goldLight:'#D4A800', goldGlow:'rgba(212,168,0,.08)', goldSoft:'rgba(212,168,0,.04)',
      glass:'rgba(255,255,255,.04)', glassBorder:'rgba(255,255,255,.04)',
      surface:'rgba(255,255,255,.02)', surfaceHover:'rgba(255,255,255,.05)',
      yellow:'#D4A800', blue:'#0051BA' },

    { id: 'dawn', peak: 5.5,
      bg:'#1A0E12', bg2:'#22181C', text:'#C8B8B8', text2:'rgba(200,184,184,.50)', text3:'rgba(200,184,184,.22)',
      pink:'#D43080', pinkDark:'#A82666', pinkGlow:'rgba(212,48,128,.10)',
      gold:'#C8A000', goldLight:'#D4A800', goldGlow:'rgba(200,160,0,.12)', goldSoft:'rgba(200,160,0,.05)',
      glass:'rgba(255,255,255,.05)', glassBorder:'rgba(255,255,255,.05)',
      surface:'rgba(255,255,255,.03)', surfaceHover:'rgba(255,255,255,.06)',
      yellow:'#D4A800', blue:'#0051BA' },

    { id: 'sunrise', peak: 7.5,
      bg:'#3A2A1A', bg2:'#42301E', text:'#D8C8B0', text2:'rgba(216,200,176,.55)', text3:'rgba(216,200,176,.25)',
      pink:'#E85090', pinkDark:'#C04074', pinkGlow:'rgba(232,80,144,.12)',
      gold:'#D4B000', goldLight:'#FFD700', goldGlow:'rgba(212,176,0,.18)', goldSoft:'rgba(212,176,0,.07)',
      glass:'rgba(255,255,255,.06)', glassBorder:'rgba(255,255,255,.06)',
      surface:'rgba(255,255,255,.04)', surfaceHover:'rgba(255,255,255,.08)',
      yellow:'#FFD700', blue:'#0051BA' },

    { id: 'noon', peak: 13.0,
      bg:'#F5F3F0', bg2:'#EDE8E2', text:'#1A1A1A', text2:'rgba(0,0,0,.60)', text3:'rgba(0,0,0,.38)',
      pink:'#FF1493', pinkDark:'#C0006E', pinkGlow:'rgba(255,20,147,.12)',
      gold:'#D4A800', goldLight:'#FFD700', goldGlow:'rgba(212,168,0,.18)', goldSoft:'rgba(212,168,0,.08)',
      glass:'rgba(255,255,255,.70)', glassBorder:'rgba(0,0,0,.06)',
      surface:'rgba(0,0,0,.03)', surfaceHover:'rgba(0,0,0,.06)',
      yellow:'#FFD700', blue:'#0051BA' },

    { id: 'afternoon', peak: 16.5,
      bg:'#E8E0D4', bg2:'#E0D6C8', text:'#2A2220', text2:'rgba(42,34,32,.55)', text3:'rgba(42,34,32,.32)',
      pink:'#F02090', pinkDark:'#C01A72', pinkGlow:'rgba(240,32,144,.14)',
      gold:'#D0A800', goldLight:'#FFD700', goldGlow:'rgba(208,168,0,.20)', goldSoft:'rgba(208,168,0,.09)',
      glass:'rgba(255,255,255,.65)', glassBorder:'rgba(0,0,0,.06)',
      surface:'rgba(0,0,0,.04)', surfaceHover:'rgba(0,0,0,.07)',
      yellow:'#FFD700', blue:'#0051BA' },

    { id: 'sunset', peak: 18.5,
      bg:'#2A1A0A', bg2:'#322010', text:'#E8D4B8', text2:'rgba(232,212,184,.50)', text3:'rgba(232,212,184,.22)',
      pink:'#FF6B9D', pinkDark:'#CC5580', pinkGlow:'rgba(255,107,157,.15)',
      gold:'#E8A800', goldLight:'#FFD700', goldGlow:'rgba(232,168,0,.25)', goldSoft:'rgba(232,168,0,.12)',
      glass:'rgba(255,255,255,.05)', glassBorder:'rgba(255,255,255,.07)',
      surface:'rgba(255,255,255,.04)', surfaceHover:'rgba(255,255,255,.07)',
      yellow:'#FFD700', blue:'#0066FF' },

    { id: 'twilight', peak: 21.5,
      bg:'#0E0A1A', bg2:'#161022', text:'#D0C8D8', text2:'rgba(208,200,216,.48)', text3:'rgba(208,200,216,.20)',
      pink:'#CC2090', pinkDark:'#A01A72', pinkGlow:'rgba(204,32,144,.10)',
      gold:'#B89000', goldLight:'#D4A800', goldGlow:'rgba(184,144,0,.10)', goldSoft:'rgba(184,144,0,.05)',
      glass:'rgba(255,255,255,.04)', glassBorder:'rgba(255,255,255,.05)',
      surface:'rgba(255,255,255,.03)', surfaceHover:'rgba(255,255,255,.06)',
      yellow:'#D4A800', blue:'#0066FF' }
  ];

  // Sigma steuert die Überlappungsbreite: höher = weichere Übergänge
  var SIGMA_SQ = 6.0; // σ²=6 → ~50% Einflussradius ~3h

  /* ─── 2. FARB-HELFER ─── */
  function hexToRgb(hex) {
    var r = parseInt(hex.slice(1,3), 16);
    var g = parseInt(hex.slice(3,5), 16);
    var b = parseInt(hex.slice(5,7), 16);
    return [r, g, b];
  }

  function rgbToHex(r, g, b) {
    return '#' + [Math.round(r), Math.round(g), Math.round(b)]
      .map(function(c) { return Math.max(0, Math.min(255, c)).toString(16).padStart(2, '0'); })
      .join('');
  }

  function parseRgba(str) {
    var m = str.match(/rgba\((\d+),\s*(\d+),\s*(\d+),\s*([\d.]+)\)/);
    if (m) return { r: +m[1], g: +m[2], b: +m[3], a: +m[4] };
    // Fallback: rgb(r,g,b)
    m = str.match(/rgb\((\d+),\s*(\d+),\s*(\d+)\)/);
    if (m) return { r: +m[1], g: +m[2], b: +m[3], a: 1.0 };
    return { r: 0, g: 0, b: 0, a: 1.0 };
  }

  function rgbaToString(r, g, b, a) {
    return 'rgba(' + Math.round(r) + ',' + Math.round(g) + ',' + Math.round(b) + ',' + a.toFixed(3) + ')';
  }

  /* ─── 3. INTERPOLATIONS-MOTOR ─── */
  // Für eine gegebene Stunde: berechne GAUSS-Gewichte für alle 7 Phasen,
  // normalisiere, dann interpoliere jede Farb-Variable als gewichteten Durchschnitt.

  function getTirolHour() {
    var now = new Date();
    var tirolTime = now.toLocaleString('de-AT', { timeZone: 'Europe/Vienna' });
    var tirolDate = new Date(tirolTime);
    return tirolDate.getHours() + tirolDate.getMinutes() / 60 + tirolDate.getSeconds() / 3600;
  }

  function computeInterpolatedColors(hour) {
    // 1. Gauß-Gewichte
    var weights = PHASES.map(function(p) {
      var diff = hour - p.peak;
      // Zirkuläre Distanz (über Mitternacht hinweg)
      if (diff > 12) diff = 24 - diff;
      if (diff < -12) diff = 24 + diff;
      return Math.exp(-(diff * diff) / SIGMA_SQ);
    });

    // 2. Normalisieren
    var total = weights.reduce(function(a, b) { return a + b; }, 0);
    if (total < 0.0001) { weights = weights.map(function() { return 1 / weights.length; }); total = 1; }
    else { weights = weights.map(function(w) { return w / total; }); }

    // 3. Phase mit höchstem Gewicht für data-tod
    var maxIdx = 0;
    for (var i = 1; i < weights.length; i++) { if (weights[i] > weights[maxIdx]) maxIdx = i; }
    var dominantPhase = PHASES[maxIdx].id;

    // 4. Farbvariablen interpoliert
    // Liste: alle Property-Namen die interpoliert werden
    var hexKeys = ['bg', 'bg2', 'text', 'pink', 'pinkDark', 'gold', 'goldLight', 'yellow', 'blue'];
    var rgbaKeys = [
      { key: 'text2', parse: function(v) { return parseRgba(v); }, format: rgbaToString },
      { key: 'text3', parse: function(v) { return parseRgba(v); }, format: rgbaToString },
      { key: 'pinkGlow', parse: function(v) { return parseRgba(v); }, format: rgbaToString },
      { key: 'goldGlow', parse: function(v) { return parseRgba(v); }, format: rgbaToString },
      { key: 'goldSoft', parse: function(v) { return parseRgba(v); }, format: rgbaToString },
      { key: 'glass', parse: function(v) { return parseRgba(v); }, format: rgbaToString },
      { key: 'glassBorder', parse: function(v) { return parseRgba(v); }, format: rgbaToString },
      { key: 'surface', parse: function(v) { return parseRgba(v); }, format: rgbaToString },
      { key: 'surfaceHover', parse: function(v) { return parseRgba(v); }, format: rgbaToString }
    ];

    var result = { dominant: dominantPhase };

    // Hex-Variablen interpolieren
    hexKeys.forEach(function(k) {
      var r = 0, g = 0, b = 0;
      PHASES.forEach(function(p, i) {
        var w = weights[i];
        if (w < 0.0001) return;
        var rgb = hexToRgb(p[k]);
        r += rgb[0] * w;
        g += rgb[1] * w;
        b += rgb[2] * w;
      });
      result[k] = rgbToHex(r, g, b);
    });

    // rgba-Variablen interpolieren
    rgbaKeys.forEach(function(item) {
      var kr = 0, kg = 0, kb = 0, ka = 0;
      PHASES.forEach(function(p, i) {
        var w = weights[i];
        if (w < 0.0001) return;
        var rgba = item.parse(p[item.key]);
        kr += rgba.r * w;
        kg += rgba.g * w;
        kb += rgba.b * w;
        ka += rgba.a * w;
      });
      result[item.key] = item.format(kr, kg, kb, ka);
    });

    return result;
  }

  /* ─── 4. CSS-VARS SETZEN ─── */
  function applyChronochrom(colors) {
    var root = document.documentElement;
    root.dataset.tod = colors.dominant;

    var map = {
      '--bg': colors.bg,
      '--bg2': colors.bg2,
      '--text': colors.text,
      '--text2': colors.text2,
      '--text3': colors.text3,
      '--pink': colors.pink,
      '--pink-dark': colors.pinkDark,
      '--pink-glow': colors.pinkGlow,
      '--gold': colors.gold,
      '--gold-light': colors.goldLight,
      '--gold-glow': colors.goldGlow,
      '--gold-soft': colors.goldSoft,
      '--glass': colors.glass,
      '--glass-border': colors.glassBorder,
      '--surface': colors.surface,
      '--surface-hover': colors.surfaceHover,
      '--yellow': colors.yellow,
      '--blue': colors.blue,
      '--tirol-pink': colors.pink,
      '--tirol-pink-dark': colors.pinkDark,
      '--tirol-pink-glow': colors.pinkGlow,
      '--pop-yellow': colors.yellow,
      '--ikea-blue': colors.blue
    };

    // Setze alle als inline Style auf :root
    for (var key in map) {
      if (map.hasOwnProperty(key)) {
        root.style.setProperty(key, map[key]);
      }
    }

    // Markiere als aktiv für CSS transitions
    root.classList.add('chrono-active');
  }

  /* ─── 5. TICK-FUNKTION (alle 10 min) ─── */
  var CHRONO_INTERVAL = 10 * 60 * 1000; // 10 Minuten

  function chronoTick() {
    var override = localStorage.getItem('tirol_auto_theme');
    if (override === 'day') {
      // Tag-Modus erzwingen
      var noon = PHASES[3]; // noon peak
      var colors = computeInterpolatedColors(noon.peak);
      applyChronochrom(colors);
      return;
    }
    if (override === 'night') {
      // Nacht-Modus erzwingen
      var night = PHASES[6]; // twilight peak
      var colors = computeInterpolatedColors(night.peak);
      applyChronochrom(colors);
      return;
    }

    // Auto-Modus
    var hour = getTirolHour();
    var colors = computeInterpolatedColors(hour);
    applyChronochrom(colors);
  }

  /* ─── 6. INIT + TICK-START ─── */
  // Beim Laden sofort ausführen
  chronoTick();
  // Alle 10 Minuten wiederholen
  setInterval(chronoTick, CHRONO_INTERVAL);

  /* ─── 7. 3-STATE TOGGLE ─── */
  (function initThemeToggle() {
    var toggleBtn = document.getElementById('themeToggle');
    if (!toggleBtn) return;

    // Migration: alter localStorage-Key 'tirol_theme' → 'tirol_auto_theme'
    var oldTheme = localStorage.getItem('tirol_theme');
    var newTheme = localStorage.getItem('tirol_auto_theme');
    if (oldTheme && !newTheme) {
      // 'night' → 'night', 'auto' → 'auto'
      localStorage.setItem('tirol_auto_theme', oldTheme === 'alpenpeak' ? 'night' : 'auto');
      localStorage.removeItem('tirol_theme');
    }

    // Aktuelle UI setzen
    var override = localStorage.getItem('tirol_auto_theme') || 'auto';
    updateToggleUI(override);

    // Klick-Handler
    toggleBtn.addEventListener('click', function() {
      var current = localStorage.getItem('tirol_auto_theme') || 'auto';
      var next = { auto: 'day', day: 'night', night: 'auto' }[current] || 'auto';
      localStorage.setItem('tirol_auto_theme', next);
      updateToggleUI(next);
      chronoTick(); // sofort anwenden
    });

    function updateToggleUI(mode) {
      if (!toggleBtn) return;
      if (mode === 'auto') {
        toggleBtn.innerHTML = '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="theme-sun"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>';
        toggleBtn.title = 'Auto-Modus (nach Uhrzeit)';
        toggleBtn.style.boxShadow = '0 0 0 2px var(--pink), 0 4px 20px var(--pink-glow)';
      } else if (mode === 'day') {
        toggleBtn.innerHTML = '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="theme-sun"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>';
        toggleBtn.title = 'Tag-Modus (erzwungen)';
        toggleBtn.style.boxShadow = '0 0 0 2px #FFD700, 0 4px 20px var(--gold-glow)';
      } else if (mode === 'night') {
        toggleBtn.innerHTML = '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="theme-moon"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>';
        toggleBtn.title = 'Nacht-Modus (erzwungen)';
        toggleBtn.style.boxShadow = '0 0 0 2px #CC2090, 0 4px 20px var(--pink-glow)';
      }
    }
  })();


  /* ════════════════════════════════════════════════════════
     WEITERE FEATURES (bestehend + ergänzt)
     ════════════════════════════════════════════════════════ */

  /* ─── 8. COUNTER ANIMATION ─── */
  (function initCounters() {
    var counterObserver = new IntersectionObserver(function(entries) {
      entries.forEach(function(entry) {
        if (entry.isIntersecting) {
          var el = entry.target;
          var target = parseInt(el.dataset.count, 10);
          if (!target) return;
          var current = 0;
          var step = Math.max(1, Math.floor(target / 60));
          var interval = setInterval(function() {
            current += step;
            if (current >= target) { current = target; clearInterval(interval); }
            el.textContent = current.toLocaleString();
          }, 20);
          counterObserver.unobserve(el);
        }
      });
    }, { threshold: 0.5 });
    document.querySelectorAll('[data-count]').forEach(function(el) {
      counterObserver.observe(el);
    });
  })();

  /* ─── 9. FAVORITE TOGGLE ─── */
  (function initFavorites() {
    var favBadge = document.getElementById('favBadge');
    var favCount = 0;
    document.querySelectorAll('.fav-btn, .accomm-fav').forEach(function(btn) {
      btn.addEventListener('click', function(e) {
        e.preventDefault();
        e.stopPropagation();
        this.classList.toggle('active');
        this.textContent = this.classList.contains('active') ? '♥' : '♡';
        favCount += this.classList.contains('active') ? 1 : -1;
        if (favBadge) {
          if (favCount > 0) { favBadge.textContent = favCount; favBadge.style.display = 'flex'; }
          else { favBadge.style.display = 'none'; }
        }
      });
    });
  })();

  /* ─── 10. BACK TO TOP ─── */
  (function initBackToTop() {
    var bttBtn = document.getElementById('backToTop');
    if (bttBtn) {
      window.addEventListener('scroll', function() {
        bttBtn.classList.toggle('visible', window.scrollY > 400);
      }, { passive: true });
      bttBtn.addEventListener('click', function() {
        window.scrollTo({ top: 0, behavior: 'smooth' });
      });
    }
  })();

  /* ─── 11. STICKY NAV + TOPBAR HIDE ─── */
  (function initStickyNav() {
    var mainNav = document.getElementById('mainNav');
    var topBar = document.querySelector('.topbar');
    if (mainNav) {
      window.addEventListener('scroll', function() {
        mainNav.classList.toggle('scrolled', window.scrollY > 0);
        if (topBar) topBar.classList.toggle('hidden', window.scrollY > 36);
      }, { passive: true });
    }
  })();

  /* ─── 12. SCROLL PROGRESS ─── */
  (function initScrollProgress() {
    var scrollProg = document.getElementById('scrollProgress');
    if (scrollProg) {
      var ticking = false;
      window.addEventListener('scroll', function() {
        if (ticking) return;
        ticking = true;
        requestAnimationFrame(function() {
        var h = document.documentElement;
        var scrollTop = h.scrollTop || document.body.scrollTop;
        var scrollHeight = h.scrollHeight - h.clientHeight;
        if (scrollHeight > 0) {
          scrollProg.style.transform = 'scaleX(' + (scrollTop / scrollHeight) + ')';
        }
          ticking = false;
        });
      }, { passive: true });
    }
  })();

  /* ─── 13. WEATHER WIDGET ─── */
  (function initWeather() {
    var widget = document.getElementById('weatherWidget');
    if (!widget) return;

    var WEATHER_ICONS = {
      0: '☀️', 1: '🌤️', 2: '🌤️', 3: '🌤️',
      45: '🌫️', 48: '🌫️',
      51: '🌦️', 53: '🌦️', 55: '🌦️', 56: '🌦️', 57: '🌦️',
      61: '🌧️', 63: '🌧️', 65: '🌧️', 66: '🌧️', 67: '🌧️',
      71: '❄️', 73: '❄️', 75: '❄️', 77: '❄️',
      80: '🌦️', 81: '🌦️', 82: '🌦️',
      85: '❄️', 86: '❄️',
      95: '⛈️', 96: '⛈️', 99: '⛈️'
    };

    function getIcon(code) { return WEATHER_ICONS[code] || '☀️'; }

    function dayAbbr(index) {
      var days = ['So', 'Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa'];
      var d = new Date();
      d.setDate(d.getDate() + index);
      return days[d.getDay()];
    }

    var url = 'https://api.open-meteo.com/v1/forecast?latitude=47.3&longitude=11.4&current=temperature_2m,weather_code&daily=temperature_2m_max,temperature_2m_min,weather_code&timezone=Europe%2FBerlin&forecast_days=3';

    var loadWeather = function() { fetch(url)
      .then(function(res) { return res.json(); })
      .then(function(data) {
        var cur = Math.round(data.current.temperature_2m);
        var curIcon = getIcon(data.current.weather_code);
        var fc = '';
        for (var i = 0; i < data.daily.time.length; i++) {
          fc += '<span class="wday">' + dayAbbr(i) + ': ' +
            Math.round(data.daily.temperature_2m_min[i]) + '°/' +
            Math.round(data.daily.temperature_2m_max[i]) + '° ' +
            getIcon(data.daily.weather_code[i]) + '</span>';
        }
        widget.innerHTML = '<div class="weather-current">' + curIcon +
          ' <span class="wtemp">' + cur + '°C</span> <span class="wloc">Tirol</span></div>' +
          '<div class="weather-forecast">' + fc + '</div>';
      })
      .catch(function() { widget.innerHTML = ''; }); };
    if ('requestIdleCallback' in window) requestIdleCallback(loadWeather, { timeout: 3500 });
    else window.addEventListener('load', function() { setTimeout(loadWeather, 1200); }, { once: true });
  })();

  /* ─── 14. MOBILE MENU ─── */
  (function initMobileMenu() {
    var hamburger = document.getElementById('hamburger');
    var mobileMenu = document.getElementById('mobileMenu');
    var mobileClose = document.getElementById('mobileClose');
    if (hamburger && mobileMenu) {
      hamburger.addEventListener('click', function() {
        hamburger.classList.toggle('active');
        mobileMenu.classList.toggle('open');
      });
    }
    if (mobileClose && mobileMenu && hamburger) {
      mobileClose.addEventListener('click', function() {
        hamburger.classList.remove('active');
        mobileMenu.classList.remove('open');
      });
    }
  })();

  /* ─── 15. SCROLL REVEAL ─── */
  (function initScrollReveal() {
    var revealObserver = new IntersectionObserver(function(entries) {
      entries.forEach(function(entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('v');
          revealObserver.unobserve(entry.target);
        }
      });
    }, { threshold: 0.1 });
    document.querySelectorAll('.reveal').forEach(function(el) {
      revealObserver.observe(el);
    });
  })();

  /* ─── 16. ACCOMMODATION TABS ─── */
  (function initAccommTabs() {
    var tabs = document.querySelectorAll('.accomm-tab');
    var cards = document.querySelectorAll('.accomm-card');
    if (!tabs.length) return;
    tabs.forEach(function(tab) {
      tab.addEventListener('click', function(e) {
        e.preventDefault();
        this.classList.toggle('active');
        var activeTiers = [];
        document.querySelectorAll('.accomm-tab.active').forEach(function(t) {
          var tier = t.getAttribute('data-tier');
          if (tier) activeTiers.push(tier);
        });
        cards.forEach(function(card) {
          var cardTier = card.getAttribute('data-tier');
          card.style.display = (activeTiers.length === 0 || activeTiers.indexOf(cardTier) !== -1) ? '' : 'none';
        });
      });
    });
  })();

})();
