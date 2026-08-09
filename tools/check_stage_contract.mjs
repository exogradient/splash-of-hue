import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

const source = await readFile(new URL("../public/index.html", import.meta.url), "utf8");

assert.match(source, /--game-stage-inset:\s*clamp\(/);
assert.match(source, /--game-stage-width:\s*min\(100%, 980px\)/);
assert.match(source, /--game-stage-height:\s*min\(720px,/);
assert.match(
  source,
  /#pick\[data-mode\] \.play-shell\s*\{[^}]*width:\s*var\(--game-stage-width\);[^}]*height:\s*var\(--game-stage-height\);/s,
);
assert.match(
  source,
  /\.reveal-shell\s*\{[^}]*width:\s*var\(--game-stage-width\);[^}]*height:\s*var\(--game-stage-height\);/s,
);
assert.match(source, /#reveal\s*\{\s*padding:\s*var\(--game-stage-inset\);\s*\}/);
assert.match(
  source,
  /body\[data-embed="play"\] #pick\[data-mode\] \.play-shell\s*\{[^}]*width:\s*100%;[^}]*height:\s*100%;/s,
);
assert.match(source, /--role-label-control-offset:\s*0\.667rem/);
assert.match(
  source,
  /body\[data-embed="play"\] #countdown\s*\{\s*background:\s*var\(--bg\);\s*\}/,
);
assert.match(
  source,
  /id="countdownNum" role="status" aria-live="polite" aria-atomic="true"/,
  "the visual countdown must announce updates without becoming a focus target",
);
assert.doesNotMatch(
  source,
  /id="countdownNum"[^>]*tabindex=/,
  "the non-interactive countdown numeral must not receive browser focus chrome",
);
assert.doesNotMatch(
  source,
  /function runCountdown\(\)[\s\S]*?focusAfterRender\(el\);[\s\S]*?countdownTimer = setInterval/,
  "the countdown must not move focus onto its visual numeral",
);
assert.match(
  source,
  /\.timer-bar\s*\{[^}]*right:\s*var\(--space-5\);[^}]*left:\s*var\(--space-5\);[^}]*width:\s*auto;/s,
  "the memory timer must span the stage between its shared horizontal insets",
);
assert.doesNotMatch(
  source,
  /\.timer-bar\s*\{[^}]*width:\s*min\(/s,
  "the memory timer must not retain a compact fixed-width cap",
);
assert.match(
  source,
  /const instrumentQuietHoldMs = 5000;/,
  "the continuous instrument needs enough post-release time for perceptual confirmation",
);
assert.match(
  source,
  /quietTimer = setTimeout\(\(\) => \{[^}]*control\.dataset\.active = 'false';[^}]*\}, instrumentQuietHoldMs\);/s,
  "the quiet transition must use the shared interaction hold",
);
assert.doesNotMatch(
  source,
  /control\.dataset\.active = 'false';[^}]*\}, 1100\);/s,
  "the former premature quiet timing must not return",
);
assert.match(
  source,
  /\.memorize-overlay\s*\{[^}]*padding:\s*calc\(max\(var\(--space-5\), env\(safe-area-inset-top\)\) \+ var\(--role-label-control-offset\)\)/s,
);
assert.match(
  source,
  /\.reveal-swatch-label\s*\{[^}]*top:\s*calc\(var\(--space-5\) \+ var\(--role-label-control-offset\)\)/s,
);

const spectrumFieldBlock = source.match(/\.spectrum-field\s*\{([^}]*)\}/)?.[1] ?? "";
assert.doesNotMatch(
  spectrumFieldBlock,
  /\b(?:border|box-shadow)\s*:/,
  "the saturation/brightness field must not have a permanent separator contour",
);
assert.match(
  source,
  /\.spectrum-hue:focus-visible,\s*\.spectrum-field:focus-visible\s*\{[^}]*outline:\s*2px solid/s,
  "the continuous instrument still needs a visible keyboard focus outline",
);

for (const mode of ["play", "match", "picture", "call", "split"]) {
  const screenBlock = source.match(
    new RegExp(`#pick\\[data-mode="${mode}"\\]\\s*\\{([^}]*)\\}`),
  )?.[1] ?? "";
  assert.doesNotMatch(
    screenBlock,
    /\b(?:padding|width|height|align-items|justify-content)\s*:/,
    `${mode} must not override the shared screen geometry`,
  );

  const block = source.match(
    new RegExp(`#pick\\[data-mode="${mode}"\\] \\.play-shell\\s*\\{([^}]*)\\}`),
  )?.[1] ?? "";
  assert.doesNotMatch(
    block,
    /\b(?:width|height|align-content)\s*:/,
    `${mode} must not override the shared stage geometry`,
  );
}

console.log("Shared game-stage geometry contract OK");
