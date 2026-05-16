/**
 * Hero v7 — Flow Field
 * Particles follow a layered sine/cosine vector field, leaving fading trails.
 */
(function () {
  'use strict';
  const canvas = document.getElementById('fhHeroCanvas');
  const hero = canvas && canvas.closest('.fh-hero');
  if (!canvas || !hero) return;
  if (typeof window.matchMedia === 'function' && window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

  const ctx = canvas.getContext('2d');
  const PALETTE = ['108,99,255', '67,217,173', '255,101,132', '245,166,35'];
  let W = 0, H = 0, particles = [], t = 0;

  function resize() {
    const r = hero.getBoundingClientRect();
    W = r.width; H = r.height;
    const dpr = Math.min(devicePixelRatio || 1, 2);
    canvas.width = Math.floor(W * dpr);
    canvas.height = Math.floor(H * dpr);
    canvas.style.width = W + 'px';
    canvas.style.height = H + 'px';
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    init();
  }

  function angle(x, y) {
    const nx = x / W, ny = y / H;
    return Math.sin(nx * 3.1 + t * 0.4) * Math.cos(ny * 2.4 + t * 0.3) * Math.PI * 2
         + Math.sin(nx * 1.7 - ny * 2.1 + t * 0.25) * Math.PI;
  }

  function mkParticle() {
    return {
      x: Math.random() * W,
      y: Math.random() * H,
      col: PALETTE[Math.floor(Math.random() * PALETTE.length)],
      life: Math.random() * 180 + 60,
      age: 0,
      speed: Math.random() * 1.2 + 0.6,
    };
  }

  function init() {
    particles = Array.from({ length: 280 }, mkParticle);
  }

  function frame() {
    // Fade trail — lower alpha = longer trails
    ctx.fillStyle = 'rgba(10,10,20,0.045)';
    ctx.fillRect(0, 0, W, H);

    t += 0.008;

    for (let i = 0; i < particles.length; i++) {
      const p = particles[i];
      const a = angle(p.x, p.y);
      const px = p.x, py = p.y;
      p.x += Math.cos(a) * p.speed;
      p.y += Math.sin(a) * p.speed;
      p.age++;

      const lifeRatio = 1 - p.age / p.life;
      const alpha = lifeRatio * 0.55;

      ctx.beginPath();
      ctx.moveTo(px, py);
      ctx.lineTo(p.x, p.y);
      ctx.strokeStyle = `rgba(${p.col},${alpha.toFixed(3)})`;
      ctx.lineWidth = lifeRatio * 1.4;
      ctx.stroke();

      // Reset when out of bounds or expired
      if (p.age > p.life || p.x < 0 || p.x > W || p.y < 0 || p.y > H) {
        particles[i] = mkParticle();
      }
    }

    requestAnimationFrame(frame);
  }

  window.addEventListener('resize', resize, { passive: true });
  resize();
  frame();
})();
