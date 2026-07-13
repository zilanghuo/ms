# Codex 上下文恢复目录搭建说明

最后更新：2026-07-13

## 目标

在一个新项目中快速建立一套可复用的上下文恢复文件，用于账号切换、Codex 实例切换、任务中断或新会话启动后，快速读取历史内容并恢复工作状态。

推荐目录名使用 `codex-context/`，不要使用 `.codex/`。

原因：

- `.codex/` 在 Codex 生态中可能被当作项目配置、状态或受保护目录。
- 某些运行环境会将 `.codex/` 设置为只读，导致 Codex 无法自动写入。
- `codex-context/` 是普通项目目录，更适合作为人和 AI 都能维护的上下文恢复包。

## 推荐目录结构

```text
codex-context/
├── context.md          # 当前上下文，最重要
├── progress.md         # 当前开发进度
├── decisions.md        # 技术、文档、流程决策
├── todo.md             # 下一步计划
├── prompts.md          # 常用 Prompt
└── sessions/
    └── .gitkeep        # 保留 sessions 目录
```

建议同时在项目根目录维护：

```text
AGENTS.md              # AI 工作规范
```

如果项目已经有 `AGENTS.md`，不要覆盖，只追加“上下文恢复文件”说明即可。

## 一键创建目录和模板

在新项目根目录执行：

```bash
mkdir -p codex-context/sessions

cat > codex-context/context.md <<'EOF'
# 当前上下文

本文件用于账号、实例或任务切换后快速恢复上下文。新实例进入本仓库后，优先读取本文件，再读取 `progress.md`、`decisions.md`、`todo.md` 和 `prompts.md`。

## 仓库信息

- 仓库路径：`请填写项目绝对路径`
- 主要工作类型：`请填写项目主要工作类型`
- 仓库规范入口：`AGENTS.md`
- 恢复文件目录：`codex-context/`

## 当前重要背景

- 请记录项目背景、业务背景、技术栈、关键目录、重要约束。
- 请记录新实例必须优先知道的上下文。
- 请记录容易被忘记但会影响后续工作的事项。

## 最近上下文

- 请记录最近正在做的任务。
- 请记录最近完成的关键变更。
- 请记录当前阻塞或需要用户确认的事项。

## 恢复顺序

1. 读取 `AGENTS.md`，确认仓库规则。
2. 读取 `codex-context/context.md`，恢复背景。
3. 读取 `codex-context/progress.md`，确认已完成和当前状态。
4. 读取 `codex-context/decisions.md`，沿用已做决策。
5. 读取 `codex-context/todo.md`，继续下一步。
6. 需要常用指令时读取 `codex-context/prompts.md`。

## 注意事项

- 不要在本目录记录 token、cookie、API key、账号密码或其他敏感凭据。
- 若本文件与用户当前明确指令冲突，以用户当前明确指令为准。
- 若恢复信息过期，应先向用户确认，再更新本文件。
EOF

cat > codex-context/progress.md <<'EOF'
# 当前开发进度

用于记录当前仓库中跨账号、跨实例、跨任务需要延续的工作状态。

## 已完成

- 请记录已经完成的事项。

## 进行中

- 请记录当前正在推进的事项。

## 阻塞或风险

- 请记录当前阻塞、风险、外部依赖、需要用户确认的问题。

## 最近验证记录

- 请记录最近执行过的检查、测试、构建、人工核验等。

## 更新规则

- 完成一个阶段后，在“已完成”追加简短记录。
- 遇到阻塞时，在“阻塞或风险”记录原因和下一步。
- 不记录敏感凭据。
EOF

cat > codex-context/decisions.md <<'EOF'
# 技术决策

用于记录已经确认的技术、文档和流程决策，避免换账号或新实例后重复判断。

## 决策记录

### YYYY-MM-DD：决策标题

- 决策：请写明最终选择。
- 原因：请写明为什么这样选。
- 影响：请写明对后续工作的影响。

## 待确认决策

- 请记录仍需确认的问题。
EOF

cat > codex-context/todo.md <<'EOF'
# 下一步计划

用于记录后续账号或实例恢复后的优先执行事项。

## 优先级高

- 请记录必须优先处理的事项。

## 优先级中

- 请记录重要但不紧急的事项。

## 优先级低

- 请记录可选优化、清理或补充事项。

## 完成定义

- 新账号或新实例进入仓库后，读取 `AGENTS.md` 和 `codex-context/context.md` 能理解当前工作背景。
- 读取 `codex-context/progress.md` 能知道已经做了什么、哪里阻塞。
- 读取 `codex-context/todo.md` 能继续下一步。

## 状态标签约定

- `[待执行]`：需求还没有落实到业务代码、文档正式产物或实际交付物。
- `[逻辑已固化]`：已经完成资料阅读、差异梳理和执行方案沉淀，下次可直接按记录执行。
- `[业务代码未改]`：明确没有改动 `packages/`、`apps/`、后端模块等业务实现文件。
- `[已完成]`：实际修改已完成，并记录了必要验证结果。
- 对“先记下来、暂时不做”的事项，建议组合使用 `[待执行][逻辑已固化][业务代码未改]`。
EOF

cat > codex-context/prompts.md <<'EOF'
# 常用 Prompt

用于保存本仓库常用提示词。使用时可按需复制或让 Codex 读取本文件后执行。

## 恢复上下文

```text
请先读取 AGENTS.md，然后依次读取 codex-context/context.md、codex-context/progress.md、codex-context/decisions.md、codex-context/todo.md，恢复当前仓库上下文。先总结你理解到的当前状态、关键规则、阻塞项和下一步计划，暂时不要修改文件。
```

## 继续上次任务

```text
请读取 AGENTS.md 和 codex-context/ 下的恢复文件，基于 codex-context/todo.md 继续上次任务。开始前先说明你准备执行的步骤；遇到与 AGENTS.md 冲突的内容，以 AGENTS.md 和我的最新指令为准。
```

## 更新恢复文件

```text
请根据本次对话和实际文件变更，更新 codex-context/context.md、codex-context/progress.md、codex-context/decisions.md、codex-context/todo.md。不要记录 token、cookie、API key、账号密码或其他敏感信息。
```

## 归纳 15 天前内容

```text
请读取 codex-context/context.md、codex-context/progress.md、codex-context/decisions.md、codex-context/todo.md 和 codex-context/sessions/ 下的会话摘要，将距今天超过 15 天且仍有保留价值的内容归纳为简短历史摘要。保留仍影响当前工作的决策、约束、阻塞和结论；删除或压缩已经过期的流水账。不要记录 token、cookie、API key、账号密码或其他敏感信息。
```
EOF

touch codex-context/sessions/.gitkeep
```

## AGENTS.md 追加说明

如果项目还没有 `AGENTS.md`，可以先创建：

```bash
cat > AGENTS.md <<'EOF'
# Codex Agent Guide

本文件定义 Codex 在本仓库中的通用工作规则。若用户需求与本规则冲突，优先按用户明确要求执行。
EOF
```

然后在 `AGENTS.md` 末尾追加：

```md
## 上下文恢复文件

- 本仓库使用 `codex-context/` 目录保存账号、实例或任务切换后的恢复上下文。
- 新实例进入本仓库后，应优先读取以下文件：
  - `codex-context/context.md`：当前上下文与重要背景。
  - `codex-context/progress.md`：当前开发进度、已完成事项与阻塞项。
  - `codex-context/decisions.md`：已经确认的技术、文档和流程决策。
  - `codex-context/todo.md`：下一步计划。
  - `codex-context/prompts.md`：常用 Prompt。
- `codex-context/sessions/` 可用于保存按日期或任务拆分的会话摘要。
- 对距当前日期超过 15 天的恢复内容，应定期归纳为简短历史摘要，只保留仍影响当前工作的决策、约束、阻塞和结论。
- 不要在 `codex-context/` 中记录 token、cookie、API key、账号密码或其他敏感凭据。
- 若 `codex-context/` 中的恢复信息与用户最新明确指令冲突，以用户最新明确指令为准。
```

如果希望用命令追加，可以执行：

```bash
cat >> AGENTS.md <<'EOF'

## 上下文恢复文件

- 本仓库使用 `codex-context/` 目录保存账号、实例或任务切换后的恢复上下文。
- 新实例进入本仓库后，应优先读取以下文件：
  - `codex-context/context.md`：当前上下文与重要背景。
  - `codex-context/progress.md`：当前开发进度、已完成事项与阻塞项。
  - `codex-context/decisions.md`：已经确认的技术、文档和流程决策。
  - `codex-context/todo.md`：下一步计划。
  - `codex-context/prompts.md`：常用 Prompt。
- `codex-context/sessions/` 可用于保存按日期或任务拆分的会话摘要。
- 对距当前日期超过 15 天的恢复内容，应定期归纳为简短历史摘要，只保留仍影响当前工作的决策、约束、阻塞和结论。
- 不要在 `codex-context/` 中记录 token、cookie、API key、账号密码或其他敏感凭据。
- 若 `codex-context/` 中的恢复信息与用户最新明确指令冲突，以用户最新明确指令为准。
EOF
```

## 文件用途说明

| 文件 | 用途 | 维护时机 |
| --- | --- | --- |
| `context.md` | 保存最重要的项目背景、当前上下文、恢复顺序 | 每次任务背景发生变化时 |
| `progress.md` | 保存已完成、进行中、阻塞项、验证记录 | 每次阶段性完成或遇到阻塞时 |
| `decisions.md` | 保存已确认的技术、文档、流程决策 | 每次做出不可轻易回滚的判断时 |
| `todo.md` | 保存下一步计划和优先级 | 每次任务结束前 |
| `prompts.md` | 保存常用 Prompt | 沉淀出可复用工作方式时 |
| `sessions/` | 保存按日期或任务拆分的会话摘要 | 长任务、跨天任务、重要任务结束后 |

## 新实例恢复 Prompt

新开账号、新开实例或新开任务时，可以直接发送：

```text
请先读取 AGENTS.md，然后依次读取 codex-context/context.md、codex-context/progress.md、codex-context/decisions.md、codex-context/todo.md，恢复当前仓库上下文。先总结你理解到的当前状态、关键规则、阻塞项和下一步计划，暂时不要修改文件。
```

## 维护建议

- `context.md` 只放真正影响恢复的信息，不要写流水账。
- `progress.md` 记录状态变化，避免新实例不知道任务卡在哪里。
- `decisions.md` 记录“为什么这样做”，避免后续重复讨论。
- `todo.md` 面向下一步行动，尽量写成可以执行的清单；对未实施但已梳理清楚的任务，使用 `[待执行][逻辑已固化][业务代码未改]` 等状态标签区分“还没做”和“方案已沉淀”。
- `prompts.md` 放经过验证好用的提示词，不要堆太多一次性 Prompt。
- `sessions/` 只保存关键会话摘要，不需要保存完整对话；长任务摘要顶部建议写明状态，例如 `[待执行][逻辑已固化][业务代码未改]` 或 `[已完成]`。
- 距当前日期超过 15 天的内容不要长期堆在当前上下文里，应归纳为简短历史摘要；只保留仍影响当前工作的决策、约束、阻塞和结论。

## 安全注意事项

不要在 `codex-context/` 中记录以下内容：

- token
- cookie
- API key
- 账号密码
- 私钥
- 生产环境连接串
- 任何不能提交到代码仓库的敏感信息

如果某项上下文必须依赖敏感信息，只记录“需要用户提供某凭据”或“凭据存放在团队约定的安全位置”，不要记录凭据本身。

## 验收命令

创建后可以执行：

```bash
find codex-context -maxdepth 2 -type f -print
rg -n 'codex-context|上下文恢复文件' AGENTS.md codex-context
```

期望至少看到：

```text
codex-context/context.md
codex-context/progress.md
codex-context/decisions.md
codex-context/todo.md
codex-context/prompts.md
codex-context/sessions/.gitkeep
```
