# bi 设计 Token 速查

用于新页面时直接复制的 CSS 变量与常用色值。以 `bi/tkDashboard` 为基准。

## 文档页 / 内容页（需求文档、接口文档、技术方案、原型内容区）

```css
:root {
  --bg: #f5f6f8;
  --card: #fff;
  --text: #333;
  --muted: #666;
  --accent: #0d9488;
  --border: #e0e0e0;
}
```

带表单与按钮的页面（原型页）可追加：

```css
  --accent-hover: #0f766e;
  --input-border: #d1d5db;
```

## 入口首页（侧栏 + 主内容区）

```css
:root {
  --side-bg: #1e293b;
  --side-text: #e2e8f0;
  --side-hover: #334155;
  --side-active: #0d9488;
  --side-active-bg: rgba(13, 148, 136, 0.2);
  --main-bg: #f1f5f9;
  --header-bg: #fff;
  --header-border: #e2e8f0;
  --breadcrumb: #64748b;
}
```

## 固定色值（不通过变量时）

| 用途       | 色值        | 示例场景           |
|------------|-------------|--------------------|
| 主色       | #0d9488     | 按钮、链接、选中   |
| 主色 hover | #0f766e     | 主按钮 hover       |
| 表头灰     | #f1f5f9 / #f9fafb | 表头背景      |
| 行 hover   | #f9fafb     | 表格行、列表项     |
| 合计行     | #f0fdf4     | 合计行背景         |
| 合计行 hover | #dcfce7   | 合计行 hover       |
| 模块蓝     | #cce5ff 字 #004085 | 表头「日期」等 |
| 模块黄     | #fff3cd 字 #856404 | 表头「商品信息」等 |
| 涨/警示    | #dc2626     | .trend-up、错误提示 |
| 跌/成功    | #16a34a     | .trend-down        |
| 导出提示   | 背景 #fef2f2 字 #991b1b 边框 #dc2626 | .export-tip |
| 标签蓝     | #e0f2fe 字 #0369a1 | 级联已选 tag   |
| 交互蓝     | #2563eb、#eff6ff | 级联 hover、高亮 |

## 字体

```css
font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans SC", sans-serif;
font-size: 14px;   /* body */
line-height: 1.5;  /* 原型页 1.5，文档页 1.6 */
```

## 圆角

- 卡片、大面板：`8px`
- 按钮、输入、tab 组：`4px`
- 小标签、图标按钮：`3px` 或 `6px`

## 阴影

- 下拉/弹层：`0 6px 20px rgba(0,0,0,0.12)`
- 冻结列：`2px 0 6px rgba(0,0,0,0.08)` 或 `2px 0 4px -2px rgba(0,0,0,0.08)`
