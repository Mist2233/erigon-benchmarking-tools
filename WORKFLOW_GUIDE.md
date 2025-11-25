# 开发工作流与提交规范指南

本文档规定了本项目（Erigon Research）的开发流程与代码提交规范，遵循 GitHub Flow 与 GTD 管理思想。

## 1. 开发工作流 (The Workflow)

在这个项目中，请严格遵守 **"No Issue, No Code"** 原则。任何代码变动都应始于一个 Issue，终于一个 Pull Request。

### 第一阶段：设计与拆解 (GTD & Issue)
1.  **提出想法**：在 GitHub Projects 看板的 `Inbox` 中记录想法。
2.  **转化为 Issue**：
    *   确定要动手时，将 Note 转化为 **Issue**。
    *   **必须包含**：明确的目标（What）、验收标准（Acceptance Criteria）。
    *   *示例*：`Issue #5: 实现 IntraBlockState 的 LRU 缓存淘汰策略`。
3.  **移动看板**：将 Issue 拖入 `Todo` 或 `In Progress`。

### 第二阶段：分支开发 (Branching)
不要直接在 `main` 分支修改代码！

1.  **创建分支**：基于 `main` 创建新分支。
2.  **命名规范**：`type/issue-id/short-desc`
    *   *示例*：
        *   `feat/5-lru-cache` (针对 Issue #5 的功能开发)
        *   `fix/8-rpc-timeout` (针对 Issue #8 的修复)
        *   `docs/setup-guide` (文档编写)

```bash
git checkout main
git pull origin main
git checkout -b feat/5-lru-cache
```

### 第三阶段：提交 (Committing)
*见下方“提交信息规范”章节。*

### 第四阶段：合并 (Pull Request)
1.  **Push 分支**：`git push -u origin feat/5-lru-cache`
2.  **创建 PR**：在 GitHub 页面创建 Pull Request。
3.  **关联 Issue**：在 PR 描述中写上 `Closes #5`（这样合并后 Issue 会自动关闭）。
4.  **Merge**：检查无误后，点击 "Squash and merge" 或 "Create a merge commit"。
5.  **清理**：删除远程和本地的功能分支。

---

## 2. 提交信息规范 (Commit Convention)

每次提交时，请使用以下格式：

```text
<type>(<scope>): <subject>
```

### 2.1 Type (类型) - 必须
这决定了这次提交的性质，也是你最纠结的前缀：

| 前缀           | 含义       | 适用场景                            | 示例                                          |
| :------------- | :--------- | :---------------------------------- | :-------------------------------------------- |
| **`feat`**     | **新功能** | 增加了代码逻辑，引入了新特性        | `feat: implement random eviction policy`      |
| **`fix`**      | **修复**   | 修复了 Bug                          | `fix: resolve nil pointer in GetState`        |
| **`perf`**     | **性能**   | **(科研重点)** 只优化性能，不改逻辑 | `perf: reduce memory allocs in hot path`      |
| **`docs`**     | **文档**   | 只改了文档，没改代码                | `docs: update setup guide`                    |
| **`chore`**    | **杂务**   | 构建过程、辅助工具、依赖库变动      | `chore: add .gitignore`, `chore: update deps` |
| **`style`**    | **格式**   | 不影响代码含义的变动 (空格, 格式化) | `style: gofmt code`                           |
| **`refactor`** | **重构**   | 代码重组，既没加新功能也没修Bug     | `refactor: simplify state object interface`   |
| **`test`**     | **测试**   | 增加或修改测试用例                  | `test: add benchmarks for sload`              |

### 2.2 Scope (范围) - 可选
用括号说明你改了哪个模块（非常有用于 Erigon 这种大项目）。
*   `feat(core): ...`
*   `fix(rpc): ...`
*   `perf(state): ...` (你的科研修改大多属于这个)

### 2.3 Subject (主题) - 必须
*   用祈使句（"add" 而不是 "added"）。
*   不要句号结尾。
*   **英文不好没关系，清晰第一**。

### ✅ 优秀提交示例

```bash
# 你刚才的 gitignore 应该这样写：
git commit -m "chore: add .gitignore for research workspace"

# 你的初始化提交：
git commit -m "feat: initial project structure"

# 未来的实验代码：
git commit -m "perf(state): add prefetch logic to Prepare function"

# 修复脚本路径：
git commit -m "fix(script): update erigon binary path in replay script"
```

---

## 3. 为什么这么做？(Why?)

1.  **自动化生成 Changelog**：以后写论文或者结题报告，直接用工具扫描 `feat` 和 `perf` 的提交，就能自动生成你的“工作量清单”。
2.  **可读性**：导师 Review 代码时，看到 `perf` 就知道这是优化点，看到 `docs` 就知道不用细看代码逻辑。
3.  **职业素养**：这是 Google、Facebook 以及以太坊社区通用的标准。

---

### 给你的建议

把上面这一大段保存为 `WORKFLOW_GUIDE.md` 放在你的 `transaction-replay` 仓库里。

以后每次提交前，如果不确定前缀用啥，就看一眼这个表格。习惯之后，你会发现写 Commit 是一种享受，因为你在清晰地记录你的思维过程。