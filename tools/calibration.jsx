import { useState, useMemo, useCallback } from "react";

// ═══════ COLOR MATH (ported from index.html) ═══════

function hsbToCss(h, s, b) {
  const [r, g, bl] = hsbToRgb(h, s, b);
  return `rgb(${Math.round(r*255)},${Math.round(g*255)},${Math.round(bl*255)})`;
}

// --- Shared scorer block: start ---
const SCORING_PARAMS = {
  curve: { divisor: 10, exponent: 2.25 },
  hueRecovery: { thresholdDegrees: 33, lostPointRate: 0.55 },
  guardPenalty: { sameHueSbPenaltyRate: 0.25, midHuePenaltyRate: 0.30 },
  sameHueRescue: { lowScoreBoost: 0.0, midScoreBoost: 0.0 },
  tiers: { elite: 8.5, strong: 5.5, learning: 2.5 },
};

function hsbToRgb(h, s, b) {
  const sN = s / 100, bN = b / 100;
  const c = bN * sN;
  const hp = h / 60;
  const x = c * (1 - Math.abs(hp % 2 - 1));
  const m = bN - c;
  let r, g, bl;
  if (hp < 1) { r = c; g = x; bl = 0; }
  else if (hp < 2) { r = x; g = c; bl = 0; }
  else if (hp < 3) { r = 0; g = c; bl = x; }
  else if (hp < 4) { r = 0; g = x; bl = c; }
  else if (hp < 5) { r = x; g = 0; bl = c; }
  else { r = c; g = 0; bl = x; }
  return [r + m, g + m, bl + m];
}

function srgbToLinear(c) {
  return c <= 0.04045 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
}

function rgbToXyz(r, g, b) {
  r = srgbToLinear(r); g = srgbToLinear(g); b = srgbToLinear(b);
  return [
    0.4124564*r + 0.3575761*g + 0.1804375*b,
    0.2126729*r + 0.7151522*g + 0.0721750*b,
    0.0193339*r + 0.1191920*g + 0.9503041*b,
  ];
}

function xyzToLab(x, y, z) {
  const xn = 0.95047, yn = 1.0, zn = 1.08883;
  function f(t) { return t > 0.008856 ? Math.cbrt(t) : 7.787 * t + 16/116; }
  const fx = f(x/xn), fy = f(y/yn), fz = f(z/zn);
  return [116*fy - 16, 500*(fx - fy), 200*(fy - fz)];
}

function hsbToLab(h, s, b) {
  const [r, g, bl] = hsbToRgb(h, s, b);
  const [x, y, z] = rgbToXyz(r, g, bl);
  return xyzToLab(x, y, z);
}

function deltaE2000(lab1, lab2) {
  const [L1, a1, b1] = lab1;
  const [L2, a2, b2] = lab2;
  const C1 = Math.sqrt(a1*a1 + b1*b1);
  const C2 = Math.sqrt(a2*a2 + b2*b2);
  const Cavg = (C1 + C2) / 2;
  const Cavg7 = Math.pow(Cavg, 7);
  const G = 0.5 * (1 - Math.sqrt(Cavg7 / (Cavg7 + Math.pow(25, 7))));
  const a1p = a1 * (1 + G);
  const a2p = a2 * (1 + G);
  const C1p = Math.sqrt(a1p*a1p + b1*b1);
  const C2p = Math.sqrt(a2p*a2p + b2*b2);
  const h1p = (Math.atan2(b1, a1p)*180/Math.PI + 360) % 360;
  const h2p = (Math.atan2(b2, a2p)*180/Math.PI + 360) % 360;
  const dLp = L2 - L1;
  const dCp = C2p - C1p;
  let dhp;
  if (C1p*C2p === 0) dhp = 0;
  else if (Math.abs(h2p - h1p) <= 180) dhp = h2p - h1p;
  else if (h2p - h1p > 180) dhp = h2p - h1p - 360;
  else dhp = h2p - h1p + 360;
  const dHp = 2 * Math.sqrt(C1p*C2p) * Math.sin(dhp/2 * Math.PI/180);
  const Lpavg = (L1 + L2) / 2;
  const Cpavg = (C1p + C2p) / 2;
  let hpavg;
  if (C1p*C2p === 0) hpavg = h1p + h2p;
  else if (Math.abs(h1p - h2p) <= 180) hpavg = (h1p + h2p) / 2;
  else if (h1p + h2p < 360) hpavg = (h1p + h2p + 360) / 2;
  else hpavg = (h1p + h2p - 360) / 2;
  const T = 1
    - 0.17*Math.cos((hpavg - 30)*Math.PI/180)
    + 0.24*Math.cos(2*hpavg*Math.PI/180)
    + 0.32*Math.cos((3*hpavg + 6)*Math.PI/180)
    - 0.20*Math.cos((4*hpavg - 63)*Math.PI/180);
  const SL = 1 + 0.015 * Math.pow(Lpavg - 50, 2) / Math.sqrt(20 + Math.pow(Lpavg - 50, 2));
  const SC = 1 + 0.045 * Cpavg;
  const SH = 1 + 0.015 * Cpavg * T;
  const Cpavg7 = Math.pow(Cpavg, 7);
  const RT = -Math.sin(60*Math.exp(-Math.pow((hpavg - 275)/25, 2))*Math.PI/180)
    * 2 * Math.sqrt(Cpavg7 / (Cpavg7 + Math.pow(25, 7)));
  const dE = Math.sqrt(
    Math.pow(dLp/SL, 2) + Math.pow(dCp/SC, 2) + Math.pow(dHp/SH, 2)
    + RT * (dCp/SC) * (dHp/SH)
  );
  return [dE, dLp, dCp, dHp];
}

function hueDistance(h1, h2) {
  const d = Math.abs(h1 - h2);
  return d > 180 ? 360 - d : d;
}

function scoreFromDeltaE(de) {
  return Math.round(
    10 / (1 + Math.pow(de / SCORING_PARAMS.curve.divisor, SCORING_PARAMS.curve.exponent)) * 100
  ) / 100;
}

const HUE_NAMES = [
  [15,'Red'],[40,'Orange'],[65,'Yellow'],[150,'Green'],
  [195,'Cyan'],[250,'Blue'],[295,'Purple'],[330,'Pink'],[360,'Red'],
];
function hueName(h) {
  for (const [b, n] of HUE_NAMES) { if (h < b) return n; }
  return 'Red';
}

function applySameHueRescue(score, de, dLp, dCp, hueDist) {
  const lowScoreBoost = SCORING_PARAMS.sameHueRescue?.lowScoreBoost || 0;
  const midScoreBoost = SCORING_PARAMS.sameHueRescue?.midScoreBoost || 0;
  const absDeltaL = Math.abs(dLp);
  const absDeltaC = Math.abs(dCp);
  const sbExtent = Math.max(absDeltaL, absDeltaC);

  if (lowScoreBoost > 0 && de >= 12 && score <= 5.75 && sbExtent >= 16) {
    const closeHueWeight = Math.max(0, 1 - hueDist / 12);
    const sbWindow = Math.min(1, Math.max(0, sbExtent - 16) / 20);
    const lowScoreWindow = Math.min(1, Math.max(0, 5.75 - score) / 2.75);
    score += lowScoreBoost * closeHueWeight * Math.max(0.35, sbWindow) * lowScoreWindow;
  }

  if (midScoreBoost > 0 && de <= 18 && score <= 6.9 && sbExtent >= 14) {
    const veryCloseHueWeight = Math.max(0, 1 - hueDist / 5);
    const sbWindow = Math.min(1, Math.max(0, sbExtent - 14) / 12);
    const midScoreWindow = Math.min(1, Math.max(0, 6.9 - score) / 1.9);
    score += midScoreBoost * veryCloseHueWeight * sbWindow * midScoreWindow;
  }

  return score;
}

function effectiveDeltaE(de, dLp, dCp, hueDist) {
  const absDeltaL = Math.abs(dLp);
  const absDeltaC = Math.abs(dCp);
  const sbExcess = Math.max(0, Math.max(absDeltaL, absDeltaC) - 14);
  const hueWeight = Math.max(0, 1 - hueDist / Math.max(1, SCORING_PARAMS.hueRecovery.thresholdDegrees));
  const hueWindow = Math.max(0, 1 - Math.abs(hueDist - 19) / 9);
  const deltaWindow = Math.max(0, 1 - de / 14);
  return de
    + (SCORING_PARAMS.guardPenalty.sameHueSbPenaltyRate || 0) * sbExcess * hueWeight
    + (SCORING_PARAMS.guardPenalty.midHuePenaltyRate || 0) * 6 * hueWindow * deltaWindow;
}

function scoreGuess(target, guess) {
  const labT = hsbToLab(target.h, target.s, target.b);
  const labG = hsbToLab(guess.h, guess.s, guess.b);
  const [de, dLp, dCp, dHp] = deltaE2000(labT, labG);
  const hueDist = hueDistance(target.h, guess.h);
  const effectiveDe = effectiveDeltaE(de, dLp, dCp, hueDist);
  let score = scoreFromDeltaE(effectiveDe);
  if (hueDist <= SCORING_PARAMS.hueRecovery.thresholdDegrees) {
    const lost = 10 - score;
    const recovery = SCORING_PARAMS.hueRecovery.lostPointRate
      * (1 - hueDist / SCORING_PARAMS.hueRecovery.thresholdDegrees);
    score = Math.round((score + lost * recovery) * 100) / 100;
  }
  score = applySameHueRescue(score, de, dLp, dCp, hueDist);
  score = Math.round(Math.max(0, Math.min(10, score)) * 100) / 100;
  return {
    delta_e: Math.round(de * 10) / 10,
    delta_l: Math.round(dLp * 10) / 10,
    delta_c: Math.round(dCp * 10) / 10,
    delta_h: Math.round(dHp * 10) / 10,
    dLp: Math.round(dLp * 10) / 10,
    dCp: Math.round(dCp * 10) / 10,
    dHp: Math.round(dHp * 10) / 10,
    hueDist: Math.round(hueDist * 10) / 10,
    score,
    target_name: hueName(target.h),
    guess_name: hueName(guess.h),
  };
}
// --- Shared scorer block: end ---

function tierLabel(score) {
  if (score >= SCORING_PARAMS.tiers.elite) return 'elite';
  if (score >= SCORING_PARAMS.tiers.strong) return 'strong';
  if (score >= SCORING_PARAMS.tiers.learning) return 'learning';
  return 'rough';
}

// ═══════ SAMPLE GENERATION ═══════

// Deterministic seeded RNG for reproducible batches
function mulberry32(seed) {
  return function() {
    seed |= 0; seed = seed + 0x6D2B79F5 | 0;
    let t = Math.imul(seed ^ seed >>> 15, 1 | seed);
    t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t;
    return ((t ^ t >>> 14) >>> 0) / 4294967296;
  };
}

function generateBatch(seed, count = 100) {
  const rng = mulberry32(seed);
  const samples = [];

  // Strategy: 10 hue anchors x 10 delta profiles per anchor
  const hueAnchors = Array.from({length: 10}, (_, i) => i * 36 + rng() * 36);

  const deltaProfiles = [
    // [hue shift range, sat shift range, bri shift range, label]
    { hShift: [0, 3],   sShift: [0, 5],   bShift: [0, 5],   label: 'near-perfect' },
    { hShift: [0, 8],   sShift: [0, 10],  bShift: [0, 10],  label: 'close-all' },
    { hShift: [0, 5],   sShift: [15, 30], bShift: [15, 30], label: 'hue-right-SB-off' },
    { hShift: [0, 5],   sShift: [25, 45], bShift: [25, 45], label: 'hue-right-SB-far' },
    { hShift: [15, 30], sShift: [0, 8],   bShift: [0, 8],   label: 'hue-off-SB-close' },
    { hShift: [30, 60], sShift: [0, 10],  bShift: [0, 10],  label: 'hue-far-SB-close' },
    { hShift: [10, 25], sShift: [10, 20], bShift: [10, 20], label: 'moderate-all' },
    { hShift: [40, 80], sShift: [15, 30], bShift: [15, 30], label: 'far-all' },
    { hShift: [0, 10],  sShift: [0, 8],   bShift: [30, 50], label: 'brightness-miss' },
    { hShift: [60, 120],sShift: [10, 25], bShift: [10, 25], label: 'wrong-family' },
  ];

  for (let hi = 0; hi < 10; hi++) {
    const baseH = hueAnchors[hi];
    const baseS = 35 + rng() * 55; // 35-90
    const baseB = 35 + rng() * 55; // 35-90

    for (let di = 0; di < 10; di++) {
      const dp = deltaProfiles[di];
      const hShift = dp.hShift[0] + rng() * (dp.hShift[1] - dp.hShift[0]);
      const sShift = dp.sShift[0] + rng() * (dp.sShift[1] - dp.sShift[0]);
      const bShift = dp.bShift[0] + rng() * (dp.bShift[1] - dp.bShift[0]);

      const hSign = rng() > 0.5 ? 1 : -1;
      const sSign = rng() > 0.5 ? 1 : -1;
      const bSign = rng() > 0.5 ? 1 : -1;

      const target = {
        h: +((baseH + rng() * 10) % 360).toFixed(1),
        s: +(Math.min(100, Math.max(10, baseS + rng() * 10))).toFixed(1),
        b: +(Math.min(100, Math.max(10, baseB + rng() * 10))).toFixed(1),
      };

      const guess = {
        h: +((target.h + hShift * hSign + 360) % 360).toFixed(1),
        s: +(Math.min(100, Math.max(10, target.s + sShift * sSign))).toFixed(1),
        b: +(Math.min(100, Math.max(10, target.b + bShift * bSign))).toFixed(1),
      };

      const result = scoreGuess(target, guess);
      samples.push({
        id: hi * 10 + di,
        target,
        guess,
        profile: dp.label,
        ...result,
      });
    }
  }

  // Sort by score ascending — contentious cases first
  samples.sort((a, b) => a.score - b.score);
  return samples;
}

// ═══════ ASSESSMENT HEURISTICS ═══════

const TOO_LOW_RULES = new Set([
  'too_low_close_hue_low_score',
  'too_low_mid_hue_low_score',
  'too_low_same_hue_moderate_de',
  'too_low_low_delta_e_low_score',
]);
const TOO_HIGH_RULES = new Set([
  'too_high_far_hue_high_score',
  'too_high_high_delta_e_high_score',
  'too_high_same_hue_large_sb',
  'too_high_mid_hue_too_generous',
]);

function verdictFromRules(rules) {
  const hasTooLow = rules.some(rule => TOO_LOW_RULES.has(rule));
  const hasTooHigh = rules.some(rule => TOO_HIGH_RULES.has(rule));
  if (hasTooLow && hasTooHigh) return 'abstain';
  if (hasTooLow) return 'too_low';
  if (hasTooHigh) return 'too_high';
  return 'ok';
}

function autoGrade(sample) {
  const { score, hueDist, delta_e, delta_l, delta_c, delta_h } = sample;
  const absDeltaL = Math.abs(delta_l);
  const absDeltaC = Math.abs(delta_c);
  const absDeltaH = Math.abs(delta_h);
  const rules = [];
  const closeHueTooLowThreshold = hueDist <= 5 ? 3.75 : 4.0;
  const sameHueRescue = (
    hueDist <= 1 &&
    delta_e <= 16 &&
    score < 6.5 &&
    Math.max(absDeltaL, absDeltaC) >= 20
  );
  const sameHueLargeSb = (
    hueDist <= 4 &&
    score >= 7.0 &&
    delta_e <= 12 &&
    Math.max(absDeltaL, absDeltaC) >= 18 &&
    !sameHueRescue
  );

  if (hueDist <= 15 && score < closeHueTooLowThreshold) rules.push('too_low_close_hue_low_score');
  if (hueDist >= 18 && hueDist <= 24 && delta_e <= 20 && score < 3.5) {
    rules.push('too_low_mid_hue_low_score');
  }
  if (sameHueRescue) rules.push('too_low_same_hue_moderate_de');
  if (delta_e < 10 && score < 6) rules.push('too_low_low_delta_e_low_score');
  if (hueDist > 40 && score > 6) rules.push('too_high_far_hue_high_score');
  if (hueDist > 10 && delta_e > 30 && score > 3) rules.push('too_high_high_delta_e_high_score');
  if (sameHueLargeSb) {
    rules.push('too_high_same_hue_large_sb');
  }
  if (hueDist >= 12 && hueDist <= 22 && delta_e <= 10 && score >= 7) {
    rules.push('too_high_mid_hue_too_generous');
  }

  const verdict = verdictFromRules(rules);
  return {
    verdict,
    confidence: verdict === 'abstain' ? 'low' : rules.length >= 2 ? 'high' : rules.length === 1 ? 'medium' : 'low',
    rules,
    signals: {
      score,
      delta_e,
      hue_dist: hueDist,
      delta_l,
      delta_c,
      delta_h,
      abs_delta_l: absDeltaL,
      abs_delta_c: absDeltaC,
      abs_delta_h: absDeltaH,
    },
  };
}

function autoAssess(sample) {
  const grade = autoGrade(sample);
  return {
    ok: grade.verdict === 'ok',
    issues: grade.rules,
  };
}

function nextManualVerdict(verdict) {
  switch (verdict) {
    case 'ok':
      return 'too_high';
    case 'too_high':
      return 'too_low';
    case 'too_low':
      return 'ok';
    case 'abstain':
      return 'ok';
    default:
      return 'too_high';
  }
}

function decisionState(sample, decisions, grade = autoGrade(sample)) {
  const decision = decisions[sample.id];
  const defaultVerdict = grade.verdict;
  const finalVerdict = decision ? decision.finalVerdict : defaultVerdict;
  const reviewed = decision?.reviewed ?? false;
  return {
    defaultVerdict,
    finalVerdict,
    defaultFlagged: defaultVerdict !== 'ok',
    finalFlagged: finalVerdict !== 'ok',
    reviewed,
    reviewAction: !reviewed
      ? 'auto_unreviewed'
      : finalVerdict === defaultVerdict
        ? 'confirmed_default'
        : 'flipped_default',
  };
}

function candidateBucket(sample, grade = autoGrade(sample)) {
  if (grade.verdict === 'abstain') return 'abstain_probe';
  if (grade.verdict !== 'ok') return 'suspected_negative';
  const nearHueThreshold = Math.abs(sample.hueDist - SCORING_PARAMS.hueRecovery.thresholdDegrees) <= 5;
  const nearCurveKnee = Math.abs(sample.delta_e - SCORING_PARAMS.curve.divisor) <= 4;
  if ((sample.score >= 3.5 && sample.score <= 7.5) || nearHueThreshold || nearCurveKnee) {
    return 'boundary_probe';
  }
  if (sample.score >= 8) return 'positive_sanity';
  return 'coverage_probe';
}

function exportSample(sample, decisions) {
  const grade = autoGrade(sample);
  const { defaultVerdict, finalVerdict, reviewed, reviewAction } = decisionState(sample, decisions, grade);
  const agreesWithAuto = reviewed ? finalVerdict === defaultVerdict : null;
  return {
    id: sample.id,
    target: sample.target,
    guess: sample.guess,
    profile: sample.profile,
    candidate_bucket: candidateBucket(sample, grade),
    metrics: {
      score: sample.score,
      delta_e: sample.delta_e,
      hue_dist: sample.hueDist,
      delta_l: sample.delta_l,
      delta_c: sample.delta_c,
      delta_h: sample.delta_h,
    },
    default_source: 'auto_grader_v1',
    default_verdict: defaultVerdict,
    final_verdict: finalVerdict,
    auto_grader: {
      version: 'v1',
      verdict: defaultVerdict,
      confidence: grade.confidence,
      abstained: defaultVerdict === 'abstain',
      rules: grade.rules,
      signals: grade.signals,
    },
    human_review: {
      status: reviewed ? 'reviewed' : 'unreviewed',
      agrees_with_auto: agreesWithAuto,
      final_verdict: reviewed ? finalVerdict : null,
      corrected_verdict: reviewed && !agreesWithAuto ? finalVerdict : null,
      action: reviewAction,
    },
    default_ok: defaultVerdict === 'ok',
    final_ok: finalVerdict === 'ok',
    reviewed,
    review_action: reviewAction,
    auto_assess: {
      ok: defaultVerdict === 'ok',
      issues: grade.rules,
    },
  };
}

function buildBatchExport(seed, samples, decisions) {
  return {
    schema_version: 3,
    collection_mode: 'auto_grader_dogfooding',
    default_labeling: 'auto_grader_prefill',
    seed,
    timestamp: new Date().toISOString(),
    scoring_params: SCORING_PARAMS,
    samples: samples.map(sample => exportSample(sample, decisions)),
  };
}

function upsertBatch(batches, batch) {
  const existingIndex = batches.findIndex(candidate => candidate.seed === batch.seed);
  if (existingIndex === -1) return [...batches, batch];
  return batches.map((candidate, index) => index === existingIndex ? batch : candidate);
}

// ═══════ COMPONENTS ═══════

function Swatch({ h, s, b, size = 40 }) {
  return (
    <div style={{
      width: size, height: size, borderRadius: 6,
      background: hsbToCss(h, s, b),
      border: '1px solid rgba(255,255,255,0.12)',
      flexShrink: 0,
    }} />
  );
}

function HsbLabel({ h, s, b, diffH, diffS, diffB }) {
  const fmt = (v) => Math.round(v);
  const diffStyle = (d) => {
    if (d === undefined) return {};
    const mag = Math.abs(d);
    if (mag < 5) return { color: 'rgba(255,255,255,0.5)' };
    if (mag < 15) return { color: '#f5c542', fontWeight: 600 };
    if (mag < 30) return { color: '#f59e42', fontWeight: 700 };
    return { color: '#f55142', fontWeight: 700 };
  };
  const tokenStyle = (d) => ({
    display: 'inline-grid',
    gridTemplateColumns: '1ch 3ch',
    columnGap: 0,
    alignItems: 'baseline',
    ...diffStyle(d),
  });
  return (
    <span style={{
      display: 'inline-grid',
      gridAutoFlow: 'column',
      gap: 8,
      fontFamily: 'monospace',
      fontSize: 12,
      letterSpacing: '-0.02em',
      fontVariantNumeric: 'tabular-nums',
    }}>
      <span style={tokenStyle(diffH)}><span>H</span><span style={{ textAlign: 'right' }}>{fmt(h)}</span></span>
      <span style={tokenStyle(diffS)}><span>S</span><span style={{ textAlign: 'right' }}>{fmt(s)}</span></span>
      <span style={tokenStyle(diffB)}><span>B</span><span style={{ textAlign: 'right' }}>{fmt(b)}</span></span>
    </span>
  );
}

function ScoreBadge({ score }) {
  const tier = tierLabel(score);
  const colors = {
    elite: { bg: 'rgba(74,222,128,0.15)', border: 'rgba(74,222,128,0.4)', text: '#4ade80' },
    strong: { bg: 'rgba(96,165,250,0.15)', border: 'rgba(96,165,250,0.4)', text: '#60a5fa' },
    learning: { bg: 'rgba(251,191,36,0.15)', border: 'rgba(251,191,36,0.4)', text: '#fbbf24' },
    rough: { bg: 'rgba(248,113,113,0.15)', border: 'rgba(248,113,113,0.4)', text: '#f87171' },
  };
  const c = colors[tier];
  return (
    <span style={{
      display: 'inline-block', padding: '2px 8px', borderRadius: 6, fontSize: 13, fontWeight: 700,
      fontVariantNumeric: 'tabular-nums', minWidth: 42, textAlign: 'center',
      background: c.bg, border: `1px solid ${c.border}`, color: c.text,
    }}>
      {score.toFixed(1)}
    </span>
  );
}

function verdictStyle(verdict) {
  switch (verdict) {
    case 'too_high':
      return { bg: 'rgba(248,113,113,0.2)', border: 'rgba(248,113,113,0.5)', text: '#f87171', icon: '\u2191' };
    case 'too_low':
      return { bg: 'rgba(96,165,250,0.2)', border: 'rgba(96,165,250,0.5)', text: '#60a5fa', icon: '\u2193' };
    case 'abstain':
      return { bg: 'rgba(251,191,36,0.18)', border: 'rgba(251,191,36,0.45)', text: '#fbbf24', icon: '?' };
    default:
      return { bg: 'rgba(74,222,128,0.15)', border: 'rgba(74,222,128,0.4)', text: '#4ade80', icon: '\u2713' };
  }
}

function Row({ sample, decision, onToggle, onConfirmDefault }) {
  const { id, target, guess, score, delta_e, hueDist, profile } = sample;
  const grade = autoGrade(sample);
  const { defaultVerdict, finalVerdict, reviewed, reviewAction } = decisionState(sample, { [id]: decision }, grade);
  const diffH = hueDistance(target.h, guess.h) * (((guess.h - target.h + 540) % 360 - 180) > 0 ? 1 : -1);
  const diffS = guess.s - target.s;
  const diffB = guess.b - target.b;
  const reviewLabel = !reviewed ? 'auto' : reviewAction === 'confirmed_default' ? 'rev' : 'flip';
  const hueGoodThreshold = SCORING_PARAMS.hueRecovery.thresholdDegrees;
  const hueWarnThreshold = hueGoodThreshold * 2;
  const status = verdictStyle(finalVerdict);
  const rowBackground = finalVerdict === 'too_high'
    ? 'rgba(248,113,113,0.06)'
    : finalVerdict === 'too_low'
      ? 'rgba(96,165,250,0.06)'
      : finalVerdict === 'abstain'
        ? 'rgba(251,191,36,0.06)'
        : 'transparent';
  const rowHover = finalVerdict === 'too_high'
    ? 'rgba(248,113,113,0.12)'
    : finalVerdict === 'too_low'
      ? 'rgba(96,165,250,0.12)'
      : finalVerdict === 'abstain'
        ? 'rgba(251,191,36,0.12)'
        : 'rgba(255,255,255,0.03)';

  return (
    <tr
      onClick={(event) => {
        if (event.shiftKey) {
          onConfirmDefault();
          return;
        }
        onToggle();
      }}
      style={{
        cursor: 'pointer',
        background: rowBackground,
        borderBottom: '1px solid rgba(255,255,255,0.06)',
        transition: 'background 0.15s',
      }}
      onMouseEnter={e => e.currentTarget.style.background = rowHover}
      onMouseLeave={e => e.currentTarget.style.background = rowBackground}
      title={reviewed
        ? 'Reviewed row. Click cycles OK, too generous, and too harsh. Shift-click restores the default auto-grader verdict.'
        : 'Click cycles OK, too generous, and too harsh. Shift-click restores the default auto-grader verdict without changing it.'}
    >
      <td style={{ padding: '6px 8px', fontSize: 11, color: 'rgba(255,255,255,0.35)', fontVariantNumeric: 'tabular-nums' }}>
        {id + 1}
      </td>
      <td style={{ padding: '6px 4px' }}>
        <div style={{
          display: 'grid',
          gridTemplateColumns: '32px 32px minmax(0, 1fr)',
          alignItems: 'center',
          gap: 6,
        }}>
          <Swatch h={target.h} s={target.s} b={target.b} size={32} />
          <Swatch h={guess.h} s={guess.s} b={guess.b} size={32} />
          <div style={{ display: 'grid', gap: 3, minWidth: 0 }}>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: 6, minWidth: 0 }}>
              <HsbLabel h={target.h} s={target.s} b={target.b} />
              <span style={{ fontSize: 10, color: 'rgba(255,255,255,0.35)' }}>{hueName(target.h)}</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: 6, minWidth: 0 }}>
              <HsbLabel h={guess.h} s={guess.s} b={guess.b} diffH={diffH} diffS={diffS} diffB={diffB} />
              <span style={{ fontSize: 10, color: 'rgba(255,255,255,0.35)' }}>{hueName(guess.h)}</span>
            </div>
          </div>
        </div>
      </td>
      <td style={{ padding: '6px 8px', textAlign: 'center' }}>
        <ScoreBadge score={score} />
      </td>
      <td style={{ padding: '6px 8px', textAlign: 'center', fontSize: 12, fontVariantNumeric: 'tabular-nums', color: 'rgba(255,255,255,0.6)' }}>
        {delta_e.toFixed(1)}
      </td>
      <td style={{ padding: '6px 8px', textAlign: 'center', fontSize: 12, fontVariantNumeric: 'tabular-nums', color: hueDist <= hueGoodThreshold ? '#4ade80' : hueDist <= hueWarnThreshold ? '#fbbf24' : '#f87171' }}>
        {hueDist.toFixed(0)}
      </td>
      <td style={{ padding: '6px 8px', fontSize: 11, color: 'rgba(255,255,255,0.4)' }}>
        {profile}
      </td>
      <td style={{ padding: '6px 8px', textAlign: 'center' }}>
        <span style={{
          display: 'inline-block', width: 22, height: 22, borderRadius: 6,
          lineHeight: '22px', textAlign: 'center', fontSize: 14,
          background: status.bg,
          border: `1px solid ${status.border}`,
          color: status.text,
          userSelect: 'none',
        }}>
          {status.icon}
        </span>
        <div style={{
          marginTop: 4,
          fontSize: 9,
          letterSpacing: '0.04em',
          textTransform: 'uppercase',
          color: reviewed
            ? (finalVerdict === defaultVerdict ? 'rgba(255,255,255,0.55)' : '#f5c542')
            : 'rgba(255,255,255,0.28)',
        }}>
          {reviewLabel}
        </div>
      </td>
    </tr>
  );
}

function Stats({ samples, decisions }) {
  const counts = samples.reduce((acc, sample) => {
    const { finalVerdict, reviewed } = decisionState(sample, decisions);
    if (finalVerdict === 'ok') acc.ok += 1;
    else if (finalVerdict === 'abstain') acc.abstain += 1;
    else acc.flagged += 1;
    if (reviewed) acc.reviewed += 1;
    return acc;
  }, { ok: 0, flagged: 0, abstain: 0, reviewed: 0 });
  return (
    <div style={{ display: 'flex', gap: 20, fontSize: 13, color: 'rgba(255,255,255,0.6)', flexWrap: 'wrap' }}>
      <span><strong style={{ color: '#4ade80' }}>{counts.ok}</strong> look correct</span>
      <span><strong style={{ color: '#f87171' }}>{counts.flagged}</strong> directional</span>
      <span><strong style={{ color: '#fbbf24' }}>{counts.abstain}</strong> abstain</span>
      <span><strong style={{ color: '#f5c542' }}>{counts.reviewed}</strong> reviewed</span>
      <span><strong style={{ color: 'rgba(255,255,255,0.75)' }}>{samples.length - counts.reviewed}</strong> pending</span>
      <span>avg score: <strong style={{ color: 'white' }}>{(samples.reduce((a, s) => a + s.score, 0) / samples.length).toFixed(2)}</strong></span>
    </div>
  );
}

// ═══════ MAIN APP ═══════

export default function CalibrationTool() {
  const [batchSeed, setBatchSeed] = useState(1);
  const [decisions, setDecisions] = useState({});   // id -> { reviewed, finalVerdict }
  const [batches, setBatches] = useState([]); // saved dogfooding batches
  const [filter, setFilter] = useState('all'); // all | flagged | ok
  const [exportStatus, setExportStatus] = useState(null);

  const samples = useMemo(() => generateBatch(batchSeed), [batchSeed]);
  const currentBatch = useMemo(
    () => buildBatchExport(batchSeed, samples, decisions),
    [batchSeed, samples, decisions]
  );

  const cycleVerdict = useCallback((id) => {
    setDecisions(prev => {
      const sample = samples.find(s => s.id === id);
      const grade = autoGrade(sample);
      const { finalVerdict } = decisionState(sample, prev, grade);
      return {
        ...prev,
        [id]: {
          reviewed: true,
          finalVerdict: nextManualVerdict(finalVerdict),
        },
      };
    });
  }, [samples]);

  const confirmDefault = useCallback((id) => {
    setDecisions(prev => {
      const sample = samples.find(s => s.id === id);
      const grade = autoGrade(sample);
      const { defaultVerdict } = decisionState(sample, prev, grade);
      return {
        ...prev,
        [id]: {
          reviewed: true,
          finalVerdict: defaultVerdict,
        },
      };
    });
  }, [samples]);

  const filteredSamples = useMemo(() => {
    if (filter === 'all') return samples;
    return samples.filter(s => {
      const { finalVerdict } = decisionState(s, decisions);
      return filter === 'flagged' ? finalVerdict !== 'ok' : finalVerdict === 'ok';
    });
  }, [samples, decisions, filter]);

  const saveBatch = () => {
    setBatches(prev => upsertBatch(prev, currentBatch));
  };

  const exportAll = async () => {
    const allBatches = upsertBatch(batches, currentBatch);
    setExportStatus({ state: 'saving', message: 'Saving export to tools/.export…' });
    try {
      const response = await fetch('/__dev/save-calibration-export', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ batches: allBatches }),
      });
      if (!response.ok) {
        throw new Error(`save failed (${response.status})`);
      }
      const payload = await response.json();
      setExportStatus({ state: 'saved', message: `Saved ${payload.path}` });
    } catch (error) {
      setExportStatus({
        state: 'error',
        message: `Export failed: ${error.message || error}`,
      });
    }
  };

  const nextBatch = () => {
    saveBatch();
    setBatchSeed(prev => prev + 1);
    setDecisions({});
  };

  const thStyle = {
    padding: '8px 8px', fontSize: 11, fontWeight: 600, textTransform: 'uppercase',
    letterSpacing: '0.05em', color: 'rgba(255,255,255,0.45)',
    borderBottom: '1px solid rgba(255,255,255,0.1)',
    position: 'sticky', top: 0, background: '#0a0a0a', zIndex: 2,
    textAlign: 'left',
  };

  return (
    <div style={{
      fontFamily: "'Inter', -apple-system, system-ui, sans-serif",
      background: '#0a0a0a', color: 'rgba(244,237,227,0.92)',
      minHeight: '100vh', padding: '20px 16px',
    }}>
      {/* Header */}
      <div style={{ maxWidth: 1200, margin: '0 auto 20px' }}>
        <h1 style={{ fontSize: 20, fontWeight: 700, marginBottom: 4 }}>Scoring Calibration</h1>
        <p style={{ fontSize: 13, color: 'rgba(255,255,255,0.45)', marginBottom: 16 }}>
          100 target/pick pairs ranked by score. Click a row to cycle OK, too generous, and too harsh. Shift-click restores the default auto-grader verdict, including abstain.
          <span style={{ color: '#4ade80' }}> Green = score looks right.</span>
          <span style={{ color: '#f87171' }}> Red = score too generous.</span>
          <span style={{ color: '#60a5fa' }}> Blue = score too harsh.</span>
          <span style={{ color: '#fbbf24' }}> Yellow = abstain.</span>
          {' '}HSB values are color-coded by delta magnitude. Export writes repo-local JSON into <code style={{ fontFamily: 'monospace', fontSize: '0.95em' }}>tools/.export/</code> and preserves auto-grader verdicts plus human audit state.
        </p>

        {/* Controls */}
        <div style={{ display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap', marginBottom: 12 }}>
          <span style={{ fontSize: 12, color: 'rgba(255,255,255,0.4)' }}>Batch #{batchSeed}</span>
          <button onClick={nextBatch} style={btnStyle}>Save & next batch</button>
          <button onClick={exportAll} style={btnStyle} disabled={exportStatus?.state === 'saving'}>
            {exportStatus?.state === 'saving' ? 'Saving export…' : 'Export to tools/.export'}
          </button>
          <span style={{ width: 1, height: 20, background: 'rgba(255,255,255,0.1)' }} />
          {['all', 'flagged', 'ok'].map(f => (
            <button key={f} onClick={() => setFilter(f)} style={{
              ...btnStyle,
              background: filter === f ? 'rgba(255,255,255,0.12)' : 'rgba(255,255,255,0.04)',
              borderColor: filter === f ? 'rgba(255,255,255,0.2)' : 'rgba(255,255,255,0.08)',
            }}>
              {f === 'all' ? `All (${samples.length})` : f === 'flagged' ? 'Flagged' : 'OK'}
            </button>
          ))}
          {batches.length > 0 && (
            <span style={{ fontSize: 12, color: 'rgba(255,255,255,0.35)' }}>
              {batches.length} batch{batches.length > 1 ? 'es' : ''} saved
            </span>
          )}
        </div>

        {exportStatus && (
          <div style={{
            marginBottom: 12,
            fontSize: 12,
            color: exportStatus.state === 'error'
              ? '#f87171'
              : exportStatus.state === 'saved'
                ? '#4ade80'
                : 'rgba(255,255,255,0.55)',
            fontFamily: exportStatus.state === 'saved' ? 'monospace' : 'inherit',
          }}>
            {exportStatus.message}
          </div>
        )}

        <Stats samples={samples} decisions={decisions} />
      </div>

      {/* Table */}
      <div style={{ maxWidth: 1200, margin: '0 auto', overflowX: 'auto' }}>
        <table style={{ width: 'max-content', borderCollapse: 'collapse' }}>
          <thead>
            <tr>
              <th style={{ ...thStyle, width: 36 }}>#</th>
              <th style={thStyle}>Target / Pick</th>
              <th style={{ ...thStyle, textAlign: 'center', width: 60 }}>Score</th>
              <th style={{ ...thStyle, textAlign: 'center', width: 50 }}>ΔE</th>
              <th style={{ ...thStyle, textAlign: 'center', width: 58 }}>Hue Δ</th>
              <th style={{ ...thStyle, width: 120 }}>Profile</th>
              <th style={{ ...thStyle, textAlign: 'center', width: 56 }}>Verdict</th>
            </tr>
          </thead>
          <tbody>
            {filteredSamples.map(s => (
              <Row
                key={`${batchSeed}-${s.id}`}
                sample={s}
                decision={decisions[s.id]}
                onToggle={() => cycleVerdict(s.id)}
                onConfirmDefault={() => confirmDefault(s.id)}
              />
            ))}
          </tbody>
        </table>
      </div>

      {/* Params reference */}
      <div style={{ maxWidth: 1200, margin: '20px auto 0', padding: 16, borderRadius: 10, background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)', fontSize: 12, color: 'rgba(255,255,255,0.4)' }}>
        <strong style={{ color: 'rgba(255,255,255,0.6)' }}>Current params:</strong>{' '}
        score = 10 / (1 + (effective ΔE/{SCORING_PARAMS.curve.divisor})^{SCORING_PARAMS.curve.exponent}) | hue recovery: +{Math.round(SCORING_PARAMS.hueRecovery.lostPointRate * 100)}% of lost points when hue dist &le; {SCORING_PARAMS.hueRecovery.thresholdDegrees} | effective ΔE guard: same-hue SB +{SCORING_PARAMS.guardPenalty.sameHueSbPenaltyRate.toFixed(2)}x excess, mid-hue +{SCORING_PARAMS.guardPenalty.midHuePenaltyRate.toFixed(2)}x window | tiers: elite &ge;{SCORING_PARAMS.tiers.elite}, strong &ge;{SCORING_PARAMS.tiers.strong}, learning &ge;{SCORING_PARAMS.tiers.learning}
      </div>
    </div>
  );
}

const btnStyle = {
  padding: '5px 12px', fontSize: 12, fontWeight: 600, borderRadius: 8, cursor: 'pointer',
  background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.1)',
  color: 'rgba(244,237,227,0.85)', transition: 'all 0.15s',
};
