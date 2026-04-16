# 商品统计 1.1 SPU视图切换 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 `商品统计-1.1.html` 中增加 `PID统计 / SPU统计` 按钮切换，并在 `SPU统计` 视图中隐藏 `PID` 相关展示。

**Architecture:** 保持现有单页面和 JS 动态渲染结构不变，在当前脚本中增加 `viewMode` 状态，通过按钮切换表头、数据行、导出说明和搜索条件。原始 `商品统计.html` 不改，`1.1` 页面单独演进。

**Tech Stack:** HTML, CSS, vanilla JavaScript

---

### Task 1: 增加视图切换按钮和样式

**Files:**
- Modify: `bi/tkDashboard/销售数据映射/htmls/商品统计-1.1.html`
- Test: `bi/tkDashboard/销售数据映射/htmls/商品统计-1.1.html`

- [ ] **Step 1: 增加视图切换按钮组样式**

在现有样式中增加单独的视图切换按钮组，例如：

```html
.view-switch {
  display: inline-flex;
  border: 1px solid var(--accent);
  border-radius: 4px;
  overflow: hidden;
}
.view-switch .switch-btn {
  padding: 0.4rem 0.9rem;
  border: none;
  background: #fff;
  color: var(--accent);
  cursor: pointer;
}
.view-switch .switch-btn.active {
  background: var(--accent);
  color: #fff;
}
```

- [ ] **Step 2: 在查询区加入按钮组**

在查询区增加：

```html
<div class="view-switch" id="viewSwitch">
  <button type="button" class="switch-btn active" data-view="pid">PID统计</button>
  <button type="button" class="switch-btn" data-view="spu">SPU统计</button>
</div>
```

- [ ] **Step 3: 检查按钮节点已写入**

Run: `rg -n "viewSwitch|switch-btn|PID统计|SPU统计" bi/tkDashboard/销售数据映射/htmls/商品统计-1.1.html`
Expected: 可以匹配到按钮组和对应样式

### Task 2: 增加 SPU 视图切换逻辑

**Files:**
- Modify: `bi/tkDashboard/销售数据映射/htmls/商品统计-1.1.html`
- Test: `bi/tkDashboard/销售数据映射/htmls/商品统计-1.1.html`

- [ ] **Step 1: 增加 viewMode 状态**

在脚本顶部增加：

```javascript
var viewMode = 'pid';
```

- [ ] **Step 2: 让 render() 根据 viewMode 切换表头和行内容**

实现规则：

```javascript
if (viewMode === 'spu') {
  // 表头不显示 PID，不显示分析列
  // 每个 SPU 只输出一行汇总
} else {
  // 保留当前 PID 统计结构
}
```

- [ ] **Step 3: 切换搜索条件与说明文案**

切换到 `SPU统计` 时：

```javascript
document.getElementById('qSearchField').value = 'spu';
document.querySelector('#qSearchField option[value="pid"]').style.display = 'none';
```

并同步更新导出提示和统计说明文案为 `SPU` 口径。

- [ ] **Step 4: 绑定按钮切换事件**

```javascript
document.querySelectorAll('#viewSwitch .switch-btn').forEach(function(btn) {
  btn.addEventListener('click', function() {
    viewMode = btn.getAttribute('data-view');
    render();
  });
});
```

- [ ] **Step 5: 运行关键字检查**

Run: `rg -n "viewMode|SPU统计|PID统计|qSearchField option\\[value=\\\"pid\\\"\\]" bi/tkDashboard/销售数据映射/htmls/商品统计-1.1.html`
Expected: 新的视图切换逻辑和文案已存在

### Task 3: 验证 SPU 视图不展示 PID

**Files:**
- Test: `bi/tkDashboard/销售数据映射/htmls/商品统计-1.1.html`
- Test: `docs/superpowers/specs/2026-04-16-product-statistics-1.1-spu-view-design.md`

- [ ] **Step 1: 读取变更后的查询区和 render 逻辑**

Run: `sed -n '1,260p' bi/tkDashboard/销售数据映射/htmls/商品统计-1.1.html && sed -n '260,760p' bi/tkDashboard/销售数据映射/htmls/商品统计-1.1.html`
Expected: 可看到按钮组和 `viewMode` 分支逻辑

- [ ] **Step 2: 结构扫描**

Run: `rg -n "PID统计|SPU统计|PID 明细|分析</th>|<th class=\"sticky-col-3\">PID</th>" bi/tkDashboard/销售数据映射/htmls/商品统计-1.1.html`
Expected: 页面保留 PID 视图能力，但 SPU 视图逻辑中不再强依赖 PID 列展示

- [ ] **Step 3: 提交本地改动**

```bash
git add docs/superpowers/specs/2026-04-16-product-statistics-1.1-spu-view-design.md docs/superpowers/plans/2026-04-16-product-statistics-1.1-spu-view.md bi/tkDashboard/销售数据映射/htmls/商品统计-1.1.html
git commit -m "feat: add spu view to product statistics 1.1"
```
