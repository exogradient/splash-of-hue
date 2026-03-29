---
title: Visual Identity
description: Visual language — principles, palette, typography, motion, spatial system
stability: evolving
responsibility: How the product looks and feels — the design constraints that guide every screen
---

# Visual Identity

## Influences

Three design engineers whose shipped work defines the quality bar. Their profiles are detailed enough to resolve ambiguity — when a design question has no clear answer, ask "what would they do?" and the framework below should answer.

All three share an ethos: design in the browser, ship working code, iterate on feel through prototyping — not mockups. splash-of-hue follows this approach.

### Rauno Freiberg (Vercel, prev. Arc)

Staff Design Engineer. Built `cmdk`, `inspx`, Vesper theme. Created "Devouring Details" ($249 course, 23 chapters). Maintains the `interfaces` repo (1.9k stars) — a behavioral specification for web interfaces.

**Core framework — the 90/10 novelty rule.** Software should be 90% familiar, 10% novel. The novel 10% creates emotional resonance only because the other 90% is predictable. "Novelty is the equivalent of an exclamation mark. You don't want too much of it." Arc failed to calibrate this — the "novelty tax" overwhelmed users. Lesson: make most things familiar, do something unexpected.

**Frequency determines treatment.** High-frequency interactions (command menus, keyboard nav) get zero animation — cmdk appears instantly. Low-frequency interactions earn novelty. He built animated list add/remove into bmrks.com, then removed it after days of use because it felt sluggish despite being fast. Keyboard interactions tolerate animation even less than touch.

**Invisible details compound.** His seminal essay argues great interaction design operates through details users never consciously notice but intuitively feel. "Tiniest margins so that when they work, no one has to think about them." He built inspx (pixel inspection tool) because spatial precision is that important to him.

**Motion rules:**
- Animation duration max 200ms for interactions to feel immediate
- Scale animations proportional to trigger: dialogs from 0.8, buttons to 0.96
- Skip animation entirely for frequent low-novelty actions
- Looping animations must pause when off-screen
- Reduced motion: `animation-play-state: paused`, don't remove animations
- Stagger elements (like birds in a flock), don't synchronize
- Elements should launch from their origin, not appear from nowhere

**Signature easing:** `cubic-bezier(.2, .8, .2, 1)` — fast-in, gentle-out. Named `--transitions-snappy`.

**Dark theme pattern:** Pure achromatic gray scale in HSL. 12 stops from `hsl(0 0% 8.5%)` to `hsl(0 0% 93%)` plus alpha variants. Warm/cool accent pairing (Vesper: peppermint + orange on black). Theme switching must NOT trigger element transitions.

**Spacing:** 8px base unit, linear scale (`--space-1` through `--space-11`, increments of 8).

**Accessibility as requirement, not feature:**
- `box-shadow` for focus rings, not `outline`
- Icon-only elements must have `aria-label`
- Images always use `<img>` (screen readers, context menus)
- Disabled buttons should not have tooltips
- Dead zones between list items eliminated (use padding, not margin)

**Touch/gesture:**
- Hide hover states on touch: `@media (hover: hover)`
- `-webkit-tap-highlight-color: rgba(0,0,0,0)` to kill iOS highlight
- Lightweight actions trigger during gesture; destructive actions only on gesture end
- Slider dragging stays active when finger moves away from track

**Performance is aesthetic.** A slow beautiful site is ugly. Render without JS first. Code-split heavy visuals. Detect hardware capabilities. Vercel's hero uses 6 stacked layers — low-powered devices skip heavy ones.

**Decision test:** (1) How often will this happen? (2) Does the novel element earn its place against 90% familiarity? (3) Is the detail invisible when working, noticeable when absent? (4) Does it launch from its origin?

### Emil Kowalski (Linear)

Design engineer, web team. Created Sonner (toast, 24M+ weekly npm), Vaul (drawer). "Animations on the Web" course at animations.dev. "I like to build things for designers and developers, think deeply about the user interface, how it looks, feels, behaves."

**Core framework — purpose-first animation.** Before writing any animation code, answer three questions: (1) Can you name the purpose? (2) How often will users see it? (3) Is it keyboard-initiated? If any answer fails, don't animate. "The goal is not to animate for animation's sake, it's to build great user interfaces."

**Five valid purposes for animation:**
1. Spatial consistency — toast enters/exits same direction, making swipe-to-dismiss intuitive
2. State communication — something changed (loading, success, error)
3. Responsiveness feedback — button scale-down confirms the UI "listens"
4. Explain functionality — the Linear AI animation explains the feature; a static image cannot
5. Delight — only for rarely-seen interactions. "Used multiple times a day, this component would quickly become irritating."

**Timing rules (concrete numbers):**
- UI animations: under 300ms (universal rule)
- Toasts: 400ms with `ease` (deliberately slower — elegant pace matches Sonner's personality)
- Drawers: 500ms with `cubic-bezier(0.32, 0.72, 0, 1)` (iOS sheet feel, from Ionic Framework)
- Dismiss/exit: 200ms with `ease-out`
- Button press: 160ms with `ease-out`, `scale(0.97)` on `:active`
- Hover state changes: 100-200ms
- Tooltip: initial delay yes; subsequent tooltips while one is open: zero delay, zero animation

**Easing rules:**
- `ease-out` for entering/exiting elements (starts fast = responsive, decelerates = smooth landing)
- `ease-in-out` for elements already on screen that are moving
- Never `ease-in` for UI (starts slow, feels sluggish)
- Built-in CSS curves are "usually not strong enough" — custom curves feel more energetic
- His Vaul curve `cubic-bezier(0.32, 0.72, 0, 1)` is the gold standard for sheet/drawer animations

**Performance rules:**
- Only animate `transform` and `opacity` (composite-only, hardware-accelerated)
- Never animate `padding`, `margin`, `height`, `width` (trigger layout + paint)
- `translateY(100%)` over pixel values — works for any element height
- CSS transitions over keyframes — transitions are interruptible, keyframes are not
- CSS variables on parents cause style recalculation for all children — set `transform` directly on the element

**Animation craft:**
- Never animate from `scale(0)` — "nothing in the world around us can disappear and reappear in such a way." Start at 0.9+ (he uses 0.93 for dropdowns).
- Set `transform-origin` to match trigger position, never leave at center for popovers
- Momentum-based dismissal: check velocity (`distance / elapsed_time`), if > 0.11 dismiss regardless of distance
- Logarithmic damping for over-scroll: `8 * (Math.log(v + 1) - 2)`
- When easing and duration still feel off, add `filter: blur(2px)` during transition — "tricks the eye into seeing a smooth transition"
- `clip-path: inset()` for reveals — hardware-accelerated, no layout shift

**Cohesion principle:** Animation values must match product personality. Sonner is elegant (slower, `ease`). A crisp product uses snappy curves. "The animation should feel like it belongs to the product, not bolted on."

**On beauty:** "People simply like beautiful things. Beauty is generally underutilized in software so you can use it as leverage to stand out." "Simply shipping a product that works is no longer enough, everyone can do that, especially now with AI."

**Accessibility:** `@media (prefers-reduced-motion: reduce)` — replace movement with opacity-only transitions, don't remove animation entirely.

**Decision test:** (1) Name the purpose or don't animate. (2) Under 300ms unless the animation IS the point. (3) `ease-out` for enter, never `ease-in`. (4) Only `transform` + `opacity`. (5) Does the timing match the product's personality?

### Paco Coursey (Linear, prev. Vercel)

Design engineer, "Webmaster" at Linear. Previously developed Vercel's design system, website, and dashboard. Created `next-themes`, `cmdk` (with Rauno). "All I want to do is build websites. Typography, motion design, copywriting, performance — the web is an endless medium."

**Core framework — restraint as methodology.** His 2021 redesign essay rejects novelty: "Instead of adding as many animations, features, and case studies as possible, this iteration reflects my values of performance, simplicity, and craft." He describes the pull toward infinite canvas, OS metaphors, weather systems — and consciously rejects it. His site is "a simple collection of documents and links." The craft is in what's removed.

**Typography as complete system:**
- Three typefaces, each with a strict role: Inter (body), Sohne (headings), Newsreader (italics only). The signature move: italic means a typeface change to serif, not just slant — emphasis feels literary, not just typographic.
- Headings differentiated by weight (500), not size. H2s are the same 16px as body text. Only h1 gets a size bump (20px). Hierarchy through weight and font, not scale.
- `letter-spacing: 0` everywhere. Trust the typeface. The one exception: ordered list counters get `-0.05em` for tight number alignment.
- OpenType features on: `"kern", "calt", "case"` for headings, `"kern", "frac", "ss02"` for body. These are free polish.
- Body: 16px with 28px line-height (1.75 — generous for readability). Heading line-heights compress.
- `font-display: block` (not swap) — he waits for the font. FOUT is a bug, not a tradeoff.

**Monochrome color system (the actual values):**

12-step neutral gray scale. Dark mode:

| Step | Hex | Role |
|------|-----|------|
| 1 | `#1a1a1a` | Page background |
| 2 | `#1c1c1c` | Subtle surfaces, theme-color meta |
| 3 | `#232323` | Code blocks, cards |
| 5 | `#2e2e2e` | Borders (used everywhere) |
| 7 | `#3e3e3e` | Hover states |
| 9 | `#707070` | Low-contrast text, sidenotes |
| 11 | `#a0a0a0` | Dim text (descriptions, dates, meta) |
| 12 | `#ededed` | Primary text |

Three-tier text hierarchy through color alone: `gray12` (primary) > `gray11` (dim) > `gray9` (low-contrast). No size change needed. The only non-gray: `--indigo: #5856d6` — and it barely appears.

`theme-color` meta tag matches body background so browser chrome blends seamlessly.

**Spacing:** 8px base, strict multiples (4, 8, 16, 24, 32, 48, 64, 128). Content width: 640px.

**Copywriting as design material.** His homepage bio is two sentences of carefully edited prose with italics for emphasis. Footer: "Pray at the altar of hard work" — a values statement as design element, not a sitemap. He studies sentence construction and hook as design tools (his "Good Writers" post contrasts Aaron Swartz's opening with the boring version).

**The restraint hierarchy:** If you can solve it with typography alone, don't add color. If you can solve it with color alone, don't add iconography. If you can solve it with weight, don't add size. If you can solve it with whitespace, don't add borders. Remove first, add last.

**Open source philosophy:** `next-themes` solves exactly one problem (theme switching) and does it perfectly. Zero feature creep. Synchronizes across tabs. Zero flash on load. The README is a list of checkmarks — not marketing copy, just capability assertions. `cmdk` ships completely unstyled — design is the user's responsibility.

**Decision test:** (1) Can I remove something instead of adding? (2) Does the hierarchy survive in pure grayscale? (3) Am I using weight or color for hierarchy, not size? (4) Does every word of copy earn its place? (5) Am I building for reading or for impression?

## Core Constraint

The interface must be achromatic. Game colors are the only chromatic element on screen. Every polished color game converges on this — dialed.gg, hued, palettle — because UI color competes with the thing you're trying to perceive. Navy backgrounds cast blue. Coral accents pull attention. The current `--bg: #1a1a2e` and `--accent: #e94560` violate this.

Achromatic doesn't mean colorless — it means the interface earns the right to use color only when communicating game state (score tiers, error states) and even then with restraint.

## Principles

**1. Type is the brand.** With no UI color, typography carries all identity. One distinctive typeface, one weight, tight tracking. This is the single highest-leverage design decision. dialed.gg uses Suisse Intl S Alt (Swiss brutalism, $50/weight). splash-of-hue needs something warmer — we're teaching, not intimidating — but equally opinionated.

**2. Motion is meaning.** Every animation serves a purpose: confirming an action, revealing information, building tension, rewarding performance. No decorative motion. No motion is worse than bad motion — zero animation reads as unfinished. But gratuitous animation reads as insecure. The test: can you explain what this animation *communicates*? If not, cut it.

**3. Disclosure is reward.** Progressive disclosure isn't a toggle — it's a sequence. Score climbs before feedback appears. Cards reveal one-by-one. Details emerge on demand. The reveal itself is the micro-reward that keeps attention. dialed.gg does this with score climb → feedback fade-in → swatch fold-reveal. The pattern: withhold, then deliver with ceremony.

**4. The game is the interface.** During gameplay, the UI disappears. Memorize is already full-bleed edge-to-edge color — this is the strongest design moment and the pattern to extend. Pick should feel immersive, not like a form. Results should feel like a reveal, not a report.

**5. Density serves education.** Unlike dialed.gg (entertainment-only), splash-of-hue teaches. Per-dimension deltas (ΔL', ΔC', ΔH'), HSB breakdowns, color names — these are educational tools, not clutter. The design must make dense information feel earned and readable, not overwhelming. Progressive disclosure handles this: clean by default, rich on demand.

## Palette

**Base:** Near-black `#0a0a0a`, not pure `#000`. One step off-black avoids OLED pixel-off harshness and the "terminal" feel. Linear and Vercel both landed here.

**Gray ramp:** 12-step achromatic scale (à la Radix Gray). Covers text hierarchy (primary → secondary → tertiary → disabled), surface elevation (background → card → raised), borders, and dividers. All neutral — no blue/warm tint in the grays.

**Text:** Primary `#e8e8e8` (not pure white — reduces contrast fatigue on dark backgrounds). Secondary and tertiary steps down the gray ramp.

**Accent:** Reserved for interactive affordances only (focus rings, active states). Not for decoration. Single hue, used sparingly enough that it doesn't compete with game colors. Candidate: a muted cool-neutral that disappears next to saturated game colors.

**Semantic (game state only):** Success/error states for score feedback. These are the *only* chromatic UI elements and they appear only in results context, never during active color perception.

## Typography

**Direction:** Warm geometric or humanist sans-serif. Not Swiss brutalism (dialed's territory) — something with enough character to feel designed but enough neutrality to not compete with color. The font must hold up at both hero scale (score reveals, titles) and detail scale (HSB readouts, deltas).

**Candidates to test in-browser against full-bleed color backgrounds:**
- Warm geometric: Satoshi, General Sans, Plus Jakarta Sans
- Humanist: Instrument Sans, Source Sans 3
- Character: Space Grotesk, Outfit, Geist Sans

**System:**
- Single weight (medium/500). One-weight discipline creates visual consistency without decision overhead. dialed.gg does this. It works.
- Tight tracking on titles (negative letter-spacing). Loose tracking on uppercase labels.
- Modular type scale: 6 sizes from detail (0.75rem) to hero (clamp-based, viewport-responsive).
- `font-variant-numeric: tabular-nums` on all numeric readouts (already correct).
- Font loading gate: body starts `opacity: 0`, reveals on `document.fonts.ready` with 2s safety timeout. Prevents FOUT flash.

## Motion

**Timing:** Under 300ms for transitions that aren't the point (screen changes, state updates). Longer for transitions that *are* the point (score reveal, swatch comparison). If the user is waiting for the animation to finish, it's too long. If they don't notice it happened, it's doing its job. (See Emil's timing rules in Influences for concrete numbers per element type.)

**Easing:** `ease-out` for entrances (starts fast, decelerates). Custom curves over built-in — built-in are "not strong enough." Never `ease-in` (feels sluggish). Spring physics for interactive elements. Rauno's `cubic-bezier(.2, .8, .2, 1)` for snappy interactions; Emil's `cubic-bezier(0.32, 0.72, 0, 1)` for sheet-like reveals.

**Catalog:**
- **Screen transitions:** Opacity + subtle translateY (8px). Fast (200ms). Not the point — just not nothing.
- **Button feedback:** `scale(0.97)` on press, `scale(1.02)` on hover. Spring easing. Confirms the tap registered.
- **Score climb:** Animated count from 0 to actual score. Duration scaled to value (low scores resolve fast, high scores build suspense). Feedback text fades in after climb completes.
- **Card stagger:** Result cards appear sequentially with 80-120ms offset. Each card's swatch comparison uses a reveal (diagonal clip-path, fold, or slide).
- **Timer bar:** Continuous width transition, not stepped. Subtle glow on the leading edge.
- **Countdown digits:** Slide out downward + blur, new digit slides in from above. Sub-200ms.
- **Confirm pulse:** Brief scale or brightness pulse on the confirm button when pressed — the picker value is locked in.

**Not yet:** Procedural audio. Highest-effort, lowest-priority polish. Note for future.

## Spatial System

**Spacing:** Token-based scale replacing ad-hoc pixel values. 8-point base with adjustments (4, 8, 12, 16, 24, 32, 48, 64, 96). Every margin, padding, and gap maps to a token.

**Layout:**
- Mobile: full-viewport, edge-to-edge during gameplay. 16px edge padding on chrome (menu, results).
- Desktop: full-width, not card-in-viewport. Educational modes (Picture It, Name It, Read It) need breathing room that a 476px card can't provide. Single breakpoint at 768px.
- Content max-width: 480px for text-heavy screens (results, history). Picker and swatches can go wider.
- `env(safe-area-inset-bottom)` on all bottom-positioned elements.

**Elevation:** Three surface levels — background, card, raised. Differentiated by gray step, not shadow. Shadows only for floating elements (modals, tooltips if they ever exist).

## Picker

The SB field + hue bar is a competitive advantage. It maps to the HSB mental model more spatially than dialed's three abstract strips — two dimensions at once (saturation × brightness) rather than three separate linear channels. This reduces the compose-in-your-head cognitive load.

**Polish, don't replace:**
- Styled circular handle with subtle shadow (not browser-default)
- Smooth canvas gradients, proper anti-aliasing
- Hue bar: rounded, gradient-filled, visible channel label
- Slider variant: gradient-filled tracks replacing browser defaults
- Consistent handle size across hue bar and SB field

## Results

Results are the highest-stakes screen — where learning happens and where shareability lives.

**Score-driven presentation:** A 9.8 and a 2.1 must look and feel different. Not just the number — the visual weight, the reveal timing, the feedback tone. High scores earn a longer, more ceremonial reveal. Low scores resolve quickly (don't rub it in with a slow count on a 1.3).

**Swatch comparison:** Diagonal clip-path split (target triangle vs guess triangle) is the most readable comparison pattern (dialed.gg). Side-by-side rectangles (current) waste space and require eye movement. The diagonal forces the comparison at the boundary line.

**Educational layer (advanced view):**
- Per-dimension deltas (ΔL', ΔC', ΔH') as a mini visualization, not just signed numbers
- Color name for both target and guess
- Feedback message with personality (see `identity-context` for voice direction)

## Competitive Positioning

| Dimension | dialed.gg | splash-of-hue |
|-----------|-----------|---------------|
| Purpose | Entertainment (test) | Education (teach + test) |
| Scoring | CIE76, hue-weighted sigmoid | CIEDE2000, per-dimension breakdown |
| Modes | Play + Daily + Multiplayer | Play + Match + Dial + Name + Read (skill-targeted) |
| Picker | 3 vertical strips (abstract) | SB field + hue bar (spatial) |
| Results | Score + roast text | Score + roast + dimensional analysis |
| Desktop | Mobile-in-a-card | Full-width, mode-appropriate layouts |
| Visual identity | Swiss brutalism (black, Suisse Intl) | Warm achromatic (near-black, warm geometric type) |
| Audio | Procedural Web Audio | Future |
| Ads | Google AdSense | None |

## Anti-Patterns

Things to actively avoid:

- **UI color during gameplay.** No accent-colored buttons, no tinted backgrounds, no colored borders while the player is perceiving or recalling color.
- **Multiple font weights.** One weight. Bold is a crutch — use size and spacing for hierarchy.
- **Decorative animation.** If it doesn't communicate, cut it.
- **Card-in-viewport desktop.** Don't shrink the experience to a phone-shaped box on a 27" monitor.
- **Browser-default form elements.** Range inputs, checkboxes, selects — all must be styled or replaced. Defaults break the visual language.
- **Ad integration.** It destroys the premium feel (dialed.gg proves this).
