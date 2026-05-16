/**
 * Hero v10 — Magnetic Field Lines
 * Streamlines arc through a multi-pole magnetic field.
 * Poles drift slowly across the canvas; mouse adds a live pole.
 * Click to spawn a new pole at cursor position.
 */
(function () {
  'use strict';
  const canvas = document.getElementById('fhHeroCanvas');
  const hero = canvas && canvas.closest('.fh-hero');
  if (!canvas || !hero) return;
  if (typeof window.matchMedia === 'function' && window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

  const ctx = canvas.getContext('2d');
  const PALETTE = [
    { r: 108, g: 99,  b: 255 }, // accent purple
    { r:  67, g: 217, b: 173 }, // teal
    { r: 255, g: 101, b: 132 }, // pink
    { r: 245, g: 166, b:  35 }, // gold
  ];
  let W = 0, H = 0;
  let mx = -9999, my = -9999; // mouse world coords (off-screen default)

  // ── Poles ────────────────────────────────────────────────────────────────
  function makePole(x, y, charge, col) {
    return {
      x, y,
      vx: (Math.random() - 0.5) * 0.28,
      vy: (Math.random() - 0.5) * 0.28,
      charge,   // +1 or -1
      col,
    };
  }

  let poles = [];

  function initPoles() {
    poles = [
      makePole(W * 0.25, H * 0.35,  1, PALETTE[0]),
      makePole(W * 0.75, H * 0.65, -1, PALETTE[1]),
      makePole(W * 0.65, H * 0.28,  1, PALETTE[2]),
      makePole(W * 0.35, H * 0.72, -1, PALETTE[3]),
      makePole(W * 0.50, H * 0.50,  1, PALETTE[0]),
      makePole(W * 0.80, H * 0.30, -1, PALETTE[1]),
    ];
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
    initPoles();
  }

  // ── Field math ────────────────────────────────────────────────────────────
  function fieldAt(px, py) {
    let fx = 0, fy = 0;
    for (const p of poles) {
      const dx = px - p.x, dy = py - p.y;
      const r2 = dx * dx + dy * dy;
      if (r2 < 1) continue;
      const r3 = Math.pow(r2, 1.5);
      fx += p.charge * dx / r3;
      fy += p.charge * dy / r3;
    }
    // Mouse pole (always positive, weak)
    if (mx > 0) {
      const dx = px - mx, dy = py - my;
      const r2 = dx * dx + dy * dy;
      if (r2 > 1) {
        const r3 = Math.pow(r2, 1.5) * 1.8;
        fx += dx / r3;
        fy += dy / r3;
      }
    }
    return { fx, fy };
  }

  // ── Streamline tracing ────────────────────────────────────────────────────
  const STEP   = 4;      // px per integration step
  const MAX_PTS = 160;   // max points per line

  function traceStreamline(sx, sy) {
    const pts = [{ x: sx, y: sy }];
    let x = sx, y = sy;
    for (let i = 0; i < MAX_PTS; i++) {
      const { fx, fy } = fieldAt(x, y);
      const mag = Math.sqrt(fx * fx + fy * fy);
      if (mag < 1e-10) break;
      x += (fx / mag) * STEP;
      y += (fy / mag) * STEP;
      if (x < -40 || x > W + 40 || y < -40 || y > H + 40) break;
      pts.push({ x, y });
    }
    return pts;
  }

  function drawStreamline(pts, col, alpha) {
    if (pts.length < 2) return;
    for (let i = 1; i < pts.length; i++) {
      const t = i / pts.length;
      const a = alpha * Math.sin(t * Math.PI); // fade in + out
      ctx.beginPath();
      ctx.moveTo(pts[i - 1].x, pts[i - 1].y);
      ctx.lineTo(pts[i].x, pts[i].y);
      ctx.strokeStyle = `rgba(${col.r},${col.g},${col.b},${a.toFixed(3)})`;
      ctx.lineWidth = 0.9 + t * 0.6;
      ctx.stroke();
    }
  }

  // Seed points: ring around each positive pole
  const SEEDS_PER_POLE = 10;

  function seedsFor(pole) {
    const seeds = [];
    for (let i = 0; i < SEEDS_PER_POLE; i++) {
      const angle = (i / SEEDS_PER_POLE) * Math.PI * 2;
      seeds.push({
        x: pole.x + Math.cos(angle) * 18,
        y: pole.y + Math.sin(angle) * 18,
        col: pole.col,
      });
    }
    return seeds;
  }

  // ── Pole dot glow ─────────────────────────────────────────────────────────
  function drawPole(p) {
    const r = 14;
    const grd = ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, r);
    grd.addColorStop(0, `rgba(${p.col.r},${p.col.g},${p.col.b},0.75)`);
    grd.addColorStop(1, `rgba(${p.col.r},${p.col.g},${p.col.b},0)`);
    ctx.beginPath();
    ctx.arc(p.x, p.y, r, 0, Math.PI * 2);
    ctx.fillStyle = grd;
    ctx.fill();

    // Core dot
    ctx.beginPath();
    ctx.arc(p.x, p.y, 3.5, 0, Math.PI * 2);
    ctx.fillStyle = `rgba(${p.col.r},${p.col.g},${p.col.b},0.9)`;
    ctx.fill();

    // + / − label
    ctx.fillStyle = 'rgba(255,255,255,0.6)';
    ctx.font = 'bold 9px sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(p.charge > 0 ? '+' : '−', p.x, p.y);
  }

  // ── Frame loop ────────────────────────────────────────────────────────────
  function frame() {
    ctx.clearRect(0, 0, W, H);

    // Drift poles, bounce off edges
    for (const p of poles) {
      p.x += p.vx; p.y += p.vy;
      if (p.x < 60 || p.x > W - 60) p.vx *= -1;
      if (p.y < 60 || p.y > H - 60) p.vy *= -1;
      p.x = Math.max(60, Math.min(W - 60, p.x));
      p.y = Math.max(60, Math.min(H - 60, p.y));
    }

    // Draw field lines from every positive pole
    for (const p of poles) {
      if (p.charge < 0) continue;
      for (const s of seedsFor(p)) {
        const pts = traceStreamline(s.x, s.y);
        drawStreamline(pts, s.col, 0.45);
      }
    }

    // Draw poles on top
    for (const p of poles) drawPole(p);

    // Mouse pole indicator
    if (mx > 0 && mx < W) {
      const grd = ctx.createRadialGradient(mx, my, 0, mx, my, 22);
      grd.addColorStop(0, 'rgba(255,255,255,0.18)');
      grd.addColorStop(1, 'rgba(255,255,255,0)');
      ctx.beginPath();
      ctx.arc(mx, my, 22, 0, Math.PI * 2);
      ctx.fillStyle = grd;
      ctx.fill();
    }

    requestAnimationFrame(frame);
  }

  // Click spawns a temporary drifting pole (max 2 extra)
  const MAX_EXTRA = 2;
  let extraCount = 0;

  hero.addEventListener('click', e => {
    if (extraCount >= MAX_EXTRA) {
      poles.splice(6, MAX_EXTRA); // remove old extras
      extraCount = 0;
    }
    const r = hero.getBoundingClientRect();
    const charge = extraCount % 2 === 0 ? 1 : -1;
    poles.push(makePole(e.clientX - r.left, e.clientY - r.top, charge, PALETTE[extraCount % PALETTE.length]));
    extraCount++;
  });

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
