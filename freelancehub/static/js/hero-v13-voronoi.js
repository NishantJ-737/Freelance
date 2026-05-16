/**
 * Hero v13 — Voronoi Cells
 * Living stained-glass cells built from drifting seed points.
 * Cells pulse with colour; mouse seed brightens nearby cells.
 * Redraws only when seeds move enough to matter.
 */
(function () {
  'use strict';
  const canvas = document.getElementById('fhHeroCanvas');
  const hero = canvas && canvas.closest('.fh-hero');
  if (!canvas || !hero) return;
  if (typeof window.matchMedia === 'function' && window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

  const ctx = canvas.getContext('2d');
  const PALETTE = [
    [108, 99, 255],
    [67, 217, 173],
    [255, 101, 132],
    [245, 166, 35],
    [80, 60, 200],
    [40, 180, 140],
  ];
  let W = 0, H = 0;
  let mx = -9999, my = -9999;
  let t = 0;

  const SEED_COUNT = 28;
  let seeds = [];

  function makeSeed(i) {
    return {
      x: Math.random() * W,
      y: Math.random() * H,
      vx: (Math.random() - 0.5) * 0.4,
      vy: (Math.random() - 0.5) * 0.4,
      col: PALETTE[i % PALETTE.length],
      phase: Math.random() * Math.PI * 2,
    };
  }

  function resize() {
    const r = hero.getBoundingClientRect();
    W = r.width; H = r.height;
    const dpr = Math.min(devicePixelRatio || 1, 2);
    canvas.width  = Math.floor(W * dpr);
    canvas.height = Math.floor(H * dpr);
    canvas.style.width  = W + 'px';
    canvas.style.height = H + 'px';
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    seeds = Array.from({ length: SEED_COUNT }, (_, i) => makeSeed(i));
  }

  // Find nearest seed index for pixel (px, py)
  function nearest(px, py) {
    let best = 0, bestD = Infinity;
    for (let i = 0; i < seeds.length; i++) {
      const dx = seeds[i].x - px, dy = seeds[i].y - py;
      const d = dx * dx + dy * dy;
      if (d < bestD) { bestD = d; best = i; }
    }
    return { idx: best, d: Math.sqrt(bestD) };
  }

  // Rasterise Voronoi using a coarse grid, then upscale
  const CELL = 6; // px per sample

  function drawVoronoi() {
    const cols2 = Math.ceil(W / CELL) + 1;
    const rows2 = Math.ceil(H / CELL) + 1;

    for (let row = 0; row < rows2; row++) {
      for (let col = 0; col < cols2; col++) {
        const px = col * CELL, py = row * CELL;
        const { idx, d } = nearest(px, py);
        const s = seeds[idx];
        const pulse = 0.5 + 0.5 * Math.sin(t * 0.8 + s.phase);

        // Mouse proximity brightens cell
        const mdist = Math.hypot(px - mx, py - my);
        const mGlow = Math.max(0, 1 - mdist / (W * 0.22)) * 0.6;

        const baseAlpha = 0.055 + pulse * 0.07 + mGlow;

        const [r, g, b] = s.col;
        ctx.fillStyle = `rgba(${r},${g},${b},${baseAlpha.toFixed(3)})`;
        ctx.fillRect(px, py, CELL + 1, CELL + 1);
      }
    }
  }

  // Draw cell borders (edges where nearest seed changes)
  function drawEdges() {
    const STEP = CELL;
    ctx.lineWidth = 0.6;

    for (let py = 0; py < H; py += STEP) {
      for (let px = 0; px < W; px += STEP) {
        const { idx: c0 } = nearest(px, py);
        const { idx: cr } = nearest(px + STEP, py);
        const { idx: cd } = nearest(px, py + STEP);

        if (c0 !== cr) {
          const s = seeds[c0];
          const pulse = 0.3 + 0.4 * Math.sin(t * 0.8 + s.phase);
          ctx.beginPath();
          ctx.moveTo(px + STEP, py);
          ctx.lineTo(px + STEP, py + STEP);
          ctx.strokeStyle = `rgba(${s.col[0]},${s.col[1]},${s.col[2]},${(pulse * 0.5).toFixed(3)})`;
          ctx.stroke();
        }
        if (c0 !== cd) {
          const s = seeds[c0];
          const pulse = 0.3 + 0.4 * Math.sin(t * 0.8 + s.phase);
          ctx.beginPath();
          ctx.moveTo(px, py + STEP);
          ctx.lineTo(px + STEP, py + STEP);
          ctx.strokeStyle = `rgba(${s.col[0]},${s.col[1]},${s.col[2]},${(pulse * 0.5).toFixed(3)})`;
          ctx.stroke();
        }
      }
    }
  }

  // Seed glow dots
  function drawSeeds() {
    for (const s of seeds) {
      const pulse = 0.5 + 0.5 * Math.sin(t * 0.8 + s.phase);
      const r2 = 4 + pulse * 4;
      const grd = ctx.createRadialGradient(s.x, s.y, 0, s.x, s.y, r2 * 3);
      grd.addColorStop(0, `rgba(${s.col[0]},${s.col[1]},${s.col[2]},${(0.5 + pulse * 0.4).toFixed(3)})`);
      grd.addColorStop(1, `rgba(${s.col[0]},${s.col[1]},${s.col[2]},0)`);
      ctx.beginPath();
      ctx.arc(s.x, s.y, r2 * 3, 0, Math.PI * 2);
      ctx.fillStyle = grd;
      ctx.fill();
    }
  }

  function frame() {
    ctx.clearRect(0, 0, W, H);
    t += 0.016;

    // Drift seeds
    for (const s of seeds) {
      s.x += s.vx; s.y += s.vy;
      if (s.x < 0 || s.x > W) s.vx *= -1;
      if (s.y < 0 || s.y > H) s.vy *= -1;
    }

    drawVoronoi();
    drawEdges();
    drawSeeds();

    requestAnimationFrame(frame);
  }

  hero.addEventListener('mousemove', e => {
    const r = hero.getBoundingClientRect();
    mx = e.clientX - r.left;
    my = e.clientY - r.top;
  }, { passive: true });
  hero.addEventListener('mouseleave', () => { mx = -9999; my = -9999; });
  window.addEventListener('resize', resize, { passive: true });

  resize();
  requestAnimationFrame(frame);
})();
