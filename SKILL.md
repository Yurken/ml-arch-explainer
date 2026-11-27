---
name: ml-arch-explainer
description: >
  Interpret AI/ML architecture figures alongside their original papers and generate
  a self-contained, Distill.pub-style interactive academic HTML reader. Use this skill
  whenever the user uploads, references, or provides a model architecture figure, neural
  network diagram, framework overview, or training/inference pipeline image (e.g., "解读这个架构图",
  "分析模型图", "生成架构解读网页", "explain this architecture diagram").
---

# ML Architecture Diagram Explainer

Transform any uploaded AI/ML paper architecture diagram into a standalone, interactive,
Distill.pub-inspired HTML deep-read guide featuring:
- Interactive reconstructed DAG flow (with pan/zoom, horizontal/vertical switch, and original image side-by-side comparison).
- Step-by-step forward/training walkthrough highlighting active paths and tensor shape transitions.
- Per-module deep inspection: intuition, KaTeX math, PyTorch-style pseudocode, design rationale & ablation intuition, prerequisite concepts, and verified/safe-linked related papers.
- End-to-end tensor trace table, symbol glossary, and deduplicated reading list.

## Execution Workflow

### Establish the primary source before interpreting the figure

When a PDF, paper link, or paper text accompanies the image, read that version first. Match the uploaded diagram to the numbered figure using its caption, module names and connections. If the figure is given only inside a PDF, render its page and use the matching figure region for comparison. Preserve the supplied image when available. When different versions disagree, identify both versions or the discrepancy.

Read the task definition, the text referring to the figure, the equations and algorithm that implement it, and any appendix or ablation needed for an assertion. Check tensor operations, time indices, parameter ownership, data splits, reward/loss definitions and training versus inference against these passages. Inspect the rendered page if text extraction loses mathematical notation. Record the source title and figure locator in `meta.source_paper`. Attach claim-level locators in each module's `evidence` list. Label observations from the figure, definitions from the paper, experimental findings and explanatory inferences distinctly. If the figure and text use different notation, show both and explain their relationship.

If only an image is supplied, look for the original via a reliable title or distinctive labels when search is available and permitted. Check the figure itself before identifying a match. If it cannot be identified, ask for the PDF or DOI when the user specifically needs a paper-grounded reading. For an ordinary image-only request, proceed with clearly marked figure-based observations if the source remains unavailable. If a supplied paper is unreadable or depicts a different figure, explain the mismatch and request the correct source before attributing claims to it. Related papers can explain background but cannot establish what this method implemented.

### Step 1: High-Precision Visual Deconstruction
Inspect the figure, caption and relevant method section when provided. If the figure is unreadable, ask for a clearer copy or the figure number before reconstructing it.
1. Identify the method name, domain (e.g., LLM, VLM, Diffusion, RL, GNN, Audio), and whether the diagram mixes **training-only branches** (losses, teacher networks, stop-gradient) with **inference paths**.
2. Enumerate EVERY visible block/module, input, output, residual/skip connection (`+`, `Concat`), conditioning arrow, gating mechanism, repeated block indicator (`×N`), and mathematical symbol.
3. Determine topological ordering (`stage`: `0, 1, 2, ...` from input to output) and parallel branches (`lane`: `0, 1, ...` for multi-stream paths like vision/text encoders or auxiliary loss branches).
4. Note any ambiguous abbreviations or unlabelled dimensions (record them explicitly in `meta.uncertainties`).

### Step 2: Knowledge Enrichment & Paper Anti-Hallucination
Ground the explanation in the figure and available paper. Label conventional formulas, illustrative pseudocode and hypothetical ablation effects as inferences when the authors do not specify or test them. For each module, cover the applicable layers:
- **Mechanics**: Clear intuition, exact mathematical formulation (LaTeX), symbol meanings, and concise PyTorch-style pseudocode.
- **Design Rationale**: Why this module exists here, comparison with common alternatives, ablation intuition ("what breaks if removed/replaced?"), and practical implementation details.
- **Knowledge & Paper Lineage**: Prerequisite concepts + related papers (`foundational`, `direct_predecessor`, `alternative`, `follow_up`).

**Strict Citation Integrity Rules**:
- If web search / fetch tools are available in the current environment, verify paper titles, authors, years, and real URLs (arXiv / ACL / NeurIPS / CVPR / OpenReview) and set `"verified": true`.
- If offline or unable to verify a direct URL, **NEVER fabricate arXiv IDs or direct paper URLs**. Only cite well-known canonical papers you are confident exist, set `"verified": false`, and use a safe search URL:
  - `https://arxiv.org/search/?query=<URL_ENCODED_TITLE>&searchtype=all`
  - or `https://scholar.google.com/scholar?q=<URL_ENCODED_TITLE>`

### Step 3: Draft Structured JSON
Read [the JSON contract](references/json_schema.md) carefully and generate a valid JSON file (e.g., `/tmp/<slug>_arch.json` or `./<slug>_arch.json`).

Key quality requirements:
- **Language**: Write all explanatory prose in clear, natural **Chinese (中文)** while preserving standard English ML terms (e.g., Multi-Head Attention, Residual Connection, Stop-Gradient) and standard math/code notation.
- **Tensor Shapes**: Use consistent dimension symbols across the entire pipeline (e.g., `B`, `L`, `D`, `H`, `V`, `C`, `H_img`, `W_img`) and define every symbol in `symbol_glossary`. If the diagram omits concrete shapes, provide canonical symbolic shapes and note that they are symbolic.
- **LaTeX Escaping**: Double-escape backslashes inside JSON strings (`\\frac`, `\\text`, `\\sigma`, `\\mathbb{R}`).
- **Completeness**: Every node in `nodes` must be covered by at least one step in `steps`.

### Step 4: Compile & Validate HTML
Run the bundled compiler script to validate the JSON, embed the original image as Base64, and produce a zero-dependency single-file HTML:

```bash
python3 <SKILL_DIR>/scripts/build_html.py \
  --data <path_to_json> \
  --image <path_to_original_diagram> \
  --out <output_html_path>
```

*(Note: `<SKILL_DIR>` is the directory containing this `SKILL.md`. If the user wants a specific output path, honor it; otherwise save as `<method_slug>_arch_guide.html` in the current working directory.)*

If `build_html.py` reports any schema/reference errors (e.g., broken edge IDs, unescaped tokens, missing fields), fix the JSON and re-run until validation passes cleanly.

### Step 5: Deliver Concise Summary
After generating the HTML successfully, reply to the user with:
1. The saved HTML file path (ready to open directly in any browser).
2. A 3-bullet executive overview of the method's core innovation and end-to-end data flow.
3. The source paper and figure locator when matched, plus any inferred abbreviations or assumptions listed transparently so the user can refine them if needed.
