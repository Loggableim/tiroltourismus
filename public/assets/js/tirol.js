(function() {
  'use strict';

  /* ─── 1. THEME TOGGLE (Sonne/Mond) ─── */
  (function initTheme() {
    var stored = localStorage.getItem('tirol_theme') || 'alpenpop';
    if (stored === 'alpenpeak') {
      document.documentElement.dataset.theme = 'alpenpeak';
    }
    var toggleBtn = document.getElementById('themeToggle');
    if (toggleBtn) {
      // Set initial icon: if dark mode, show sun (☀️); light mode show moon (🌙)
      var isDark = document.documentElement.dataset.theme === 'alpenpeak';
      toggleBtn.textContent = isDark ? '☀️' : '🌙';

      toggleBtn.addEventListener('click', function() {
        var html = document.documentElement;
        var currentlyDark = html.dataset.theme === 'alpenpeak';
        if (currentlyDark) {
          // Switch to light (AlpenPop)
          delete html.dataset.theme;
          localStorage.setItem('tirol_theme', 'alpenpop');
          toggleBtn.textContent = '🌙';
        } else {
          // Switch to dark (AlpenPeak)
          html.dataset.theme = 'alpenpeak';
          localStorage.setItem('tirol_theme', 'alpenpeak');
          toggleBtn.textContent = '☀️';
        }
        // Smooth transition
        html.classList.add('theme-transitioning');
        document.body.style.transition = 'background-color 0.6s ease, color 0.6s ease';
        setTimeout(function() {
          html.classList.remove('theme-transitioning');
          document.body.style.transition = '';
        }, 600);
      });
    }
  })();

  /* ─── 2. COUNTER ANIMATION ─── */
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

  /* ─── 3. FAVORITE TOGGLE ─── */
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

  /* ─── 4. BACK TO TOP ─── */
  (function initBackToTop() {
    var bttBtn = document.getElementById('backToTop');
    if (bttBtn) {
      window.addEventListener('scroll', function() {
        bttBtn.classList.toggle('visible', window.scrollY > 400);
      });
      bttBtn.addEventListener('click', function() {
        window.scrollTo({ top: 0, behavior: 'smooth' });
      });
    }
  })();

  /* ─── 5. STICKY NAV ─── */
  (function initStickyNav() {
    var mainNav = document.getElementById('mainNav');
    if (mainNav) {
      window.addEventListener('scroll', function() {
        mainNav.classList.toggle('scrolled', window.scrollY > 0);
      });
    }
  })();

  /* ─── 6. SCROLL PROGRESS ─── */
  (function initScrollProgress() {
    var scrollProg = document.getElementById('scrollProgress');
    if (scrollProg) {
      window.addEventListener('scroll', function() {
        var h = document.documentElement;
        var scrollTop = h.scrollTop || document.body.scrollTop;
        var scrollHeight = h.scrollHeight - h.clientHeight;
        if (scrollHeight > 0) {
          scrollProg.style.width = ((scrollTop / scrollHeight) * 100) + '%';
        }
      });
    }
  })();

  /* ─── 7. WEATHER WIDGET ─── */
  (function initWeather() {
    var widget = document.getElementById('weatherWidget');
    if (!widget) return;

    var WEATHER_ICONS = {
      0: '☀️',       // Clear sky
      1: '🌤️',       // Mainly clear
      2: '🌤️',       // Partly cloudy
      3: '🌤️',       // Overcast
      45: '🌫️',      // Foggy
      48: '🌫️',      // Depositing rime fog
      51: '🌦️',      // Light drizzle
      53: '🌦️',      // Moderate drizzle
      55: '🌦️',      // Dense drizzle
      56: '🌦️',      // Light freezing drizzle
      57: '🌦️',      // Dense freezing drizzle
      61: '🌧️',      // Slight rain
      63: '🌧️',      // Moderate rain
      65: '🌧️',      // Heavy rain
      66: '🌧️',      // Light freezing rain
      67: '🌧️',      // Heavy freezing rain
      71: '❄️',       // Slight snow
      73: '❄️',       // Moderate snow
      75: '❄️',       // Heavy snow
      77: '❄️',       // Snow grains
      80: '🌦️',       // Slight rain showers
      81: '🌦️',       // Moderate rain showers
      82: '🌦️',       // Violent rain showers
      85: '❄️',       // Slight snow showers
      86: '❄️',       // Heavy snow showers
      95: '⛈️',       // Thunderstorm
      96: '⛈️',       // Thunderstorm with slight hail
      99: '⛈️'        // Thunderstorm with heavy hail
    };

    function getWeatherIcon(code) {
      return WEATHER_ICONS[code] || '☀️';
    }

    function dayAbbr(index) {
      var days = ['So', 'Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa'];
      var d = new Date();
      d.setDate(d.getDate() + index);
      return days[d.getDay()];
    }

    var url = 'https://api.open-meteo.com/v1/forecast?latitude=47.3&longitude=11.4&current=temperature_2m,weather_code,wind_speed_10m&daily=temperature_2m_max,temperature_2m_min,weather_code&timezone=Europe%2FBerlin&forecast_days=3';

    fetch(url)
      .then(function(res) { return res.json(); })
      .then(function(data) {
        var currentTemp = Math.round(data.current.temperature_2m);
        var currentCode = data.current.weather_code;
        var currentIcon = getWeatherIcon(currentCode);

        var daily = data.daily;
        var forecastHtml = '';
        for (var i = 0; i < daily.time.length; i++) {
          var min = Math.round(daily.temperature_2m_min[i]);
          var max = Math.round(daily.temperature_2m_max[i]);
          var icon = getWeatherIcon(daily.weather_code[i]);
          var abbr = dayAbbr(i);
          forecastHtml += '<span class="wday">' + abbr + ': ' + min + '°/' + max + '° ' + icon + '</span>';
        }

        widget.innerHTML = '<div class="weather-current">' + currentIcon + ' <span class="wtemp">' + currentTemp + '°C</span> <span class="wloc">Tirol</span></div>' +
          '<div class="weather-forecast">' + forecastHtml + '</div>';
      })
      .catch(function() {
        widget.innerHTML = '';
      });
  })();

  /* ─── 8. MOBILE MENU ─── */
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

    if (mobileClose && mobileMenu) {
      mobileClose.addEventListener('click', function() {
        hamburger.classList.remove('active');
        mobileMenu.classList.remove('open');
      });
    }
  })();

  /* ─── 9. SCROLL REVEAL ─── */
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

  /* ─── 10. ACCOMMODATION TABS ─── */
  (function initAccommTabs() {
    var tabs = document.querySelectorAll('.accomm-tab');
    var cards = document.querySelectorAll('.accomm-card');

    if (!tabs.length) return;

    tabs.forEach(function(tab) {
      tab.addEventListener('click', function(e) {
        e.preventDefault();

        // Toggle active on clicked tab
        this.classList.toggle('active');

        // Determine which tiers are active
        var activeTiers = [];
        document.querySelectorAll('.accomm-tab.active').forEach(function(t) {
          var tier = t.getAttribute('data-tier');
          if (tier) activeTiers.push(tier);
        });

        // Show/hide cards
        cards.forEach(function(card) {
          var cardTier = card.getAttribute('data-tier');
          if (activeTiers.length === 0 || activeTiers.indexOf(cardTier) !== -1) {
            card.style.display = '';
          } else {
            card.style.display = 'none';
          }
        });
      });
    });
  })();

})();
