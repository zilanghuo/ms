# 紫鸟照片详情自动导出

该脚本不依赖 Codex 的可视化点击：它调用本机紫鸟 WebDriver 服务启动已有会话的店铺浏览器，再通过 Selenium 附着调试端口，自动导出“已绑定账号”和“联盟账号”的照片详情数据。

## 前提

- 紫鸟 WebDriver 已在 `127.0.0.1:18888` 启动。
- 目标店铺已人工完成登录；验证码、人机校验和风控验证不能由此脚本绕过。
- Python 环境已安装 `selenium`。
- ChromeDriver 与紫鸟浏览器内核版本匹配。

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

也可用精确店铺名称匹配代替 `--browser-id`：

```bash
--browser-name "<店铺名称的唯一片段>"
```

成功时仅输出两个“已触发导出”状态行；实际文件生成应在浏览器下载记录或默认下载目录中确认。

脚本会等待下载完成并重命名文件，默认保存到 `~/Downloads`：

- `1店-已绑定账号-YYYYMMDD.xlsx`
- `1店-联盟账号-YYYYMMDD.xlsx`

可通过 `--download-dir` 指定目录、通过 `--shop-label` 修改文件名前缀。为防止误覆盖，同名文件已经存在时脚本会停止并报错。

## 定时执行

在确认一次手工运行稳定后，再用 `launchd`（macOS）或 `cron`（Linux）调用上述命令。定时任务应使用绝对路径，并将标准输出与错误输出写到非敏感日志文件。

## 验证

```bash
/tmp/ziniao-webdriver-venv/bin/python -m unittest discover -s tests -v
```
