# 算法笔记

个人刷题记录，按算法类型分文件夹管理。

## 项目结构

```
根目录/
├── CLAUDE.md           # 项目说明（本文件）
├── 1. 数组/
│   ├── README.md       # 数组基础知识
│   └── leetcode.ipynb  # 做题记录
├── 2. 链表/
│   ├── README.md
│   └── leetcode.ipynb
└── ...
```

## 文件夹命名

`序号. 算法名称`，序号表示学习顺序。

## 每章 .ipynb 结构

每个题目占 **两个单元格**：

1. **Markdown 单元格**
   ```markdown
   ## N. 题目名称

   - **难度**：简单 / 中等 / 困难
   - **标签**：哈希表 / 双指针 / 排序 / ...

   **题目**：简洁描述

   **示例**：`输入 -> 输出`

   **思路**：算法步骤、时间/空间复杂度

   **亮点**：核心技巧或关键洞察
   ```

2. **Code 单元格**（可运行）
   ```python
   from typing import List

   class Solution:
       def xxx(self, ...):
           ...

   # 测试
   sol = Solution()
   print(sol.xxx(...))  # 预期输出
   ```

## 添加新题目

1. 在对应章节的 `.ipynb` 末尾添加：
   - 一个 Markdown 块：题目描述 + 思路 + 亮点
   - 一个 Code 块：Solution 类 + 测试用例

2. 格式要求：
   - 代码放在 ` ```python ` 代码块中，保证可运行
   - 思路需注明时间/空间复杂度
   - 亮点描述核心洞察，不是复述思路

## 生成交互式 HTML 讲解

本仓库已绑定 `leetcode-viz` skill，可为每一道 LeetCode 题生成精美的交互式 HTML 讲解页面。

### 触发方式

当你说以下任意一句时，会触发这个 skill：
- "为第 X 题生成 HTML 解释"
- "可视化第 X 题"
- "生成 HTML 讲解"
- "把这个题做成 HTML 页面"
- "按最长连续序列的格式生成 XXX 的 HTML"

### 输出

生成的文件保存到对应章节的 `visual/` 目录下，例如：

```
1. 数组/
├── leetcode.ipynb
└── visual/
    ├── 两数之和.html
    ├── 移动零.html
    └── ...
```

### 设计风格

蓝橙混合风格（蓝色主色 + 暖橙色 Anthropic 强调），包含：
- 10 个章节的完整讲解（题目理解 → 核心思路 → 伪代码骨架 → 交互可视化 → 过程模拟 → 代码解释 → 复杂度 → 易错点 → 总结）
- 可步进的交互式算法演示（上一步/下一步/自动播放/重置）
- 彩色编码单元格表示算法状态

### 注意

- HTML 为单文件自包含（所有样式和 JS 内嵌），可直接在浏览器打开
- 交互演示部分需要针对每道题的算法类型设计不同的可视化策略（见 skill 文件）

## 伪代码骨架章节（每个 HTML 必含）

每个可视化 HTML 在「核心思路」与「交互可视化」之间必须有一节 **伪代码骨架**，作为「思路文字」与「真实代码」之间的抽象层——比文字思路更精确，比真实代码更去噪。

### 位置与编号

- 作为第 **3** 章（紧跟「核心思路」），其 id 为 `pseudo`
- 后续所有章节编号 +1；TOC 中插入对应一行 `<a href="#pseudo">3. 伪代码骨架</a>`，其后编号顺延

### 文风（风格 1：代码骨架 + 中文动宾 + 注释公式）

- **控制流与变量**用代码表达：`while`/`if`/`else`/`for`/`return`，变量名沿用代码里的真实变量名
- **操作**用中文动宾短句概括，如「更新左最大值」「计算左边贡献」「左指针右移」
- **精确公式**放在行尾 `#` 注释里，如 `# ans += leftMax - h[left]`
- 去掉 `self`、类型注解、`List[int]` 等样板，只保留算法骨架
- HTML 中 `<` 必须写成 `&lt;`

### 着色（token 颜色）

伪代码用 `<pre class="pseudo"><code>` 包裹，每个 token 用 `<span>` 着色：

| 类别 | class | 颜色 | 示例 |
|---|---|---|---|
| 关键字 | `kw` | #C792EA（紫） | while / if / return |
| 变量 | `var` | #82AAFF（蓝） | left / ans / leftMax |
| 中文操作 | `zh` | #C3E88D（绿，加粗） | 更新左最大值 |
| 注释公式 | `cm` | #7C8DB5（灰，斜体） | # ans += ... |
| 数字 | `num` | #F78C6C（橙） | 0 / 1 |

需要在 `</style>` 前加入以下 CSS（若已存在则跳过）：

    .pseudo .kw{color:#C792EA}
    .pseudo .var{color:#82AAFF}
    .pseudo .zh{color:#C3E88D;font-weight:600}
    .pseudo .cm{color:#7C8DB5;font-style:italic}
    .pseudo .num{color:#F78C6C}
    .pseudo-legend{display:flex;flex-wrap:wrap;justify-content:center;gap:14px;margin:10px 0 4px;font-size:12px;color:var(--text-light)}
    .pseudo-legend span{display:inline-flex;align-items:center;gap:5px}
    .pseudo-legend i{width:12px;height:12px;border-radius:3px;display:inline-block}

### 章节结构

    <section class="card" id="pseudo">
      <h2>3. 伪代码骨架</h2>
      <p>引导句：说明这一层抽象的作用（控制流/变量用代码、操作用中文短句、公式放注释）</p>
      <pre class="pseudo"><code>...该题伪代码（风格 1 + 着色）...</code></pre>
      <div class="pseudo-legend">
        <span><i style="background:#C792EA"></i>关键字</span>
        <span><i style="background:#82AAFF"></i>变量</span>
        <span><i style="background:#C3E88D"></i>中文操作</span>
        <span><i style="background:#7C8DB5"></i>注释公式</span>
      </div>
      <div class="note blue">一句话点睛（关键判断、对称性或边界）</div>
    </section>

参考实现见 `1. 数组/visual/11. 接雨水.html` 的第 3 章。

## 磨眼睛 Web App（手机刷题闪卡）

本仓库自带一个手机 Web App：解析各章节 `leetcode.ipynb` 生成闪卡式 PWA，托管在 GitHub Pages，用于「磨眼睛」式刷题。

### 访问

- 网址：`https://sikm-lqs.github.io/leetcode-learn/`
- 手机浏览器打开后可「添加到主屏幕」当独立 App 使用，支持完全离线（Service Worker 全量缓存题库和 visual 讲解）

### App 相关文件（不影响刷题笔记本身）

```
scripts/build_app.py          # 构建脚本：解析 ipynb → dist/（唯一维护入口）
app/index.template.html       # 单文件 SPA 模板（含 __DATA_JSON__ / __VERSION__ 占位符，勿删）
.github/workflows/deploy.yml  # push main 时自动构建并部署 Pages
dist/                         # 构建产物（已 gitignore，不入库）
```

### 维护方式

- **日常加题**：正常往 `*/leetcode.ipynb` 末尾加题（遵循上文两单元格格式），push 到 main 后 App 自动更新，无需额外操作
- **新题带可视化**：HTML 放到对应章节 `visual/` 下，文件名必须是 `{题号}. {题目名}.html`，构建时自动匹配为题卡上的跳转链接
- **本地预览**：
  ```bash
  python3 scripts/build_app.py
  python3 -m http.server 8000 --directory dist   # 浏览器开 http://localhost:8000
  ```
- **解析校验**：`python3 scripts/build_app.py --check` 只解析不产出，缺字段（如缺思路）的题目会打印提醒
- **改 App 样式/逻辑**：只改 `app/index.template.html`，改完跑一次构建验证

### 数据说明

- 掌握度标记（没思路/有思路/秒了）存在手机浏览器 localStorage，仅本机可见，换设备不同步
- 磨眼模式按掌握度加权抽题：没思路 6 > 有思路 2 > 秒了 0.5（未标记 3）
- Service Worker 版本号 = 题库数据 hash，题库更新后旧缓存自动清理，页面提示刷新
