#!/usr/bin/env python3
"""
Compile structured ML architecture JSON + original diagram image into a
self-contained Distill.pub-style interactive HTML guide.
"""

from __future__ import annotations

import argparse
import base64
import html
import json
import mimetypes
import re
import shutil
import subprocess
import sys
from urllib.parse import urlsplit
from pathlib import Path
from typing import Any

# A tuple contains allowed strings. A one-element list describes each array item.
# Keys ending in '?' are optional.
TENSOR = {"name": str, "shape": str, "dtype?": str}
PAPER = {
    "title": str, "authors_year": str, "relation": ("foundational", "direct_predecessor", "alternative", "follow_up"),
    "takeaway?": str, "url?": str, "verified": bool,
}
GROUP = {
    "id": str, "label": str, "node_ids": [str],
    "color?": ("blue", "purple", "green", "amber", "slate"),
}
NODE = {
    "id": str, "name": str, "short_name?": str, "stage": int, "lane?": int,
    "category": ("input", "encoder", "attention", "projection", "decoder", "loss", "output"),
    "repeat_badge?": str, "role": str, "io": {"inputs": [TENSOR], "outputs": [TENSOR]},
    "mechanics": {"intuition": str, "formula_latex?": str, "formula_notes?": [str], "pseudocode?": str},
    "rationale?": {"why_here": str, "alternatives?": [str], "ablation_impact?": str, "implementation_notes?": str},
    "evidence?": [{"kind": ("paper", "figure", "experiment", "inference"), "locator": str, "claim": str}],
    "concepts?": [{"term": str, "brief": str}], "papers?": [PAPER],
}
SCHEMA = {
    "meta": {"source_paper?": {"title": str, "figure": str}, "title": str, "subtitle?": str, "domain?": str, "venue_year?": str, "core_insight": str,
             "tags?": [str], "default_layout?": ("horizontal", "vertical"), "overview_summary": str, "uncertainties?": [str]},
    "symbol_glossary": [{"symbol": str, "meaning": str}],
    "groups?": [GROUP],
    "nodes": [NODE],
    "edges": [{"id": str, "source": str, "target": str, "type": ("main", "residual", "conditioning", "loss"),
               "label?": str, "tensor_shape?": str, "description?": str}],
    "steps": [{"step_number?": int, "title": str, "phase": ("forward", "training", "inference"),
               "focus_node": str, "active_nodes": [str], "active_edges?": [str], "narration": str}],
}


def check_shape(value, spec, path):
    if isinstance(spec, dict):
        if not isinstance(value, dict):
            raise ValueError(f"{path} must be an object")
        for field, child in spec.items():
            key = field.rstrip("?")
            if key in value:
                check_shape(value[key], child, f"{path}.{key}")
            elif key == field:
                raise ValueError(f"{path}.{key} is required")
    elif isinstance(spec, list):
        if not isinstance(value, list):
            raise ValueError(f"{path} must be an array")
        for i, item in enumerate(value):
            check_shape(item, spec[0], f"{path}[{i}]")
    elif isinstance(spec, tuple):
        if value not in spec:
            raise ValueError(f"{path} must be one of {', '.join(spec)}")
    elif type(value) is not spec:
        raise ValueError(f"{path} must be {spec.__name__}")


def unique_ids(items, name):
    ids = set()
    for item in items:
        key = item["id"]
        if not key.strip() or key in ids:
            raise ValueError(f"{name}: empty or duplicate id {key!r}")
        ids.add(key)
    return ids


def validate_data(data):
    check_shape(data, SCHEMA, "data")
    if not data["meta"]["title"].strip() or not data["nodes"] or not data["steps"]:
        raise ValueError("meta.title, nodes and steps must be nonempty")
    source = data["meta"].get("source_paper")
    if source and not all(source[field].strip() for field in ("title", "figure")):
        raise ValueError("meta.source_paper needs a nonempty title and figure locator")
    nodes = unique_ids(data["nodes"], "nodes")
    edges = unique_ids(data["edges"], "edges")
    if data.get("groups"):
        unique_ids(data["groups"], "groups")
        for grp in data["groups"]:
            if not grp["label"].strip() or not grp["node_ids"]:
                raise ValueError(f"groups.{grp['id']}: label and node_ids must be nonempty")
            unknown = set(grp["node_ids"]) - nodes
            if unknown:
                raise ValueError(f"groups.{grp['id']}: unknown node_ids {sorted(unknown)}")
    for node in data["nodes"]:
        if source and not node.get("evidence"):
            raise ValueError(f"{node['id']}: a paper-grounded node needs evidence")
        for entry in node.get("evidence", []):
            if not entry["claim"].strip() or not entry["locator"].strip():
                raise ValueError(f"{node['id']}: incomplete evidence claim or locator")
        if min(node["stage"], node.get("lane", 0)) < 0:
            raise ValueError(f"{node['id']}: stage and lane must be nonnegative")
        formula = node["mechanics"].get("formula_latex", "")
        if any(ord(c) < 32 and c != "\n" for c in formula):
            raise ValueError(f"{node['id']}: control character in formula_latex; check JSON backslash escaping")
        for paper in node.get("papers", []):
            url = paper.get("url", "")
            if paper["verified"]:
                parts = urlsplit(url)
                if parts.scheme != "https" or not parts.hostname:
                    raise ValueError(f"{paper['title']}: verified citations need a direct HTTPS link")
            elif url:
                parts = urlsplit(url)
                if (parts.scheme, parts.netloc, parts.path) not in {
                    ("https", "arxiv.org", "/search/"), ("https", "scholar.google.com", "/scholar"),
                }:
                    raise ValueError(f"{paper['title']}: omit the unverified URL or provide a scholarly search link")
    for edge in data["edges"]:
        if {edge["source"], edge["target"]} - nodes:
            raise ValueError(f"{edge['id']}: unknown source or target")
    covered = set()
    for number, step in enumerate(data["steps"], 1):
        active = set(step["active_nodes"])
        if step.get("step_number", number) != number:
            raise ValueError(f"Step {number}: step_number must match the sequence")
        if active - nodes or step["focus_node"] not in active:
            raise ValueError(f"Step {number}: active_nodes must identify existing nodes and include focus_node")
        if set(step.get("active_edges", [])) - edges:
            raise ValueError(f"Step {number}: unknown active edge")
        covered.update(active)
    if nodes - covered:
        raise ValueError(f"Missing walkthrough steps for nodes: {sorted(nodes - covered)}")


def encode_image_data_uri(image_path: Path | None) -> str:
    if image_path is None:
        return ""
    if not image_path.exists():
        raise FileNotFoundError(f"Image file not found: {image_path}")

    mime, _ = mimetypes.guess_type(str(image_path))
    if mime not in {"image/png", "image/jpeg", "image/webp", "image/gif", "image/svg+xml"}:
        raise ValueError("Use a PNG, JPEG, WebP, GIF or SVG diagram.")
    raw = image_path.read_bytes()
    b64 = base64.b64encode(raw).decode("ascii")
    return f"data:{mime};base64,{b64}"


def safe_json_for_script(obj: Any) -> str:
    """Serialize JSON safely for embedding inside an HTML <script> tag."""
    return (
        json.dumps(obj, ensure_ascii=False, indent=2)
        .replace("<", "\\u003c")
        .replace("\u2028", "\\u2028")
        .replace("\u2029", "\\u2029")
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build a standalone interactive HTML guide for an ML architecture diagram."
    )
    parser.add_argument("--data", required=True, help="Path to structured JSON file.")
    parser.add_argument(
        "--image",
        required=False,
        default=None,
        help="Path to original architecture diagram image (embedded as Base64).",
    )
    parser.add_argument(
        "--template",
        required=False,
        default=None,
        help="Path to HTML template (defaults to ../assets/template.html).",
    )
    parser.add_argument("--out", required=True, help="Output HTML file path.")
    args = parser.parse_args()

    script_dir = Path(__file__).resolve().parent
    template_path = (
        Path(args.template)
        if args.template
        else script_dir.parent / "assets" / "template.html"
    )
    data_path = Path(args.data)
    image_path = Path(args.image) if args.image else None
    out_path = Path(args.out)

    if not template_path.exists():
        print(f"[ERROR] Template not found: {template_path}", file=sys.stderr)
        return 1
    if not data_path.exists():
        print(f"[ERROR] Data JSON not found: {data_path}", file=sys.stderr)
        return 1

    try:
        data = json.loads(data_path.read_text(encoding="utf-8"))
        validate_data(data)
        node_runtime = shutil.which("node")
        if node_runtime:
            verification = subprocess.run(
                [node_runtime, str(script_dir / "check_math.cjs")],
                input=json.dumps(data, ensure_ascii=False), text=True, capture_output=True,
            )
            if verification.returncode:
                raise ValueError(verification.stderr.strip())
        else:
            print("[WARN] Node.js unavailable; verify formulas in the generated guide.", file=sys.stderr)
        image_uri = encode_image_data_uri(image_path)
        template = template_path.read_text(encoding="utf-8")
        vendor = script_dir.parent / "assets/vendor/katex"
        license_text = (vendor / "LICENSE").read_text(encoding="utf-8")
        css = (vendor / "katex.css").read_text(encoding="utf-8")
        js = (vendor / "katex.min.js").read_text(encoding="utf-8")
        math_js = (script_dir.parent / "assets/math.js").read_text(encoding="utf-8")
        bundle = f"<!-- KaTeX 0.16.47\n{license_text}-->\n<style>{css}</style>\n<script>{js}</script>\n<script>{math_js}</script>"
        tokens = {
            "__PAGE_TITLE__": html.escape(data["meta"]["title"]),
            "/*__ARCH_DATA_PLACEHOLDER__*/null": safe_json_for_script(data),
            '/*__IMAGE_URI_PLACEHOLDER__*/""': safe_json_for_script(image_uri),
            "<!--__KATEX_BUNDLE__-->": bundle,
        }
        for token in tokens:
            if template.count(token) != 1:
                raise ValueError(f"Template must include {token} exactly once")
        pattern = "|".join(re.escape(token) for token in tokens)
        result = re.sub(pattern, lambda m: tokens[m[0]], template)
        if out_path.resolve() in {p.resolve() for p in (data_path, template_path, image_path) if p}:
            raise ValueError("Output path must differ from the input paths")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(result, encoding="utf-8")
    except (ValueError, OSError) as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1
    print(f"[OK] Generated interactive guide: {out_path.resolve()}")
    print(
        f"     Nodes: {len(data['nodes'])} | Edges: {len(data['edges'])} | "
        f"Steps: {len(data['steps'])} | Original image embedded: {'Yes' if image_uri else 'No'}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
