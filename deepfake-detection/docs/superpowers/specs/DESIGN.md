# Design System: DeepScan

## 1. Visual Theme & Atmosphere

A forensic-dark interface that feels like a well-funded cybersecurity operations center —
clinical precision with controlled warmth from the single forest-green accent. Density sits
at 5 (Daily App Balanced), variance at 7 (Offset Asymmetric), motion at 6 (Fluid CSS).
Sections below the hero alternate between near-black (#0d0f0d) and a barely-elevated dark
surface (#111a13) — never white, never gray. The atmosphere should feel like a tool trusted
by professionals, not a startup landing page. Generous vertical rhythm, tight typographic
hierarchy, and asymmetric layout grids prevent the generic "SaaS template" look.

## 2. Color Palette & Roles

- **Void Black** (#0d0f0d) — Primary page canvas, deepest background surface
- **Forest Floor** (#111a13) — Alternating section background, slightly elevated surface
- **Moss Card** (#182019) — Card fills, input backgrounds, elevated containers
- **Glass Veil** (rgba(255,255,255,0.05)) — Glassmorphic surface tint for hero overlays
- **Forest Green** (#34a85a) — Single accent: CTAs, active states, focus rings, stat values, eyebrows
- **Deep Grove** (#1a5c35) — Gradient start, pressed button state
- **Bone White** (#f5f5f0) — Primary text on dark backgrounds
- **Faded Linen** (rgba(255,255,255,0.55)) — Secondary text, descriptions, card body copy
- **Whisper** (rgba(255,255,255,0.28)) — Metadata, timestamps, muted labels
- **Hairline** (rgba(255,255,255,0.08)) — Card borders, structural dividers
- **Mid Seam** (rgba(255,255,255,0.12)) — Hover borders, active dividers
- **Crimson Dim** (#fb7185) — Deepfake/fake verdict color
- **Verdant** (#4ade80) — Authentic/real verdict color

## 3. Typography Rules

- **Display (Syne):** Track-tight (-0.03em), weight 700–800. Used for section titles and hero
  headlines. Scale via clamp(). Never screaming — hierarchy through weight contrast, not sheer size.
- **UI (Plus Jakarta Sans):** Weight 400–600. Body copy at 1rem/1.6 line-height. Max 65ch per line.
  Used for descriptions, card text, labels, nav items.
- **Mono (JetBrains Mono):** Used exclusively for stat numbers, timestamps, code snippets,
  latency values, confidence percentages. Weight 500.
- **Eyebrows:** Uppercase, 0.68rem, letter-spacing 0.12em, Forest Green (#34a85a). Never bold.
- **Banned:** Inter, Georgia, Times New Roman, Garamond. No generic system font stacks for
  display contexts. No serif in any dashboard or software UI context.

## 4. Component Stylings

- **Primary Button:** Forest Green fill (#34a85a), color #000, font-weight 700, border-radius 10px,
  padding 0.65rem 1.4rem. On active: translateY(1px) + slight darken. No outer glow whatsoever.
  Arrow icon inline, 13px, stroke 2.5.
- **Ghost Button:** Transparent fill, 1px Hairline border, Bone White text. On hover: border becomes
  Mid Seam, background gets Glass Veil tint. Same border-radius as primary.
- **Cards:** border-radius 16px (not 24px — avoid "bubble" look). 1px Hairline border. Background
  Moss Card (#182019). Tint shadow to green: `0 4px 24px rgba(52,168,90,0.06)`. On hover: border
  lifts to Mid Seam, translateY(-2px). Cards used only when elevation serves hierarchy — use
  border-top dividers for dense list contexts.
- **Stat Pills:** Monospace numbers in Forest Green. Label in Whisper. Pill background Glass Veil,
  border Hairline. Compact padding 0.6rem 1rem.
- **Eyebrow Labels:** Forest Green, uppercase, 0.68rem, letter-spacing 0.12em, weight 600.
  Never inside a colored badge — just inline text above headings.
- **Plan Cards (Pricing):** Highlighted plan uses a 1px Forest Green border + rgba(52,168,90,0.06)
  background tint. "Most popular" tag: Forest Green background, #000 text, sits at top-center
  of card, border-radius 0 0 8px 8px. Never a glowing ring.
- **Testimonial Cards:** Quote mark in Syne at 3.5rem, Forest Green, opacity 0.4. Body text in
  Plus Jakarta Sans 0.9rem/1.7. Author avatar: 38px circle, Forest Green background, initials
  in black, weight 700.
- **Trust Badges:** Pill shape, 1px Hairline border, Moss Card fill, Whisper text 0.78rem.
  Never colored — neutral signal of credibility, not marketing flair.
- **Use Case Cards:** Left-aligned text. Icon in a 44px square with rgba(52,168,90,0.1) background,
  10px border-radius. Hover: border lifts to Forest Green, card rises 3px.
- **Step Cards (How It Works):** Number label in Forest Green mono, 0.68rem. Icon box 48px,
  slightly larger than use-case. Connector line between cards: 2px dashed Hairline on desktop only.

## 5. Layout Principles

- **Section rhythm:** Alternating void/forest-floor backgrounds. Padding clamp(4rem, 8vw, 7rem) vertical.
- **Max container:** 1080px centered, 1.5rem side padding on mobile.
- **How It Works:** 3-column on desktop (≥900px), single column on mobile. Cards equal height via CSS Grid.
- **Use Cases:** 2×2 grid on desktop (asymmetric: left col wider), single column mobile.
  NOT 4 equal columns — use grid-template-columns: 5fr 4fr repeat with row spans.
- **Testimonials:** Masonry-style 3-column on desktop. NOT equal height cards stacked.
  Achieve with CSS columns or grid auto-rows.
- **Pricing:** 3 columns, middle card (Pro) visually elevated via border accent — not physically taller.
- **Trust row:** Centered flex-wrap, no more than 6 badges. Below trust row: full-width CTA block.
- **Bottom CTA:** Asymmetric — large headline left, button right on desktop. Full-width dark card
  with subtle Forest Green top border (2px). No centered layout.
- **Dividers between sections:** Never use `<hr>` — use background color transitions only.
- **No equal 3-card horizontal rows** for feature sections. Use asymmetric bento or zig-zag pairs.

## 6. Motion & Interaction

- **Spring defaults:** stiffness 260, damping 22 for cards. stiffness 180, damping 18 for page
  entrance animations. Premium, weighted feel — not snappy or bouncy.
- **whileInView reveals:** opacity 0→1, y 32→0. viewport margin -60px. once: true.
- **Stagger:** 0.09s between siblings in grids. 0.12s between section header and grid.
- **Hover states:** transform and border-color only. Never animate width/height/top/left.
- **Card hover:** translateY(-3px) + border-color transition 180ms ease-out.
- **Button active:** translateY(1px) 80ms, no spring needed for micro-feedback.
- **No perpetual animations on landing page** — reserve for dashboard components.
  Exception: the hero scan-line pulse on the upload zone.

## 7. Anti-Patterns (Banned)

- No Inter font anywhere
- No pure black (#000000) — use Void Black (#0d0f0d)
- No neon glow shadows or colored box-shadow spreads
- No oversaturated accent variations (no #00ff00 style greens)
- No gradient text on large display headlines
- No 3-column or 4-column equal-width card grids — always asymmetric
- No centered hero layouts — always split-screen or left-aligned
- No "Elevate", "Seamless", "Unleash", "Next-Gen", "Revolutionary" copy
- No emojis anywhere in the UI
- No scroll indicators, bouncing arrows, or "Scroll to explore" text
- No generic placeholder names (John Doe, Acme Corp, Nexus)
- No fake round numbers (100%, 50%, 99.99%)
- No Unsplash links — use SVG avatars with initials
- No floating labels on inputs — always label above
- No circular loading spinners — skeletal loaders only
- No generic Georgia quote marks for testimonials — use Syne display at large scale
- No equal-height testimonial cards forced via min-height — let content breathe
- No section titles that start with "Our" ("Our Features", "Our Pricing")
- No white backgrounds anywhere on this dark-mode-first product
