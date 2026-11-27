# ML Architecture Explainer

把 AI/ML 论文架构图做成可离线打开的中文交互精读页。点击模块可读公式、张量形状、PyTorch 风格伪代码和设计动机。开启单步演进，用方向键沿计算路径阅读，也可以切到双屏对照原图。

## 安装

将本仓库克隆到所用 Agent 的技能目录。编译器使用 Python 3.9 或更新版本的标准库。环境中有 Node.js 时，会自动用内置 KaTeX 校验公式，并指出有误的 JSON 字段。

**Codex**

```sh
git clone https://github.com/Yurken/ml-arch-explainer.git ~/.codex/skills/ml-arch-explainer
```

**Claude Code**

```sh
git clone https://github.com/Yurken/ml-arch-explainer.git ~/.claude/skills/ml-arch-explainer
```

也可将仓库克隆到项目内的 `.agents/skills/ml-arch-explainer`（Codex）或 `.claude/skills/ml-arch-explainer`（Claude Code）。在新会话中附上原图和论文 PDF 或链接。技能会先定位图号、核对正文公式和算法，再给每个模块标出原文依据。只有图片时，会尝试查找并匹配原论文。

> 用 ml-arch-explainer 解读这张架构图，区分训练和推理路径，标出图中需要推断的维度，生成中文交互 HTML。

## 运行示例

从仓库根目录执行以下命令，随后用浏览器打开生成的 HTML。示例用自绘图展示 Transformer 输入端的词嵌入和位置相加。

```sh
python3 scripts/build_html.py \
  --data examples/input-embedding.json \
  --image examples/input-embedding.svg \
  --out input-embedding.html
```

生成页面支持图解分栏、连续精读和明暗主题。正文、交互图标签、张量形状与符号表共享离线公式渲染器。原图是可选参数。构建时会校验节点、边、演进步骤和论文链接字段，并将公式渲染器、数学字体和所给原图嵌入同一个文件。访问关联论文链接需要联网。

[技能工作流](SKILL.md) · [JSON 数据契约](references/json_schema.md) · [KaTeX 0.16.47 第三方许可](assets/vendor/katex/LICENSE)
