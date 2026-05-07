/* FreelanceHub — main.js */
'use strict';

// ── Price Suggestion on Post Service ──────────────────────────────
async function suggestPrice() {
  const categoryId = document.getElementById('category_id')?.value;
  const title = document.getElementById('title')?.value || '';
  const desc = document.getElementById('description')?.value || '';
  if (!categoryId) return;
  try {
    const res = await fetch(`/api/suggest-price?category=${categoryId}&title=${encodeURIComponent(title)}&description=${encodeURIComponent(desc)}`);
    const data = await res.json();
    const box = document.getElementById('price-suggestion');
    const inp = document.getElementById('price');
    if (box) {
      box.innerHTML = `<i class="bi bi-lightbulb-fill" style="color:var(--gold);"></i> <strong>Suggested: Rs.${data.suggested.toLocaleString('en-IN')}</strong> &mdash; Range: Rs.${data.min.toLocaleString('en-IN')} – Rs.${data.max.toLocaleString('en-IN')} <span style="color:var(--text-soft);font-size:12px;">(${data.message})</span> <button type="button" onclick="document.getElementById('price').value=${data.suggested}" style="margin-left:8px;font-size:12px;color:var(--accent);background:none;border:none;cursor:pointer;padding:0;font-weight:600;">Use this →</button>`;
      box.style.display = 'flex';
    }
  } catch (e) {}
}

async function autoCategorize() {
  const title = document.getElementById('title')?.value || '';
  const desc = document.getElementById('description')?.value || '';
  if (title.length < 5 && desc.length < 10) return;
  try {
    const res = await fetch(`/api/auto-categorize?title=${encodeURIComponent(title)}&description=${encodeURIComponent(desc)}`);
    const data = await res.json();
    const sel = document.getElementById('category_id');
    if (sel && data.category_id) {
      sel.value = data.category_id;
      const label = document.getElementById('ai-category-label');
      if (label) {
        label.textContent = `AI suggests: ${data.category_name} (${Math.round(data.confidence * 100)}% confident)`;
        label.style.display = 'inline';
      }
      await suggestPrice();
    }
  } catch (e) {}
}

// ── Character counters ─────────────────────────────────────────────
function initCharCounters() {
  document.querySelectorAll('[data-maxlength]').forEach(el => {
    const max = parseInt(el.dataset.maxlength);
    const counter = document.querySelector(`[data-counter-for="${el.id}"]`);
    if (!counter) return;
    const update = () => {
      const left = max - el.value.length;
      counter.textContent = `${el.value.length} / ${max}`;
      counter.style.color = left < 20 ? 'var(--accent-2)' : 'var(--text-soft)';
    };
    el.addEventListener('input', update);
    update();
  });
}

// ── Tag input ─────────────────────────────────────────────────────
function initTagInput() {
  const inp = document.getElementById('tags');
  const preview = document.getElementById('tag-preview');
  if (!inp || !preview) return;
  const render = () => {
    const tags = inp.value.split(',').map(t => t.trim()).filter(Boolean);
    preview.innerHTML = tags.map(t => `<span class="fh-tag-chip">#${t}</span>`).join('');
  };
  inp.addEventListener('input', render);
  render();
}

// ── Image preview ─────────────────────────────────────────────────
function initImagePreview() {
  const fileInput = document.getElementById('image_file');
  const urlInput = document.getElementById('image_url');
  const preview = document.getElementById('img-preview');
  if (!preview) return;
  const showImg = src => { preview.src = src; preview.style.display = 'block'; };
  if (fileInput) {
    fileInput.addEventListener('change', () => {
      if (fileInput.files[0]) {
        const reader = new FileReader();
        reader.onload = e => showImg(e.target.result);
        reader.readAsDataURL(fileInput.files[0]);
      }
    });
  }
  if (urlInput) {
    urlInput.addEventListener('blur', () => { if (urlInput.value) showImg(urlInput.value); });
  }
}

// ── Payment method selection on checkout ──────────────────────────
function selectPayment(method) {
  document.querySelectorAll('.fh-checkout-step').forEach(s => s.classList.remove('selected'));
  const step = document.querySelector(`[data-method="${method}"]`);
  if (step) step.classList.add('selected');
  const radio = document.getElementById(`pay_${method}`);
  if (radio) radio.checked = true;
}

// ── Confirm dialog ────────────────────────────────────────────────
function confirmAction(msg, form) {
  if (window.confirm(msg)) form.submit();
  return false;
}

// ── Copy to clipboard ─────────────────────────────────────────────
function copyToClipboard(text, btn) {
  navigator.clipboard.writeText(text).then(() => {
    const orig = btn.innerHTML;
    btn.innerHTML = '<i class="bi bi-check2"></i> Copied!';
    setTimeout(() => { btn.innerHTML = orig; }, 2000);
  });
}

// ── Smooth number animation on stats ─────────────────────────────
function animateCount(el) {
  const target = parseInt(el.dataset.target || el.textContent.replace(/\D/g, ''));
  if (!target) return;
  let start = 0;
  const duration = 1200;
  const startTime = performance.now();
  const update = (now) => {
    const elapsed = now - startTime;
    const progress = Math.min(elapsed / duration, 1);
    const ease = 1 - Math.pow(1 - progress, 3);
    el.textContent = Math.round(start + (target - start) * ease).toLocaleString('en-IN') + '+';
    if (progress < 1) requestAnimationFrame(update);
  };
  requestAnimationFrame(update);
}

function initStatCounters() {
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        animateCount(entry.target);
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.5 });
  document.querySelectorAll('.fh-stat-num[data-target]').forEach(el => observer.observe(el));
}

// ── Lazy load images ──────────────────────────────────────────────
function initLazyLoad() {
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const img = entry.target;
        if (img.dataset.src) {
          img.src = img.dataset.src;
          observer.unobserve(img);
        }
      }
    });
  });
  document.querySelectorAll('img[data-src]').forEach(img => observer.observe(img));
}

// ── Price range slider sync ───────────────────────────────────────
function initPriceSlider() {
  const minInp = document.getElementById('min_price');
  const maxInp = document.getElementById('max_price');
  const minLabel = document.getElementById('min-price-label');
  const maxLabel = document.getElementById('max-price-label');
  if (!minInp || !maxInp) return;
  const update = () => {
    if (minLabel) minLabel.textContent = parseInt(minInp.value).toLocaleString('en-IN');
    if (maxLabel) maxLabel.textContent = parseInt(maxInp.value).toLocaleString('en-IN');
  };
  minInp.addEventListener('input', update);
  maxInp.addEventListener('input', update);
  update();
}

// ── Admin tabs ────────────────────────────────────────────────────
function showAdminTab(tab) {
  document.querySelectorAll('.fh-admin-content').forEach(c => c.style.display = 'none');
  document.querySelectorAll('.fh-admin-tab').forEach(t => t.classList.remove('active'));
  const content = document.getElementById(`admin-tab-${tab}`);
  const btn = document.querySelector(`[onclick="showAdminTab('${tab}')"]`);
  if (content) content.style.display = 'block';
  if (btn) btn.classList.add('active');
}

// ── Toast notifications ───────────────────────────────────────────
function showToast(msg, type = 'success') {
  const container = document.getElementById('toast-container') || (() => {
    const c = document.createElement('div');
    c.id = 'toast-container';
    c.style.cssText = 'position:fixed;bottom:88px;left:50%;transform:translateX(-50%);z-index:9999;display:flex;flex-direction:column;gap:8px;pointer-events:none;';
    document.body.appendChild(c);
    return c;
  })();
  const toast = document.createElement('div');
  const colors = { success: '#43d9ad', danger: '#ff6584', info: '#6c63ff', warning: '#f5a623' };
  toast.style.cssText = `background:${colors[type]||colors.info};color:white;padding:10px 20px;border-radius:99px;font-size:14px;font-weight:600;box-shadow:0 4px 20px rgba(0,0,0,.2);pointer-events:auto;opacity:0;transition:opacity .2s;font-family:'DM Sans',sans-serif;`;
  toast.textContent = msg;
  container.appendChild(toast);
  setTimeout(() => { toast.style.opacity = '1'; }, 10);
  setTimeout(() => { toast.style.opacity = '0'; setTimeout(() => toast.remove(), 200); }, 3000);
}

// ── Role card selection on signup ─────────────────────────────────
function initRoleCards() {
  document.querySelectorAll('.fh-role-card').forEach(card => {
    card.addEventListener('click', () => {
      document.querySelectorAll('.fh-role-card').forEach(c => c.classList.remove('selected'));
      card.classList.add('selected');
      const radio = card.querySelector('input[type=radio]');
      if (radio) radio.checked = true;
    });
  });
}

// ── Password strength indicator ───────────────────────────────────
function initPasswordStrength() {
  const inp = document.getElementById('password');
  const bar = document.getElementById('strength-bar');
  const label = document.getElementById('strength-label');
  if (!inp || !bar) return;
  inp.addEventListener('input', () => {
    const v = inp.value;
    let score = 0;
    if (v.length >= 8) score++;
    if (/[A-Z]/.test(v)) score++;
    if (/[0-9]/.test(v)) score++;
    if (/[^A-Za-z0-9]/.test(v)) score++;
    const levels = ['', 'Weak', 'Fair', 'Good', 'Strong'];
    const colors = ['', '#ff6584', '#f5a623', '#43d9ad', '#6c63ff'];
    bar.style.width = `${score * 25}%`;
    bar.style.background = colors[score] || '#e4e4f0';
    if (label) { label.textContent = levels[score] || ''; label.style.color = colors[score] || ''; }
  });
}

// ── Scroll to top ─────────────────────────────────────────────────
function initScrollTop() {
  const btn = document.createElement('button');
  btn.innerHTML = '<i class="bi bi-arrow-up"></i>';
  btn.style.cssText = 'position:fixed;bottom:100px;left:28px;width:40px;height:40px;border-radius:50%;border:1.5px solid var(--border);background:white;color:var(--text-mid);font-size:16px;cursor:pointer;display:none;align-items:center;justify-content:center;z-index:900;box-shadow:var(--shadow-md);transition:all .22s;';
  btn.onclick = () => window.scrollTo({ top: 0, behavior: 'smooth' });
  btn.title = 'Scroll to top';
  document.body.appendChild(btn);
  window.addEventListener('scroll', () => {
    btn.style.display = window.scrollY > 400 ? 'flex' : 'none';
  });
}

// ── Init on DOM ready ─────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  initCharCounters();
  initTagInput();
  initImagePreview();
  initStatCounters();
  initLazyLoad();
  initPriceSlider();
  initRoleCards();
  initPasswordStrength();
  initScrollTop();

  // Checkout payment steps
  document.querySelectorAll('.fh-checkout-step').forEach(step => {
    step.addEventListener('click', () => {
      document.querySelectorAll('.fh-checkout-step').forEach(s => s.classList.remove('selected'));
      step.classList.add('selected');
      const radio = step.querySelector('input[type=radio]');
      if (radio) radio.checked = true;
    });
  });

  // Auto-suggest on post service page
  const titleInp = document.getElementById('title');
  const descInp = document.getElementById('description');
  const catSel = document.getElementById('category_id');
  if (titleInp) {
    let timer;
    const debounce = () => { clearTimeout(timer); timer = setTimeout(autoCategorize, 600); };
    titleInp.addEventListener('input', debounce);
    if (descInp) descInp.addEventListener('input', debounce);
  }
  if (catSel) catSel.addEventListener('change', suggestPrice);
});
