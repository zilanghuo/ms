# tk 服务重启验证流程

适用对象：`tk` Linux 服务器重启后的服务恢复、检查和故障处理。  
更新时间：2026-10-16

## 一、恢复目标

tk 重启后，需要确认以下链路可用：

```text
ms-cloud TikTok 服务
  -> ms-cloud 本地 SSH 隧道 127.0.0.1:8888
  -> tk Tinyproxy 127.0.0.1:8888
  -> TikTok Business API

tk ecomhub Java 服务
  -> 0.0.0.0:9301

紫鸟图形环境
  -> Xvfb :99
  -> VNC 127.0.0.1:5900
```

## 二、服务清单与重启行为

| 服务 | 所在机器 | 端口/用途 | 重启后预期 | 备注 |
|---|---|---|---|---|
| `tinyproxy.service` | tk | `127.0.0.1:8888` | 自动启动 | 仅供 SSH 隧道转发使用，不开放公网 |
| `ziniao-desktop.service` | tk | Xvfb `:99` | 自动启动 | 紫鸟 Linux 客户端的虚拟桌面 |
| `ziniao-vnc.service` | tk | `127.0.0.1:5900` | 自动启动 | 经 SSH 隧道从 Mac 访问 |
| `ecomhub-mcp.jar` | tk | `9301` | **不会自动启动** | 当前由 `nohup java -jar` 启动，需手工恢复 |
| `tk-http-proxy-tunnel.service` | ms-cloud | `127.0.0.1:8888` | 自动重连 | 隧道目标为 tk 的 Tinyproxy |

## 三、重启后的验证顺序

### 1. 确认 tk 可以 SSH 登录

在 Mac 本地终端执行：

```bash
ssh tk 'uptime; hostname'
```

预期：返回 tk 主机名与正常运行时长。

若出现：

```text
Connection timed out during banner exchange
```

表示 22 端口可能可达，但 SSH 服务没有完成握手。此时不要反复并发连接；等待一小段时间后重试，并通过云控制台检查 CPU、内存、磁盘和系统日志。若持续不可恢复，再使用云控制台重启实例。

### 2. 验证 tk 基础服务

```bash
ssh tk '
  systemctl is-active tinyproxy.service ziniao-desktop.service ziniao-vnc.service
  ss -ltnp | grep -E ":(8888|5900)" || true
'
```

预期：三个服务均返回 `active`，并且可看到：

- `127.0.0.1:8888`：Tinyproxy
- `127.0.0.1:5900`：x11vnc

若任一服务未启动：

```bash
ssh tk 'sudo systemctl restart tinyproxy.service ziniao-desktop.service ziniao-vnc.service'
```

再次执行本节验证命令。

### 3. 验证并恢复 Java 服务

检查：

```bash
ssh tk '
  pgrep -af "java -jar|ecomhub-mcp" || true
  ss -ltnp | grep ":9301" || true
'
```

预期：存在 `java -jar ecomhub-mcp.jar` 进程，且 `9301` 正在监听。

若未监听，按当前原部署方式启动：

```bash
ssh tk '
  set -e
  cd /home/ms-mcp
  nohup java -jar ecomhub-mcp.jar > ecomhub-mcp.log 2>&1 &
  echo $! > ecomhub-mcp.pid
  sleep 10
  ss -ltnp | grep ":9301"
'
```

若启动失败，查看最近日志：

```bash
ssh tk 'tail -n 100 /home/ms-mcp/ecomhub-mcp.log'
```

注意：当前 Java 服务没有 systemd 单元，因此每次 tk 重启后都要执行本节恢复。后续建议将它改为 systemd 托管，以实现自动恢复。

### 4. 验证 ms-cloud 到 tk 的代理隧道

```bash
ssh ms-cloud '
  systemctl is-active tk-http-proxy-tunnel.service
  ss -ltnp | grep "127.0.0.1:8888" || true
  curl -sS -o /dev/null \
    -w "TikTok proxy: CONNECT=%{http_connect} HTTP=%{http_code}\\n" \
    -x http://127.0.0.1:8888 \
    --connect-timeout 10 \
    https://business-api.tiktok.com/
'
```

预期：

```text
active
TikTok proxy: CONNECT=200 HTTP=301
```

`HTTP=301` 是目标站点响应，可接受；关键判断是 `CONNECT=200`。

若隧道未恢复：

```bash
ssh ms-cloud 'sudo systemctl restart tk-http-proxy-tunnel.service'
```

然后重复本节验证命令。

### 5. 验证紫鸟图形界面（需要时）

在 Mac 建立 SSH 隧道，终端需要保持运行：

```bash
ssh -N -L 5900:127.0.0.1:5900 tk
```

使用 TigerVNC Viewer 连接：

```text
localhost:5900
```

VNC 端口仅监听 tk 本机地址，不能也不应在云安全组开放 `5900/tcp`。

## 四、一次性快速检查

只检查 tk：

```bash
ssh tk '
  echo "[uptime]"; uptime
  echo "[services]"; systemctl is-active tinyproxy.service ziniao-desktop.service ziniao-vnc.service
  echo "[listeners]"; ss -ltnp | grep -E ":(9301|8888|5900)" || true
  echo "[java]"; pgrep -af "java -jar|ecomhub-mcp" || true
'
```

检查 ms-cloud 隧道：

```bash
ssh ms-cloud '
  echo "[tunnel]"; systemctl is-active tk-http-proxy-tunnel.service
  echo "[listener]"; ss -ltnp | grep "127.0.0.1:8888" || true
'
```

## 五、禁止事项

- 不要把 VNC `5900`、Tinyproxy `8888`、紫鸟 API `18888` 或动态 WebDriver 调试端口暴露到公网。
- 不要将交互式的 `SbProxy-linux` 直接配置成 systemd 常驻服务；它会等待手机号输入，可能造成循环日志和服务器异常负载。
- 不要在文档、Shell 历史或 systemd 单元中写入紫鸟账号密码、Cookie、Token 或其他敏感信息。

## 六、重启后的完成判定

以下条件全部满足即视为恢复完成：

1. `ssh tk` 可正常执行命令。
2. tk 的 Tinyproxy、紫鸟桌面、VNC 服务均为 `active`。
3. `9301` 存在 Java 监听。
4. ms-cloud 的 `tk-http-proxy-tunnel.service` 为 `active`。
5. 从 ms-cloud 代理访问 TikTok Business API 返回 `CONNECT=200`。

