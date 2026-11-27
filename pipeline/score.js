/* Re-rank in the browser with user-chosen pillar weights (PRD FR-1.1). Mirrors pipeline/indicators.screen:
   score = 100 × Σ weight × pillar, with weights normalised to sum to 1; P(TOP3) from ±20% weight draws.
   tests/test_score_js.py checks this against the Python screen. */
(function (root) {
  const PILLARS = ["Market growth", "Market size", "K-momentum (trade)", "Entry ease"];

  function normalise(weights) {
    const total = PILLARS.reduce((a, p) => a + Math.max(0, Number(weights[p]) || 0), 0) || 1;
    return PILLARS.map(p => Math.max(0, Number(weights[p]) || 0) / total);
  }

  function rng(seed) {  // small deterministic generator, so the same weights always give the same P(TOP3)
    let t = seed >>> 0;
    return () => { t += 0x6D2B79F5; let r = Math.imul(t ^ (t >>> 15), 1 | t); r ^= r + Math.imul(r ^ (r >>> 7), 61 | r); return ((r ^ (r >>> 14)) >>> 0) / 4294967296; };
  }

  function rerank(rows, weights, draws = 5000) {
    const w = normalise(weights);
    const scored = rows.map(r => ({ ...r, score: 100 * PILLARS.reduce((a, p, k) => a + w[k] * r[p], 0) }));
    const counts = new Map(scored.map(r => [r.iso3, 0]));
    const rand = rng(42);
    for (let d = 0; d < draws && scored.length > 3; d++) {
      const v = w.map(x => x * (0.8 + 0.4 * rand())), sum = v.reduce((a, b) => a + b, 0);
      const s = scored.map(r => [r.iso3, PILLARS.reduce((a, p, k) => a + (v[k] / sum) * r[p], 0)]);
      s.sort((a, b) => b[1] - a[1]);
      for (let i = 0; i < 3; i++) counts.set(s[i][0], counts.get(s[i][0]) + 1);
    }
    return scored
      .sort((a, b) => b.score - a.score)
      .map((r, i) => ({ ...r, rank: i + 1, p_top3: scored.length <= 3 ? 1 : counts.get(r.iso3) / draws }));
  }

  const api = { PILLARS, rerank, normalise };
  if (typeof module !== "undefined" && module.exports) module.exports = api; else root.WellScore = api;
})(typeof window !== "undefined" ? window : globalThis);
