/**
 * Hero v2 — Aurora Particle Field
 * Floating particles drift and connect when near; mouse repels them.
 */
(function () {
  'use strict';
  const canvas = document.getElementById('fhHeroCanvas');
  const hero = canvas && canvas.closest('.fh-hero');
  if (!canvas || !hero) return;
  if (typeof window.matchMedia === 'function' && window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

  const ctx = canvas.getContext('2d');
  const PALETTE = ['108,99,255', '67,217,173', '255,101,132', '245,166,35'];
  let W = 0, H = 0, particles = [];
  let mx = -9999, my = -9999;

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

  function mkParticle() {
    return {
      x: Math.random() * W,
      y: Math.random() * H,
      vx: (Math.random() - 0.5) * 0.55,
      vy: (Math.random() - 0.5) * 0.55,
      r: Math.random() * 2 + 1,
      col: PALETTE[Math.floor(Math.random() * PALETTE.length)],
      a: Math.random() * 0.45 + 0.2,
    };
  }

  function init() {
    resize();
    particles = Array.from({ length: 130 }, mkParticle);
  }

  const LINK_DIST = 115;
  const REPEL = 90;

  function frame() {
    ctx.clearRect(0, 0, W, H);

    for (let i = 0; i < particles.length; i++) {
      const p = particles[i];

      // Mouse repulsion
      const dx = p.x - mx, dy = p.y - my;
      const d2 = dx * dx + dy * dy;
      if (d2 < REPEL * REPEL && d2 > 0.01) {
        const d = Math.sqrt(d2);
        p.vx += (dx / d) * 0.2;
        p.vy += (dy / d) * 0.2;
      }

      p.vx *= 0.98; p.vy *= 0.98;
      p.x += p.vx; p.y += p.vy;
      if (p.x < 0) p.x = W; if (p.x > W) p.x = 0;
      if (p.y < 0) p.y = H; if (p.y > H) p.y = 0;

      // Edges
      for (let j = i + 1; j < particles.length; j++) {
        const q = particles[j];
        const ex = p.x - q.x, ey = p.y - q.y;
        const ed = Math.sqrt(ex * ex + ey * ey);
        if (ed < LINK_DIST) {
          const alpha = (1 - ed / LINK_DIST) * 0.22;
          ctx.strokeStyle = `rgba(${p.col},${alpha.toFixed(3)})`;
          ctx.lineWidth = 0.9;
          ctx.beginPath();
          ctx.moveTo(p.x, p.y);
          ctx.lineTo(q.x, q.y);
          ctx.stroke();
        }
      }

      // Dot with soft glow
      const g = ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, p.r * 4);
      g.addColorStop(0, `rgba(${p.col},${p.a})`);
      g.addColorStop(1, `rgba(${p.col},0)`);
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.r * 4, 0, Math.PI * 2);
      ctx.fillStyle = g;
      ctx.fill();

      ctx.beginPath();
      ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(${p.col},${p.a + 0.2})`;
      ctx.fill();
    }

    requestAnimationFrame(frame);
  }

  hero.addEventListener('mousemove', e => {
    const r = hero.getBoundingClientRect();
    mx = e.clientX - r.left; my = e.clientY - r.top;
  }, { passive: true });
  hero.addEventListener('mouseleave', () => { mx = -9999; my = -9999; });
  window.addEventListener('resize', () => { resize(); particles = Array.from({ length: 130 }, mkParticle); }, { passive: true });

  init();
  frame();
})();
