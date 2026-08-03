# Codex 双实例从 0 搭建通用说明

最后更新：2026-07-24

## 目标

在同一台 macOS 上同时使用两份 Codex：

- 官方 Codex 兼容入口：`/Applications/Codex.app`
- 新版 ChatGPT desktop 中的 Codex runtime：`/Applications/ChatGPT.app`
- 第二份 Codex：例如 `/Applications/Codex Max.app`

第二份 Codex 应该有独立的：

- `CODEX_HOME`
- Electron `userData`
- 应用入口

但第二份 Codex 的真正运行体仍然来自官方 `Codex.app` 或 `ChatGPT.app` 的克隆，并且必须保留 OpenAI 的 Developer ID 签名。

> 重要：2026-07 之后部分机器只有 `/Applications/ChatGPT.app`，没有 `/Applications/Codex.app`。这种形态已经验证可用，但 runtime 路径、可执行文件名和 launcher 脚本必须使用 ChatGPT 形态：`/Applications/Codex Max Runtime/ChatGPT.app/Contents/MacOS/ChatGPT`。不要再写成旧的 `Codex Max.app/Contents/MacOS/Codex`。

## 核心结论

不要修改第二份运行体内部文件，不要 patch `app.asar`，不要重新签名运行体。

推荐结构是：

```text
/Applications/Codex.app
/Applications/ChatGPT.app
/Applications/Codex Max.app
/Applications/Codex Max Runtime/Codex.app
/Applications/Codex Max Runtime/ChatGPT.app
~/.codex
~/.codex-max
~/Library/Application Support/Codex Max
```

含义：

- `/Applications/Codex.app`：旧形态官方 Codex 或保留的 Codex 兼容入口。
- `/Applications/ChatGPT.app`：新形态官方桌面 app，当前 Codex runtime 也可能在其中。
- `/Applications/Codex Max.app`：轻量 launcher，只负责设置环境变量并启动 runtime。
- `/Applications/Codex Max Runtime/Codex.app`：旧 Codex.app 形态下，从官方 Codex 克隆出来的真正运行体。
- `/Applications/Codex Max Runtime/ChatGPT.app`：新 ChatGPT.app 形态下，从官方 ChatGPT 克隆出来的真正运行体。
- `~/.codex-max`：第二份 Codex 的独立 home。
- `~/Library/Application Support/Codex Max`：第二份 Codex 的独立 Electron userData。

## 前置条件

1. 已安装官方 `/Applications/Codex.app` 或 `/Applications/ChatGPT.app`，或有一份可验证签名的官方安装包。
2. 官方 Codex 或 ChatGPT desktop app 能正常启动。
3. 如果需要命令行能力，`codex` CLI 已经可用且能成功运行。
4. 当前用户有权限写入 `/Applications`；没有权限时需要用管理员权限执行相关命令。
5. 不要把别人机器上的 `~/.codex`、`~/.codex-max`、token、MCP 配置和插件缓存直接复制到自己机器。

## 0. 执行前分流判断

先判断当前机器属于哪种安装形态。不要跳过本节。

```bash
if [ -d "/Applications/Codex.app" ]; then
  echo "OK: 找到 /Applications/Codex.app，使用旧 Codex.app 形态。"
elif [ -d "/Applications/ChatGPT.app" ]; then
  echo "OK: 找到 /Applications/ChatGPT.app，使用新 ChatGPT.app 形态。"
else
  echo "STOP: 未找到 /Applications/Codex.app 或 /Applications/ChatGPT.app。"
  echo "请先安装并正常启动官方桌面 app。"
  exit 1
fi
```

如果走 `ChatGPT.app` 分支，先做只读探测，确认实际 bundle 结构：

```bash
APP="/Applications/ChatGPT.app"

/usr/libexec/PlistBuddy -c 'Print :CFBundleIdentifier' "$APP/Contents/Info.plist"
/usr/libexec/PlistBuddy -c 'Print :CFBundleShortVersionString' "$APP/Contents/Info.plist"

find "$APP/Contents/MacOS" -maxdepth 1 -type f -perm -111 -print
find "$APP/Contents/Resources" -maxdepth 2 \( -name 'codex' -o -name '*.icns' -o -name 'app.asar' \) -print

codesign -dv --verbose=4 "$APP" 2>&1 | rg 'Authority|TeamIdentifier|Signature|Identifier'
spctl -a -vv "$APP"
codesign --verify --deep --strict "$APP"
```

期望能看到：

```text
Identifier=com.openai.codex
TeamIdentifier=2DC432GLL2
Authority=Developer ID Application: OpenAI OpCo, LLC (2DC432GLL2)
```

注意：某些受限沙盒里执行 `codesign --verify` / `spctl` 可能误报 `invalid signature` 或 `internal error in Code Signing subsystem`。如果同一份 app 在非沙盒终端里能通过 `codesign --verify --deep --strict` 和 `spctl -a -vv`，以非沙盒复核结果为准。真正不能通过签名校验时，不要继续克隆 runtime。

再检查 CLI。注意：`which codex` 只能说明入口存在，不能说明 CLI 可用。

```bash
if command -v codex >/dev/null 2>&1; then
  codex --version
else
  echo "未找到 codex CLI；如果只做桌面双实例，可以暂时跳过 CLI 配置。"
fi
```

如果 `codex --version` 报 vendor 二进制缺失、权限错误或其他启动错误，说明 CLI 当前不可用于后续 `codex mcp list`、`codex plugin list`、`codexmax` 等验收。它不直接否定 launcher 方案，但 CLI 部分必须先修复或单独跳过。

## 变量

下面用 `Codex Max` 作为第二份 Codex 的名字。要创建别的名字，只改这一段变量，并保证 `SECOND_HOME`、`SECOND_USER_DATA`、`RUNTIME_APP`、`LAUNCHER_APP`、`LAUNCHER_BUNDLE_ID` 互不冲突。

```bash
SECOND_NAME="Codex Max"
SECOND_HOME="$HOME/.codex-max"
SECOND_USER_DATA="$HOME/Library/Application Support/$SECOND_NAME"

RUNTIME_DIR="/Applications/$SECOND_NAME Runtime"
LAUNCHER_APP="/Applications/$SECOND_NAME.app"
LAUNCHER_EXEC="codex-second-launcher"
LAUNCHER_BUNDLE_ID="local.codex.max.launcher"

if [ -d "/Applications/Codex.app" ]; then
  MAIN_APP="/Applications/Codex.app"
  RUNTIME_APP="$RUNTIME_DIR/Codex.app"
  RUNTIME_EXEC_REL="Contents/MacOS/Codex"
elif [ -d "/Applications/ChatGPT.app" ]; then
  MAIN_APP="/Applications/ChatGPT.app"
  RUNTIME_APP="$RUNTIME_DIR/ChatGPT.app"
  RUNTIME_EXEC_REL="Contents/MacOS/ChatGPT"
else
  echo "未找到官方 Codex.app 或 ChatGPT.app，停止。"
  exit 1
fi
```

## 1. 验证官方 runtime 来源

```bash
test -d "$MAIN_APP" || { echo "找不到 $MAIN_APP"; exit 1; }

/usr/libexec/PlistBuddy -c 'Print :CFBundleShortVersionString' "$MAIN_APP/Contents/Info.plist"
/usr/libexec/PlistBuddy -c 'Print :CFBundleVersion' "$MAIN_APP/Contents/Info.plist"

codesign -dv --verbose=4 "$MAIN_APP" 2>&1 | rg 'Authority|TeamIdentifier|Signature|Identifier'
spctl -a -vv "$MAIN_APP"
codesign --verify --deep --strict "$MAIN_APP"
```

期望能看到 OpenAI Developer ID，例如：

```text
Authority=Developer ID Application: OpenAI OpCo, LLC (2DC432GLL2)
TeamIdentifier=2DC432GLL2
```

如果官方 app 自己签名不通过，先修复官方安装，不要继续创建第二份。

如果 `/Applications/ChatGPT.app` 正在运行且不方便替换，但本地通过 Homebrew 下载到一份签名正常的官方包，可以先解压到 `/tmp`，只把该临时 app 作为 `MAIN_APP` 克隆来源：

```bash
brew fetch --cask chatgpt
rm -rf /tmp/chatgpt-codex-source
mkdir -p /tmp/chatgpt-codex-source
ditto -x -k "$(brew --cache --cask chatgpt)" /tmp/chatgpt-codex-source

MAIN_APP="/tmp/chatgpt-codex-source/ChatGPT.app"
RUNTIME_APP="$RUNTIME_DIR/ChatGPT.app"
RUNTIME_EXEC_REL="Contents/MacOS/ChatGPT"

codesign --verify --deep --strict "$MAIN_APP"
spctl -a -vv "$MAIN_APP"
```

这样可以不替换当前正在运行的 `/Applications/ChatGPT.app`，只重建第二份 runtime。

## 2. 创建独立 home 和 userData

```bash
mkdir -p "$SECOND_HOME" "$SECOND_USER_DATA"
```

从 0 搭建时，建议先保持 `SECOND_HOME` 为空，让第二份 Codex 首次启动后自己生成配置。需要 MCP、插件或模型配置时，再在第二份环境下单独配置。

可选 CLI 检查：

```bash
CODEX_HOME="$SECOND_HOME" codex mcp list
CODEX_HOME="$SECOND_HOME" codex plugin list
```

如果 `codex` 命令不存在或 `codex --version` 执行失败，说明 CLI 尚未安装、没有进入 `PATH`，或当前安装不完整。这不影响 launcher 方案本身，但会影响命令行使用和 CLI 相关验收。

## 3. 克隆 runtime

从官方 app 克隆一份 runtime。不要改 runtime 内部文件。

```bash
test ! -e "$RUNTIME_APP" || { echo "$RUNTIME_APP 已存在，停止；升级请看后文"; exit 1; }

mkdir -p "$RUNTIME_DIR"
cp -cR "$MAIN_APP" "$RUNTIME_APP"
```

验证 runtime 签名：

```bash
codesign -dv --verbose=4 "$RUNTIME_APP" 2>&1 | rg 'Authority|TeamIdentifier|Signature|Identifier'
spctl -a -vv "$RUNTIME_APP"
codesign --verify --deep --strict "$RUNTIME_APP"
```

这里必须仍然是 OpenAI Developer ID。不要对 runtime 执行：

```bash
codesign --force --deep --sign - "$RUNTIME_APP"
```

## 4. 创建 launcher app

launcher 只负责设置第二份 Codex 的 home 和 userData，然后启动 runtime。

```bash
test ! -e "$LAUNCHER_APP" || { echo "$LAUNCHER_APP 已存在，停止"; exit 1; }

mkdir -p "$LAUNCHER_APP/Contents/MacOS" "$LAUNCHER_APP/Contents/Resources"
```

写入 `Info.plist`：

```bash
cat > "$LAUNCHER_APP/Contents/Info.plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>CFBundleDevelopmentRegion</key>
  <string>en</string>
  <key>CFBundleDisplayName</key>
  <string>$SECOND_NAME</string>
  <key>CFBundleExecutable</key>
  <string>$LAUNCHER_EXEC</string>
  <key>CFBundleIconFile</key>
  <string>electron</string>
  <key>CFBundleIdentifier</key>
  <string>$LAUNCHER_BUNDLE_ID</string>
  <key>CFBundleInfoDictionaryVersion</key>
  <string>6.0</string>
  <key>CFBundleName</key>
  <string>$SECOND_NAME</string>
  <key>CFBundlePackageType</key>
  <string>APPL</string>
  <key>CFBundleShortVersionString</key>
  <string>1.0</string>
  <key>CFBundleVersion</key>
  <string>1</string>
  <key>LSMinimumSystemVersion</key>
  <string>12.0</string>
  <key>NSHighResolutionCapable</key>
  <true/>
</dict>
</plist>
EOF
```

写入 launcher 可执行脚本：

```bash
cat > "$LAUNCHER_APP/Contents/MacOS/$LAUNCHER_EXEC" <<EOF
#!/bin/sh
export CODEX_HOME="$SECOND_HOME"
export CODEX_ELECTRON_USER_DATA_PATH="$SECOND_USER_DATA"
exec "$RUNTIME_APP/$RUNTIME_EXEC_REL" \
  --user-data-dir="$SECOND_USER_DATA"
EOF

chmod +x "$LAUNCHER_APP/Contents/MacOS/$LAUNCHER_EXEC"
```

复制图标并签名 launcher：

```bash
cp "$RUNTIME_APP/Contents/Resources/electron.icns" \
  "$LAUNCHER_APP/Contents/Resources/electron.icns"

codesign --force --sign - "$LAUNCHER_APP"

/System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister -f \
  "$LAUNCHER_APP"
```

launcher 可以 ad-hoc 签名，因为 Browser / Chrome backend 校验的是实际 runtime peer。runtime 不能 ad-hoc 重签。

## 5. 启动第二份 Codex

```bash
open "$LAUNCHER_APP"
```

首次启动后，如果系统弹出辅助功能、屏幕录制、自动化控制等权限提示，按实际提示给第二份 app 或 runtime 授权。

如果需要直接从命令行启动 runtime，也可以：

```bash
CODEX_HOME="$SECOND_HOME" \
CODEX_ELECTRON_USER_DATA_PATH="$SECOND_USER_DATA" \
  "$RUNTIME_APP/$RUNTIME_EXEC_REL" \
  --user-data-dir="$SECOND_USER_DATA"
```

## 6. 验证隔离是否生效

检查进程：

```bash
ps -axo pid,ppid,tty,command | rg "$SECOND_NAME Runtime|codex app-server"
```

如果能找到第二份 Codex 的 `app-server` PID，可以检查它是否打开了第二份 home：

```bash
lsof -p <APP_SERVER_PID> | rg "$SECOND_HOME|state_|logs_|goals_|memories_"
```

检查日志中 Browser / Chrome backend 是否正常：

```bash
find "$HOME/Library/Logs/com.openai.codex" -path '*codex-desktop-*.log' -mmin -20 -print0 |
  xargs -0 rg -n 'browser_use_availability_resolved|BrowserUseThreadConfig|native pipe rejected|missing-code-signing-identity|untrusted-code-signing-identity'
```

期望看到可用状态，不应出现：

```text
missing-code-signing-identity
untrusted-code-signing-identity
```

## 7. 配置第二份 CLI

如果希望命令行也使用第二份 Codex home，可以在 shell 配置里加函数：

```bash
codexmax() {
  CODEX_HOME="$HOME/.codex-max" codex "$@"
}
```

如果第二份需要固定 provider 或 model，可以写成：

```bash
codexmax() {
  CODEX_HOME="$HOME/.codex-max" codex -c model_provider="你的 provider" -m "你的 model" "$@"
}
```

验证：

```bash
codexmax mcp list
codexmax plugin list
```

CLI 的关键是 `CODEX_HOME`。它不依赖 launcher，也不参与 Electron 单实例锁。

## 8. 以后升级第二份 Codex

官方 `/Applications/Codex.app` 或 `/Applications/ChatGPT.app` 升级后，第二份 runtime 不会自动升级。按下面流程重建 runtime。

先退出第二份 Codex，然后检查进程：

```bash
ps -axo pid,ppid,tty,command | rg "$SECOND_NAME Runtime|$LAUNCHER_APP|codex app-server"
```

只处理明确属于第二份 Codex 的进程。不要 kill 用户手动开的 Terminal、iTerm、shell、TTY 或官方 Codex。

备份旧 runtime：

```bash
TS="$(date +%Y%m%d-%H%M%S)"
ditto "$RUNTIME_APP" "$HOME/Desktop/$SECOND_NAME Runtime.app.bak.$TS"
```

替换 runtime：

```bash
rm -rf -- "$RUNTIME_APP"
mkdir -p "$RUNTIME_DIR"
cp -cR "$MAIN_APP" "$RUNTIME_APP"
```

重新验证签名：

```bash
codesign -dv --verbose=4 "$RUNTIME_APP" 2>&1 | rg 'Authority|TeamIdentifier|Signature|Identifier'
spctl -a -vv "$RUNTIME_APP"
codesign --verify --deep --strict "$RUNTIME_APP"
```

如果签名不是 OpenAI Developer ID，停止，不要启动。

## 9. 常见问题

### 两个 Codex 只能打开一个窗口

通常是 Electron `userData` 没有隔离。检查 launcher 是否同时设置了：

```text
CODEX_ELECTRON_USER_DATA_PATH
--user-data-dir
```

并且它们指向第二份专用目录。

### Browser / Chrome backend 报签名错误

如果日志出现：

```text
browser-use native pipe rejected socket peer reason=missing-code-signing-identity
```

或：

```text
untrusted-code-signing-identity
```

通常表示 runtime 被修改或重新签名了。删除第二份 runtime，重新从官方 `Codex.app` 或 `ChatGPT.app` 克隆，不要修改 `Info.plist`、`app.asar` 或 `ElectronAsarIntegrity`。

### 打开 Codex Max 失败，提示路径不存在

检查 launcher：

```bash
sed -n '1,80p' "/Applications/Codex Max.app/Contents/MacOS/codex-second-launcher"
```

如果当前 runtime 实际是：

```text
/Applications/Codex Max Runtime/ChatGPT.app
```

launcher 里就必须执行：

```text
/Applications/Codex Max Runtime/ChatGPT.app/Contents/MacOS/ChatGPT
```

不要写成：

```text
/Applications/Codex Max Runtime/Codex Max.app/Contents/MacOS/Codex
```

### 打开第二份却使用了官方 Codex 的配置

检查 launcher 脚本：

```bash
sed -n '1,80p' "$LAUNCHER_APP/Contents/MacOS/$LAUNCHER_EXEC"
```

必须看到第二份专用的：

```text
CODEX_HOME
CODEX_ELECTRON_USER_DATA_PATH
--user-data-dir
```

### CLI 仍然用官方配置

CLI 不会自动读取 launcher。每次调用 CLI 都要显式设置：

```bash
CODEX_HOME="$SECOND_HOME" codex ...
```

或者使用 `codexmax` 这类 shell 函数。

### 想创建第三份、第四份 Codex

可以复用同一套方法，但每一份都必须有独立的：

- `SECOND_NAME`
- `SECOND_HOME`
- `SECOND_USER_DATA`
- `RUNTIME_DIR`
- `RUNTIME_APP`
- `LAUNCHER_APP`
- `LAUNCHER_BUNDLE_ID`

不要让多个 launcher 共用同一个 Electron userData。

## 禁止事项

不要对 runtime 做这些事：

```text
修改 Contents/Info.plist
修改 Contents/Resources/app.asar
修改 ElectronAsarIntegrity
codesign --force --deep --sign -
```

不要为了清理第二份 Codex 而 kill：

```text
login
-zsh
bash
fish
Terminal
iTerm
用户手动开的 shell 或 TTY
```

## 最小验收标准

搭建完成后，至少确认：

1. 官方 `/Applications/Codex.app` 或 `/Applications/ChatGPT.app` 仍能打开。
2. 第二份 launcher 能打开第二份 Codex。
3. 两份 Codex 可以同时存在。
4. 第二份 Codex 的 `app-server` 使用的是第二份 `CODEX_HOME`。
5. 第二份 runtime 仍是 OpenAI Developer ID 签名。
6. 日志中没有 `missing-code-signing-identity` 或 `untrusted-code-signing-identity`。
7. CLI 如果需要第二份环境，调用时确实带了第二份 `CODEX_HOME`。

## 10. 当前已验证案例：只有 ChatGPT.app 的机器

2026-07-24 在只有 `/Applications/ChatGPT.app`、没有 `/Applications/Codex.app` 的机器上，已验证可用结构：

```text
/Applications/ChatGPT.app
/Applications/Codex Max.app
/Applications/Codex Max Runtime/ChatGPT.app
/Users/a1/.codex-max
/Users/a1/Library/Application Support/Codex Max
```

关键点：

- launcher 必须执行 `/Applications/Codex Max Runtime/ChatGPT.app/Contents/MacOS/ChatGPT`。
- 第二份 app-server 会打开 `/Users/a1/.codex-max/state_*.sqlite`、`logs_*.sqlite`、`goals_*.sqlite`、`memories_*.sqlite`。
- 桌面日志中应看到 Browser Use runtime 选择 `/Applications/Codex Max Runtime/ChatGPT.app/Contents/Resources/codex`。
- 如需在不替换当前主 app 的情况下重建 runtime，可用 `brew fetch --cask chatgpt` 下载官方包，解压到 `/tmp/chatgpt-codex-source/ChatGPT.app` 后作为 `MAIN_APP` 克隆来源。
