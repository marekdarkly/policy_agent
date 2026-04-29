// ============================================================================
// LaunchDarkly AI Configs Insights — Demo Cleanup
// ============================================================================
//
// Hides irrelevant + unattributed rows on the AI Configs insights table so the
// page reads as a clean "ToggleHealth multi-agent system" dashboard during
// demos. Touches DOM only — no network, no auth, no LD data is changed.
//
// Two ways to use:
//
// 1. As a bookmarklet (one-click toggle in the bookmarks bar):
//    Build the bookmarklet by running the snippet at the bottom of this file
//    (`make-bookmarklet`) and pasting the output as the URL of a new bookmark.
//    Click the bookmark while on the insights page to toggle hiding on/off.
//
// 2. As a Tampermonkey / Violentmonkey userscript:
//    Save this file as a `.user.js` import in your userscript manager. It will
//    auto-run on app.launchdarkly.com.
//
// ============================================================================
//
// ==UserScript==
// @name         LD AI Configs — Demo Cleanup (ToggleHealth)
// @namespace    togglehealth.demo
// @version      1.0.0
// @description  Hide irrelevant rows on the LD AI Configs insights page for cleaner demos.
// @match        https://app.launchdarkly.com/projects/*/ai/insights*
// @match        https://app.launchdarkly.com/projects/*/ai/configs*
// @match        https://app.launchdarkly.com/projects/*/ai*
// @run-at       document-idle
// ==/UserScript==

(function () {
  'use strict';

  // --------------------------------------------------------------------------
  // Config — edit this list to control what disappears.
  // Matching is case-insensitive substring against the visible Config column.
  // --------------------------------------------------------------------------
  const DENY_SUBSTRINGS = [
    // Other demos in this project — not part of the ToggleHealth story
    'battlecards',
    'launchairways',
    'togglebank',
    'toggle bank',
    'insurancebot',
    'feed summarizer',
    'g-eval',
    'evaluator-',
    'llm-as-judge',
    'toggle-health', // the legacy combined config; the per-agent rows tell the story instead
    'destination',
    'travel insights',
    'togglebot',
    // Generic / placeholder judges that don't add to the story
    'ld-ai-judge-',
  ];

  // Rows whose Config column is empty (`–` / `—` / blank) are always hidden.
  const HIDE_EMPTY_CONFIG = true;

  // Visual cue when hiding is active so demo presenter can see it's toggled on.
  const BANNER_ID = 'th-ld-cleanup-banner';

  // --------------------------------------------------------------------------
  const STATE_ATTR = 'data-th-cleanup';
  const isOn = () => document.body.getAttribute(STATE_ATTR) === 'on';

  function rowConfigText(row) {
    // Take the first non-empty cell — that's the Config column on the
    // insights page. Strip whitespace and trim trailing dashes/em-dashes.
    const cells = row.querySelectorAll('td, [role="cell"]');
    for (const c of cells) {
      const txt = (c.innerText || c.textContent || '').trim();
      if (txt) return txt;
    }
    return '';
  }

  function isEmptyConfig(text) {
    if (!text) return true;
    const t = text.trim();
    return t === '' || t === '-' || t === '–' || t === '—';
  }

  function isDenied(text) {
    const lower = text.toLowerCase();
    return DENY_SUBSTRINGS.some((needle) => lower.includes(needle));
  }

  function applyHide() {
    const rows = document.querySelectorAll('tr, [role="row"]');
    let hidden = 0;
    rows.forEach((row) => {
      // Skip header rows / aria-rowindex=1 / rows with <th>
      if (row.querySelector('th')) return;
      const text = rowConfigText(row);
      if (!text) return; // header-like
      if ((HIDE_EMPTY_CONFIG && isEmptyConfig(text)) || isDenied(text)) {
        row.style.display = 'none';
        row.setAttribute('data-th-hidden', '1');
        hidden++;
      }
    });
    return hidden;
  }

  function clearHide() {
    document.querySelectorAll('[data-th-hidden="1"]').forEach((el) => {
      el.style.display = '';
      el.removeAttribute('data-th-hidden');
    });
  }

  function ensureBanner(active, hiddenCount) {
    let banner = document.getElementById(BANNER_ID);
    if (!active) {
      if (banner) banner.remove();
      return;
    }
    if (!banner) {
      banner = document.createElement('div');
      banner.id = BANNER_ID;
      Object.assign(banner.style, {
        position: 'fixed',
        bottom: '12px',
        right: '12px',
        zIndex: 99999,
        padding: '8px 12px',
        background: 'rgba(31, 41, 55, 0.92)',
        color: '#fff',
        font: '12px/1.3 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
        borderRadius: '6px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.25)',
        cursor: 'pointer',
        userSelect: 'none',
      });
      banner.title = 'Click to disable demo cleanup';
      banner.addEventListener('click', toggle);
      document.body.appendChild(banner);
    }
    banner.textContent = `Demo cleanup ON · ${hiddenCount} row(s) hidden`;
  }

  let observer = null;

  function start() {
    document.body.setAttribute(STATE_ATTR, 'on');
    const hidden = applyHide();
    ensureBanner(true, hidden);
    if (!observer) {
      observer = new MutationObserver(() => {
        if (!isOn()) return;
        const h = applyHide();
        ensureBanner(true, h);
      });
      observer.observe(document.body, { childList: true, subtree: true });
    }
  }

  function stop() {
    document.body.setAttribute(STATE_ATTR, 'off');
    if (observer) { observer.disconnect(); observer = null; }
    clearHide();
    ensureBanner(false, 0);
  }

  function toggle() { (isOn() ? stop : start)(); }

  // Auto-start when loaded as a userscript; bookmarklet enters via toggle().
  if (typeof window.__TH_LD_CLEANUP__ === 'undefined') {
    window.__TH_LD_CLEANUP__ = { toggle, start, stop };
    start();
  } else {
    // Re-running (e.g. bookmarklet re-click) → toggle.
    window.__TH_LD_CLEANUP__.toggle();
  }
})();

// ----------------------------------------------------------------------------
// make-bookmarklet (run this snippet in any JS console to produce a bookmark
// URL from the IIFE above; it just minifies the function body and prefixes
// `javascript:`):
//
//   const src = await fetch('scripts/ld-insights-cleanup.user.js').then(r => r.text());
//   const body = src.split('\n').filter(l => !/^\s*\/\//.test(l)).join('\n');
//   console.log('javascript:' + encodeURIComponent('(' + body + ')()'));
//
// (Or just open the file, copy the IIFE, wrap it in `javascript:` and URI-encode.)
// ----------------------------------------------------------------------------
