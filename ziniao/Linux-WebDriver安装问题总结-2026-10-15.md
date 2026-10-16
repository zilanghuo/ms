# Linux 部署紫鸟 WebDriver 问题总结

日期：2026-10-15  
服务器：`tk`（Ubuntu 24.04，Linux 6.8 内核）

## 一、目标

在 Linux 服务器上重新部署紫鸟客户端、紫鸟 WebDriver 运行环境和图形化登录环境，后续执行 TikTok Shop 三个店铺的商品照片详情导出、Excel 上传及定时任务。

## 二、安装过程中遇到的问题

### 1. 原系统版本不满足紫鸟客户端要求

旧服务器为 Alibaba Linux 3，内核和 glibc 版本较旧。紫鸟 Linux 客户端启动时提示缺少 `GLIBC_2.34`，无法通过普通 Python 虚拟环境解决，因为这是客户端二进制依赖的系统 glibc 版本。

处理方式：将服务器升级为 Ubuntu 24.04，当前内核为 6.8，满足紫鸟客户端的运行基础。

### 2. 紫鸟客户端缺少 ALSA 动态库

客户端安装成功后首次启动提示：

```text
libasound.so.2: cannot open shared object file
```

原因是 Ubuntu 24.04 使用 `libasound2t64` 包提供兼容库。

处理方式：安装 `libasound2t64`，客户端随后可以进入图形启动阶段。

### 3. VPS 压缩包解压工具缺失

紫鸟 VPS 辅助包已经下载，但服务器没有 `unzip`，导致解压失败。

处理方式：安装 `unzip`，将 VPS 文件解压到 `/opt/ziniao-vps`。

### 4. 无桌面环境，客户端无法启动

直接执行客户端时提示：

```text
Missing X server or $DISPLAY
```

原因是服务器没有物理桌面和 X Server。

处理方式：安装并配置：

- Xvfb：提供虚拟显示器 `:99`
- Openbox：提供轻量窗口管理器
- x11vnc：通过 VNC 查看虚拟桌面
- dbus-x11、xauth：补齐桌面程序运行依赖

紫鸟客户端当前运行在虚拟显示器 `:99`，VNC 只监听服务器本机 `127.0.0.1:5900`。

### 5. X11 认证配置导致客户端退出

首次启用 X11 认证时，Xvfb 已配置认证文件，但紫鸟进程没有设置 `XAUTHORITY`，日志出现：

```text
Authorization required, but no authorization protocol specified
```

处理过程中还发现紫鸟启动器会派生真正的 Electron 浏览器进程，然后自身退出。如果 systemd 将启动器当作唯一主进程，会误判服务结束并清理子进程。

最终处理方式：

- 让虚拟显示器使用本机专用 X11 会话。
- 在桌面启动脚本中持续监管派生出的紫鸟浏览器进程。
- `ziniao-desktop.service` 和 `ziniao-vnc.service` 设置为开机自启。

### 6. macOS 自带屏幕共享与无密码 VNC 兼容性不好

最初 x11vnc 使用 `-nopw`，Mac 屏幕共享客户端一直停留在连接或密码窗口。

后来改为 VNC 密码模式。第一次写入密码时命令参数顺序错误，实际保存的密码不是预期值；已重新写入并验证服务正常。

当前临时 VNC 密码未记录在本文档中，避免把认证信息写入项目文档。

### 7. macOS 屏幕共享性能和中文输入体验较差

当前 macOS 自带屏幕共享存在以下问题：

- 画面刷新较慢；
- 复杂密码无法方便粘贴到本地 VNC 认证框；
- 中文键盘和剪贴板同步不稳定。

处理方式：

- Mac 上已安装 TigerVNC Viewer，作为替代客户端。
- 在 tk 上安装 `xclip` 和 `xdotool`，增加 `/usr/local/bin/ziniao-paste`。
- 在紫鸟远程输入框获得焦点后，可在 Mac 本地执行：

  ```bash
  pbpaste | ssh tk /usr/local/bin/ziniao-paste
  ```

  该命令把 Mac 剪贴板内容写入 tk 的 X11 剪贴板，并向当前焦点框发送粘贴操作。

### 8. 错误地将交互式 VPS 工具作为 systemd 服务

`SbProxy-linux` 并不是适合直接作为无交互守护服务运行的命令。错误配置后，它进入手机号输入菜单并持续提示手机号为空，同时派生 `vps-server` 子进程，造成服务器负载升高，最终出现：

```text
Connection timed out during banner exchange
```

此时 22 端口仍可建立 TCP 连接，但 SSH 服务无法及时完成握手。

处理方式：

- 重启实例恢复 SSH。
- 停止并移除 `ziniao-vps.service`。
- 清理遗留 `vps-server` 子进程。
- 后续不能把交互式 `SbProxy-linux` 直接写成开机 systemd 服务。

### 9. 重启后 Java 服务不会自动恢复

`/home/ms-mcp/ecomhub-mcp.jar` 原部署脚本使用 `nohup java -jar` 启动，没有注册 systemd 服务。因此实例重启后，9301 端口不会自动监听。

处理方式：按原部署脚本重新启动 Java 服务，当前 9301 已恢复监听。后续应考虑为该服务增加正式的 systemd 单元，避免每次重启手工恢复。

### 10. tk 系统升级后 ms-cloud 隧道的主机指纹变化

tk 系统升级后 SSH 主机密钥变化，ms-cloud 上原有 `known_hosts` 记录失效，导致隧道连接失败。

处理方式：

- 更新 ms-cloud 上 tk 的 SSH 主机指纹。
- 重新确认专用 SSH 公钥已经加入 tk 的授权列表。
- 在 tk 安装 Tinyproxy，仅监听 `127.0.0.1:8888`。
- 重启 `tk-http-proxy-tunnel.service`。

最终验证结果：ms-cloud 通过本地 8888 代理访问 TikTok Business API，HTTP CONNECT 成功。

## 三、当前服务状态

当前已确认或配置的服务：

| 服务 | 监听/用途 | 状态 |
|---|---|---|
| 紫鸟桌面 | Xvfb `:99` | 已配置开机自启 |
| VNC | tk `127.0.0.1:5900` | 已配置开机自启 |
| Tinyproxy | tk `127.0.0.1:8888` | 已配置并运行 |
| ecomhub Java | tk `9301` | 已手工恢复，尚未注册 systemd |
| ms-cloud 隧道 | ms-cloud 本地 `127.0.0.1:8888` | 已验证自动重连 |
| 紫鸟 VPS 辅助程序 | 不应直接作为交互式 systemd 服务 | 已移除错误服务 |

## 四、当前未完成事项

1. 通过 TigerVNC 或其他稳定远程桌面完成紫鸟账号登录。
2. 在紫鸟客户端中确认三个店铺可见并完成授权。
3. 将 `pictureData/ziniao_photo_export.py` 迁移到 Linux 目录。
4. 在 Linux 创建 Python 虚拟环境并安装 Selenium、requests 等依赖。
5. 配置 Linux 版凭据文件、ChromeDriver 路径和下载目录。
6. 先用单日、单店执行验证，再运行三个店铺的日期范围导出。
7. 将 ecomhub Java 服务注册为 systemd，确保重启后自动恢复。
8. 为紫鸟 WebDriver 导出任务增加正式的 systemd timer 或 DolphinScheduler 调度，不依赖 Codex 手动触发。

## 五、端口与安全边界

对外安全组原则上只开放 SSH `22/tcp`。以下端口均应保持本机或隧道访问：

- VNC：`127.0.0.1:5900`
- 紫鸟本机 API：`127.0.0.1:18888`
- Tinyproxy：`127.0.0.1:8888`
- WebDriver 调试端口：动态分配，仅本机使用

VNC 访问方式是在 Mac 本地建立 SSH 隧道，而不是开放公网 5900：

```bash
ssh -N -L 5900:127.0.0.1:5900 tk
```

然后使用 TigerVNC Viewer 连接 `localhost:5900`。

## 六、结论

Linux 无桌面部署紫鸟 WebDriver 是可行的，但必须同时解决系统 glibc、Electron 动态库、Xvfb 虚拟显示、窗口管理、VNC 访问和进程生命周期问题。当前基础环境已经搭好，主要剩余工作是完成紫鸟人工登录、迁移导出脚本和建立稳定的后台调度。

