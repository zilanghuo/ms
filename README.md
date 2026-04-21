# ms

ms 需求分析。

## 本地访问

本仓库按静态站点方式启动，只保留一个访问端口：`8080`。

在仓库根目录执行：

```bash
python3 -m http.server 8080
```

启动后访问：

```text
http://192.168.10.9:8080/index.html
```

说明：

- 根目录 [`index.html`](/Users/a1/Documents/Office/code/ms-proj/index.html) 会自动跳转到 [`bi/tkDashboard/index.html`](/Users/a1/Documents/Office/code/ms-proj/bi/tkDashboard/index.html)
- 不再需要额外再起第二个端口用于首页或子页面访问
