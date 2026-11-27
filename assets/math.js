// The offline guide and build-time verifier use the same splitter and KaTeX options.
function createMathRenderer(katex) {
  const escape = s => s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
                       .replace(/"/g, "&quot;").replace(/'/g, "&#39;");
  const cache = new Map();
  function typeset(tex, display = false) {
    if (/[\x00-\x08\x0b\x0c\x0e-\x1f]/.test(tex)) throw Error("Control character in LaTeX; check JSON escaping");
    const key = (display ? "D" : "I") + tex;
    if (!cache.has(key)) {
      cache.set(key, katex.renderToString(tex, {
        displayMode: display, throwOnError: true, trust: false,
        strict: code => code === "unknownSymbol" ? "error" : "ignore"
      }));
    }
    return cache.get(key);
  }

  // Recognize legacy tensor dimensions and common manuscript notation without
  // interpreting ordinary words, source code or technical names as formulas.
  const atom = /(?<![a-zA-Z0-9_\\])(?:\[[A-Za-z0-9_,. ×+-]+\]|[A-Za-zΑ-Ωα-ωϕϵϑÂĜ𝒵](?:_[A-Za-z0-9]+|\^[A-Za-z0-9]+|[₀-₉₊₋₍₎ₐ-ₜᵢⱼᵣᵤᵥᵦ-ᵪ]+|[⁰¹²³⁴-⁹⁺⁻⁽⁾ᵏⁿⁱ]+)*|[⊙∥∈∑∏≈≤≥])(?=$|[^A-Za-z0-9_])/gu;
  function legacy(tex) {
    return tex
      .replace(/[₀-₉₊₋₍₎ₐ-ₜᵢⱼᵣᵤᵥᵦ-ᵪ]+/gu, s => "_{" + s.normalize("NFKC") + "}")
      .replace(/[⁰¹²³⁴-⁹⁺⁻⁽⁾ᵏⁿⁱ]+/gu, s => "^{" + s.normalize("NFKC") + "}")
      .replace(/([_^])([A-Za-z0-9]{2,})/g, (_, op, sub) => op + "{" + (/^[a-z]{2,}$/.test(sub) ? "\\mathrm{" + sub + "}" : sub) + "}")
      .replace(/∥/g, "\\Vert ").replace(/Â/g, "\\hat{A}").replace(/Ĝ/g, "\\hat{G}").replace(/𝒵/gu, "\\mathcal{Z}");
  }
  function legacyProse(s) {
    if (/\\(?:[A-Za-z]+|[()[\]])/.test(s)) throw Error("Wrap the LaTeX in math delimiters: " + s);
    let out = "", last = 0;
    for (const m of s.matchAll(atom)) {
      const token = m[0];
      // Leave the English articles/pronoun alone in ordinary English prose.
      const englishWord = /^[aAI]$/.test(token) && /[A-Za-z]{2,}\s+$/.test(s.slice(0, m.index));
      const englishStart = /^[aAI]$/.test(token) && /^\s+[A-Za-z]{2,}/.test(s.slice(m.index + token.length));
      if (englishWord || englishStart) continue;
      out += escape(s.slice(last, m.index)) + typeset(legacy(token));
      last = m.index + token.length;
    }
    return out + escape(s.slice(last));
  }

  // A closing delimiter inside a braced text argument or following a
  // backslash is part of the expression, not the end of the math span.
  function endOfMath(s, start, closing) {
    let depth = 0;
    for (let i = start; i < s.length; i++) {
      if (depth === 0 && s.startsWith(closing, i)) return i;
      if (s[i] === "\\") i++;
      else if (s[i] === "{") depth++;
      else if (s[i] === "}") depth = Math.max(0, depth - 1);
    }
    return -1;
  }
  function format(value, mode = "text") {
    const s = String(value ?? "");
    if (!s) return "";
    const opening = /\\\$|\$\$|\\\(|\\\[|\$/g;
    const hasMarkup = opening.test(s);
    opening.lastIndex = 0;
    if (mode === "display" && !/^(?:\\\(|\\\[|\$)/.test(s.trim())) return typeset(s, true);
    if (!hasMarkup && mode === "symbol" && s.includes("\\")) return typeset(s);
    if (!hasMarkup && mode === "symbol" && !/[\p{Script=Han}\p{Script=Hiragana}\p{Script=Katakana}]/u.test(s)) {
      if (!/^[A-Za-z]{2,}(?:[ -][A-Za-z]{2,})*$/.test(s)) return typeset(legacy(s));
      return typeset("\\mathrm{" + s.replace(/ /g, "\\ ") + "}");
    }
    let out = "", last = 0, m;
    while ((m = opening.exec(s))) {
      const left = m[0], start = opening.lastIndex;
      if (left === "\\$") {
        out += legacyProse(s.slice(last, m.index)) + "$";
        last = start;
        continue;
      }
      const right = left === "\\(" ? "\\)" : left === "\\[" ? "\\]" : left;
      const stop = endOfMath(s, start, right);
      if (stop < 0) {
        if (left === "$" && /^\d/.test(s.slice(start))) continue;
        throw new Error("Unclosed math delimiter " + left);
      }
      out += legacyProse(s.slice(last, m.index)) + typeset(s.slice(start, stop), mode === "display" || left === "$$" || left === "\\[");
      opening.lastIndex = last = stop + right.length;
    }
    return out + legacyProse(s.slice(last));
  }
  return { format };
}

if (typeof module !== "undefined" && module.exports) module.exports = createMathRenderer;
