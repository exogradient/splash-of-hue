---
title: Frontend Design Analysis
date: 2026-03-28
---

# Frontend Design Analysis

Competitive analysis of color game UIs and current-state audit to inform splash-of-hue's visual redesign.

## Current State: splash-of-hue

**Design tokens (7 total):** `--bg: #1a1a2e`, `--surface: #16213e`, `--border: #0f3460`, `--text: #e0e0e0`, `--text-dim: #8888aa`, `--accent: #e94560`, `--radius: 10px`. No spacing scale, no type scale, no transition tokens.

**Typography:** System font stack, ad-hoc rem sizes (2rem title down to 0.72rem detail). No custom font, no weight system, no letter-spacing system. `tabular-nums` correctly applied on numeric readouts.

**Layout:** Single `<style>` block, ~155 lines CSS. Flex-based, 480px max-width. Zero media queries. Zero animations beyond button hover opacity and timer bar width.

**What works:**
- Full-bleed memorize screen — edge-to-edge color, minimal overlay. Strongest visual moment.
- SB field picker — well-implemented canvas renderer with proper pointer capture.
- Progressive disclosure on results — clean default, details behind tap.
- Single-file simplicity — 648 lines, easy to iterate.

**What's missing:**
- No distinctive identity — navy/coral reads as "developer dark mode default."
- Zero motion — no page transitions, no score animation, no confirm feedback, no countdown animation.
- No visual hierarchy beyond primary/secondary buttons.
- No micro-interactions.
- Result cards are uniform regardless of performance (a 9.8 looks the same as a 2.1).

## Competitive Landscape

### dialed.gg — Primary Reference

**Identity:** Minimalist Swiss brutalism. Black chrome, white type, full-bleed color. The UI is deliberately achromatic so game colors are the only chromatic element.

**Typography:** Suisse Intl S Alt (500 weight only) — a premium Swiss grotesque (~$50/weight). Extreme negative letter-spacing on titles (`-5.52px`). Single-weight discipline throughout creates visual consistency. Font loading: body starts `opacity: 0`, reveals after `document.fonts.ready`.

**Type scale:**
- Hero: `min(92px, 22vw)`, tracking -5.52px
- Large scores: `min(82px, 16vw)`, tracking -4.92px
- Body: 21px / 18px, tracking -0.36px to -0.42px
- Labels: 12px, uppercase, tracking 1.92px

**Spacing:** Bespoke, not gridded — consistent 30px edge padding, `env(safe-area-inset-bottom)` on all bottom elements. Tuned by eye per element rather than 4px/8px grid.

**Color picker:** Three vertical HSB strip sliders (120px total width), slides in from left with spring easing (0.55s). 25px circular drag handles with shadow. Channel label appears on drag, fades after 500ms.

**Motion language:**
- Score: animated climb from 0 to actual (1.2-2s duration scaled to score), feedback text fades in after.
- Countdown: digit slide-out (downward + blur) and slide-in (from above + blur).
- Swatch reveal: CSS 3D fold (`rotate3d(-1, 1, 0, 180deg)`) with 100ms stagger between cards.
- Hard mode toggle: earthquake shake with chromatic aberration (`text-shadow` RGB split), elastic spring counter-motion, SVG gaussian blur.
- Buttons: hover `scale(1.02-1.08)`, active `scale(0.94-0.97)`. Daily button has animated conic-gradient ring.

**Sound design:** Entirely procedural via Web Audio API — no audio files. Slider ticks, keystroke thuds, mode announcements via SpeechSynthesis. Signals technical sophistication.

**Result display:** Diagonal `clip-path: polygon()` split — player color and target color in opposing triangles. Score overlaid.

**Information architecture:** Maximum progressive disclosure. Intro shows only: title, two sentences, three mode buttons. Leaderboard tucked behind icon. Score descriptions reveal after climb animation. 100+ unique feedback messages in 0.1-point increments with brutal humor.

**Mobile:** `viewport-fit=cover`, `user-scalable=no`, safe area insets everywhere, `darkreader-lock` meta tag, `user-select: none` globally.

**Desktop:** Single breakpoint at 768px. Centered 476px card with deep layered shadow. Desktop-only: logo, version nav, dark/light toggle, mute.

**What makes it premium:** Custom paid font, single-weight discipline, extreme negative tracking, procedural audio, zero UI chrome, achromatic palette, overkill animation on secondary interactions, version history communicating craft.

### hued (playhued.com)

Vite + React + Tailwind. Dual fonts: Figtree (geometric sans, 300/500) + Instrument Serif (display/italic). Full light/dark via HSL custom properties — **entire color system is achromatic** (all `0 0% XX%`). Hue controlled left/right, saturation up/down, fine-tune crosshair for precision.

**Notable:** The Figtree + Instrument Serif pairing creates personality without color. Desktop swipe controls caused real usability complaints (erratic detection, hue jumping past yellow's narrow band). Daily-only + 3 guesses limits replay value.

### hue-miliation (huemiliation.com)

Dark theme with neon accents (cyan, green, indigo). Inter (body) + Playfair Display (titles/emotional feedback) — serif for personality, sans for instructions. CSS `conic-gradient` color wheel with radial gradient overlay.

**Standout feature: personality system.** 20+ randomized sarcastic messages per score tier. 32 sarcastic rank titles. 5 unlockable achievements with grayscale-to-green animations. The game is mechanically simple but the voice makes it shareable.

**Rough edges:** Ad modal with 30-second hard timeout, `console.log` in production, no loading states. Personality compensates for technical polish gaps.

### color.method.ac (Method of Action)

White background, clinical aesthetic. **Six challenge types:** Hue → Saturation → Complementary → Analogous → Triadic → Tetradic. This simple-to-complex progression is the most educational structure of any game in the set.

**Unique features:** Pre-game screen calibration step (adjust brightness to see subtle differences). Color blind assist using shape morphing (each primary = different shape, intermediates morph between). Both build trust and accessibility.

**Dated:** Clearfix hacks, vendor-prefixed transforms. White-on-white is functionally correct (no UI competing with game colors) but feels clinical.

### colorguesser.com

Given a color *name*, guess its hex via color wheel — the inverse direction of dialed.gg. Daily (5 colors), Opposite (complementary matching), Infinite (practice). Plus a tools suite: contrast checker, palette generator, blindness simulator, mixer, shades/tints.

**Notable:** The tools ecosystem alongside the game creates stickiness beyond replay. The name→color direction tests vocabulary rather than discrimination.

### palettle.com

Wordle-for-colors: 6 guesses to match a character's 5-color palette. Color keyboard: 8-column, 3-row grid with hue grouping and 3 saturation/lightness variants per column. Reference image progressively desaturates at 3+ guesses (punishment as visual feedback).

**Tactile buttons:** `translate(2px, 2px)` on `:active` with inset shadow depth. Emoji grid results for sharing.

## Cross-Cutting Patterns

### Achromatic UI is consensus

Every polished color game keeps the interface grayscale. The game colors must be the only chromatic signal. splash-of-hue's navy/coral palette violates this — the coral accent competes with game colors, and the navy gives the background a blue cast that shifts color perception.

### Typography is the brand signal

With no UI color available, type is the primary differentiator:
- dialed.gg: paid Swiss grotesque, extreme negative tracking, single weight
- hued: geometric + serif pairing, two weights
- hue-miliation: sans + serif for tone contrast

System fonts communicate nothing. A single distinctive typeface choice is the highest-leverage design decision.

### Motion conveys craft

Score reveal animations, page transitions, micro-interactions on buttons — these are the signals users (consciously or not) associate with polish. dialed.gg's overkill approach (chromatic aberration shake for a toggle, procedural audio for slider ticks) works because excess on secondary interactions signals "we care about everything."

### Picker UX is an unsolved problem

No one has a great picker. Vertical strips (dialed) are clean but abstract. Wheels (hue-miliation) are intuitive but imprecise. Swipe (hued) is novel but broken. splash-of-hue's SB field + hue bar is actually competitive — it maps to the mental model better than strips. This is a potential advantage.

### Progressive disclosure is mandatory

Show score, hide the math. Show result, hide the analysis. dialed.gg and splash-of-hue both do this — but dialed animates the reveal (score climb, then feedback fade-in), which makes disclosure feel like a reward rather than a toggle.

## Implications for splash-of-hue

### Where dialed.gg can be beaten

1. **Education.** dialed tests but doesn't teach. splash-of-hue's mode decomposition (Play/Match/Dial/Name/Read) targets specific perceptual skills. This is the core differentiator.
2. **Scoring accuracy.** dialed uses CIE76; splash-of-hue already uses CIEDE2000 with per-dimension breakdown. More perceptually accurate and more informative.
3. **Picker.** The SB field is more spatial and intuitive than three abstract strips. Worth investing in polish rather than replacing.
4. **Desktop experience.** dialed is mobile-in-a-card on desktop. No keyboard shortcuts, no wider layouts.
5. **No ads.** dialed runs `adsbygoogle`, breaking its own premium aesthetic.

### What must change

1. **Achromatic palette.** Drop the navy/coral. Move to pure black or near-black with white/gray text. Game colors become the only chromatic element.
2. **Custom typeface.** One distinctive font, one weight. This is the single highest-impact change.
3. **Motion language.** Score animations, page transitions, button micro-interactions. Doesn't need to match dialed's complexity — but zero motion reads as unfinished.
4. **Result differentiation.** A 9.8 and a 2.1 should look and feel different. Diagonal split swatches, score-driven visual emphasis, animated reveals.

### What to keep

1. **SB field picker.** Polish it (handle styling, gradient smoothness) rather than replacing.
2. **Full-bleed memorize.** Already matches the competitive bar.
3. **Progressive disclosure on results.** Already correct pattern.
4. **Single-file architecture.** Inline everything until forced to split.
5. **Per-dimension ΔE breakdown.** No competitor shows this — educational differentiator.

### Open questions

- **Font choice:** What typeface fits "teaches color perception" without mimicking dialed's Swiss brutalism? Candidates: a warm geometric (e.g. Satoshi, General Sans), a humanist sans (e.g. Source Sans 3, Instrument Sans), or something with more character (e.g. Space Grotesk, Outfit). Need to test against full-bleed color backgrounds.
- **Personality voice:** dialed's feedback is brutal/funny. hue-miliation leans harder on snark. What's splash-of-hue's voice? The educational angle suggests something that's honest but constructive — "coach" rather than "roast comic." But the planned `brutal` default suggests otherwise.
- **Achromatic how far:** Pure black (#000) like dialed, or near-black with subtle warmth/coolness? Pure black maximizes color contrast but can feel sterile. A very subtle warm gray (e.g. #111110) might better fit an educational tone.
- **Desktop strategy:** Card-in-viewport (like dialed) or full-width with more spatial layouts? The educational modes (Name It, Read It, Dial It In) might benefit from layouts that aren't mobile-constrained.
