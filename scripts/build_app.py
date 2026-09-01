#!/usr/bin/env python3
"""构建脚本：解析各章节 leetcode.ipynb -> dist/ 单文件 SPA + PWA 离线缓存。

用法：
    python3 scripts/build_app.py          # 构建到 dist/
    python3 scripts/build_app.py --check  # 仅校验解析结果，不产出 dist/

产物：
    dist/index.html              单文件 SPA（题库 JSON 内嵌）
    dist/manifest.webmanifest
    dist/sw.js                   Service Worker（precache 全部页面）
    dist/icon.svg / icon-{180,192,512}.png
    dist/{章节}/visual/*.html    交互式可视化讲解（原样复制）
"""
import hashlib
import html
import json
import re
import shutil
import struct
import sys
import zlib
from datetime import date
from pathlib import Path
from urllib.parse import quote, unquote

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"

DIFF_MAP = {"简单": 1, "中等": 2, "困难": 3}


# ---------------------------------------------------------------- markdown
def inline_md(s: str) -> str:
    s = html.escape(s)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    return s


def md_to_html(text: str) -> str:
    """极简 markdown -> HTML：段落 / - 列表 / `代码` / **加粗** / ```围栏。"""
    lines = [l.rstrip() for l in text.strip().split("\n")]
    out: list[str] = []
    para: list[str] = []
    items: list[str] = []
    code: list[str] = []
    in_code = False

    def flush_para():
        if para:
            out.append("<p>" + "<br>".join(inline_md(l) for l in para) + "</p>")
            para.clear()

    def flush_items():
        if items:
            out.append("<ul>" + "".join(f"<li>{inline_md(i)}</li>" for i in items) + "</ul>")
            items.clear()

    def flush_code():
        if code:
            out.append(
                '<pre class="md-pre">' + html.escape("\n".join(code)) + "</pre>"
            )
            code.clear()

    for l in lines:
        if l.strip().startswith("```"):
            if in_code:
                flush_code()
                in_code = False
            else:
                flush_para()
                flush_items()
                in_code = True
            continue
        if in_code:
            code.append(l)
        elif l.startswith("- "):
            flush_para()
            items.append(l[2:].strip())
        elif not l.strip():
            flush_para()
            flush_items()
        else:
            flush_items()
            para.append(l)
    if in_code:
        flush_code()
    flush_para()
    flush_items()
    return "".join(out)


# ---------------------------------------------------------------- 解析
def field(src: str, name: str) -> str:
    m = re.search(
        rf"\*\*{name}\*\*[：:]\s*(.*?)(?=\n\s*-?\s*\*\*|\n\n|\Z)", src, re.S
    )
    return m.group(1).strip() if m else ""


def strip_test(code: str) -> str:
    m = re.search(r"^#\s*测试\s*$", code, re.M)
    return code[: m.start()].rstrip() if m else code.rstrip()


def parse_notebook(path: Path, ch_id: str, ch_name: str) -> list[dict]:
    nb = json.loads(path.read_text(encoding="utf-8"))
    cells = nb["cells"]
    problems: list[dict] = []
    for i, cell in enumerate(cells):
        if cell["cell_type"] != "markdown":
            continue
        src = "".join(cell["source"]).strip()
        head = re.match(r"^## (\d+)\.\s*(.+)$", src, re.M)
        if not head:
            continue
        num, title = int(head.group(1)), head.group(2).strip()
        diff = field(src, "难度").strip() or "中等"
        tags = [t.strip() for t in re.split(r"[/、,，]", field(src, "标签")) if t.strip()]
        code = ""
        if i + 1 < len(cells) and cells[i + 1]["cell_type"] == "code":
            code = strip_test("".join(cells[i + 1]["source"]))
        visual = None
        vfile = path.parent / "visual" / f"{num}. {title}.html"
        if vfile.exists():
            visual = quote(f"{ch_id}/visual/{vfile.name}")
        problems.append(
            {
                "id": f"{ch_id}::{num:02d}",
                "ch": ch_id,
                "chName": ch_name,
                "num": num,
                "title": title,
                "diff": diff,
                "tags": tags,
                "desc_html": md_to_html(field(src, "题目")),
                "ex_html": md_to_html(field(src, "示例")),
                "idea_html": md_to_html(field(src, "思路")),
                "hl_html": md_to_html(field(src, "亮点")),
                "code": code,
                "visual": visual,
            }
        )
    return problems


def collect() -> tuple[list[dict], list[dict]]:
    chapters, problems = [], []

    def order(p: Path):
        m = re.match(r"^(\d+)\.", p.name)
        return int(m.group(1)) if m else 999

    for d in sorted(ROOT.iterdir(), key=order):
        nb = d / "leetcode.ipynb"
        if not (d.is_dir() and nb.exists()):
            continue
        m = re.match(r"^(\d+)\.\s*(.+)$", d.name)
        ch_id, ch_name = d.name, (m.group(2) if m else d.name)
        ps = parse_notebook(nb, ch_id, ch_name)
        if not ps:
            continue
        chapters.append({"id": ch_id, "name": ch_name, "count": len(ps)})
        problems.extend(ps)
    return chapters, problems


# ---------------------------------------------------------------- PWA 资产
def write_png(size: int, path: Path):
    """纯 Python 生成 PNG 图标：深底 + 蓝环 + 橙心（眼睛意象）。"""
    cx = cy = size / 2
    rows = bytearray()
    for y in range(size):
        rows.append(0)
        for x in range(size):
            d = ((x - cx + 0.5) ** 2 + (y - cy + 0.5) ** 2) ** 0.5
            if d < size * 0.18:
                r, g, b = 232, 146, 108  # 橙
            elif d < size * 0.30:
                r, g, b = 91, 156, 246  # 蓝
            else:
                r, g, b = 10, 16, 30  # 深底
            rows += bytes((r, g, b))

    def chunk(tag: bytes, data: bytes) -> bytes:
        return (
            struct.pack(">I", len(data))
            + tag
            + data
            + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        )

    ihdr = struct.pack(">IIBBBBB", size, size, 8, 2, 0, 0, 0)
    path.write_bytes(
        b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", zlib.compress(bytes(rows), 9)) + chunk(b"IEND", b"")
    )


ICON_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
<rect width="100" height="100" rx="22" fill="#0A101E"/>
<ellipse cx="50" cy="50" rx="30" ry="22" fill="none" stroke="#5B9CF6" stroke-width="7"/>
<circle cx="50" cy="50" r="10" fill="#E8926C"/>
</svg>
"""


SW_TEMPLATE = """// 由 scripts/build_app.py 自动生成，勿手改
const VERSION = '__VER__';
const CACHE = 'grind-' + VERSION;
const ASSETS = __ASSETS__;
self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(ASSETS)).then(() => self.skipWaiting()));
});
self.addEventListener('activate', e => {
  e.waitUntil(caches.keys()
    .then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k))))
    .then(() => self.clients.claim()));
});
self.addEventListener('fetch', e => {
  if (e.request.method !== 'GET') return;
  e.respondWith(
    caches.match(e.request, { ignoreSearch: true }).then(r =>
      r || fetch(e.request).then(res => {
        const cp = res.clone();
        caches.open(CACHE).then(c => c.put(e.request, cp));
        return res;
      }).catch(() => caches.match('./index.html'))
    )
  );
});
"""


def build_sw(assets: list[str], version: str) -> str:
    return SW_TEMPLATE.replace("__VER__", version).replace(
        "__ASSETS__", json.dumps(assets, ensure_ascii=False)
    )


MANIFEST = {
    "name": "磨眼睛 · LeetCode 闪卡",
    "short_name": "磨眼睛",
    "start_url": "./",
    "scope": "./",
    "display": "standalone",
    "background_color": "#0A101E",
    "theme_color": "#0A101E",
    "icons": [
        {"src": "icon-192.png", "sizes": "192x192", "type": "image/png"},
        {"src": "icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any maskable"},
    ],
}


# ---------------------------------------------------------------- 主流程
def build(check_only: bool = False):
    chapters, problems = collect()
    total = len(problems)
    n_visual = sum(1 for p in problems if p["visual"])
    missing_idea = [p["id"] for p in problems if not p["idea_html"]]
    print(f"解析完成：{len(chapters)} 章 / {total} 题 / {n_visual} 题带可视化")
    if missing_idea:
        print("  ! 缺思路字段:", ", ".join(missing_idea))
    if check_only:
        return

    data = {
        "builtAt": date.today().isoformat(),
        "chapters": chapters,
        "problems": problems,
    }
    version = hashlib.sha256(
        json.dumps(data, ensure_ascii=False, sort_keys=True).encode()
    ).hexdigest()[:12]

    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir()

    # 复制 visual HTML（保持 章节名/visual/ 结构，与链接路径一致）
    for p in problems:
        if p["visual"]:
            raw = unquote(p["visual"])
            src, dst = ROOT / raw, DIST / raw
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)

    # 图标
    (DIST / "icon.svg").write_text(ICON_SVG, encoding="utf-8")
    for s in (180, 192, 512):
        write_png(s, DIST / f"icon-{s}.png")

    # manifest / sw
    (DIST / "manifest.webmanifest").write_text(
        json.dumps(MANIFEST, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    assets = (
        ["./", "./index.html", "./manifest.webmanifest", "./icon.svg",
         "./icon-180.png", "./icon-192.png", "./icon-512.png"]
        + ["./" + p["visual"] for p in problems if p["visual"]]
    )
    (DIST / "sw.js").write_text(build_sw(assets, version), encoding="utf-8")

    # 注入模板
    tpl = (ROOT / "app" / "index.template.html").read_text(encoding="utf-8")
    data_json = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    out = tpl.replace("__DATA_JSON__", data_json).replace("__VERSION__", version)
    (DIST / "index.html").write_text(out, encoding="utf-8")

    size_kb = (DIST / "index.html").stat().st_size / 1024
    print(f"构建完成 -> dist/  index.html {size_kb:.0f} KB  版本 {version}")


if __name__ == "__main__":
    build(check_only="--check" in sys.argv)
