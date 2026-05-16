/**
 * Hero v11 — Lightning Arcs
 * Electric bolts fork and branch between drifting anchor nodes.
 * Mouse proximity attracts a bolt toward the cursor.
 */
(function () {
  'use strict';
  const canvas = document.getElementById('fhHeroCanvas');
  const hero = canvas && canvas.closest('.fh-hero');
  if (!canvas || !hero) return;
  if (typeof window.matchMedia === 'function' && window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

  const ctx = canvas.getContext('2d');
  const PALETTE = ['108,99,255', '67,217,173', '255,101,132', '245,166,35', '200,200,255'];
  let W = 0, H = 0;
  let mx = -1, my = -1;

  // Anchor nodes that bolts arc between
  let nodes = [];
  const NODE_COUNT = 7;

  function makeNode() {
    return {
      x: Math.random() * W,
      y: Math.random() * H,
      vx: (Math.random() - 0.5) * 0.5,
      vy: (Math.random() - 0.5) * 0.5,
      col: PALETTE[Math.floor(Math.random() * PALETTE.length)],
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
    nodes = Array.from({ length: NODE_COUNT }, makeNode);
  }

  // Returns a 0–1 multiplier: dim near centre (text area), bright near edges
  function edgeFade(x, y) {
    const dx = x - W * 0.5;
    const dy = y - H * 0.44; // text sits slightly above centre
    const dist = Math.sqrt(dx * dx + dy * dy);
    const innerR = Math.min(W, H) * 0.20; // full dim inside here
    const outerR = Math.min(W, H) * 0.46; // full bright beyond here
    return Math.min(1, Math.max(0.06, (dist - innerR) / (outerR - innerR)));
  }

  // Recursive lightning bolt from (x1,y1) to (x2,y2)
  function bolt(x1, y1, x2, y2, depth, col, alpha) {
    if (depth === 0 || alpha < 0.02) {
      const fade = edgeFade((x1 + x2) / 2, (y1 + y2) / 2);
      const a = alpha * fade;
      if (a < 0.015) return;
      ctx.beginPath();
      ctx.moveTo(x1, y1);
      ctx.lineTo(x2, y2);
      ctx.strokeStyle = `rgba(${col},${a.toFixed(3)})`;
      ctx.lineWidth = 0.5 + fade * 0.8; // thicker toward edges too
      ctx.stroke();
      return;
    }

    const mx2 = (x1 + x2) / 2 + (Math.random() - 0.5) * (depth * 28);
    const my2 = (y1 + y2) / 2 + (Math.random() - 0.5) * (depth * 28);

    bolt(x1, y1, mx2, my2, depth - 1, col, alpha);
    bolt(mx2, my2, x2, y2, depth - 1, col, alpha);

    // Fork branch
    if (depth >= 2 && Math.random() < 0.35) {
      const fx = mx2 + (Math.random() - 0.5) * depth * 55;
      const fy = my2 + (Math.random() - 0.5) * depth * 55;
      bolt(mx2, my2, fx, fy, depth - 2, col, alpha * 0.45);
    }
  }

  // Per-arc state: which pair of nodes, current alpha, timer
  let arcs = [];
  const ARC_INTERVAL = 18; // frames between new arcs
  let frameCount = 0;

  function spawnArc() {
    if (nodes.length < 2) return;
    const i = Math.floor(Math.random() * nodes.length);
    let j = i;
    while (j === i) j = Math.floor(Math.random() * nodes.length);
    const n1 = nodes[i], n2 = nodes[j];
    const dist = Math.hypot(n1.x - n2.x, n1.y - n2.y);
    if (dist > W * 0.75) return; // skip very far pairs
    arcs.push({ x1: n1.x, y1: n1.y, x2: n2.x, y2: n2.y, col: n1.col, alpha: 0.7, life: 0 });
  }

  function frame() {
    ctx.fillStyle = 'rgba(10,10,20,0.28)';
    ctx.fillRect(0, 0, W, H);

    frameCount++;
    if (frameCount % ARC_INTERVAL === 0) spawnArc();

    // Mouse arc
    if (mx > 0) {
      const closest = nodes.reduce((best, n) => {
        const d = Math.hypot(n.x - mx, n.y - my);
        return d < best.d ? { n, d } : best;
      }, { n: null, d: Infinity });
      if (closest.d < W * 0.4) {
        bolt(closest.n.x, closest.n.y, mx, my, 3, closest.n.col, 0.5);
      }
    }

    // Draw and age arcs
    arcs = arcs.filter(a => a.alpha > 0.03);
    for (const a of arcs) {
      bolt(a.x1, a.y1, a.x2, a.y2, 4, a.col, a.alpha);
      a.alpha *= 0.82;
    }

    // Drift nodes + draw glow dots
    for (const n of nodes) {
      n.x += n.vx; n.y += n.vy;
      if (n.x < 0 || n.x > W) n.vx *= -1;
      if (n.y < 0 || n.y > H) n.vy *= -1;

      const grd = ctx.createRadialGradient(n.x, n.y, 0, n.x, n.y, 12);
      grd.addColorStop(0, `rgba(${n.col},0.7)`);
      grd.addColorStop(1, `rgba(${n.col},0)`);
      ctx.beginPath();
      ctx.arc(n.x, n.y, 12, 0, Math.PI * 2);
      ctx.fillStyle = grd;
      ctx.fill();
    }

    requestAnimationFrame(frame);
  }

  // Click: blast arcs from click point to all nearby nodes
  hero.addEventListener('click', e => {
    const r = hero.getBoundingClientRect();
    const cx = e.clientX - r.left;
    const cy = e.clientY - r.top;
    const col = PALETTE[Math.floor(Math.random() * PALETTE.length)];
    for (const n of nodes) {
      const d = Math.hypot(n.x - cx, n.y - cy);
      if (d < W * 0.55) {
        arcs.push({ x1: cx, y1: cy, x2: n.x, y2: n.y, col, alpha: 0.85 });
      }
    }
  });

  hero.addEventListener('mousemove', e => {
    const r = hero.getBoundingClientRect();
    mx = e.clientX - r.left;
    my = e.clientY - r.top;
  }, { passive: true });
  hero.addEventListener('mouseleave', () => { mx = -1; my = -1; });
  window.addEventListener('resize', resize, { passive: true });

  resize();
  requestAnimationFrame(frame);
})();
