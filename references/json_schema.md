# Architecture Explanation JSON Schema

The Agent must produce a single UTF-8 JSON object conforming to this specification before invoking `scripts/build_html.py`.

## Top-Level Structure

See [the complete executable example](../examples/input-embedding.json) for the field names, types and nesting.

- `meta` requires `title`, `core_insight`, and `overview_summary`. Use `uncertainties` for inferred labels, shapes or implementation choices.
- `symbol_glossary` is an array of `symbol` / `meaning` entries. Supply an empty array when no symbols are used.
- `groups` (optional) is an array of logical phase/stage containers drawn as subtle background regions behind their member nodes. Each group needs `id`, `label`, `node_ids` (existing node IDs), and optional `color` (`"blue"` | `"purple"` | `"green"` | `"amber"` | `"slate"`). Use `groups` whenever the original figure has color-coded stages or multi-phase blocks.
- Each node needs a unique string `id`, a `name`, a nonnegative integer `stage`, `category`, `role`, `io.inputs` and `io.outputs` lists (each tensor has `name` and `shape`), and `mechanics.intuition`. Include formulas, pseudocode, rationale, concepts and papers where they support the explanation.
- Give each edge its own unique `id`, two existing node IDs in `source` and `target`, and a `type`. A graph with one node can use an empty edge list.
- Order the nonempty `steps` array by execution. Each step needs `title`, `phase`, `narration`, and a `focus_node` in its `active_nodes` list. Together the steps must cover all nodes. Set `active_edges` to explicit edge IDs or an empty list. Omit it to highlight edges between active nodes.
- Each paper requires `title`, `authors_year`, `relation` and boolean `verified`. Provide a direct HTTPS link after checking the primary paper record. Otherwise omit `url` to generate a title search, or supply an arXiv or Google Scholar search URL.


## Original paper and claim-level evidence

When the original figure has been matched, set `meta.source_paper` to an object with nonempty `title` and `figure` (e.g. "Fig. 2, PDF p. 4"). Each node then requires an `evidence` array with at least one entry. Use a precise `locator` (section, equation, algorithm line, figure panel or table), a short `claim`, and a `kind` of `paper`, `figure`, `experiment` or `inference`. For an inference, cite the passage or figure detail that motivates it and state the remaining assumption. Use printed page numbers or explicitly label PDF page indices as one-based. Use locators that work offline. Image-only guides may omit the source object.

## Enum Constraints

- `meta.default_layout`: `"horizontal"` (recommended when `stages <= 7`) or `"vertical"` (recommended when `stages >= 8` with narrow lanes).
- `groups[].color`: `"blue"` | `"purple"` | `"green"` | `"amber"` | `"slate"`.
- `nodes[].category`:
  - `"input"` — Raw inputs, tokenizers, patchify, embeddings
  - `"encoder"` — Feature extractors, backbones, CNN/ViT/MLP blocks
  - `"attention"` — Self-attention, cross-attention, fusion, routing, MoE
  - `"projection"` — Linear projections, adapters, normalization, pooling
  - `"decoder"` — Decoders, generators, denoising U-Net/DiT heads
  - `"loss"` — Loss functions, discriminators, reward models, training-only objectives
  - `"output"` — Final predictions, logits, generated images/tokens/actions
- `edges[].type`:
  - `"main"` — Primary forward data flow (solid dark line)
  - `"residual"` — Skip / residual / identity connections (curved dashed indigo line)
  - `"conditioning"` — Cross-attention KV, timestep/text conditioning, control signals (dotted amber line)
  - `"loss"` — Supervision / gradient / training-only flow (dashed crimson line)
- `steps[].phase`: `"forward"` | `"training"` | `"inference"`
- `papers[].relation`:
  - `"foundational"` (奠基工作)
  - `"direct_predecessor"` (直接前作)
  - `"alternative"` (同类替代方案)
  - `"follow_up"` (后续演进)

## Layout & Readability Guidelines for Clean Diagrams

- **Control Graph Complexity**: Aim for **5 to 12 semantic nodes** and **≤ 7 stages** (`stage: 0..6`). Avoid 10+ horizontal stages that force extreme zoom-out.
- **Merge Symmetric Parallel Sub-Blocks**: If a diagram contains 3–4 symmetric sibling components with identical incoming/outgoing wiring (e.g., 4 parallel basis functions or N identical heads), consider merging them into **one composite node** (detailing all variants inside `mechanics` and `formula_latex`) unless each sibling has distinct downstream connections. This eliminates repetitive fan-out/fan-in edge spaghetti.
- **Use `groups` for Multi-Phase Figures**: Mirror the original figure's color-coded boxes (e.g., Stage 1 / Stage 2 / Stage 3) using `groups` so readers immediately grasp macro structure.
- **Concise Labels**:
  - `short_name`: strictly `<= 12` Chinese characters (or `<= 18` ASCII chars) so SVG nodes never clip.
  - `name`: concise (`<= 20` Chinese characters).
  - Edge `label` / `tensor_shape`: concise (`<= 14` chars). Avoid repeating verbose labels on parallel edges.
- **Readable Prose & Formulas**:
  - Keep `mechanics.intuition` and `rationale.why_here` scannable (2–4 concise sentences; avoid dense single-paragraph walls of text).
  - Break long `formula_latex` expressions (`> 65` chars) into multi-line `\begin{aligned} ... \end{aligned}` blocks so they fit cleanly inside the reading column without horizontal scrolling.
  - Keep `pseudocode` concise (2–8 lines) with inline tensor shape comments (`# [B, L, D]`).

## JSON & LaTeX Escaping Pitfalls

- Always escape backslashes in JSON strings: write `"\\frac{Q K^T}{\\sqrt{d_k}}"`, NEVER `"\frac{...}"` (`\f` is a form-feed character in JSON!).
- Use `formula_latex` for pure display math (WITHOUT surrounding `$$`).
- In `formula_notes` or prose, wrap inline math in single `$ ... $` (e.g., `"维度为 $d_k = D / H$"`).

## Math in interface fields

In a JSON string, use "$h_{\\mathrm{sem}}$" in prose or a label, and "[B, D_{\\mathrm{model}}]" in a pure tensor shape. A pure glossary "symbol" may contain "\\hat A_k" or "\\mathcal Z". The renderer accepts single or double dollar delimiters and LaTeX parenthesis/bracket delimiters. Escape a literal dollar as "\\$". Put grouping, operators and arguments inside the same span. Use explicit delimiters for ambiguous shorthand or a multi-letter mathematical identifier. Use the pseudocode and dtype fields for literal code.

Build-time KaTeX checks run automatically when Node.js is on PATH. An invalid expression reports its JSON field path. On Python-only systems the embedded renderer works offline; inspect graph and reader math and correct any visible formula errors before delivery.
