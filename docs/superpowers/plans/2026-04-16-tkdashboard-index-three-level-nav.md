# tkDashboard index 三层导航 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 `bi/tkDashboard/index.html` 的业务栏目导航调整为“一级栏目 / 二级版本 / 三级原型”三层结构，同时保持技术文档和源数据集成列表现状不变。

**Architecture:** 保持现有单 HTML、侧栏点击切换 iframe 的模式不变，只在 `index.html` 内修改导航 DOM 和少量样式。点击逻辑继续绑定到具体原型链接，不为版本节点增加新交互。

**Tech Stack:** HTML, CSS, vanilla JavaScript

---

### Task 1: 调整三层导航样式

**Files:**
- Modify: `bi/tkDashboard/index.html`
- Test: `bi/tkDashboard/index.html`

- [ ] **Step 1: 增加版本层样式**

在 `<style>` 中新增版本层容器与标题样式，例如：

```html
.nav-version {
  margin: 0.2rem 0 0.55rem;
}
.nav-version-title {
  margin: 0.15rem 0.65rem 0.2rem 1.65rem;
  padding: 0.32rem 0.6rem;
  color: #cbd5e1;
  font-size: 0.82rem;
  font-weight: 600;
  border-left: 2px solid rgba(148, 163, 184, 0.35);
}
.nav-version .nav-item {
  margin-left: 2.1rem;
  padding-left: 0.9rem;
  font-size: 0.82rem;
}
```

- [ ] **Step 2: 保持原有 active 和 hover 逻辑兼容**

确认三级链接仍然使用原有 `.nav-item`、`.nav-item:hover`、`.nav-item.active` 规则，不增加新的 active class 类型。

- [ ] **Step 3: 运行样式片段检查**

Run: `rg -n "nav-version|nav-version-title" bi/tkDashboard/index.html`
Expected: 能匹配到新增的版本层样式和结构类名

### Task 2: 将业务栏目改为三层结构

**Files:**
- Modify: `bi/tkDashboard/index.html`
- Test: `bi/tkDashboard/index.html`

- [ ] **Step 1: 重构“销售数据&pid”导航结构**

将原来的二层链接改成“栏目 + 版本 + 原型”：

```html
<div class="nav-group">
  <div class="nav-group-title">销售数据&pid</div>
  <div class="nav-version">
    <div class="nav-version-title">销售数据&pid 1.0</div>
    <a class="nav-item active" href="#" data-src="销售数据映射/htmls/店铺统计.html" data-breadcrumb="店铺统计">店铺统计</a>
    <a class="nav-item" href="#" data-src="销售数据映射/htmls/商品统计.html" data-breadcrumb="商品统计">商品统计</a>
    <a class="nav-item" href="#" data-src="PID/htmls/需求二-数据看板.html" data-breadcrumb="PID 数据看板">PID数据看板</a>
  </div>
</div>
```

- [ ] **Step 2: 重构“库存模块”导航结构**

同样改成三层：

```html
<div class="nav-group">
  <div class="nav-group-title">库存模块</div>
  <div class="nav-version">
    <div class="nav-version-title">库存模块 1.0</div>
    <a class="nav-item" href="#" data-src="库存检查/htmls/TK库存检查-PID&SKU看板.html" data-breadcrumb="库存检查看板">库存检查看板</a>
    <a class="nav-item" href="#" data-src="缺补货/htmls/缺补货看板.html" data-breadcrumb="缺补货看板">缺补货看板</a>
  </div>
</div>
```

- [ ] **Step 3: 保持两个栏目现状不变**

确保以下区块仍然保留原有结构，不包入 `.nav-version`：

```html
<div class="nav-group-title">销售数据&pid(技术文档)</div>
<div class="nav-group-title">源数据集成列表</div>
```

### Task 3: 验证导航结构与交互

**Files:**
- Test: `bi/tkDashboard/index.html`
- Test: `docs/superpowers/specs/2026-04-16-tkdashboard-index-three-level-nav-design.md`

- [ ] **Step 1: 读取变更后的导航区块**

Run: `sed -n '1,220p' bi/tkDashboard/index.html`
Expected: 业务栏目为三层，技术文档和源数据集成列表仍为原结构

- [ ] **Step 2: 结构扫描**

Run: `rg -n "销售数据&pid 1.0|库存模块 1.0|销售数据&pid\\(技术文档\\)|源数据集成列表" bi/tkDashboard/index.html`
Expected: 版本层节点存在，保留栏目节点仍存在

- [ ] **Step 3: 提交本地改动**

```bash
git add docs/superpowers/specs/2026-04-16-tkdashboard-index-three-level-nav-design.md docs/superpowers/plans/2026-04-16-tkdashboard-index-three-level-nav.md bi/tkDashboard/index.html
git commit -m "feat: add three-level nav to tkdashboard index"
```
