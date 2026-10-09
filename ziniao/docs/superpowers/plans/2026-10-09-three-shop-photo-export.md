# 三店照片详情导出 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为紫鸟照片详情导出脚本增加 `--all-shops`，一次按顺序处理三家内置店铺。

**Architecture:** 在脚本中用不可变店铺配置表示“文件名前缀 + 紫鸟店铺全名”。将现有单店执行主体提取为接收店铺配置的函数，`--all-shops` 仅负责确定配置列表；每店在独立 `try/finally` 中启动、下载、上传和关闭窗口。

**Tech Stack:** Python 3.9、argparse、Selenium、紫鸟本地 HTTP WebDriver API、unittest。

## Global Constraints

- 不在代码、测试、文档或日志中写入凭据、Token 或真实连接密码。
- 默认三店顺序为 1店、3店、英国直邮店。
- `--all-shops` 与 `--browser-id`、`--browser-name`、`--shop-label` 互斥。
- 每店下载完成后才覆盖同名文件；每店结束后调用 `stopBrowser`。
- 不修改用户已有的无关工作区改动。

---

### Task 1: 店铺配置与命令行选择

**Files:**
- Modify: `/Users/a1/Documents/Office/code/ms-proj/ziniao/pictureData/ziniao_photo_export.py`
- Modify: `/Users/a1/Documents/Office/code/ms-proj/ziniao/pictureData/tests/test_ziniao_photo_export.py`

**Interfaces:**
- Produces: `SHOP_CONFIGS: tuple[ShopConfig, ...]`
- Produces: `select_shops(all_shops: bool, browser_id: str | None, browser_name: str | None, shop_label: str | None) -> tuple[ShopConfig, ...]`

- [ ] **Step 1: Write the failing tests**

```python
def test_select_shops_returns_three_configured_shops():
    shops = exporter.select_shops(True, None, None, None)
    assert [(shop.label, shop.browser_name) for shop in shops] == [
        ("1店", "美国TK-艾斯特尼-美区跨境1店"),
        ("3店", "美国TK-艾斯特尼-美区跨境3店（原大魔王）"),
        ("英国直邮店", "美国TK-艾斯特尼-英国直邮店"),
    ]
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `/tmp/ziniao-webdriver-venv/bin/python -m unittest tests.test_ziniao_photo_export -v`

Expected: FAIL because `select_shops` does not exist.

- [ ] **Step 3: Add minimal configuration and selector**

```python
@dataclass(frozen=True)
class ShopConfig:
    label: str
    browser_name: str | None = None
    browser_id: str | None = None

SHOP_CONFIGS = (...)

def select_shops(all_shops, browser_id, browser_name, shop_label):
    if all_shops:
        return SHOP_CONFIGS
    return (ShopConfig(shop_label or "1店", browser_name, browser_id),)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `/tmp/ziniao-webdriver-venv/bin/python -m unittest discover -s tests -v`

Expected: PASS.

### Task 2: 独立的逐店导出生命周期

**Files:**
- Modify: `/Users/a1/Documents/Office/code/ms-proj/ziniao/pictureData/ziniao_photo_export.py`
- Modify: `/Users/a1/Documents/Office/code/ms-proj/ziniao/pictureData/tests/test_ziniao_photo_export.py`

**Interfaces:**
- Consumes: `ShopConfig` 和 `target_dates`。
- Produces: `export_shop(...) -> None`，负责单店完整生命周期。

- [ ] **Step 1: Write the failing test**

```python
@patch.object(exporter, "stop_browser")
@patch.object(exporter, "start_browser", return_value=9222)
@patch.object(exporter, "resolve_browser_id", return_value="shop-id")
def test_export_shop_closes_browser_after_failure(...):
    with self.assertRaisesRegex(RuntimeError, "导出失败"):
        exporter.export_shop(...)
    mock_stop_browser.assert_called_once_with(api_base, credentials, "shop-id")
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `/tmp/ziniao-webdriver-venv/bin/python -m unittest discover -s tests -v`

Expected: FAIL because `export_shop` does not exist.

- [ ] **Step 3: Extract one-store lifecycle**

Move the current browser startup, driver attachment, date loop, account loop, upload, `driver.quit()` and `stop_browser()` into `export_shop`. Wrap only the current shop’s execution in `try/finally`; preserve the existing download and upload functions unchanged.

- [ ] **Step 4: Run tests to verify they pass**

Run: `/tmp/ziniao-webdriver-venv/bin/python -m unittest discover -s tests -v`

Expected: PASS.

### Task 3: CLI integration and documentation

**Files:**
- Modify: `/Users/a1/Documents/Office/code/ms-proj/ziniao/pictureData/ziniao_photo_export.py`
- Modify: `/Users/a1/Documents/Office/code/ms-proj/ziniao/pictureData/README.md`
- Modify: `/Users/a1/Documents/Office/code/ms-proj/ziniao/pictureData/tests/test_ziniao_photo_export.py`

**Interfaces:**
- Consumes: `--all-shops`, existing date arguments and existing upload options.
- Produces: a three-store loop invoking `export_shop` once per selected shop.

- [ ] **Step 1: Write failing argument-validation tests**

```python
def test_all_shops_conflicts_with_single_shop_arguments():
    with self.assertRaisesRegex(ValueError, "--all-shops"):
        exporter.validate_shop_arguments(True, "id", None, None)
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `/tmp/ziniao-webdriver-venv/bin/python -m unittest discover -s tests -v`

Expected: FAIL because `validate_shop_arguments` does not exist.

- [ ] **Step 3: Implement CLI integration and README examples**

Add `--all-shops`; validate mutual exclusion before contacting the local API; select shops once and call `export_shop` sequentially. Document the exact three shop names, generated filename prefixes, default behavior and a `--start-date`/`--end-date` example.

- [ ] **Step 4: Verify full suite and syntax**

Run: `/tmp/ziniao-webdriver-venv/bin/python -m unittest discover -s tests -v && PYTHONPYCACHEPREFIX=/tmp/ziniao-pycache /tmp/ziniao-webdriver-venv/bin/python -m py_compile ziniao_photo_export.py`

Expected: all tests PASS and no syntax output.
