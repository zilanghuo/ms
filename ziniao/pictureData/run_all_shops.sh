#!/bin/sh

# 三店照片详情导出启动器：交互输入日期范围，随后调用 Python 自动执行、上传并关闭浏览器。
set -eu

SCRIPT_DIR=$(CDPATH= cd "$(dirname "$0")" && pwd)
PYTHON_BIN=${ZINIAO_PYTHON:-/tmp/ziniao-webdriver-venv/bin/python}
CREDENTIALS_FILE=${ZINIAO_CREDENTIALS_FILE:-/tmp/ziniao-webdriver-credentials.json}
CHROME_DRIVER=${ZINIAO_CHROME_DRIVER:-/Users/a1/.ziniao/webdriver/chromedriver129}
TIMEOUT=${ZINIAO_TIMEOUT:-60}
EXPORT_SCRIPT="$SCRIPT_DIR/ziniao_photo_export.py"

if [ ! -x "$PYTHON_BIN" ]; then
    echo "未找到可执行的 Python：$PYTHON_BIN" >&2
    echo "可通过 ZINIAO_PYTHON 指定 Python 路径。" >&2
    exit 1
fi

if [ ! -f "$CREDENTIALS_FILE" ]; then
    echo "未找到紫鸟凭据文件：$CREDENTIALS_FILE" >&2
    echo "可通过 ZINIAO_CREDENTIALS_FILE 指定凭据文件路径。" >&2
    exit 1
fi

if [ ! -f "$EXPORT_SCRIPT" ]; then
    echo "未找到导出脚本：$EXPORT_SCRIPT" >&2
    exit 1
fi

printf '开始日期（YYYY-MM-DD）：'
IFS= read -r START_DATE
printf '结束日期（YYYY-MM-DD，含当天）：'
IFS= read -r END_DATE

if [ -z "$START_DATE" ] || [ -z "$END_DATE" ]; then
    echo "开始日期和结束日期均不能为空。" >&2
    exit 1
fi

echo "开始执行三店导出：$START_DATE 至 $END_DATE"
exec "$PYTHON_BIN" "$EXPORT_SCRIPT" \
    --credentials-file "$CREDENTIALS_FILE" \
    --all-shops \
    --start-date "$START_DATE" \
    --end-date "$END_DATE" \
    --chrome-driver "$CHROME_DRIVER" \
    --timeout "$TIMEOUT"
