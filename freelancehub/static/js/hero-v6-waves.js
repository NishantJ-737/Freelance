/**
 * Hero v6 — Layered Sine Waves
 * Multiple wave layers flow across the hero; mouse shifts their phase.
 */
(function () {
  'use strict';
  const canvas = document.getElementById('fhHeroCanvas');
  const hero = canvas && canvas.closest('.fh-hero');
  if (!canvas || !hero) return;
  if (typeof window.matchMedia === 'function' && window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

  const ctx = canvas.getContext('2d');
  let W = 0, H = 0;
  let mx = 0.5;

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

  // amp/freq relative to canvas; yOff = 0 (top) … 1 (bottom)
  const WAVES = [
    { amp: 0.085, freq: 1.7, sp: 0.00070, col: '108,99,255', alpha: 0.14, lw: 1.8, yOff: 0.38 },
    { amp: 0.060, freq: 2.5, sp: 0.00110, col: '67,217,173', alpha: 0.12, lw: 1.2, yOff: 0.48 },
    { amp: 0.100, freq: 1.1, sp: 0.00048, col: '255,101,132', alpha: 0.10, lw: 2.4, yOff: 0.58 },
    { amp: 0.042, freq: 3.3, sp: 0.00160, col: '245,166,35', alpha: 0.09, lw: 0.9, yOff: 0.33 },
    { amp: 0.072, freq: 0.8, sp: 0.00035, col: '108,99,255', alpha: 0.07, lw: 3.2, yOff: 0.68 },
    { amp: 0.050, freq: 2.0, sp: 0.00090, col: '67,217,173', alpha: 0.08, lw: 1.0, yOff: 0.72 },
  ];

  function sampleY(w, x, t) {
    const phase = t * w.sp * 1000 + (mx - 0.5) * 3.5;
    const nx = x / W;
    return H * w.yOff
      + H * w.amp * Math.sin(nx * Math.PI * 2 * w.freq + phase)
      + H * w.amp * 0.28 * Math.sin(nx * Math.PI * 2 * w.freq * 0.5 + phase * 0.7);
  }

  function drawWave(w, t) {
    const STEP = 3;

    // Filled area below the wave line
    ctx.beginPath();
    ctx.moveTo(0, sampleY(w, 0, t));
    for (let x = STEP; x <= W; x += STEP) ctx.lineTo(x, sampleY(w, x, t));
    ctx.lineTo(W, H); ctx.lineTo(0, H); ctx.closePath();
    const fillGrad = ctx.createLinearGradient(0, H * w.yOff - H * w.amp, 0, H * w.yOff + H * w.amp);
    fillGrad.addColorStop(0, `rgba(${w.col},${w.alpha})`);
    fillGrad.addColorStop(1, `rgba(${w.col},0)`);
    ctx.fillStyle = fillGrad;
    ctx.fill();

    // Bright wave line on top
    ctx.beginPath();
    ctx.moveTo(0, sampleY(w, 0, t));
    for (let x = STEP; x <= W; x += STEP) ctx.lineTo(x, sampleY(w, x, t));
    ctx.strokeStyle = `rgba(${w.col},${(w.alpha * 2.2).toFixed(3)})`;
    ctx.lineWidth = w.lw;
    ctx.lineJoin = 'round';
    ctx.stroke();

    // Floating highlight dots riding the wave crest
    const DOT_COUNT = 5;
    for (let i = 0; i < DOT_COUNT; i++) {
      const t2 = (t * w.sp * 300 + i * (W / DOT_COUNT)) % W;
      const dx = (t2 + W) % W;
      const dy = sampleY(w, dx, t);
      ctx.beginPath();
      ctx.arc(dx, dy, w.lw + 0.8, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(${w.col},${w.alpha * 4})`;
      ctx.fill();
    }
  }

  function frame(ts) {
    ctx.clearRect(0, 0, W, H);
    WAVES.forEach(w => drawWave(w, ts));
    requestAnimationFrame(frame);
  }

  hero.addEventListener('mousemove', e => {
    const r = hero.getBoundingClientRect();
    mx = (e.clientX - r.left) / r.width;
  }, { passive: true });
  hero.addEventListener('mouseleave', () => { mx = 0.5; });
  window.addEventListener('resize', resize, { passive: true });

  resize();
  requestAnimationFrame(frame);
})();
