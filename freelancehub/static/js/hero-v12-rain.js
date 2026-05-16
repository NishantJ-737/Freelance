/**
 * Hero v12 — Digital Rain
 * Columns of falling glyphs (mix of Latin, Devanagari, and symbols).
 * Glyphs cycle randomly; leading glyph is bright white, trail fades.
 * Mouse column lights up in accent colour.
 */
(function () {
  'use strict';
  const canvas = document.getElementById('fhHeroCanvas');
  const hero = canvas && canvas.closest('.fh-hero');
  if (!canvas || !hero) return;
  if (typeof window.matchMedia === 'function' && window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

  const ctx = canvas.getContext('2d');
  let W = 0, H = 0;
  let mouseCol = -1;

  const FONT_SIZE = 14;
  // Mix of Devanagari, katakana-style symbols, and digits
  const CHARS =
    'अआइईउऊएऐओऔकखगघचछजझटठडढणतथदधनपफबभमयरलवशषसह' +
    '०१२३४५६७८९' +
    'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789@#$%&*<>[]{}';

  const PALETTE_LEAD  = '255,255,255';
  const PALETTE_MAIN  = '67,217,173';   // teal
  const PALETTE_MOUSE = '108,99,255';   // purple for mouse column

  let cols = 0;
  let drops = []; // y position (in rows) for each column
  let speeds = [];
  let glyphs = []; // current glyph per column

  function resize() {
    const r = hero.getBoundingClientRect();
    W = r.width; H = r.height;
    const dpr = Math.min(devicePixelRatio || 1, 2);
    canvas.width  = Math.floor(W * dpr);
    canvas.height = Math.floor(H * dpr);
    canvas.style.width  = W + 'px';
    canvas.style.height = H + 'px';
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

    cols = Math.floor(W / FONT_SIZE);
    drops  = Array.from({ length: cols }, () => Math.random() * -(H / FONT_SIZE));
    speeds = Array.from({ length: cols }, () => Math.random() * 0.6 + 0.3);
    glyphs = Array.from({ length: cols }, randChar);
  }

  function randChar() {
    return CHARS[Math.floor(Math.random() * CHARS.length)];
  }

  function frame() {
    // Fade trail
    ctx.fillStyle = 'rgba(10,10,20,0.10)';
    ctx.fillRect(0, 0, W, H);

    ctx.font = `${FONT_SIZE}px monospace`;
    ctx.textAlign = 'center';

    for (let i = 0; i < cols; i++) {
      const x = i * FONT_SIZE + FONT_SIZE / 2;
      const y = drops[i] * FONT_SIZE;
      const isMouse = i === mouseCol;
      const col = isMouse ? PALETTE_MOUSE : PALETTE_MAIN;

      // Leading glyph — bright
      ctx.fillStyle = `rgba(${PALETTE_LEAD},0.95)`;
      ctx.fillText(glyphs[i], x, y);

      // One glyph behind — accent colour bright
      ctx.fillStyle = `rgba(${col},0.75)`;
      ctx.fillText(randChar(), x, y - FONT_SIZE);

      // Randomly mutate glyph
      if (Math.random() < 0.06) glyphs[i] = randChar();

      drops[i] += speeds[i];

      // Reset column when it scrolls past bottom
      if (drops[i] * FONT_SIZE > H + FONT_SIZE * 2 && Math.random() < 0.015) {
        drops[i] = -Math.random() * 20;
        speeds[i] = Math.random() * 0.6 + 0.3;
      }
    }

    requestAnimationFrame(frame);
  }

  hero.addEventListener('mousemove', e => {
    const r = hero.getBoundingClientRect();
    mouseCol = Math.floor((e.clientX - r.left) / FONT_SIZE);
  }, { passive: true });
  hero.addEventListener('mouseleave', () => { mouseCol = -1; });
  window.addEventListener('resize', resize, { passive: true });

  resize();
  requestAnimationFrame(frame);
})();
