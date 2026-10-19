/* HanX Games — shared behaviour: nav, scroll reveals, counters, tilt, gallery, particles. */
(function () {
  'use strict';
  var HX = (window.HX = window.HX || {});
  var reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  HX.reduced = reduced;
  var isTR = document.documentElement.lang === 'tr';
  HX.locale = isTR ? 'tr-TR' : 'en-US';
  var T = isTR
    ? { viewer: 'Ekran görüntüsü görüntüleyici', close: 'Kapat', prev: 'Önceki', next: 'Sonraki' }
    : { viewer: 'Screenshot viewer', close: 'Close', prev: 'Previous', next: 'Next' };

  /* ---------- Language switch remembers the choice ---------- */
  document.querySelectorAll('.lang a').forEach(function (a) {
    a.addEventListener('click', function () { try { localStorage.setItem('hx-lang', a.getAttribute('hreflang')); } catch (e) { /* storage blocked */ } });
  });

  /* ---------- Navigation ---------- */
  var nav = document.querySelector('.nav');
  if (nav) {
    var onScroll = function () { nav.classList.toggle('is-scrolled', window.scrollY > 12); };
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
    var burger = nav.querySelector('.nav__burger');
    var setOpen = function (open) {
      nav.classList.toggle('is-open', open);
      document.body.classList.toggle('nav-open', open);
      if (burger) burger.setAttribute('aria-expanded', String(open));
    };
    if (burger) burger.addEventListener('click', function () { setOpen(!nav.classList.contains('is-open')); });
    nav.querySelectorAll('.nav__links a').forEach(function (a, i) {
      a.style.setProperty('--i', i);
      a.addEventListener('click', function () { setOpen(false); });
    });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape') setOpen(false); });
  }

  /* ---------- Reveal on scroll ---------- */
  var revealEls = document.querySelectorAll('[data-reveal], .ficon, [data-count], [data-in]');
  if ('IntersectionObserver' in window && !reduced) {
    // Anything already on screen at load (the hero) animates in right away.
    var vh = window.innerHeight;
    revealEls = Array.prototype.filter.call(revealEls, function (el) {
      var r = el.getBoundingClientRect();
      if (r.top < vh * 0.95 && r.bottom > 0 && !el.hasAttribute('data-count')) { el.classList.add('is-in'); return false; }
      return true;
    });
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (!en.isIntersecting) return;
        en.target.classList.add('is-in');
        if (en.target.hasAttribute('data-count')) countUp(en.target);
        io.unobserve(en.target);
      });
    }, { threshold: 0.18, rootMargin: '0px 0px -40px 0px' });
    revealEls.forEach(function (el) { io.observe(el); });
  } else {
    revealEls.forEach(function (el) { el.classList.add('is-in'); if (el.hasAttribute('data-count')) countUp(el, true); });
  }

  /* ---------- Counters ---------- */
  function countUp(el, instant) {
    var to = parseFloat(el.getAttribute('data-count'));
    var suffix = el.getAttribute('data-suffix') || '';
    var fmt = function (v) { return Math.round(v).toLocaleString(HX.locale) + suffix; };
    if (instant) { el.textContent = fmt(to); return; }
    var dur = parseInt(el.getAttribute('data-dur') || '1600', 10), t0 = null;
    var step = function (t) {
      if (!t0) t0 = t;
      var p = Math.min(1, (t - t0) / dur);
      el.textContent = fmt(to * (1 - Math.pow(1 - p, 4)));
      if (p < 1) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
  }
  HX.countUp = countUp;

  /* ---------- Tilt cards ---------- */
  if (!reduced && window.matchMedia('(hover: hover)').matches) {
    document.querySelectorAll('[data-tilt]').forEach(function (el) {
      var max = parseFloat(el.getAttribute('data-tilt')) || 8;
      el.addEventListener('pointermove', function (e) {
        var r = el.getBoundingClientRect();
        var x = (e.clientX - r.left) / r.width - 0.5, y = (e.clientY - r.top) / r.height - 0.5;
        el.style.transform = 'perspective(900px) rotateX(' + (-y * max).toFixed(2) + 'deg) rotateY(' + (x * max).toFixed(2) + 'deg) translateY(-4px)';
        el.style.setProperty('--mx', ((x + 0.5) * 100).toFixed(1) + '%');
        el.style.setProperty('--my', ((y + 0.5) * 100).toFixed(1) + '%');
      });
      el.addEventListener('pointerleave', function () { el.style.transform = ''; });
    });
  }

  /* ---------- Parallax ---------- */
  var para = document.querySelectorAll('[data-parallax]');
  if (para.length && !reduced) {
    var ticking = false;
    var update = function () {
      var vh = window.innerHeight;
      para.forEach(function (el) {
        var r = el.getBoundingClientRect();
        if (r.bottom < -200 || r.top > vh + 200) return;
        var k = parseFloat(el.getAttribute('data-parallax')) || 0.15;
        var off = (r.top + r.height / 2 - vh / 2) * -k;
        el.style.transform = 'translate3d(0,' + off.toFixed(1) + 'px,0)';
      });
      ticking = false;
    };
    window.addEventListener('scroll', function () { if (!ticking) { ticking = true; requestAnimationFrame(update); } }, { passive: true });
    update();
  }

  /* ---------- Gallery + lightbox ---------- */
  var icon = function (d) { return '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="' + d + '"/></svg>'; };
  document.querySelectorAll('.gallery').forEach(function (g) {
    var track = g.querySelector('.shots');
    g.querySelectorAll('[data-dir]').forEach(function (b) {
      b.addEventListener('click', function () {
        track.scrollBy({ left: parseInt(b.getAttribute('data-dir'), 10) * track.clientWidth * 0.8, behavior: 'smooth' });
      });
    });
  });
  var shots = Array.prototype.slice.call(document.querySelectorAll('.shot'));
  if (shots.length) {
    var lb = document.createElement('div');
    lb.className = 'lightbox';
    lb.setAttribute('role', 'dialog');
    lb.setAttribute('aria-modal', 'true');
    lb.setAttribute('aria-label', T.viewer);
    lb.innerHTML = '<img alt="">' +
      '<button type="button" data-lb-close aria-label="' + T.close + '">' + icon('M6 6l12 12M18 6L6 18') + '</button>' +
      '<button type="button" data-lb-prev aria-label="' + T.prev + '">' + icon('M15 5l-7 7 7 7') + '</button>' +
      '<button type="button" data-lb-next aria-label="' + T.next + '">' + icon('M9 5l7 7-7 7') + '</button>';
    document.body.appendChild(lb);
    var lbImg = lb.querySelector('img'), cur = 0, lastFocus = null;
    var show = function (i) {
      cur = (i + shots.length) % shots.length;
      var im = shots[cur].querySelector('img');
      lbImg.src = im.currentSrc || im.src;
      lbImg.alt = im.alt;
    };
    var open = function (i) { lastFocus = document.activeElement; show(i); lb.classList.add('is-open'); lb.querySelector('[data-lb-close]').focus(); };
    var close = function () { lb.classList.remove('is-open'); if (lastFocus) lastFocus.focus(); };
    shots.forEach(function (s, i) { s.addEventListener('click', function () { open(i); }); });
    lb.querySelector('[data-lb-close]').addEventListener('click', close);
    lb.querySelector('[data-lb-prev]').addEventListener('click', function () { show(cur - 1); });
    lb.querySelector('[data-lb-next]').addEventListener('click', function () { show(cur + 1); });
    lb.addEventListener('click', function (e) { if (e.target === lb) close(); });
    document.addEventListener('keydown', function (e) {
      if (!lb.classList.contains('is-open')) return;
      if (e.key === 'Escape') close();
      if (e.key === 'ArrowLeft') show(cur - 1);
      if (e.key === 'ArrowRight') show(cur + 1);
    });
  }

  /* ---------- Particle system ----------
     HX.particles(canvas, {
       count, colors, size:[min,max], speed:[min,max], dir:'up'|'down'|'none',
       drift, shape:'dot'|'glyph'|'leaf'|'flake'|'rain'|'square', glyphs:[...],
       link: px distance for network lines, mouse: bool, twinkle: bool, glow: bool
     }) */
  HX.particles = function (canvas, o) {
    if (!canvas || reduced) return;
    o = Object.assign({ count: 60, colors: ['#ffffff'], size: [1, 3], speed: [0.2, 0.7], dir: 'up', drift: 0.25,
      shape: 'dot', glyphs: ['♠', '♥', '♦', '♣'], link: 0, mouse: false, twinkle: false, glow: false, alpha: [0.35, 1], font: 'serif' }, o);
    var ctx = canvas.getContext('2d'), dpr = Math.min(window.devicePixelRatio || 1, 2);
    var W = 0, H = 0, parts = [], mouse = { x: -9999, y: -9999 }, running = true, raf = 0;
    var rnd = function (a, b) { return a + Math.random() * (b - a); };
    var make = function (fresh) {
      var p = {
        x: rnd(0, W), y: fresh ? rnd(0, H) : (o.dir === 'up' ? H + 20 : o.dir === 'down' ? -20 : rnd(0, H)),
        r: rnd(o.size[0], o.size[1]), v: rnd(o.speed[0], o.speed[1]),
        c: o.colors[(Math.random() * o.colors.length) | 0], a: rnd(o.alpha[0], o.alpha[1]),
        ph: Math.random() * Math.PI * 2, rot: Math.random() * Math.PI * 2, vr: rnd(-0.02, 0.02),
        vx: rnd(-o.drift, o.drift), vy: rnd(-o.drift, o.drift),
        g: o.glyphs[(Math.random() * o.glyphs.length) | 0]
      };
      return p;
    };
    var resize = function () {
      var r = canvas.getBoundingClientRect();
      W = r.width; H = r.height;
      canvas.width = Math.round(W * dpr); canvas.height = Math.round(H * dpr);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      var n = Math.round(o.count * Math.min(1.6, Math.max(0.45, (W * H) / (1280 * 760))));
      while (parts.length < n) parts.push(make(true));
      parts.length = n;
    };
    var draw = function (t) {
      ctx.clearRect(0, 0, W, H);
      for (var i = 0; i < parts.length; i++) {
        var p = parts[i];
        p.ph += 0.02;
        if (o.dir === 'up') { p.y -= p.v; p.x += Math.sin(p.ph) * o.drift; }
        else if (o.dir === 'down') { p.y += p.v; p.x += Math.sin(p.ph * 0.7) * o.drift + (o.shape === 'rain' ? p.v * 0.25 : 0); }
        else { p.x += p.vx; p.y += p.vy; if (p.x < 0 || p.x > W) p.vx *= -1; if (p.y < 0 || p.y > H) p.vy *= -1; }
        p.rot += p.vr;
        if (o.mouse) {
          var dx = p.x - mouse.x, dy = p.y - mouse.y, d2 = dx * dx + dy * dy;
          if (d2 < 16000) { var f = (16000 - d2) / 16000 * 1.4; p.x += dx / 60 * f; p.y += dy / 60 * f; }
        }
        if ((o.dir === 'up' && p.y < -30) || (o.dir === 'down' && p.y > H + 30) || p.x < -60 || p.x > W + 60) {
          if (o.dir !== 'none') { parts[i] = make(false); continue; }
        }
        var a = p.a * (o.twinkle ? 0.55 + 0.45 * Math.sin(p.ph * 2.2) : 1);
        ctx.globalAlpha = a;
        ctx.fillStyle = p.c; ctx.strokeStyle = p.c;
        if (o.shape === 'dot') {
          if (o.glow) {
            var gr = ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, p.r * 4);
            gr.addColorStop(0, p.c); gr.addColorStop(1, 'rgba(0,0,0,0)');
            ctx.fillStyle = gr; ctx.beginPath(); ctx.arc(p.x, p.y, p.r * 4, 0, 6.283); ctx.fill();
            ctx.fillStyle = p.c;
          }
          ctx.beginPath(); ctx.arc(p.x, p.y, p.r, 0, 6.283); ctx.fill();
        } else if (o.shape === 'square') {
          var s = Math.round(p.r * 2); ctx.fillRect(Math.round(p.x), Math.round(p.y), s, s);
        } else if (o.shape === 'glyph') {
          ctx.save(); ctx.translate(p.x, p.y); ctx.rotate(Math.sin(p.rot) * 0.5);
          ctx.font = (p.r * 6) + 'px ' + o.font; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
          ctx.fillText(p.g, 0, 0); ctx.restore();
        } else if (o.shape === 'leaf') {
          ctx.save(); ctx.translate(p.x, p.y); ctx.rotate(p.rot); ctx.scale(1, 0.55 + 0.45 * Math.sin(p.ph * 1.5));
          ctx.beginPath(); ctx.ellipse(0, 0, p.r * 2.4, p.r, 0, 0, 6.283); ctx.fill();
          ctx.globalAlpha = a * 0.5; ctx.lineWidth = 0.8; ctx.strokeStyle = 'rgba(0,0,0,.4)';
          ctx.beginPath(); ctx.moveTo(-p.r * 2.2, 0); ctx.lineTo(p.r * 2.2, 0); ctx.stroke(); ctx.restore();
        } else if (o.shape === 'flake') {
          ctx.save(); ctx.translate(p.x, p.y); ctx.rotate(p.rot); ctx.lineWidth = 1.1;
          for (var k = 0; k < 3; k++) { ctx.rotate(1.047); ctx.beginPath(); ctx.moveTo(-p.r * 2, 0); ctx.lineTo(p.r * 2, 0); ctx.stroke(); }
          ctx.restore();
        } else if (o.shape === 'rain') {
          ctx.lineWidth = p.r * 0.5; ctx.beginPath(); ctx.moveTo(p.x, p.y); ctx.lineTo(p.x - p.v * 0.6, p.y - p.v * 4); ctx.stroke();
        }
      }
      if (o.link) {
        ctx.lineWidth = 1;
        for (var m = 0; m < parts.length; m++) {
          for (var n = m + 1; n < parts.length; n++) {
            var ax = parts[m].x - parts[n].x, ay = parts[m].y - parts[n].y, dd = ax * ax + ay * ay;
            if (dd < o.link * o.link) {
              ctx.globalAlpha = (1 - Math.sqrt(dd) / o.link) * 0.35;
              ctx.strokeStyle = parts[m].c;
              ctx.beginPath(); ctx.moveTo(parts[m].x, parts[m].y); ctx.lineTo(parts[n].x, parts[n].y); ctx.stroke();
            }
          }
        }
      }
      ctx.globalAlpha = 1;
      if (running) raf = requestAnimationFrame(draw);
    };
    resize();
    window.addEventListener('resize', resize);
    if (o.mouse) {
      var host = canvas.parentElement;
      host.addEventListener('pointermove', function (e) { var r = canvas.getBoundingClientRect(); mouse.x = e.clientX - r.left; mouse.y = e.clientY - r.top; });
      host.addEventListener('pointerleave', function () { mouse.x = mouse.y = -9999; });
    }
    if ('IntersectionObserver' in window) {
      new IntersectionObserver(function (en) {
        var vis = en[0].isIntersecting;
        if (vis && !running) { running = true; raf = requestAnimationFrame(draw); }
        if (!vis && running) { running = false; cancelAnimationFrame(raf); }
      }).observe(canvas);
    }
    raf = requestAnimationFrame(draw);
  };

  /* Auto-start canvases declared with data-fx='{"json":"options"}' */
  document.querySelectorAll('canvas[data-fx]').forEach(function (c) {
    try { HX.particles(c, JSON.parse(c.getAttribute('data-fx'))); } catch (e) { /* ignore bad config */ }
  });

  var y = document.querySelector('[data-year]');
  if (y) y.textContent = new Date().getFullYear();
})();
