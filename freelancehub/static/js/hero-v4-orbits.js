/**
 * Hero v4 — Orbital Rings
 * Elliptical orbits at different tilts and speeds; nodes leave glowing trails.
 */
(function () {
  'use strict';
  const canvas = document.getElementById('fhHeroCanvas');
  const hero = canvas && canvas.closest('.fh-hero');
  if (!canvas || !hero) return;
  if (typeof window.matchMedia === 'function' && window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

  const ctx = canvas.getContext('2d');
  let W = 0, H = 0;

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

  const ORBITS = [
    { rx: 0.30, ry: 0.11, tilt: 0.30, speed:  0.00055, col: '108,99,255', nodes: 2, phase: 0.0 },
    { rx: 0.40, ry: 0.15, tilt: -0.55, speed:  0.00035, col: '67,217,173', nodes: 3, phase: 1.2 },
    { rx: 0.52, ry: 0.19, tilt:  0.90, speed:  0.00022, col: '255,101,132', nodes: 2, phase: 2.4 },
    { rx: 0.20, ry: 0.08, tilt: -0.20, speed:  0.00088, col: '245,166,35',  nodes: 2, phase: 0.7 },
    { rx: 0.60, ry: 0.22, tilt:  1.25, speed:  0.00015, col: '108,99,255',  nodes: 4, phase: 3.1 },
  ];

  // Trail history per node
  const trails = ORBITS.map(o => Array.from({ length: o.nodes }, () => []));
  const TRAIL_LEN = 38;

  function frame(ts) {
    const t = ts * 0.001;
    // Fade instead of clear — creates persistent glow
    ctx.fillStyle = 'rgba(10,10,20,0.18)';
    ctx.fillRect(0, 0, W, H);

    const cx = W * 0.63, cy = H * 0.50;
    const scale = Math.min(W, H);

    ORBITS.forEach((o, oi) => {
      const rx = o.rx * scale;
      const ry = o.ry * scale;

      // Draw orbit ring
      ctx.save();
      ctx.translate(cx, cy);
      ctx.rotate(o.tilt);
      ctx.beginPath();
      ctx.ellipse(0, 0, rx, ry, 0, 0, Math.PI * 2);
      ctx.strokeStyle = `rgba(${o.col},0.10)`;
      ctx.lineWidth = 1;
      ctx.stroke();
      ctx.restore();

      // Draw nodes + trails
      for (let ni = 0; ni < o.nodes; ni++) {
        const angle = t * o.speed * 1000 + (ni / o.nodes) * Math.PI * 2 + o.phase;

        // World position (tilted ellipse)
        const lx = Math.cos(angle) * rx;
        const ly = Math.sin(angle) * ry;
        const cosT = Math.cos(o.tilt), sinT = Math.sin(o.tilt);
        const sx = cx + lx * cosT - ly * sinT;
        const sy = cy + lx * sinT + ly * cosT;

        // Trail
        const trail = trails[oi][ni];
        trail.push({ x: sx, y: sy });
        if (trail.length > TRAIL_LEN) trail.shift();

        for (let ti = 1; ti < trail.length; ti++) {
          const alpha = (ti / trail.length) * 0.5;
          ctx.beginPath();
          ctx.moveTo(trail[ti - 1].x, trail[ti - 1].y);
          ctx.lineTo(trail[ti].x, trail[ti].y);
          ctx.strokeStyle = `rgba(${o.col},${alpha.toFixed(3)})`;
          ctx.lineWidth = (ti / trail.length) * 1.8;
          ctx.stroke();
        }

        // Glow halo
        const grd = ctx.createRadialGradient(sx, sy, 0, sx, sy, 14);
        grd.addColorStop(0, `rgba(${o.col},0.65)`);
        grd.addColorStop(1, `rgba(${o.col},0)`);
        ctx.beginPath();
        ctx.arc(sx, sy, 14, 0, Math.PI * 2);
        ctx.fillStyle = grd;
        ctx.fill();

        // Core dot
        ctx.beginPath();
        ctx.arc(sx, sy, 2.8, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(${o.col},0.95)`;
        ctx.fill();
      }
    });

    requestAnimationFrame(frame);
  }

  window.addEventListener('resize', resize, { passive: true });
  resize();
  requestAnimationFrame(frame);
})();
