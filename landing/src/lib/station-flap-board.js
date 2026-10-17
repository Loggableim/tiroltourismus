/**
 * Fixed-capacity station split-flap board (Bahnhof/Flughafen-Anzeige).
 * Exposes window.TTStationFlap — mount once per page, then render / animate.
 */
(function (global) {
  'use strict';

  var DEFAULT_COLS = 52;
  var DEFAULT_ROWS = 2;

  function arrayFrom(str) {
    return Array.from(str || '');
  }

  /** Pack text into row-major cells; unused slots stay null (empty flap). */
  function packCells(text, cols, rows) {
    var cap = cols * rows;
    var cells = new Array(cap);
    var i;
    for (i = 0; i < cap; i++) cells[i] = null;
    var chars = arrayFrom(text);
    var r = 0;
    var c = 0;
    var ci = 0;
    while (ci < chars.length && r < rows) {
      if (c >= cols) {
        r++;
        c = 0;
        if (r >= rows) break;
      }
      cells[r * cols + c] = chars[ci];
      ci++;
      c++;
    }
    return cells;
  }

  function makeCell(classBase, ch, emptyClass) {
    var span = document.createElement('span');
    span.className = classBase + (ch == null ? ' ' + emptyClass : '');
    if (ch == null) span.textContent = '\u00a0';
    else span.textContent = ch;
    return span;
  }

  function TTStationFlap(opts) {
    this.el = opts.el;
    this.cellClass = opts.cellClass || 'tt-ch';
    this.emptyClass = opts.emptyClass || 'tt-ch-empty';
    this.cols = opts.cols || DEFAULT_COLS;
    this.rows = opts.rows || DEFAULT_ROWS;
    this.boardClass = opts.boardClass || 'tt-flap-board';
    this.glyphsLatin =
      opts.glyphsLatin ||
      'ABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÜČŘŠŽ0123456789·—';
    this.glyphsCjk =
      opts.glyphsCjk || '山川云雪峰谷林泉风光探索蒂罗尔天地八方旅途境';
    this.flapMs = opts.flapMs || 700;
    this.el.classList.add(this.boardClass);
    this.el.style.setProperty('--flap-cols', String(this.cols));
    this.el.style.setProperty('--flap-rows', String(this.rows));
  }

  TTStationFlap.prototype.capacity = function () {
    return this.cols * this.rows;
  };

  TTStationFlap.prototype._pool = function (langHint) {
    var l = String(langHint || '').toLowerCase();
    if (l.indexOf('zh') === 0 || l === 'cn') return this.glyphsCjk;
    return this.glyphsLatin;
  };

  /** Static board — same visual as after animation (empty cells stay visible). */
  TTStationFlap.prototype.renderStatic = function (text, langHint) {
    var self = this;
    var cells = packCells(text, self.cols, self.rows);
    self.el.textContent = '';
    self.el.setAttribute('lang', langHint || '');
    var frag = document.createDocumentFragment();
    cells.forEach(function (ch) {
      frag.appendChild(makeCell(self.cellClass, ch, self.emptyClass));
    });
    self.el.appendChild(frag);
  };

  TTStationFlap.prototype.cancel = function (state) {
    if (state.raf) {
      cancelAnimationFrame(state.raf);
      state.raf = 0;
    }
    if (state.fadeTimer) {
      clearTimeout(state.fadeTimer);
      state.fadeTimer = 0;
    }
  };

  TTStationFlap.prototype.crossfade = function (text, langHint, state) {
    var self = this;
    self.cancel(state);
    self.el.style.transition = 'opacity 180ms ease';
    self.el.style.opacity = '0';
    state.fadeTimer = setTimeout(function () {
      state.fadeTimer = 0;
      self.renderStatic(text, langHint);
      self.el.style.opacity = '1';
    }, 180);
  };

  TTStationFlap.prototype.animateTo = function (text, langHint, reducedMotion, state) {
    var self = this;
    if (reducedMotion) {
      self.crossfade(text, langHint, state);
      return;
    }
    self.cancel(state);
    self.el.style.transition = '';
    self.el.style.opacity = '1';
    self.el.setAttribute('lang', langHint || '');

    var targetCells = packCells(text, self.cols, self.rows);
    var pool = self._pool(langHint);
    var cap = self.capacity();
    var nodes = [];
    var frag = document.createDocumentFragment();
    var i;

    for (i = 0; i < cap; i++) {
      var target = targetCells[i];
      var span = makeCell(self.cellClass, pool[(Math.random() * pool.length) | 0], self.emptyClass);
      if (target == null) {
        span.classList.add(self.emptyClass);
        span.textContent = '\u00a0';
      }
      frag.appendChild(span);
      nodes.push({
        el: span,
        target: target,
        glyph: span.textContent,
        empty: target == null
      });
    }

    self.el.textContent = '';
    self.el.appendChild(frag);

    var startTime = 0;
    var lastTick = 0;
    var lead = self.flapMs * 0.12;
    var spread = self.flapMs * 0.78;
    var animNodes = nodes.filter(function (n) {
      return !n.empty;
    });
    var total = animNodes.length;
    if (!total) {
      self.renderStatic(text, langHint);
      return;
    }

    var settleTimes = new Array(total);
    for (i = 0; i < total; i++) {
      settleTimes[i] =
        total > 1 ? lead + (i / (total - 1)) * spread : self.flapMs * 0.5;
    }

    function stepFrame(now) {
      if (!startTime) startTime = now;
      var elapsed = now - startTime;
      var swap = elapsed - lastTick >= 52;
      if (swap) lastTick = elapsed;

      var done = true;
      var j;
      for (j = 0; j < total; j++) {
        var item = animNodes[j];
        if (elapsed >= settleTimes[j]) {
          if (item.target == null) continue;
          if (item.el.textContent !== item.target) {
            item.el.textContent = item.target;
            item.el.style.transform = 'rotateX(0deg)';
            item.el.style.opacity = '1';
            item.el.removeAttribute('data-flapping');
          }
        } else {
          done = false;
          if (swap) {
            item.glyph = pool[(Math.random() * pool.length) | 0];
            item.el.textContent = item.glyph;
          }
          item.el.setAttribute('data-flapping', 'true');
          var phase = elapsed / 45 + j * 0.68;
          var angle = Math.sin(phase) * 54;
          item.el.style.transform = 'rotateX(' + angle.toFixed(1) + 'deg)';
          item.el.style.opacity = String(
            (0.56 + 0.44 * Math.abs(Math.cos(phase))).toFixed(2)
          );
        }
      }

      if (done) {
        state.raf = 0;
        self.renderStatic(text, langHint);
      } else {
        state.raf = requestAnimationFrame(stepFrame);
      }
    }

    state.raf = requestAnimationFrame(stepFrame);
  };

  global.TTStationFlap = TTStationFlap;
  global.TTStationFlap.packCells = packCells;
})(typeof window !== 'undefined' ? window : globalThis);
