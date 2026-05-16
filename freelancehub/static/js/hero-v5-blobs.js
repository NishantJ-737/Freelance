/**
 * Hero v5 — Morphing Gradient Blobs
 * Large semi-transparent blobs drift and breathe; mouse attracts the nearest one.
 */
(function () {
  'use strict';
  const canvas = document.getElementById('fhHeroCanvas');
  const hero = canvas && canvas.closest('.fh-hero');
  if (!canvas || !hero) return;
  if (typeof window.matchMedia === 'function' && window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

  const ctx = canvas.getContext('2d');
  let W = 0, H = 0;
  let mx = null, my = null;

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

  // Blob definitions (normalized to [0,1])
  const BLOBS = [
    { nx: 0.72, ny: 0.35, nr: 0.38, col: [108, 99, 255],  sp: 0.00042, ph: 0.0 },
    { nx: 0.88, ny: 0.68, nr: 0.30, col: [67,  217, 173], sp: 0.00058, ph: 2.1 },
    { nx: 0.58, ny: 0.78, nr: 0.24, col: [255, 101, 132], sp: 0.00050, ph: 4.3 },
    { nx: 0.94, ny: 0.22, nr: 0.20, col: [245, 166, 35],  sp: 0.00070, ph: 1.4 },
    { nx: 0.50, ny: 0.45, nr: 0.18, col: [108, 99, 255],  sp: 0.00035, ph: 3.7 },
  ];

  function drawBlob(b, t) {
    // Drift position using two independent sine waves
    const bx = (b.nx + Math.sin(t * b.sp + b.ph) * 0.07 + Math.sin(t * b.sp * 0.6 + b.ph + 1) * 0.03) * W;
    const by = (b.ny + Math.cos(t * b.sp * 0.8 + b.ph) * 0.055 + Math.cos(t * b.sp * 0.4 + b.ph + 2) * 0.025) * H;

    // Mouse attraction (nearest blob only, handled via slight pull)
    let fx = bx, fy = by;
    if (mx !== null) {
      const ddx = mx - bx, ddy = my - by;
      const dd = Math.sqrt(ddx * ddx + ddy * ddy);
      const pull = Math.max(0, 1 - dd / (W * 0.4)) * 30;
      fx = bx + (ddx / (dd || 1)) * pull;
      fy = by + (ddy / (dd || 1)) * pull;
    }

    // Breathing radius
    const br = (b.nr * Math.min(W, H)) * (1 + Math.sin(t * b.sp * 1.4 + b.ph) * 0.14);

    const grd = ctx.createRadialGradient(fx, fy, 0, fx, fy, br);
    grd.addColorStop(0,   `rgba(${b.col.join(',')},0.22)`);
    grd.addColorStop(0.45,`rgba(${b.col.join(',')},0.10)`);
    grd.addColorStop(1,   `rgba(${b.col.join(',')},0)`);

    ctx.beginPath();
    ctx.arc(fx, fy, br, 0, Math.PI * 2);
    ctx.fillStyle = grd;
    ctx.fill();
  }

  function frame(ts) {
    ctx.clearRect(0, 0, W, H);
    BLOBS.forEach(b => drawBlob(b, ts));
    requestAnimationFrame(frame);
  }

  hero.addEventListener('mousemove', e => {
    const r = hero.getBoundingClientRect();
    mx = e.clientX - r.left; my = e.clientY - r.top;
  }, { passive: true });
  hero.addEventListener('mouseleave', () => { mx = null; my = null; });
  window.addEventListener('resize', resize, { passive: true });

  resize();
  requestAnimationFrame(frame);
})();
