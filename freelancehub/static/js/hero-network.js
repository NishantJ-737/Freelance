/**
 * FreelanceHub hero — “Marketplace constellation”
 * Network mesh suggesting connections between talent & projects (not a stock sphere demo).
 * Vanilla Canvas + rAF; respects prefers-reduced-motion.
 */
(function () {
  'use strict';

  const canvas = document.getElementById('fhHeroCanvas');
  const hero = canvas && canvas.closest('.fh-hero');
  if (!canvas || !hero) return;

  const prefersReduced =
    typeof window.matchMedia === 'function' &&
    window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  const ctx = canvas.getContext('2d');
  const ACCENT = [108, 99, 255];
  const TEAL = [67, 217, 173];
  const CORAL = [255, 101, 132];
  const GOLD = [245, 166, 35];

  function mix(a, b, t) {
    return a.map((v, i) => Math.round(v + (b[i] - v) * t));
  }

  /** Even distribution on sphere + slight ellipsoid (unique silhouette vs perfect ball) */
  function buildNodes(count, rx, ry, rz) {
    const nodes = [];
    const inc = Math.PI * (3 - Math.sqrt(5));
    for (let i = 0; i < count; i++) {
      const y = 1 - (i / (count - 1 || 1)) * 2;
      const r = Math.sqrt(Math.max(0, 1 - y * y));
      const phi = i * inc;
      const x = Math.cos(phi) * r * rx;
      const yy = y * ry;
      const z = Math.sin(phi) * r * rz;
      const hue = i % 4;
      const pal = [ACCENT, TEAL, CORAL, GOLD][hue];
      const pal2 = [TEAL, ACCENT, GOLD, CORAL][hue];
      nodes.push({
        ox: x,
        oy: yy,
        oz: z,
        rgb: mix(pal, pal2, (i % 7) / 10),
      });
    }
    return nodes;
  }

  function dist3(a, b) {
    const dx = a.ox - b.ox;
    const dy = a.oy - b.oy;
    const dz = a.oz - b.oz;
    return Math.sqrt(dx * dx + dy * dy + dz * dz);
  }

  /** Neighbor edges only — reads as a “network”, stays performant */
  function buildEdges(nodeList, thresh) {
    const edges = [];
    const n = nodeList.length;
    for (let i = 0; i < n; i++) {
      for (let j = i + 1; j < n; j++) {
        const d = dist3(nodeList[i], nodeList[j]);
        if (d < thresh) edges.push([i, j, d]);
      }
    }
    return edges;
  }

  const nodes = buildNodes(72, 1.15, 0.92, 1.08);
  const edges = buildEdges(nodes, 0.42);

  let rotY = 0;
  let rotX = 0.18;
  let targetBoostY = 0;
  let targetBoostX = 0;
  let mx = 0;
  let my = 0;
  let raf = 0;

  function rotateY(p, a) {
    const c = Math.cos(a);
    const s = Math.sin(a);
    return {
      x: p.x * c + p.z * s,
      y: p.y,
      z: -p.x * s + p.z * c,
    };
  }

  function rotateX(p, a) {
    const c = Math.cos(a);
    const s = Math.sin(a);
    return {
      x: p.x,
      y: p.y * c - p.z * s,
      z: p.y * s + p.z * c,
    };
  }

  function project(p, w, h) {
    const perspective = 520;
    const sc = perspective / (perspective + p.z * 160);
    const cx = w * 0.5;
    const cy = h * 0.52;
    return {
      x: cx + p.x * sc * (h * 0.42),
      y: cy + p.y * sc * (h * 0.42),
      z: p.z,
      sc,
    };
  }

  function paint(w, h, frozen) {
    ctx.clearRect(0, 0, w, h);
    const working = nodes.map((n) => {
      let p = { x: n.ox, y: n.oy, z: n.oz };
      p = rotateY(p, rotY);
      p = rotateX(p, rotX);
      return { ...p, rgb: n.rgb };
    });

    const projected = working.map((p) => project(p, w, h));

    edges.sort((a, b) => {
      const za = (working[a[0]].z + working[a[1]].z) / 2;
      const zb = (working[b[0]].z + working[b[1]].z) / 2;
      return za - zb;
    });

    for (let i = 0; i < edges.length; i++) {
      const [ia, ib] = edges[i];
      const pa = projected[ia];
      const pb = projected[ib];
      const depth = (working[ia].z + working[ib].z) / 2;
      const alpha = frozen ? 0.14 : 0.09 + (depth + 0.9) * 0.07;
      const midRgb = mix(working[ia].rgb, working[ib].rgb, 0.5);
      ctx.strokeStyle = `rgba(${midRgb[0]},${midRgb[1]},${midRgb[2]},${Math.max(0.04, Math.min(0.28, alpha))})`;
      ctx.lineWidth = Math.max(0.35, 0.55 * ((pa.sc + pb.sc) / 2));
      ctx.beginPath();
      ctx.moveTo(pa.x, pa.y);
      ctx.lineTo(pb.x, pb.y);
      ctx.stroke();
    }

    projected.forEach((p, idx) => {
      const depth = working[idx].z;
      const a = frozen ? 0.35 : 0.22 + (depth + 1) * 0.12;
      ctx.fillStyle = `rgba(${working[idx].rgb[0]},${working[idx].rgb[1]},${working[idx].rgb[2]},${Math.max(0.15, Math.min(0.65, a))})`;
      const r = Math.max(1.2, 2.4 * p.sc);
      ctx.beginPath();
      ctx.arc(p.x, p.y, r, 0, Math.PI * 2);
      ctx.fill();
    });
  }

  let cw = 0;
  let ch = 0;

  function syncCanvasSize() {
    const rect = hero.getBoundingClientRect();
    const w = rect.width;
    const h = rect.height;
    if (w < 1 || h < 1) return { w: cw || 300, h: ch || 200 };
    if (Math.abs(w - cw) > 0.5 || Math.abs(h - ch) > 0.5) {
      cw = w;
      ch = h;
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      canvas.width = Math.floor(w * dpr);
      canvas.height = Math.floor(h * dpr);
      canvas.style.width = `${w}px`;
      canvas.style.height = `${h}px`;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    }
    return { w: cw, h: ch };
  }

  function loop() {
    const { w, h } = syncCanvasSize();
    const autoY = 0.0011;
    const autoX = 0.00035;
    rotY += autoY + targetBoostY * 0.0018;
    rotX += autoX + targetBoostX * 0.0012;
    targetBoostY += (mx * 1.15 - targetBoostY) * 0.04;
    targetBoostX += (my * 0.85 - targetBoostX) * 0.04;
    paint(w, h, false);
    raf = requestAnimationFrame(loop);
  }

  function onMove(clientX, clientY) {
    const rect = hero.getBoundingClientRect();
    const nx = ((clientX - rect.left) / rect.width - 0.5) * 2;
    const ny = ((clientY - rect.top) / rect.height - 0.5) * 2;
    mx = Math.max(-1, Math.min(1, nx));
    my = Math.max(-1, Math.min(1, ny));
  }

  function stop() {
    if (raf) cancelAnimationFrame(raf);
    raf = 0;
  }

  hero.addEventListener(
    'mousemove',
    (e) => {
      if (prefersReduced) return;
      onMove(e.clientX, e.clientY);
    },
    { passive: true }
  );

  hero.addEventListener(
    'touchstart',
    (e) => {
      if (prefersReduced || !e.touches[0]) return;
      onMove(e.touches[0].clientX, e.touches[0].clientY);
    },
    { passive: true }
  );

  hero.addEventListener(
    'touchmove',
    (e) => {
      if (prefersReduced || !e.touches[0]) return;
      onMove(e.touches[0].clientX, e.touches[0].clientY);
    },
    { passive: true }
  );

  hero.addEventListener('mouseleave', () => {
    mx = 0;
    my = 0;
  });

  window.addEventListener(
    'resize',
    () => {
      syncCanvasSize();
      if (prefersReduced) paint(cw, ch, true);
    },
    { passive: true }
  );

  if (typeof ResizeObserver !== 'undefined') {
    const ro = new ResizeObserver(() => {
      syncCanvasSize();
      if (prefersReduced) paint(cw, ch, true);
    });
    ro.observe(hero);
  }

  if (prefersReduced) {
    syncCanvasSize();
    paint(cw, ch, true);
    return;
  }

  syncCanvasSize();
  loop();
})();
