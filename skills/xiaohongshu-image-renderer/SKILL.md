---
name: xiaohongshu-image-renderer
description: "Use when generating, regenerating, paginating, rendering, or visually validating Xiaohongshu long-image packages from a confirmed master, including Markdown tables."
---

# Xiaohongshu Image Renderer

<!-- skill-workflow-link -->
[查看完整流程图与操作说明](references/workflow.md)
<!-- /skill-workflow-link -->

团队首次使用先读 [配置与依赖](references/team-setup.md)；已有配置与本轮明确入口直接复用，不重复索取。

Read [visual-contract.md](references/visual-contract.md) completely before any image work.
For the existing locked template, paginate, render, regenerate and visually
validate directly against that contract; a new general design-system search
is not a prerequisite. Use ui-ux-pro-max only when the user has authorized a
template design change that needs it. Generic design suggestions cannot
change the locked memo into a poster, card layout or different visual style,
and do not replace the bundled renderer or its validation gates.

## First use and runtime

Use Node.js 20 or newer and an installed Chrome/Chromium. From this installed Skill directory run `npm ci`; the lockfile declares Playwright explicitly. No Codex cache or author-local package path is required. The renderer starts a separate headless browser profile and never reuses a signed-in browser.

Chrome is found on the current system PATH or standard application locations. Use `--chrome-path <executable>` or `XHS_CHROME_PATH` for another installation. macOS and Linux paths are supported; Windows execution and process cleanup still require platform verification before promising support. Install a Chinese font from the listed fallback families; pagination depends on the actual installed fonts and is measured again on every run.

Before locking a new input, compute lowercase `sourceHash` as `SHA256(title.trim() + "\n" + body.replace(/\s+/gu, "").trim())`, encoded as UTF-8. Start with the member's confirmed title/body; do not invent Feishu identifiers. After this initial preparation, the input is locked.

## Locked input

Treat `<package-dir>/source.json` as the exact locked contract: it must retain
its non-empty `title`, non-empty `body`, and matching lowercase SHA-256
`sourceHash`; preserve supplied identity fields. Never edit `source.json` or
`copy.json`, and never alter, summarize, reorder, or omit source copy.

## Render and validate

Use only these bundled production commands; do not hand-write SVG, HTML, CSS,
pagination, screenshots, or substitute renderers:

Run from this installed Skill directory.

```bash
node scripts/render-package.mjs <package-dir>
node scripts/validate-package.mjs <package-dir>
# If Chrome is not auto-discovered:
# node scripts/render-package.mjs <package-dir> --chrome-path <executable>
```

Stop immediately if either command fails or the validator reports `ok: false`.
Do not return a partial package or attempt manual repair.

The package directory may contain the locked input and only these declared
renderer artifacts: `pages.json`, `pagination.txt`, `_render-work/page-NN.html`,
`NN.png`, `render-stats.json`, `validation.json`, `manifest.json`, and
`final-verification.json`. Do not add README files or alternate filenames.

Return the validated package path, filenames, `sourceHash`, `exactText`, and
validator result, including every page's `fillRatio`. This skill creates only local files: never write to Feishu,
open a publishing surface, or publicly publish.
