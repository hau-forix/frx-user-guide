// Paste into the page (orca eval / DevTools console) to get exact annotate.py boxes instead of guessing.
// Edit TARGETS: [marker number, CSS selector or text to match, optional "at" corner].
// Returns JSON of raw-pixel boxes (CSS px x devicePixelRatio), ready for spec "marks" with "scale": 1.
// The screenshot must be taken at the same scroll position and zoom, right after running this.
(() => {
  const TARGETS = [
    [1, 'button:has-text("New Client")', 'r'],
    [2, 'input[placeholder*="Search"]', 'r'],
    // [3, '[data-card=new_tickets] [data-slot=card-header]', 'tl'],
  ];
  const dpr = window.devicePixelRatio || 1;
  const find = (q) => {
    const m = q.match(/^(.*?):has-text\("(.+)"\)$/);
    if (!m) return document.querySelector(q);
    return [...document.querySelectorAll(m[1] || '*')].find((e) => e.textContent.trim().includes(m[2])) || null;
  };
  const out = TARGETS.map(([n, q, at]) => {
    const e = find(q);
    if (!e) return { n, q, missing: true };
    const b = e.getBoundingClientRect();
    return { n, at: at || 'tl', box: [b.left, b.top, b.right, b.bottom].map((v) => Math.round(v * dpr)) };
  });
  return JSON.stringify({ dpr, viewport: [innerWidth, innerHeight], scrollY, marks: out });
})();
