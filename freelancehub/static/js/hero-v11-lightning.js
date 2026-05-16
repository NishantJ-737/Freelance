/**
 * Hero v11 — Lightning Arcs (final)
 * Electric bolts fork and branch between drifting anchor nodes.
 * - Hover: nearest node snaps a bolt to cursor
 * - Click: blast arcs to all nearby nodes
 * - Hold: intensity ramps up — more arcs, brighter, more forks
 * - Bolts dim near centre text, brighten toward edges
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

  // Hold state — ramps 0→1 while held, decays when released
  let held = false;
  let holdIntensity = 0;

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

  // Returns 0–1 multiplier: dim near centre text, bright near edges
  function edgeFade(x, y) {
    const dx = x - W * 0.5;
    const dy = y - H * 0.44;
    const dist = Math.sqrt(dx * dx + dy * dy);
    const innerR = Math.min(W, H) * 0.20;
    const outerR = Math.min(W, H) * 0.46;
    return Math.min(1, Math.max(0.06, (dist - innerR) / (outerR - innerR)));
  }

  // Recursive lightning bolt
  function bolt(x1, y1, x2, y2, depth, col, alpha) {
    if (depth === 0 || alpha < 0.02) {
      const fade = edgeFade((x1 + x2) / 2, (y1 + y2) / 2);
      const a = alpha * fade;
      if (a < 0.015) return;
      ctx.beginPath();
      ctx.moveTo(x1, y1);
      ctx.lineTo(x2, y2);
      ctx.strokeStyle = `rgba(${col},${a.toFixed(3)})`;
      ctx.lineWidth = 0.5 + fade * 0.8;
      ctx.stroke();
      return;
    }

    const jitter = depth * 28 * (1 + holdIntensity * 0.6); // more jagged when held
    const mx2 = (x1 + x2) / 2 + (Math.random() - 0.5) * jitter;
    const my2 = (y1 + y2) / 2 + (Math.random() - 0.5) * jitter;

    bolt(x1, y1, mx2, my2, depth - 1, col, alpha);
    bolt(mx2, my2, x2, y2, depth - 1, col, alpha);

    // Fork branches — more frequent and longer while held
    const forkChance = 0.35 + holdIntensity * 0.45;
    if (depth >= 2 && Math.random() < forkChance) {
      const spread = depth * 55 * (1 + holdIntensity * 0.8);
      const fx = mx2 + (Math.random() - 0.5) * spread;
      const fy = my2 + (Math.random() - 0.5) * spread;
      bolt(mx2, my2, fx, fy, depth - 2, col, alpha * (0.45 + holdIntensity * 0.25));
    }
  }

  // Per-arc state
  let arcs = [];
  let frameCount = 0;

  function spawnArc(alphaBoost = 0) {
    if (nodes.length < 2) return;
    const i = Math.floor(Math.random() * nodes.length);
    let j = i;
    while (j === i) j = Math.floor(Math.random() * nodes.length);
    const n1 = nodes[i], n2 = nodes[j];
    if (Math.hypot(n1.x - n2.x, n1.y - n2.y) > W * 0.75) return;
    arcs.push({ x1: n1.x, y1: n1.y, x2: n2.x, y2: n2.y, col: n1.col, alpha: 0.7 + alphaBoost });
  }

  function frame() {
    // Trail fade — tighter when intense so bolts look crisper
    const trailAlpha = held ? 0.35 + holdIntensity * 0.15 : 0.28;
    ctx.fillStyle = `rgba(10,10,20,${trailAlpha})`;
    ctx.fillRect(0, 0, W, H);

    // Ramp hold intensity
    if (held) {
      holdIntensity = Math.min(1, holdIntensity + 0.018);
    } else {
      holdIntensity = Math.max(0, holdIntensity - 0.03);
    }

    frameCount++;
    // Spawn more arcs the more intensely held (interval shrinks from 18→4)
    const interval = Math.max(4, Math.round(18 - holdIntensity * 14));
    if (frameCount % interval === 0) spawnArc(holdIntensity * 0.5);

    // Mouse arc — brighter + deeper when held
    if (mx > 0) {
      const closest = nodes.reduce((best, n) => {
        const d = Math.hypot(n.x - mx, n.y - my);
        return d < best.d ? { n, d } : best;
      }, { n: null, d: Infinity });
      if (closest.d < W * 0.4) {
        const mouseAlpha = 0.5 + holdIntensity * 0.45;
        const mouseDepth = holdIntensity > 0.5 ? 4 : 3;
        bolt(closest.n.x, closest.n.y, mx, my, mouseDepth, closest.n.col, mouseAlpha);

        // At high intensity arc to additional nodes too
        if (holdIntensity > 0.6) {
          const sorted = [...nodes]
            .map(n => ({ n, d: Math.hypot(n.x - mx, n.y - my) }))
            .sort((a, b) => a.d - b.d);
          for (let k = 1; k < Math.min(3, sorted.length); k++) {
            if (sorted[k].d < W * 0.5) {
              bolt(sorted[k].n.x, sorted[k].n.y, mx, my, 2, sorted[k].n.col,
                   (holdIntensity - 0.6) * 0.8);
            }
          }
        }
      }
    }

    // Draw and age arcs
    arcs = arcs.filter(a => a.alpha > 0.03);
    for (const a of arcs) {
      const depth = holdIntensity > 0.5 ? 5 : 4;
      bolt(a.x1, a.y1, a.x2, a.y2, depth, a.col, a.alpha);
      a.alpha *= 0.82;
    }

    // Drift nodes + glow
    for (const n of nodes) {
      n.x += n.vx; n.y += n.vy;
      if (n.x < 0 || n.x > W) n.vx *= -1;
      if (n.y < 0 || n.y > H) n.vy *= -1;

      const glowR = 12 + holdIntensity * 10;
      const grd = ctx.createRadialGradient(n.x, n.y, 0, n.x, n.y, glowR);
      grd.addColorStop(0, `rgba(${n.col},${0.7 + holdIntensity * 0.3})`);
      grd.addColorStop(1, `rgba(${n.col},0)`);
      ctx.beginPath();
      ctx.arc(n.x, n.y, glowR, 0, Math.PI * 2);
      ctx.fillStyle = grd;
      ctx.fill();
    }

    requestAnimationFrame(frame);
  }

  // Click: blast arcs to all nearby nodes
  hero.addEventListener('click', e => {
    const r = hero.getBoundingClientRect();
    const cx = e.clientX - r.left;
    const cy = e.clientY - r.top;
    const col = PALETTE[Math.floor(Math.random() * PALETTE.length)];
    for (const n of nodes) {
      if (Math.hypot(n.x - cx, n.y - cy) < W * 0.55) {
        arcs.push({ x1: cx, y1: cy, x2: n.x, y2: n.y, col, alpha: 0.85 + holdIntensity * 0.15 });
      }
    }
  });

  hero.addEventListener('mousedown', () => { held = true; });
  hero.addEventListener('mouseup',   () => { held = false; });
  hero.addEventListener('mouseleave', () => { mx = -1; my = -1; held = false; });

  hero.addEventListener('mousemove', e => {
    const r = hero.getBoundingClientRect();
    mx = e.clientX - r.left;
    my = e.clientY - r.top;
  }, { passive: true });

  window.addEventListener('resize', resize, { passive: true });

  resize();
  requestAnimationFrame(frame);
})();
