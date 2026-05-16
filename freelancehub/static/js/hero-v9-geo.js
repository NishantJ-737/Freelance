/**
 * Hero v9 — Geometric Pulse
 * Triangulated grid; edges light up in radial waves from mouse clicks
 * and a slow ambient pulse. Mouse proximity brightens nearby vertices.
 */
(function () {
  'use strict';
  const canvas = document.getElementById('fhHeroCanvas');
  const hero = canvas && canvas.closest('.fh-hero');
  if (!canvas || !hero) return;
  if (typeof window.matchMedia === 'function' && window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

  const ctx = canvas.getContext('2d');
  const PALETTE = ['108,99,255', '67,217,173', '255,101,132', '245,166,35'];
  let W = 0, H = 0;
  let mx = 0.5, my = 0.5; // normalized mouse

  // Grid settings
  const COLS = 18, ROWS = 10;
  let pts = []; // flat array of {x,y,ox,oy} — ox/oy = base position

  // Active pulses: {x,y,r,maxR,col,born}
  let pulses = [];
  // Ambient slow pulse
  let ambT = 0;

  function resize() {
    const r = hero.getBoundingClientRect();
    W = r.width; H = r.height;
    const dpr = Math.min(devicePixelRatio || 1, 2);
    canvas.width = Math.floor(W * dpr);
    canvas.height = Math.floor(H * dpr);
    canvas.style.width = W + 'px';
    canvas.style.height = H + 'px';
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    buildGrid();
  }

  function buildGrid() {
    pts = [];
    const cellW = W / COLS;
    const cellH = H / ROWS;
    for (let row = 0; row <= ROWS; row++) {
      for (let col = 0; col <= COLS; col++) {
        // Slight hex offset on odd rows
        const xOff = (row % 2 === 1) ? cellW * 0.5 : 0;
        const bx = col * cellW + xOff;
        const by = row * cellH;
        // Small random jitter baked in
        const jx = (Math.random() - 0.5) * cellW * 0.38;
        const jy = (Math.random() - 0.5) * cellH * 0.38;
        pts.push({ ox: bx + jx, oy: by + jy });
      }
    }
  }

  // Returns alpha [0,1] for an edge midpoint given all active pulses + ambient
  function edgeGlow(ex, ey, t) {
    let glow = 0;

    // Ambient radial pulse from centre
    const dx = ex - W * 0.5, dy = ey - H * 0.5;
    const distC = Math.sqrt(dx * dx + dy * dy);
    const ambR = (ambT % 1) * Math.max(W, H) * 0.85;
    const ambDelta = Math.abs(distC - ambR);
    glow += Math.max(0, 1 - ambDelta / (W * 0.12)) * 0.07;

    // Click pulses
    for (const p of pulses) {
      const px = ex - p.x, py = ey - p.y;
      const d = Math.sqrt(px * px + py * py);
      const delta = Math.abs(d - p.r);
      const age = (t - p.born) / 1200; // 0→1 over 1.2 s
      if (age > 1) continue;
      const fade = 1 - age;
      glow += Math.max(0, 1 - delta / (W * 0.08)) * fade * 0.65;
    }

    // Mouse proximity glow
    const mdx = ex - mx * W, mdy = ey - my * H;
    const md = Math.sqrt(mdx * mdx + mdy * mdy);
    glow += Math.max(0, 1 - md / (W * 0.18)) * 0.22;

    return Math.min(glow, 1);
  }

  function edgeColor(ex, ey) {
    // Pick palette colour based on position
    const idx = Math.floor(((ex / W) * 2 + (ey / H)) * 1.5) % PALETTE.length;
    return PALETTE[idx];
  }

  function frame(t) {
    ctx.clearRect(0, 0, W, H);
    ambT += 0.0004;

    // Prune dead pulses
    pulses = pulses.filter(p => (t - p.born) < 1400);
    // Advance pulse radii
    for (const p of pulses) {
      p.r = ((t - p.born) / 1200) * p.maxR;
    }

    const cols1 = COLS + 1;

    // Draw triangulated edges
    for (let row = 0; row < ROWS; row++) {
      for (let col = 0; col < COLS; col++) {
        // Four corners of this cell
        const tl = pts[row * cols1 + col];
        const tr = pts[row * cols1 + col + 1];
        const blRow = row + 1;
        // Hex offset
        const off = (row % 2 === 1) ? 0 : 0; // already baked into ox/oy
        const bl = pts[blRow * cols1 + col];
        const br = pts[blRow * cols1 + col + 1];

        if (!tl || !tr || !bl || !br) continue;

        // Two triangles: tl-tr-bl and tr-br-bl
        const tris = [
          [tl, tr, bl],
          [tr, br, bl],
        ];

        for (const tri of tris) {
          const [a, b, c] = tri;
          const ex = (a.ox + b.ox + c.ox) / 3;
          const ey = (a.oy + b.oy + c.oy) / 3;
          const g = edgeGlow(ex, ey, t);
          if (g < 0.01) continue;

          const col3 = edgeColor(ex, ey);

          // Triangle fill (very faint)
          ctx.beginPath();
          ctx.moveTo(a.ox, a.oy);
          ctx.lineTo(b.ox, b.oy);
          ctx.lineTo(c.ox, c.oy);
          ctx.closePath();
          ctx.fillStyle = `rgba(${col3},${(g * 0.06).toFixed(3)})`;
          ctx.fill();

          // Triangle edges
          const edges = [[a, b], [b, c], [c, a]];
          for (const [p1, p2] of edges) {
            const emx = (p1.ox + p2.ox) / 2;
            const emy = (p1.oy + p2.oy) / 2;
            const eg = edgeGlow(emx, emy, t);
            if (eg < 0.01) continue;
            ctx.beginPath();
            ctx.moveTo(p1.ox, p1.oy);
            ctx.lineTo(p2.ox, p2.oy);
            ctx.strokeStyle = `rgba(${col3},${(eg * 0.75).toFixed(3)})`;
            ctx.lineWidth = 0.6 + eg * 1.4;
            ctx.stroke();
          }
        }
      }
    }

    // Vertex dots near mouse or pulsed
    for (const p of pts) {
      const mdx = p.ox - mx * W, mdy = p.oy - my * H;
      const md = Math.sqrt(mdx * mdx + mdy * mdy);
      const prox = Math.max(0, 1 - md / (W * 0.14));
      if (prox < 0.05) continue;
      ctx.beginPath();
      ctx.arc(p.ox, p.oy, 1 + prox * 2.5, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(255,255,255,${(prox * 0.55).toFixed(3)})`;
      ctx.fill();
    }

    requestAnimationFrame(frame);
  }

  // Click spawns a pulse
  hero.addEventListener('click', e => {
    const r = hero.getBoundingClientRect();
    pulses.push({
      x: e.clientX - r.left,
      y: e.clientY - r.top,
      r: 0,
      maxR: Math.max(W, H) * 0.9,
      col: PALETTE[Math.floor(Math.random() * PALETTE.length)],
      born: performance.now(),
    });
  });

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
