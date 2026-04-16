# TK库存检查 SPU原型统一化 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 `TK库存检查` 原型中的 `SPU维度` 调整为与 `PID&SKU维度` 同构的库存检查视图，仅保留 `SPU` 粒度差异。

**Architecture:** 保持现有单 HTML 双 tab 结构不变，直接在 `TK库存检查-PID&SKU看板.html` 内统一 `SPU` 视图的文案、汇总卡片和表格字段。改动仅限静态原型表达与说明文字，不涉及接口、数据模型或新页面拆分。

**Tech Stack:** HTML, CSS, vanilla JavaScript

---

### Task 1: 对齐 SPU 视图的文案与汇总区

**Files:**
- Modify: `bi/tkDashboard/库存检查/htmls/TK库存检查-PID&SKU看板.html`
- Test: `bi/tkDashboard/库存检查/htmls/TK库存检查-PID&SKU看板.html`

- [ ] **Step 1: 更新 SPU 视图说明文案**

将 `SPU` 视图中的说明从占位语义改为确定性描述，重点表达：

```html
<div class="legend">
  数据规则：SPU维度基于 <code>PID&amp;SKU</code> 底表按 <code>SPU</code> 聚合生成；除主维度外，其余库存业务字段与明细视图保持一致。<code>库存是否异常</code> 按 SPU 聚合后的库存差异重新判断：差异大于 0 为少同步，小于 0 为超卖风险，等于 0 为同步正确。
</div>
```

- [ ] **Step 2: 调整 SPU 汇总卡片标签**

保留与 `PID&SKU` 视图一致的卡片结构，仅调整维度文案：

```html
<div class="summary-card">
  <div class="summary-label">SPU总数</div>
  <div class="summary-value">216</div>
  <div class="summary-sub">当前查询范围内的 SPU 数量</div>
</div>
<div class="summary-card summary-danger">
  <div class="summary-label">异常SPU数</div>
  <div class="summary-value">28</div>
  <div class="summary-sub">少同步或超卖风险项</div>
</div>
```

- [ ] **Step 3: 运行文本检查确认不存在旧占位描述**

Run: `rg -n "建议在明细基础上按 SPU 聚合生成|先汇总、后下钻|风险等级|说明" bi/tkDashboard/库存检查/htmls/TK库存检查-PID\\&SKU看板.html`
Expected: 仅剩符合新口径的文案，不再出现旧的 SPU 占位表达

### Task 2: 对齐 SPU 视图表格字段结构

**Files:**
- Modify: `bi/tkDashboard/库存检查/htmls/TK库存检查-PID&SKU看板.html`
- Test: `bi/tkDashboard/库存检查/htmls/TK库存检查-PID&SKU看板.html`

- [ ] **Step 1: 将 SPU 表头调整为与 PID&SKU 视图同构**

保留 `时间 / 店铺 / SPU / SPU名称`，移除 `PID / SKU / SKU名称`，并补齐其余字段分组：

```html
<tr>
  <th class="sticky-col-1 th-group group-base" rowspan="2">时间</th>
  <th class="sticky-col-2 th-group group-base" rowspan="2">店铺</th>
  <th class="sticky-col-3 th-group group-base" rowspan="2">SPU</th>
  <th class="sticky-col-4 th-group group-base" rowspan="2">SPU名称</th>
  <th class="th-group group-purchase" colspan="1">采购</th>
  <th class="th-group group-domestic" colspan="4">国内</th>
  <th class="th-group group-third" colspan="3">三方</th>
  <th class="th-group group-fbt" colspan="3">FBT</th>
  <th class="th-group group-oversea" colspan="2">海外</th>
  <th class="th-group group-summary" colspan="3">汇总</th>
  <th class="th-group group-detail" colspan="9">仓明细</th>
</tr>
```

- [ ] **Step 2: 将 SPU 明细行补齐为完整业务字段**

每行保留与 `PID&SKU` 视图同样的库存字段，只去掉 `PID / SKU / SKU名称` 数据列。例如：

```html
<tr>
  <td class="sticky-col-1">2026-04-12</td>
  <td class="sticky-col-2">美国TK-艾斯特尼-美区跨境1店</td>
  <td class="sticky-col-3">AL-W0161</td>
  <td class="sticky-col-4">Women Lounge Set</td>
  <td class="num">1,245</td>
  <td class="num">168</td>
  <td class="num">420</td>
  <td class="num">102</td>
  <td class="num">66</td>
  <td class="num">36</td>
  <td class="num">260</td>
  <td class="num">430</td>
  <td class="num">452</td>
  <td class="num">-22</td>
  <td class="num">85</td>
  <td class="num">124</td>
  <td class="num">210</td>
  <td class="num">680</td>
  <td class="num">955</td>
  <td class="num">1,193</td>
  <td class="num">1,375</td>
  <td class="num">2,568</td>
  <td class="num">56</td>
  <td class="num">48</td>
  <td class="num">8</td>
  <td><span class="status-tag status-bad">少同步</span></td>
</tr>
```

- [ ] **Step 3: 运行结构检查确认 SPU 视图已移除旧字段**

Run: `rg -n "<th>风险等级</th>|<th>说明</th>|建议下钻查看 PID&SKU 明细|当前未发现异常|FBT / FBA 口径待补" bi/tkDashboard/库存检查/htmls/TK库存检查-PID\\&SKU看板.html`
Expected: 不再匹配旧版 SPU 专用字段和说明列

### Task 3: 验证改动结果

**Files:**
- Test: `bi/tkDashboard/库存检查/htmls/TK库存检查-PID&SKU看板.html`
- Test: `docs/superpowers/specs/2026-04-15-tk-inventory-spu-prototype-alignment-design.md`

- [ ] **Step 1: 读取变更后的 SPU 视图区块**

Run: `sed -n '620,860p' bi/tkDashboard/库存检查/htmls/TK库存检查-PID\\&SKU看板.html`
Expected: `SPU` 视图文案、汇总卡片、表头和数据列与设计一致

- [ ] **Step 2: 人工对照 spec 做覆盖检查**

逐项确认以下设计要求已覆盖：

```text
1. SPU视图与 PID&SKU 视图保持同构布局
2. 仅去掉 PID / SKU / SKU名称 三列
3. 保留其余库存业务字段
4. 汇总卡片文案切换为 SPU 维度
5. 移除“建议后续生成”等占位文案
```

- [ ] **Step 3: 提交本地改动**

```bash
git add docs/superpowers/specs/2026-04-15-tk-inventory-spu-prototype-alignment-design.md docs/superpowers/plans/2026-04-15-tk-inventory-spu-prototype-alignment.md bi/tkDashboard/库存检查/htmls/TK库存检查-PID\&SKU看板.html
git commit -m "feat: align tk inventory spu prototype"
```
