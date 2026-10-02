// reveal-all: answers only; hints, solutions and derivations stay closed
const ctl = document.getElementById('answerctl');
if (ctl) ctl.addEventListener('click', () => {
  const all = [...document.querySelectorAll('details.ans')];
  const open = all.every(d => d.open);
  all.forEach(d => d.open = !open);
  ctl.textContent = open ? 'Open all answers' : 'Close all answers';
});
// a collapsed <details> does not print: open everything first
window.addEventListener('beforeprint', () => document.querySelectorAll('details').forEach(d => d.open = true));
// copy buttons on quiz prompts
document.querySelectorAll('button.copy').forEach(b => b.addEventListener('click', async () => {
  const pre = b.previousElementSibling;
  try { await navigator.clipboard.writeText(pre.innerText); b.textContent = 'Copied'; }
  catch (e) {  // no clipboard permission: select the text instead
    const r = document.createRange(); r.selectNodeContents(pre);
    const s = getSelection(); s.removeAllRanges(); s.addRange(r);
    b.textContent = 'Selected, press Ctrl+C';
  }
  setTimeout(() => b.textContent = 'Copy prompt', 2000);
}));
// layer filter on the hub's reference list
document.querySelectorAll('#filters button').forEach(b => b.addEventListener('click', () => {
  b.classList.toggle('off');
  const off = [...document.querySelectorAll('#filters button.off')].map(x => x.dataset.l);
  document.querySelectorAll('li.ref').forEach(li => li.style.display = off.includes(li.dataset.layer) ? 'none' : '');
}));
// maths: KaTeX auto-render runs from a deferred script, before DOMContentLoaded fires
document.addEventListener('DOMContentLoaded', () => {
  if (window.renderMathInElement) renderMathInElement(document.body, {
    delimiters: [{left: '\\[', right: '\\]', display: true}, {left: '\\(', right: '\\)', display: false}],
    ignoredClasses: ['mermaid', 'prompt'], throwOnError: false
  });
});

// ---- zoom on every diagram: Mermaid (.mermaid) or inline SVG (.plot) ----
// The SVG is looked up at click time, because Mermaid renders after this script runs.
function dragToPan(el) {
  let sx = 0, sy = 0, sl = 0, st = 0, down = false;
  el.addEventListener('pointerdown', e => {
    if (e.button !== 0 || !(el.classList.contains('zoomed') || el.classList.contains('zoom-stage'))) return;
    down = true; sx = e.clientX; sy = e.clientY; sl = el.scrollLeft; st = el.scrollTop;
    el.classList.add('panning'); el.setPointerCapture(e.pointerId);
  });
  el.addEventListener('pointermove', e => {
    if (!down) return;
    el.scrollLeft = sl - (e.clientX - sx); el.scrollTop = st - (e.clientY - sy);
  });
  const up = () => { down = false; el.classList.remove('panning'); };
  el.addEventListener('pointerup', up); el.addEventListener('pointercancel', up);
}
function svgAspect(svg) {           // height / width, from the viewBox when there is one
  const vb = svg.viewBox && svg.viewBox.baseVal;
  if (vb && vb.width) return vb.height / vb.width;
  const r = svg.getBoundingClientRect(); return r.width ? r.height / r.width : 0.6;
}
function openFull(holder, fig) {
  const svg = holder.querySelector('svg'); if (!svg) return;
  const ov = document.createElement('div'); ov.className = 'zoom-overlay';
  const cap = fig.querySelector('figcaption b');
  ov.innerHTML = '<p class="zoom-top"><span class="zoom-cap"></span><span>' +
    '<button data-z="out" title="Zoom out">&minus;</button><button data-z="fit" title="Fit to screen">fit</button>' +
    '<button data-z="in" title="Zoom in">+</button><button data-z="close" title="Close (Esc)">close &#x2715;</button></span></p>' +
    '<div class="zoom-stage"></div>';
  ov.querySelector('.zoom-cap').innerHTML = (cap ? cap.textContent : 'Diagram') + '<span class="zoom-hint">wheel to zoom · drag to pan · Esc to close</span>';
  const stage = ov.querySelector('.zoom-stage');
  const mark = document.createComment('zoomed-svg');
  const saved = {w: svg.style.width, mw: svg.style.maxWidth, h: svg.style.height};
  svg.parentNode.insertBefore(mark, svg);
  document.body.appendChild(ov); stage.appendChild(svg);
  document.body.style.overflow = 'hidden';
  const aspect = svgAspect(svg);
  const fitW = () => Math.max(200, Math.min(stage.clientWidth - 40, (stage.clientHeight - 40) / aspect));
  let scale = 1;
  const apply = (cx, cy) => {        // keep the point under the cursor still while zooming
    const before = svg.getBoundingClientRect();
    svg.style.width = (fitW() * scale) + 'px'; svg.style.height = 'auto';
    if (cx !== undefined) {
      const after = svg.getBoundingClientRect(), k = after.width / before.width;
      stage.scrollLeft += (cx - before.left) * (k - 1);
      stage.scrollTop += (cy - before.top) * (k - 1);
    }
  };
  apply();
  const close = () => {
    mark.parentNode.insertBefore(svg, mark); mark.remove();
    svg.style.width = saved.w; svg.style.maxWidth = saved.mw; svg.style.height = saved.h;
    ov.remove(); document.body.style.overflow = ''; document.removeEventListener('keydown', key);
  };
  const key = e => {
    if (e.key === 'Escape') close();
    if (e.key === '+' || e.key === '=') { scale = Math.min(scale * 1.25, 8); apply(); }
    if (e.key === '-') { scale = Math.max(scale / 1.25, 0.3); apply(); }
  };
  document.addEventListener('keydown', key);
  ov.querySelector('.zoom-top').addEventListener('click', e => {
    const z = e.target.dataset.z; if (!z) return;
    if (z === 'close') return close();
    if (z === 'in') scale = Math.min(scale * 1.25, 8);
    if (z === 'out') scale = Math.max(scale / 1.25, 0.3);
    if (z === 'fit') scale = 1;
    apply();
  });
  stage.addEventListener('wheel', e => {
    e.preventDefault();
    scale = e.deltaY < 0 ? Math.min(scale * 1.15, 8) : Math.max(scale / 1.15, 0.3);
    apply(e.clientX, e.clientY);
  }, {passive: false});
  ov.addEventListener('click', e => { if (e.target === ov) close(); });
  dragToPan(stage);
}
document.querySelectorAll('figure.dia').forEach(fig => {
  const holder = fig.querySelector('.mermaid, .plot');
  if (!holder) return;
  const bar = document.createElement('p'); bar.className = 'zoombar';
  bar.innerHTML = '<button data-z="out" title="Zoom out">&minus;</button><button data-z="fit" title="Back to fit">fit</button>' +
    '<button data-z="in" title="Zoom in">+</button><button data-z="full" title="Full screen">&#x2922;</button>';
  fig.insertBefore(bar, fig.firstChild);
  let scale = 1, base = 0;
  bar.addEventListener('click', e => {
    const z = e.target.dataset.z, svg = holder.querySelector('svg');
    if (!z || !svg) return;
    if (z === 'full') return openFull(holder, fig);
    if (scale === 1) base = svg.getBoundingClientRect().width || 600;   // measure at fit
    if (z === 'in') scale = Math.min(scale * 1.25, 6);
    if (z === 'out') scale = Math.max(scale / 1.25, 0.4);
    if (z === 'fit') scale = 1;
    if (Math.abs(scale - 1) < 0.01) {
      scale = 1; svg.style.width = ''; svg.style.maxWidth = ''; svg.style.height = '';
      holder.classList.remove('zoomed');
    } else {
      svg.style.maxWidth = 'none'; svg.style.width = (base * scale) + 'px'; svg.style.height = 'auto';
      holder.classList.add('zoomed');
    }
  });
  dragToPan(holder);
});
