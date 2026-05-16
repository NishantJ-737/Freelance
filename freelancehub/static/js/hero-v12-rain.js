/**
 * Hero v12 — Digital Rain
 * Columns of falling glyphs (mix of Latin, Devanagari, and symbols).
 * Glyphs cycle randomly; leading glyph is bright white, trail fades.
 * Mouse column lights up in accent colour.
 * Glyphs dim near centre text area and brighten toward edges.
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
  const CHARS =
    'अआइईउऊएऐओऔकखगघचछजझटठडढणतथदधनपफबभमयरलवशषसह' +
    '०१२३४५६७८९' +
    'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789@#$%&*<>[]{}';

  const PALETTE_LEAD  = '255,255,255';
  const PALETTE_MAIN  = '67,217,173';
  const PALETTE_MOUSE = '108,99,255';

  let cols = 0;
  let drops = [];
  let speeds = [];
  let glyphs = [];

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

  // 0–1 multiplier: near-zero at text centre, full brightness at edges
  function edgeFade(x, y) {
    const dx = x - W * 0.5;
    const dy = y - H * 0.44;
    const dist = Math.sqrt(dx * dx + dy * dy);
    const innerR = Math.min(W, H) * 0.22;
    const outerR = Math.min(W, H) * 0.50;
    return Math.min(1, Math.max(0.05, (dist - innerR) / (outerR - innerR)));
  }

  function frame() {
    ctx.fillStyle = 'rgba(10,10,20,0.10)';
    ctx.fillRect(0, 0, W, H);

    ctx.font = `${FONT_SIZE}px monospace`;
    ctx.textAlign = 'center';

    for (let i = 0; i < cols; i++) {
      const x = i * FONT_SIZE + FONT_SIZE / 2;
      const y = drops[i] * FONT_SIZE;
      const isMouse = i === mouseCol;
      const col = isMouse ? PALETTE_MOUSE : PALETTE_MAIN;

      const fade = edgeFade(x, y);

      // Leading glyph — bright white, dimmed near centre
      ctx.fillStyle = `rgba(${PALETTE_LEAD},${(0.95 * fade).toFixed(3)})`;
      ctx.fillText(glyphs[i], x, y);

      // One glyph behind — accent colour
      ctx.fillStyle = `rgba(${col},${(0.75 * fade).toFixed(3)})`;
      ctx.fillText(randChar(), x, y - FONT_SIZE);

      if (Math.random() < 0.06) glyphs[i] = randChar();

      drops[i] += speeds[i];

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
  hero.addEventListener('selectstart', e => { e.preventDefault(); });
  window.addEventListener('resize', resize, { passive: true });

  resize();
  requestAnimationFrame(frame);
})();
