/**
 * Hero v8 — Starfield Warp
 * Stars shoot outward from center; mouse tilts the origin point.
 */
(function () {
  'use strict';
  const canvas = document.getElementById('fhHeroCanvas');
  const hero = canvas && canvas.closest('.fh-hero');
  if (!canvas || !hero) return;
  if (typeof window.matchMedia === 'function' && window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

  const ctx = canvas.getContext('2d');
  const PALETTE = ['108,99,255', '67,217,173', '255,101,132', '245,166,35', '255,255,255'];
  let W = 0, H = 0;
  let tx = 0.5, ty = 0.5; // target origin (normalized)
  let ox = 0.5, oy = 0.5; // smoothed origin

  const STAR_COUNT = 220;
  let stars = [];

  function resize() {
    const r = hero.getBoundingClientRect();
    W = r.width; H = r.height;
    const dpr = Math.min(devicePixelRatio || 1, 2);
    canvas.width = Math.floor(W * dpr);
    canvas.height = Math.floor(H * dpr);
    canvas.style.width = W + 'px';
    canvas.style.height = H + 'px';
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    init();
  }

  function mkStar() {
    const angle = Math.random() * Math.PI * 2;
    const speed = Math.random() * 2.5 + 0.8;
    return {
      angle,
      dist: Math.random() * Math.max(W, H) * 0.55,
      speed,
      col: PALETTE[Math.floor(Math.random() * PALETTE.length)],
      size: Math.random() * 1.4 + 0.4,
    };
  }

  function init() {
    stars = Array.from({ length: STAR_COUNT }, mkStar);
  }

  function frame() {
    ctx.fillStyle = 'rgba(10,10,20,0.22)';
    ctx.fillRect(0, 0, W, H);

    // Lerp origin toward mouse
    ox += (tx - ox) * 0.05;
    oy += (ty - oy) * 0.05;
    const cx = ox * W, cy = oy * H;

    for (let i = 0; i < stars.length; i++) {
      const s = stars[i];
      const prevDist = s.dist;
      s.dist += s.speed * (s.dist / 80 + 0.8);

      const px = cx + Math.cos(s.angle) * prevDist;
      const py = cy + Math.sin(s.angle) * prevDist;
      const nx = cx + Math.cos(s.angle) * s.dist;
      const ny = cy + Math.sin(s.angle) * s.dist;

      const progress = s.dist / (Math.max(W, H) * 0.75);
      const alpha = Math.min(progress * 1.2, 0.7);
      const lw = s.size * Math.min(progress * 2, 1.8);

      ctx.beginPath();
      ctx.moveTo(px, py);
      ctx.lineTo(nx, ny);
      ctx.strokeStyle = `rgba(${s.col},${alpha.toFixed(3)})`;
      ctx.lineWidth = lw;
      ctx.stroke();

      // Reset star when it flies off screen
      if (nx < -20 || nx > W + 20 || ny < -20 || ny > H + 20) {
        stars[i] = mkStar();
        stars[i].dist = Math.random() * 8; // start near center
      }
    }

    requestAnimationFrame(frame);
  }

  hero.addEventListener('mousemove', e => {
    const r = hero.getBoundingClientRect();
    tx = (e.clientX - r.left) / r.width;
    ty = (e.clientY - r.top) / r.height;
  }, { passive: true });
  hero.addEventListener('mouseleave', () => { tx = 0.5; ty = 0.5; });
  window.addEventListener('resize', resize, { passive: true });

  resize();
  frame();
})();
