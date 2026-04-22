# 在 Cursor 里用 Draw.io 画图

## Cursor 不能「直连」draw.io，但可以这样用

- **不能做的**：Cursor 无法像遥控器一样连接或控制浏览器里的 draw.io 网页版，也不能直接打开 draw.io 桌面端。
- **能做的**：在 Cursor 里安装 **Draw.io 扩展** 后，可以直接在编辑器里**打开、编辑、保存** `.drawio` 文件，等于把 draw.io 嵌在 Cursor 里用。

## 使用步骤

1. **安装扩展**  
   - 在 Cursor 左侧打开「扩展」面板（或 `Cmd+Shift+X`）。  
   - 搜索 **Draw.io Integration**（发布者：Henning Dieterichs，ID：`hediet.vscode-drawio`）。  
   - 点击「安装」。

2. **打开/编辑本目录下的 .drawio 图**  
   - 双击 `数据流转图.drawio`，或在资源管理器中右键 →「Open with Draw.io」。  
   - 会在 Cursor 内打开 Draw.io 编辑器，可拖拽、连线、改文字、改样式。

3. **让我帮你改图**  
   - 你可以说「把数据源里加一个 xxx」「把这条线连到 GMV 计算表」等。  
   - 我会改的是 **`.drawio` 文件里的 XML 内容**；你保存后在图里就能看到效果，如需微调再在 Draw.io 里拖一拖即可。

## 本目录里的图

| 文件 | 说明 |
|------|------|
| `数据流转图.drawio` | tkDashboard 技术方案的数据流转图（数据源 → 计算层 → 产出），可在 Cursor 中用 Draw.io 打开编辑。 |

画图时以《技术方案.html》里的数据流转图结构为参考即可。
