/**
 * Hero v3 — Cyber Grid
 * Perspective grid flowing toward the viewer; mouse tilts the vanishing point.
 */
(function () {
  'use strict';
  const canvas = document.getElementById('fhHeroCanvas');
  const hero = canvas && canvas.closest('.fh-hero');
  if (!canvas || !hero) return;
  if (typeof window.matchMedia === 'function' && window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

  const ctx = canvas.getContext('2d');
  let W = 0, H = 0, offset = 0;
  let mx = 0.5, my = 0.5;

  function resize() {
    const r = hero.getBoundingClientRect();
    W = r.width; H = r.height;
    const dpr = Math.min(devicePixelRatio || 1, 2);
    canvas.width = Math.floor(W * dpr);
    canvas.height = Math.floor(H * dpr);
    canvas.style.width = W + 'px';
    canvas.style.height = H + 'px';
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }

  const COLS = 14;
  const ROWS = 18;
  const SPEED = 0.00045;

  // Project a world point (wx in [-1,1], depth in [0,1]) to screen coords
  function proj(wx, depth) {
    const vp = { x: W * (0.5 + (mx - 0.5) * 0.1), y: H * (0.68 + (my - 0.5) * 0.06) };
    const sc = 1 / (1 + (1 - depth) * 2.8);
    return {
      x: vp.x + wx * W * 0.7 * sc,
      y: vp.y - (1 - depth) * H * 0.62,
      sc,
    };
  }

  function frame(ts) {
    ctx.clearRect(0, 0, W, H);

    // Vertical lines
    for (let i = 0; i <= COLS; i++) {
      const wx = (i / COLS - 0.5) * 2;
      ctx.beginPath();
      let first = true;
      for (let s = 0; s <= 40; s++) {
        const rawDepth = s / 40;
        const depth = ((rawDepth + offset) % 1);
        const p = proj(wx, depth);
        const alpha = depth * 0.28;
        if (first) { ctx.moveTo(p.x, p.y); first = false; }
        else ctx.lineTo(p.x, p.y);
      }
      const isCenter = i === Math.floor(COLS / 2);
      ctx.strokeStyle = isCenter
        ? `rgba(67,217,173,0.35)`
        : `rgba(108,99,255,0.18)`;
      ctx.lineWidth = isCenter ? 1.2 : 0.7;
      ctx.stroke();
    }

    // Horizontal rings
    for (let j = 0; j < ROWS; j++) {
      const rawDepth = j / ROWS;
      const depth = ((rawDepth + offset) % 1);
      const alpha = depth * 0.3;
      const isAccent = j % 3 === 0;

      ctx.beginPath();
      let first = true;
      for (let i = 0; i <= COLS; i++) {
        const wx = (i / COLS - 0.5) * 2;
        const p = proj(wx, depth);
        if (first) { ctx.moveTo(p.x, p.y); first = false; }
        else ctx.lineTo(p.x, p.y);
      }
      ctx.strokeStyle = isAccent
        ? `rgba(67,217,173,${(alpha * 1.8).toFixed(3)})`
        : `rgba(108,99,255,${alpha.toFixed(3)})`;
      ctx.lineWidth = isAccent ? 1.1 : 0.55;
      ctx.stroke();
    }

    // Pulse dots at grid intersections near viewer
    for (let i = 0; i <= COLS; i++) {
      const wx = (i / COLS - 0.5) * 2;
      for (let j = 0; j < 3; j++) {
        const rawDepth = j / ROWS;
        const depth = ((rawDepth + offset) % 1);
        if (depth < 0.15) continue;
        const p = proj(wx, depth);
        const r = depth * 3;
        const alpha = depth * 0.7;
        ctx.beginPath();
        ctx.arc(p.x, p.y, r, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(67,217,173,${alpha.toFixed(3)})`;
        ctx.fill();
      }
    }

    offset = (offset + SPEED) % 1;
    requestAnimationFrame(frame);
  }

  hero.addEventListener('mousemove', e => {
    const r = hero.getBoundingClientRect();
    mx = (e.clientX - r.left) / r.width;
    my = (e.clientY - r.top) / r.height;
  }, { passive: true });
  hero.addEventListener('mouseleave', () => { mx = 0.5; my = 0.5; });
  window.addEventListener('resize', resize, { passive: true });

  resize();
  requestAnimationFrame(frame);
})();
