#!/bin/bash
set -euo pipefail

MODE="${1:-create}"
SOURCE_APP="${SOURCE_APP:-/Applications/ChatGPT.app}"

SECOND_NAME="Codex Max"
SECOND_HOME="$HOME/.codex-max"
SECOND_USER_DATA="$HOME/Library/Application Support/$SECOND_NAME"

RUNTIME_DIR="/Applications/$SECOND_NAME Runtime"
RUNTIME_APP="$RUNTIME_DIR/$SECOND_NAME.app"

LAUNCHER_APP="/Applications/$SECOND_NAME.app"
LAUNCHER_EXEC="codex-second-launcher"
LAUNCHER_BUNDLE_ID="local.codex.max.launcher"

test -d "$SOURCE_APP" || { echo "Source app not found: $SOURCE_APP"; exit 1; }

if [ "$MODE" != "create" ] && [ "$MODE" != "repair" ]; then
  echo "Usage: $0 [create|repair]"
  exit 1
fi

if [ "$MODE" = "create" ]; then
  test ! -e "$RUNTIME_APP" || { echo "$RUNTIME_APP already exists"; exit 1; }
  test ! -e "$LAUNCHER_APP" || { echo "$LAUNCHER_APP already exists"; exit 1; }
fi

if [ "$MODE" = "repair" ] && [ ! -e "$RUNTIME_APP" ] && [ -e "$RUNTIME_DIR/ChatGPT.app" ]; then
  mv "$RUNTIME_DIR/ChatGPT.app" "$RUNTIME_APP"
fi

mkdir -p "$SECOND_HOME" "$SECOND_USER_DATA"

if [ ! -e "$RUNTIME_APP" ]; then
  mkdir -p "$RUNTIME_DIR"
  cp -cR "$SOURCE_APP" "$RUNTIME_APP"
fi

mkdir -p "$LAUNCHER_APP/Contents/MacOS" "$LAUNCHER_APP/Contents/Resources"

cat > "$LAUNCHER_APP/Contents/Info.plist" <<PLIST
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
  <string>14.0</string>
  <key>NSHighResolutionCapable</key>
  <true/>
</dict>
</plist>
PLIST

cat > "$LAUNCHER_APP/Contents/MacOS/$LAUNCHER_EXEC" <<LAUNCHER
#!/bin/sh
export CODEX_HOME="$SECOND_HOME"
export CODEX_ELECTRON_USER_DATA_PATH="$SECOND_USER_DATA"
exec "$RUNTIME_APP/Contents/MacOS/ChatGPT" \\
  --user-data-dir="$SECOND_USER_DATA"
LAUNCHER

chmod +x "$LAUNCHER_APP/Contents/MacOS/$LAUNCHER_EXEC"
cp "$RUNTIME_APP/Contents/Resources/electron.icns" "$LAUNCHER_APP/Contents/Resources/electron.icns"

codesign --force --sign - "$LAUNCHER_APP"

/System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister -f "$LAUNCHER_APP"

echo "Ready:"
echo "  $RUNTIME_APP"
echo "  $LAUNCHER_APP"
echo "  $SECOND_HOME"
echo "  $SECOND_USER_DATA"
