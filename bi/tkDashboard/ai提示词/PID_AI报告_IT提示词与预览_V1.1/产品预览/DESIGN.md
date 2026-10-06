# Design
## Source of truth
- Status: Draft，2026-09-23。适用于本目录独立预览项目。
- 上级设计：E:/AI工作栈搭建/DESIGN.md；保留浅色后台、轻边框、圆角不超过8px的原则。
- 依据：用户PID截图、需求确认稿V0.1、数据源清单。用户新增系统内报告、下载和CSS要求。
## Brand
清晰、克制、可信。来源、时间、示例标识必须可见；避免大屏装饰。
## Product goals
从原SPU行打开报告，在首屏判断推广方向，再查证据，最后下载。仅本地交互原型，不连接生产接口。
## Personas and jobs
运营看销量和广告；剪辑、商务看素材供给与恢复；供应链看热卖色码及逐批衔接。
## Information architecture
PID列表 → 宽幅模态报告 → 决策摘要 → 销量证据 / 热卖库存 / 广告素材 / 行动与来源。
## Design principles
结论先行；每项判断有来源；未知保持未知；状态色不作为唯一信息载体。
## Visual language
白色与浅灰底；蓝色操作、紫色AI、红色风险、琥珀色待核。系统中文字体，正文14px，8px间距基准，圆角6–8px。无外部字体或图片依赖。
## Components
原表格与筛选视觉上下文；原生dialog宽幅报告；摘要卡、KPI、details证据、表格、状态徽标、下载菜单、提示条。
## Accessibility
原生dialog焦点约束与Esc关闭；按钮可键盘使用；focus-visible；语义表格、标题和details；不依赖hover。
## Responsive behavior
桌面最大1320px；窄屏全宽报告、卡片堆叠、表格在内部横滚；390px检查无整页溢出。
## Interaction states
加载、示例报告、采购数据缺失、生成失败及重试；关闭返回原按钮；下载保留当前快照与示例标识。状态选择器仅在预览外框。
## Content voice
业务语言，先动作后证据；数字均为虚构演示，禁止当成AL-W0199真实分析。
## Implementation constraints
单文件HTML内嵌CSS/JS，下载HTML为离线可读快照；打印样式展开展开区。DeepSeek、真实取数、历史存储与鉴权未接入。
## Open questions
- 宽幅弹层布局和下载格式待用户看预览后反馈。
- PDF首版为浏览器打印另存；后端直接生成PDF由IT估工。
## Acceptance
实际点击AI→加载→报告→展开证据→下载HTML→重新打开；采购缺失与失败重试；桌面/窄屏截图；JS语法检查。验证日志保留原始输出，不等同生产系统验收。


## V1.1 日期编辑
报告头部日期草稿与已生成快照分离，点击重新分析提交；提供近7/14/30完整日和还原日期。草稿未提交时暂禁下载；离线快照移除日期编辑器。非原示例区间显示待接入占位，禁止复用旧数字。

