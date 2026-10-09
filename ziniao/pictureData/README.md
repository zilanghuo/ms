# 紫鸟照片详情自动导出

该脚本不依赖 Codex 的可视化点击：它调用本机紫鸟 WebDriver 服务启动已有会话的店铺浏览器，再通过 Selenium 附着调试端口，自动导出“已绑定账号”和“联盟账号”的照片详情数据。

## 前提

- 紫鸟 WebDriver 已在 `127.0.0.1:18888` 启动。
- 目标店铺已人工完成登录；验证码、人机校验和风控验证不能由此脚本绕过。
- Python 环境已安装 `selenium`。
- ChromeDriver 与紫鸟浏览器内核版本匹配。
- 脚本当前以无界面模式启动店铺浏览器，不显示窗口；执行结束后仍会关闭本次店铺浏览器。

## 凭据文件

凭据文件不在本目录创建，也不能提交到 Git。将它放在受限路径，并设置仅本人可读：

```json
{
  "company": "<企业名称>",
  "username": "<用户名>",
  "password": "<密码>"
}
```

## 运行

默认导出前两天；使用店铺 ID 时：

```bash
python3 ziniao_photo_export.py \
  --credentials-file /安全路径/ziniao-credentials.json \
  --browser-id <紫鸟浏览器ID> \
  --chrome-driver /Users/a1/.ziniao/webdriver/chromedriver129
```

补数示例：

```bash
python3 ziniao_photo_export.py \
  --credentials-file /安全路径/ziniao-credentials.json \
  --browser-id <紫鸟浏览器ID> \
  --date 2026-10-04 \
  --chrome-driver /Users/a1/.ziniao/webdriver/chromedriver129
```

按天补数并上传的日期范围示例（包含首尾日期，按日期从早到晚执行）：

```bash
python3 ziniao_photo_export.py \
  --credentials-file /安全路径/ziniao-credentials.json \
  --browser-id <紫鸟浏览器ID> \
  --start-date 2026-10-01 \
  --end-date 2026-10-04 \
  --chrome-driver /Users/a1/.ziniao/webdriver/chromedriver129
```

## 三店批量导出

使用 `--all-shops` 时，脚本会按以下顺序独立启动、导出、上传并关闭店铺窗口：

1. `1店`：美国TK-艾斯特尼-美区跨境1店
2. `3店`：美国TK-艾斯特尼-美区跨境3店（原大魔王）
3. `英国直邮店`：美国TK-艾斯特尼-英国直邮店（直接打开 GB 站点的照片详情页）

三店按同一日期范围导出的示例：

```bash
python3 ziniao_photo_export.py \
  --credentials-file /安全路径/ziniao-credentials.json \
  --all-shops \
  --start-date 2026-10-01 \
  --end-date 2026-10-04 \
  --chrome-driver /Users/a1/.ziniao/webdriver/chromedriver129
```

三店模式的文件名示例：

- `1店-已绑定账号-YYYYMMDD.xlsx`
- `3店-联盟账号-YYYYMMDD.xlsx`
- `英国直邮店-已绑定账号-YYYYMMDD.xlsx`

`--all-shops` 不能和单店定位参数 `--browser-id`、`--browser-name` 或 `--shop-label` 同时使用；未传 `--all-shops` 时，单店模式维持原有行为。

### 交互式启动器

日常执行可直接启动三店脚本；它会依次询问开始日期和结束日期（均为 `YYYY-MM-DD`，并包含结束日期），再调用 Python 进行导出、上传和关闭浏览器：

```bash
cd /Users/a1/Documents/Office/code/ms-proj/ziniao/pictureData
sh run_all_shops.sh
```

启动器默认使用本机现有的虚拟环境、凭据文件与 ChromeDriver。若本机路径发生变更，可在启动时覆盖，而无需把凭据写入脚本：

```bash
ZINIAO_CREDENTIALS_FILE=/安全路径/ziniao-credentials.json \
ZINIAO_PYTHON=/安全路径/venv/bin/python \
sh run_all_shops.sh
```

也可用精确店铺名称匹配代替 `--browser-id`：

```bash
--browser-name "<店铺名称的唯一片段>"
```

每个日期均会依次处理“已绑定账号”和“联盟账号”：先发起导出、等待导出记录出现后点击下载、重命名，再上传至接口。实际文件也可在浏览器下载记录或默认下载目录中确认。

脚本会等待下载完成并重命名文件，默认保存到 `~/Downloads`：

- `1店-已绑定账号-YYYYMMDD.xlsx`
- `1店-联盟账号-YYYYMMDD.xlsx`

可通过 `--download-dir` 指定目录、通过 `--shop-label` 修改文件名前缀。同名文件存在时，脚本会先等待新的下载文件完整落盘，再以原子替换方式覆盖旧文件；若本轮下载失败，旧文件保持不变。

默认会在 `finally` 中调用紫鸟的 `stopBrowser` 关闭本次店铺浏览器窗口；仅在需要人工检查页面时加入 `--keep-browser-open`。

## 定时执行

在确认一次手工运行稳定后，再用 `launchd`（macOS）或 `cron`（Linux）调用上述命令。定时任务应使用绝对路径，并将标准输出与错误输出写到非敏感日志文件。

## 验证

```bash
/tmp/ziniao-webdriver-venv/bin/python -m unittest discover -s tests -v
```
