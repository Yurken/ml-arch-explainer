# Architecture Explanation JSON Schema

The Agent must produce a single UTF-8 JSON object conforming to this specification before invoking `scripts/build_html.py`.

## Top-Level Structure

See [the complete executable example](../examples/input-embedding.json) for the field names, types and nesting.

- `meta` requires `title`, `core_insight`, and `overview_summary`. Use `uncertainties` for inferred labels, shapes or implementation choices.
- `symbol_glossary` is an array of `symbol` / `meaning` entries. Supply an empty array when no symbols are used.
- Each node needs a unique string `id`, a `name`, a nonnegative integer `stage`, `category`, `role`, `io.inputs` and `io.outputs` lists (each tensor has `name` and `shape`), and `mechanics.intuition`. Include formulas, pseudocode, rationale, concepts and papers where they support the explanation.
- Give each edge its own unique `id`, two existing node IDs in `source` and `target`, and a `type`. A graph with one node can use an empty edge list.
- Order the nonempty `steps` array by execution. Each step needs `title`, `phase`, `narration`, and a `focus_node` in its `active_nodes` list. Together the steps must cover all nodes. Set `active_edges` to explicit edge IDs or an empty list. Omit it to highlight edges between active nodes.
- Each paper requires `title`, `authors_year`, `relation` and boolean `verified`. Provide a direct HTTPS link after checking the primary paper record. Otherwise omit `url` to generate a title search, or supply an arXiv or Google Scholar search URL.


## Enum Constraints

- `meta.default_layout`: `"horizontal"` (recommended for most diagrams) or `"vertical"`.
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

## Layout Tips for Clean Diagrams

- Assign `stage` sequentially from `0` (inputs) to `K` (outputs / losses).
- Use `lane` (`0`, `1`, `2`...) to separate parallel streams cleanly (e.g., Vision stream = `lane: 0`, Text stream = `lane: 1`, Shared fusion = `lane: 0` at a later `stage`).
- Keep `short_name` concise (<= 22 characters) so SVG boxes stay crisp and uncluttered.
- Aim for 5 to 14 well-chosen semantic nodes: group trivial repeated sub-ops (like `Linear -> GELU -> Linear`) into one meaningful module (`FFN / MLP`) unless the diagram specifically emphasizes their internal split.

## JSON & LaTeX Escaping Pitfalls

- Always escape backslashes in JSON strings: write `"\\frac{Q K^T}{\\sqrt{d_k}}"`, NEVER `"\frac{...}"` (`\f` is a form-feed character in JSON!).
- Use `formula_latex` for pure display math (WITHOUT surrounding `$$`).
- In `formula_notes` or prose, wrap inline math in single `$ ... $` (e.g., `"维度为 $d_k = D / H$"`).
