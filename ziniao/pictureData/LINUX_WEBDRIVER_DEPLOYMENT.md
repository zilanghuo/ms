# 紫鸟 WebDriver Linux 无桌面部署指南

本文说明如何在 Linux 服务器上部署紫鸟 WebDriver，并运行本目录的照片详情导出脚本。本文仅新增部署说明，不修改现有 Python 脚本、`run_all_shops.sh` 或店铺配置。

## 1. 适用范围

- 紫鸟客户端已开通 WebDriver 权限。
- 使用 Linux 版紫鸟客户端，以无头模式运行店铺浏览器。
- 由 `ziniao_photo_export.py` 导出三个店铺的照片详情 Excel，并上传至已配置的 HTTP 接口。
- 服务器不需要桌面环境、`DISPLAY` 或人工点击界面；首次店铺登录、验证码或风控验证仍需在可视化环境中人工完成。

## 2. 部署结构

建议以独立运行账号部署，以下路径均可按实际情况调整：

| 用途 | 建议路径 |
| --- | --- |
| 紫鸟 Linux 客户端 | `/opt/ziniao/ziniaobrowser` |
| 本项目脚本目录 | `/opt/ziniao-photo-export` |
| Python 虚拟环境 | `/opt/ziniao-photo-export/venv` |
| 紫鸟凭据文件 | `/etc/ziniao-photo-export/credentials.json` |
| Excel 下载目录 | `/data/ziniao/downloads` |
| 运行日志目录 | `/var/log/ziniao-photo-export` |
| 本地 WebDriver API | `127.0.0.1:18888` |

不要把 WebDriver API 端口映射到公网，也不要将凭据文件、Cookie、下载文件上传到代码仓库。

## 3. 安装紫鸟客户端

从紫鸟官方渠道取得 Linux 客户端，并放置为 `/opt/ziniao/ziniaobrowser`。赋予可执行权限：

```bash
sudo chmod +x /opt/ziniao/ziniaobrowser
```

Linux WebDriver 模式建议以下列参数启动：

```bash
/opt/ziniao/ziniaobrowser \
  --no-sandbox \
  --run_type=web_driver \
  --ipc_type=http \
  --port=18888
```

紫鸟客户端、店铺环境和代理网络需要先完成一次人工授权与登录。无头模式不会绕过验证码、二次验证或平台风控。

> Linux 版紫鸟通常使用内核随附的 `webdriver`，无需按 macOS 的方式单独下载 ChromeDriver。实际 driver 文件位置以 `startBrowser` 返回的内核路径及紫鸟版本为准，并且必须与返回的 Chromium 主版本匹配。

如进程无法启动，先按紫鸟 Linux 版安装要求补齐其依赖库，再检查服务运行账号对紫鸟目录、缓存目录和网络代理的访问权限。

## 4. 安装脚本与 Python 依赖

将本目录内容部署到 `/opt/ziniao-photo-export`，不要包含本机凭据文件。以运行账号创建虚拟环境并安装依赖：

```bash
sudo mkdir -p /opt/ziniao-photo-export /data/ziniao/downloads /var/log/ziniao-photo-export
sudo chown -R ziniao:ziniao /opt/ziniao-photo-export /data/ziniao /var/log/ziniao-photo-export

sudo -u ziniao python3 -m venv /opt/ziniao-photo-export/venv
sudo -u ziniao /opt/ziniao-photo-export/venv/bin/python -m pip install --upgrade pip
sudo -u ziniao /opt/ziniao-photo-export/venv/bin/python -m pip install 'selenium>=4.15,<5'
```

其中 `ziniao` 是示例运行账号，可替换为实际的非 root 服务账号。

## 5. 创建并保护凭据文件

创建 `/etc/ziniao-photo-export/credentials.json`：

```json
{
  "company": "<紫鸟公司名>",
  "username": "<紫鸟用户名>",
  "password": "<紫鸟密码>"
}
```

仅授予服务账号读取权限：

```bash
sudo install -d -m 700 -o ziniao -g ziniao /etc/ziniao-photo-export
sudo chown ziniao:ziniao /etc/ziniao-photo-export/credentials.json
sudo chmod 600 /etc/ziniao-photo-export/credentials.json
```

不要将真实凭据写进 systemd unit、Shell 脚本、命令历史或日志。

## 6. 确认 Linux WebDriver 与本脚本的连接方式

本脚本通过以下流程工作：

1. 向 `http://127.0.0.1:18888` 调用 `getBrowserList` 和 `startBrowser`。
2. `startBrowser` 使用 `isHeadless=true` 打开指定店铺。
3. 从响应的 `debuggingPort` 附着 Selenium。
4. 打开照片详情页，按日期、账号类型导出并下载 Excel。
5. 上传 Excel，最后调用 `stopBrowser`。

部署前请确认可用的 Linux driver 路径。例如内核返回的浏览器路径附近含有 `webdriver` 时，可先检查：

```bash
test -x <LINUX_WEBDRIVER_PATH> && <LINUX_WEBDRIVER_PATH> --version
```

随后使用该绝对路径传给 `--chrome-driver`。不要沿用 macOS 的 `/Users/.../chromedriver129` 路径。

## 7. 手工执行验证

先只跑一天，观察日志与下载目录：

```bash
cd /opt/ziniao-photo-export

/opt/ziniao-photo-export/venv/bin/python ziniao_photo_export.py \
  --credentials-file /etc/ziniao-photo-export/credentials.json \
  --all-shops \
  --date 2026-10-10 \
  --chrome-driver <LINUX_WEBDRIVER_PATH> \
  --download-dir /data/ziniao/downloads \
  --timeout 60 \
  --download-timeout 300 \
  --upload-endpoint 'http://<internal-host>:<port>/<upload-path>'
```

成功标准：每个有数据的“已绑定账号”“联盟账号”均生成一份 Excel，日志中出现“已上传”，并且进程结束后对应店铺窗口已被 `stopBrowser` 关闭。

## 8. 将紫鸟客户端设为 systemd 服务

创建 `/etc/systemd/system/ziniao-webdriver.service`：

```ini
[Unit]
Description=Ziniao WebDriver API
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=ziniao
Group=ziniao
Environment=HOME=/home/ziniao
ExecStart=/opt/ziniao/ziniaobrowser --no-sandbox --run_type=web_driver --ipc_type=http --port=18888
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

启用并查看状态：

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now ziniao-webdriver.service
sudo systemctl status ziniao-webdriver.service
```

服务只应监听回环地址。若必须跨主机调用，请改用 VPN、SSH 隧道或受控内网代理，不要直接开放 API 端口。

## 9. 定时任务示例

建议在确认手工执行稳定后再配置定时任务。创建 `/etc/systemd/system/ziniao-photo-export.service`：

```ini
[Unit]
Description=Export TikTok Shop photo details through Ziniao
After=network-online.target ziniao-webdriver.service
Requires=ziniao-webdriver.service

[Service]
Type=oneshot
User=ziniao
Group=ziniao
WorkingDirectory=/opt/ziniao-photo-export
ExecStart=/opt/ziniao-photo-export/venv/bin/python /opt/ziniao-photo-export/ziniao_photo_export.py --credentials-file /etc/ziniao-photo-export/credentials.json --all-shops --date <YYYY-MM-DD> --chrome-driver <LINUX_WEBDRIVER_PATH> --download-dir /data/ziniao/downloads --timeout 60 --download-timeout 300 --upload-endpoint http://<internal-host>:<port>/<upload-path>
StandardOutput=append:/var/log/ziniao-photo-export/export.log
StandardError=append:/var/log/ziniao-photo-export/export-error.log
```

如需每日固定执行，创建 `/etc/systemd/system/ziniao-photo-export.timer`：

```ini
[Unit]
Description=Run Ziniao photo export every day

[Timer]
OnCalendar=*-*-* 03:30:00
Persistent=true

[Install]
WantedBy=timers.target
```

当前 Python 脚本在未传 `--date` 时默认导出执行日的前两天。若使用 timer 并希望始终按此前两天的逻辑运行，可从 `ExecStart` 删除 `--date <YYYY-MM-DD>`。

启用 timer：

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now ziniao-photo-export.timer
systemctl list-timers ziniao-photo-export.timer
```

## 10. 运维检查清单

- `ziniao-webdriver.service` 处于 `active (running)`。
- `127.0.0.1:18888` 可访问，且没有被暴露到公网。
- 运行账号可写入 `/data/ziniao/downloads` 与 `/var/log/ziniao-photo-export`。
- `--chrome-driver` 指向与紫鸟 Chromium 内核匹配的 Linux driver。
- 店铺代理网络、平台登录状态正常。
- 凭据文件权限为 `600`，目录权限为 `700`。
- 每日检查 `export-error.log`，并配置日志轮转与下载文件的保留策略。

## 11. 常见问题

### `ModuleNotFoundError: selenium`

确认运行命令使用的是 `/opt/ziniao-photo-export/venv/bin/python`，并在该虚拟环境内重新安装 Selenium。

### `no such window` 或调试连接中断

先确认紫鸟客户端服务未退出、店铺网络可用、服务器内存和磁盘空间充足。本项目脚本对这类瞬时中断有有限重连与下载接管逻辑；反复失败时应检查紫鸟客户端日志和店铺代理。

### 下载没有 Excel 文件

确认 `--download-dir` 是绝对路径且可写；确认导出按钮是否有数据可导出；确认无头店铺会话允许直接下载而不弹出保存位置选择框。

### 无头模式页面空白或登录失效

先用可视化环境完成平台登录、验证码和必要授权，再切换到 `isHeadless=true`。无头模式无法代替人工完成平台风控验证。
