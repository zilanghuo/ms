#!/usr/bin/env python3
"""通过紫鸟本地 WebDriver 启动店铺并导出 TikTok Shop 照片详情数据。"""

from __future__ import annotations

import argparse
import json
import re
import time
import uuid
from dataclasses import dataclass, replace
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any
from urllib import request

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException, WebDriverException


PHOTO_DETAILS_URL = (
    "https://seller.us.tiktokshopglobalselling.com/compass/video-analytics/"
    "photo-details?shop_region=US"
)
UK_PHOTO_DETAILS_URL = (
    "https://seller.eu.tiktokshopglobalselling.com/compass/video-analytics/"
    "photo-details?shop_region=GB"
)
DEFAULT_UPLOAD_ENDPOINT = "http://124.71.66.128:9210/tk/temp/excel/import/example"
DEFAULT_DOWNLOAD_TIMEOUT = 300
RECONNECT_DELAYS = (2, 5, 10)


def log(message: str) -> None:
    """输出带本机当前时间的运行日志。"""
    print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {message}", flush=True)
DATE_PANEL_XPATH = (
    "//div[contains(concat(' ', normalize-space(@class), ' '), ' arco-picker-range ') "
    "and .//div[contains(@class, 'arco-picker-header-value')]]"
)
CALENDAR_MONTH_PATTERN = r"(\d{4})(?:\s*年)?\s*[-－]?\s*(\d{1,2})\s*月"


@dataclass(frozen=True)
class ShopConfig:
    """一次导出任务对应的紫鸟店铺及归档文件名前缀。"""

    label: str
    browser_name: str | None = None
    browser_id: str | None = None
    filename_label: str | None = None
    page_url: str = PHOTO_DETAILS_URL
    navigation_labels: tuple[str, ...] = ()
    start_url: str | None = None


SHOP_CONFIGS = (
    ShopConfig("1店", browser_name="美国TK-艾斯特尼-美区跨境1店"),
    ShopConfig(
        "3店",
        browser_name="美国TK-艾斯特尼-美区跨境3店（原大魔王）",
        filename_label="美国TK-艾斯特尼-美区跨境3店 (原大魔王)",
    ),
    ShopConfig(
        "英国直邮店",
        browser_name="美国TK-艾斯特尼-英国直邮店",
        page_url=UK_PHOTO_DETAILS_URL,
    ),
)


def parse_date(value: str | None) -> date:
    """返回指定的 ISO 日期；未指定时返回本机前两天。"""
    if value is None:
        return date.today() - timedelta(days=2)
    return date.fromisoformat(value)


def iter_dates(start_date: date, end_date: date):
    """按自然日正序遍历闭区间，并校验日期范围。"""
    if start_date > end_date:
        raise ValueError("开始日期不能晚于结束日期。")
    current_date = start_date
    while current_date <= end_date:
        yield current_date
        current_date += timedelta(days=1)


def build_export_filename(shop_label: str, account_label: str, target_date: date) -> str:
    """生成稳定且便于归档的 Excel 文件名。"""
    return f"商品照片详情_{account_label}_{shop_label}_{target_date:%Y-%m-%d}.xlsx"


def validate_shop_arguments(
    all_shops: bool,
    browser_id: str | None,
    browser_name: str | None,
    shop_label: str | None,
) -> None:
    """避免三店模式和单店定位参数同时出现。"""
    if all_shops and (browser_id or browser_name or shop_label):
        raise ValueError("--all-shops 不能与 --browser-id、--browser-name 或 --shop-label 同时使用。")


def select_shops(
    all_shops: bool,
    browser_id: str | None,
    browser_name: str | None,
    shop_label: str | None,
) -> tuple[ShopConfig, ...]:
    """返回本轮执行的店铺清单；未启用三店模式时保持单店兼容。"""
    validate_shop_arguments(all_shops, browser_id, browser_name, shop_label)
    if all_shops:
        return SHOP_CONFIGS
    configured_shop = next((shop for shop in SHOP_CONFIGS if shop.browser_name == browser_name), None)
    if configured_shop is not None:
        return (replace(configured_shop, label=shop_label) if shop_label else configured_shop,)
    return (ShopConfig(shop_label or "1店", browser_name=browser_name, browser_id=browser_id),)


def parse_upload_response(raw_response: str) -> dict[str, Any]:
    response = json.loads(raw_response)
    if response.get("code") not in (0, 200):
        raise RuntimeError(f"Excel 上传失败：{response.get('msg', raw_response)}")
    return response


def upload_excel(upload_endpoint: str, file_path: Path) -> dict[str, Any]:
    """以接口约定的 multipart 字段 file 上传一个 Excel 文件。"""
    boundary = f"----ziniao-{uuid.uuid4().hex}"
    body = b"".join(
        (
            f"--{boundary}\r\n".encode(),
            f'Content-Disposition: form-data; name="file"; filename="{file_path.name}"\r\n'.encode(),
            b"Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet\r\n\r\n",
            file_path.read_bytes(),
            f"\r\n--{boundary}--\r\n".encode(),
        )
    )
    http_request = request.Request(
        upload_endpoint,
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )
    with request.urlopen(http_request, timeout=120) as response:
        return parse_upload_response(response.read().decode("utf-8"))


def extract_debug_port(response: dict[str, Any]) -> int:
    """从紫鸟启动浏览器响应中提取本地调试端口。"""
    queue: list[Any] = [response]
    while queue:
        current = queue.pop(0)
        if isinstance(current, dict):
            for key, value in current.items():
                if key in {"debuggingPort", "debugPort"}:
                    try:
                        port = int(value)
                    except (TypeError, ValueError) as error:
                        raise RuntimeError("紫鸟返回的调试端口无效。") from error
                    if 1 <= port <= 65535:
                        return port
                    raise RuntimeError("紫鸟返回的调试端口无效。")
                queue.append(value)
        elif isinstance(current, list):
            queue.extend(current)
    raise RuntimeError("紫鸟启动响应中未找到调试端口。")


def extract_core_major(response: dict[str, Any]) -> int | None:
    """从紫鸟启动响应中读取 Chromium 主版本号。"""
    queue: list[Any] = [response]
    while queue:
        current = queue.pop(0)
        if isinstance(current, dict):
            for key, value in current.items():
                if key in {"core_version", "coreVersion"}:
                    try:
                        return int(str(value).split(".", 1)[0])
                    except (TypeError, ValueError):
                        return None
                queue.append(value)
        elif isinstance(current, list):
            queue.extend(current)
    return None


def resolve_chrome_driver(configured_path: str, core_major: int | None) -> str:
    """优先选取与紫鸟 Chromium 主版本匹配的同目录 ChromeDriver。"""
    if core_major is None:
        return configured_path
    matching_path = Path(configured_path).parent / f"chromedriver{core_major}"
    if matching_path.is_file():
        return str(matching_path)
    return configured_path


def read_credentials(path: Path) -> dict[str, str]:
    values = json.loads(path.read_text(encoding="utf-8"))
    required = ("company", "username", "password")
    if any(not isinstance(values.get(key), str) or not values[key] for key in required):
        raise RuntimeError("凭据文件必须包含非空的 company、username、password 字段。")
    return {key: values[key] for key in required}


def ziniao_call(api_base: str, credentials: dict[str, str], action: str, **extra: Any) -> dict[str, Any]:
    payload = {**credentials, "action": action, "requestId": str(uuid.uuid4()), **extra}
    http_request = request.Request(
        api_base,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with request.urlopen(http_request, timeout=120) as response:
        result = json.loads(response.read().decode("utf-8"))
    if str(result.get("statusCode")) != "0":
        raise RuntimeError(f"紫鸟 {action} 失败：{result.get('msg', '未知错误')}")
    return result


def resolve_browser_id(browser_list: list[dict[str, Any]], browser_id: str | None, browser_name: str | None) -> str:
    if browser_id:
        return browser_id
    matches = [
        item for item in browser_list
        if browser_name and browser_name in str(item.get("browserName", ""))
    ]
    if len(matches) != 1:
        raise RuntimeError("未找到唯一店铺；请传入 --browser-id，或用更精确的 --browser-name。")
    for key in ("browserId", "id", "browser_id"):
        if matches[0].get(key):
            return str(matches[0][key])
    raise RuntimeError("紫鸟店铺记录中没有 browserId。")


def start_browser(api_base: str, credentials: dict[str, str], browser_id: str) -> tuple[int, int | None]:
    ziniao_call(api_base, credentials, "updateCore")
    response = ziniao_call(
        api_base,
        credentials,
        "startBrowser",
        browserId=browser_id,
        isHeadless=True,
        privacyMode=False,
    )
    return extract_debug_port(response), extract_core_major(response)


def stop_browser(api_base: str, credentials: dict[str, str], browser_id: str) -> None:
    """调用紫鸟接口关闭本次启动的店铺窗口。"""
    ziniao_call(api_base, credentials, "stopBrowser", browserId=browser_id)


def attach_driver(debug_port: int, chrome_driver_path: str) -> webdriver.Chrome:
    options = Options()
    options.add_experimental_option("debuggerAddress", f"127.0.0.1:{debug_port}")
    return webdriver.Chrome(service=Service(chrome_driver_path), options=options)


def is_webdriver_connection_lost(error: BaseException) -> bool:
    """判断是否为紫鸟浏览器关闭或 ChromeDriver 断连。"""
    return isinstance(error, WebDriverException)


def configure_download_directory(driver: webdriver.Chrome, download_dir: Path) -> None:
    """允许附着的浏览器下载文件至指定目录。"""
    try:
        driver.execute_cdp_cmd(
            "Browser.setDownloadBehavior",
            {"behavior": "allow", "downloadPath": str(download_dir), "eventsEnabled": True},
        )
    except Exception:
        driver.execute_cdp_cmd("Page.setDownloadBehavior", {"behavior": "allow", "downloadPath": str(download_dir)})


def click_visible_date_cell(driver: webdriver.Chrome, locator: tuple[str, str], timeout: int) -> None:
    """从候选日期单元格中选择实际显示的一个，避开隐藏日历面板。"""
    def find_visible(current: webdriver.Chrome):
        return next((cell for cell in current.find_elements(*locator) if cell.is_displayed()), False)

    cell = WebDriverWait(driver, timeout).until(find_visible)
    driver.execute_script("arguments[0].click()", cell)


def calendar_month_offset(header_text: str | None, target_date: date) -> int:
    """返回日期面板当前月份相对于目标月份的月差。"""
    matched = re.search(CALENDAR_MONTH_PATTERN, header_text or "")
    if matched is None:
        raise ValueError(f"无法识别日期面板月份：{header_text!r}")
    current_year, current_month = (int(value) for value in matched.groups())
    return (target_date.year - current_year) * 12 + target_date.month - current_month


def calendar_month_button_index(offset: int) -> int:
    """Arco 双月面板图标顺序为上一年、上月、下月、下一年。"""
    if offset == 0:
        raise ValueError("目标月份与当前月份相同，无需点击月份按钮。")
    return 2 if offset > 0 else 1


def switch_calendar_to_target_month(driver: webdriver.Chrome, target_date: date, timeout: int) -> None:
    """将可见 Arco 日期面板切换到目标月份，支持跨月补数。"""
    header_locator = (By.XPATH, f"{DATE_PANEL_XPATH}//*[contains(@class, 'arco-picker-header-value')]")

    def visible_header(current: webdriver.Chrome):
        for header in current.find_elements(*header_locator):
            if header.is_displayed() and re.search(CALENDAR_MONTH_PATTERN, header.text):
                return header
        return False

    for _ in range(120):
        header = WebDriverWait(driver, timeout).until(visible_header)
        offset = calendar_month_offset(header.text, target_date)
        if offset == 0:
            return
        button_index = calendar_month_button_index(offset)
        button_locator = (By.XPATH, f"{DATE_PANEL_XPATH}//*[contains(@class, 'arco-picker-header-icon')]")
        button = WebDriverWait(driver, timeout).until(
            lambda current: (
                visible_buttons[button_index]
                if len(
                    visible_buttons := [
                        element
                        for element in current.find_elements(*button_locator)
                        if element.is_displayed() and "hidden" not in (element.get_attribute("class") or "")
                    ]
                ) > button_index
                else False
            )
        )
        previous_header_text = header.text
        driver.execute_script("arguments[0].click()", button)
        WebDriverWait(driver, timeout).until(
            lambda current: (next_header := visible_header(current)) and next_header.text != previous_header_text
        )
    raise RuntimeError("日期面板切换月份超过允许次数。")


def set_date_range(driver: webdriver.Chrome, target_date: date, timeout: int) -> None:
    wait = WebDriverWait(driver, timeout)
    date_text = target_date.strftime("%Y/%m/%d")
    date_cell = (
        By.XPATH,
        f"{DATE_PANEL_XPATH}"
        "//div[contains(@class, 'arco-picker-cell-in-view') and not(contains(@class, 'disabled'))]"
        f"[.//div[contains(@class, 'arco-picker-date-value') and normalize-space()='{target_date.day}']]",
    )
    start_field = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[placeholder='开始日期']")))
    driver.execute_script("arguments[0].click()", start_field)
    switch_calendar_to_target_month(driver, target_date, timeout)
    click_visible_date_cell(driver, date_cell, timeout)
    end_field = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[placeholder='结束日期']")))
    driver.execute_script("arguments[0].click()", end_field)
    switch_calendar_to_target_month(driver, target_date, timeout)
    click_visible_date_cell(driver, date_cell, timeout)
    wait.until(
        lambda current: all(
            current.find_element(By.CSS_SELECTOR, f"input[placeholder='{placeholder}']").get_attribute("value") == date_text
            for placeholder in ("开始日期", "结束日期")
        )
    )


def click_account_tab(driver: webdriver.Chrome, account_label: str, timeout: int) -> None:
    locator = (By.XPATH, f"//*[(@role='tab' or self::button) and starts-with(normalize-space(.), '{account_label}')]")
    WebDriverWait(driver, timeout).until(EC.element_to_be_clickable(locator)).click()


def click_navigation_label(driver: webdriver.Chrome, label: str, timeout: int) -> None:
    """点击侧边菜单或其可点击容器中的指定文案。"""
    locator = (
        By.XPATH,
        f"//*[normalize-space(.)='{label}']",
    )
    element = WebDriverWait(driver, timeout).until(EC.element_to_be_clickable(locator))
    driver.execute_script("arguments[0].click()", element)


def open_shop_report(driver: webdriver.Chrome, shop: ShopConfig, timeout: int) -> None:
    """打开店铺的数据分析页；需要菜单路径的店铺按配置逐层导航。"""
    driver.set_page_load_timeout(timeout)
    try:
        driver.get(shop.start_url or shop.page_url)
    except TimeoutException:
        pass
    for label in shop.navigation_labels:
        click_navigation_label(driver, label, timeout)


def ensure_shop_report_url(driver: webdriver.Chrome, shop: ShopConfig) -> None:
    """阻止在页面跳转后继续执行日期、导出等敏感操作。"""
    current_url = driver.current_url
    if not current_url:
        raise WebDriverException("紫鸟浏览器调试连接未返回当前页面地址。")
    if not current_url.startswith(shop.page_url):
        raise RuntimeError(
            f"页面地址异常：当前为 {current_url}，期望以 {shop.page_url} 开头。"
        )


def click_download(driver: webdriver.Chrome, timeout: int) -> bool:
    """关闭残留浮层后，以 DOM 点击触发导出按钮。"""
    try:
        driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
    except Exception:
        pass
    direct = (By.CSS_SELECTOR, "button[data-uid^='asyncexport:button_handleexport']")
    try:
        button = WebDriverWait(driver, 3).until(EC.element_to_be_clickable(direct))
        if not button.is_enabled() or "disabled" in (button.get_attribute("class") or ""):
            return False
        driver.execute_script("arguments[0].click()", button)
        return True
    except Exception:
        direct_buttons = driver.find_elements(*direct)
        if any(
            button.is_displayed() and (not button.is_enabled() or "disabled" in (button.get_attribute("class") or ""))
            for button in direct_buttons
        ):
            return False
    fallback = (By.XPATH, "(//table/preceding::button[not(@disabled)])[last()-1]")
    button = WebDriverWait(driver, timeout).until(EC.element_to_be_clickable(fallback))
    driver.execute_script("arguments[0].click()", button)
    return True


def export_account_type(driver: webdriver.Chrome, account_label: str, target_date: date, timeout: int = 30) -> bool:
    click_account_tab(driver, account_label, timeout)
    WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.TAG_NAME, "table")))
    return click_download(driver, timeout)


def wait_and_rename_download(
    driver: webdriver.Chrome,
    download_dir: Path,
    existing_files: set[Path],
    target_name: str,
    timeout: int,
) -> Path:
    """等待导出记录就绪，点击下载，并将本次 xlsx 以业务文件名归档。"""
    destination = download_dir / target_name
    deadline = time.monotonic() + timeout
    download_clicked = False
    while time.monotonic() < deadline:
        partial = list(download_dir.glob("*.crdownload"))
        candidates = [path for path in download_dir.glob("*.xlsx") if path not in existing_files]
        if candidates and not partial:
            source = max(candidates, key=lambda path: path.stat().st_mtime)
            source.replace(destination)
            return destination
        if not download_clicked:
            download_buttons = driver.find_elements(
                By.XPATH,
                "//button[normalize-space()='下载' or .//*[normalize-space()='下载']]",
            )
            clickable_buttons = []
            for button in download_buttons:
                try:
                    if button.is_displayed() and button.is_enabled():
                        clickable_buttons.append(button)
                except StaleElementReferenceException:
                    continue
            if clickable_buttons:
                try:
                    driver.execute_script("arguments[0].click()", clickable_buttons[0])
                    download_clicked = True
                except Exception:
                    pass
        time.sleep(1)
    raise RuntimeError(f"等待下载文件超时：{target_name}")


def export_shop(
    *,
    api_base: str,
    credentials: dict[str, str],
    browser_list: list[dict[str, Any]],
    shop: ShopConfig,
    chrome_driver_path: str,
    target_dates: list[date],
    timeout: int,
    download_dir: Path,
    download_timeout: int,
    upload_endpoint: str,
    skip_upload: bool,
    keep_browser_open: bool,
) -> None:
    """完成一间店铺的启动、导出、上传和关闭生命周期。"""
    browser_id = resolve_browser_id(browser_list, shop.browser_id, shop.browser_name)
    driver: webdriver.Chrome | None = None

    def start_export_driver() -> webdriver.Chrome:
        debug_port, core_major = start_browser(api_base, credentials, browser_id)
        connected_driver = attach_driver(debug_port, resolve_chrome_driver(chrome_driver_path, core_major))
        configure_download_directory(connected_driver, download_dir)
        return connected_driver

    def reconnect_driver(context: str) -> webdriver.Chrome:
        """按递增间隔重启紫鸟浏览器并重新附着调试端口。"""
        nonlocal driver
        last_error: Exception | None = None
        for attempt, delay_seconds in enumerate(RECONNECT_DELAYS, start=1):
            log(
                f"[{shop.label}] 浏览器调试连接中断，{delay_seconds} 秒后第 {attempt}/"
                f"{len(RECONNECT_DELAYS)} 次重连：{context}"
            )
            try:
                if driver is not None:
                    driver.quit()
            except Exception:
                pass
            try:
                stop_browser(api_base, credentials, browser_id)
            except Exception:
                pass
            time.sleep(delay_seconds)
            try:
                driver = start_export_driver()
                return driver
            except Exception as error:
                last_error = error
        raise RuntimeError(f"[{shop.label}] 浏览器重连失败：{context}") from last_error

    def set_current_date(target_date: date, open_page: bool) -> None:
        """首次打开报告页，后续日期复用当前页面；窗口关闭时重启一次。"""
        nonlocal driver
        try:
            if open_page:
                open_shop_report(driver, shop, timeout)
            ensure_shop_report_url(driver, shop)
            set_date_range(driver, target_date, timeout)
            ensure_shop_report_url(driver, shop)
        except (TypeError, ValueError, WebDriverException):
            reconnect_driver(f"页面日期 {target_date:%Y-%m-%d}")
            open_shop_report(driver, shop, timeout)
            ensure_shop_report_url(driver, shop)
            set_date_range(driver, target_date, timeout)
            ensure_shop_report_url(driver, shop)

    try:
        download_dir.mkdir(parents=True, exist_ok=True)
        driver = start_export_driver()
        for date_index, target_date in enumerate(target_dates):
            set_current_date(target_date, open_page=date_index == 0)
            for account_label in ("已绑定账号", "联盟账号"):
                def restore_account_page() -> webdriver.Chrome:
                    nonlocal driver
                    reconnect_driver(f"{target_date:%Y-%m-%d} {account_label}")
                    open_shop_report(driver, shop, timeout)
                    ensure_shop_report_url(driver, shop)
                    set_date_range(driver, target_date, timeout)
                    ensure_shop_report_url(driver, shop)
                    return driver

                try:
                    ensure_shop_report_url(driver, shop)
                except Exception as error:
                    if not is_webdriver_connection_lost(error):
                        raise
                    restore_account_page()
                existing_files = set(download_dir.glob("*.xlsx"))
                try:
                    exported = export_account_type(driver, account_label, target_date, timeout)
                except (WebDriverException, AttributeError):
                    restore_account_page()
                    exported = export_account_type(driver, account_label, target_date, timeout)
                if not exported:
                    log(f"[{shop.label}] {account_label} 在 {target_date:%Y-%m-%d} 无可导出数据，已跳过。")
                    continue
                saved_path = wait_and_rename_download(
                    driver,
                    download_dir,
                    existing_files,
                    build_export_filename(shop.filename_label or shop.browser_name or shop.label, account_label, target_date),
                    download_timeout,
                )
                log(f"[{shop.label}] 已导出并重命名：{saved_path}")
                if not skip_upload:
                    upload_excel(upload_endpoint, saved_path)
                    log(f"[{shop.label}] 已上传：{saved_path.name}")
    finally:
        try:
            if driver is not None:
                driver.quit()
        finally:
            if not keep_browser_open:
                stop_browser(api_base, credentials, browser_id)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--credentials-file", required=True, type=Path)
    parser.add_argument("--browser-id")
    parser.add_argument("--browser-name")
    parser.add_argument("--all-shops", action="store_true", help="依次导出内置的三家店铺")
    parser.add_argument("--date", help="YYYY-MM-DD；默认前两天。不能与日期范围参数同时使用")
    parser.add_argument("--start-date", help="YYYY-MM-DD；日期范围开始（含）")
    parser.add_argument("--end-date", help="YYYY-MM-DD；日期范围结束（含）")
    parser.add_argument("--api-base", default="http://127.0.0.1:18888")
    parser.add_argument("--chrome-driver", required=True)
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--download-dir", type=Path, default=Path.home() / "Downloads")
    parser.add_argument("--download-timeout", type=int, default=DEFAULT_DOWNLOAD_TIMEOUT)
    parser.add_argument("--shop-label", help="单店导出文件名前缀，默认 1店")
    parser.add_argument("--upload-endpoint", default=DEFAULT_UPLOAD_ENDPOINT)
    parser.add_argument("--skip-upload", action="store_true")
    parser.add_argument("--keep-browser-open", action="store_true", help="执行完成后不调用紫鸟 stopBrowser")
    args = parser.parse_args()
    if args.date and (args.start_date or args.end_date):
        parser.error("--date 不能与 --start-date 或 --end-date 同时使用。")
    if bool(args.start_date) != bool(args.end_date):
        parser.error("--start-date 与 --end-date 必须同时传入。")
    try:
        target_dates = (
            list(iter_dates(parse_date(args.start_date), parse_date(args.end_date)))
            if args.start_date
            else [parse_date(args.date)]
        )
    except ValueError as error:
        parser.error(str(error))
    try:
        shops = select_shops(args.all_shops, args.browser_id, args.browser_name, args.shop_label)
    except ValueError as error:
        parser.error(str(error))
    credentials = read_credentials(args.credentials_file)
    browser_list = ziniao_call(args.api_base, credentials, "getBrowserList").get("browserList", [])
    for shop in shops:
        export_shop(
            api_base=args.api_base,
            credentials=credentials,
            browser_list=browser_list,
            shop=shop,
            chrome_driver_path=args.chrome_driver,
            target_dates=target_dates,
            timeout=args.timeout,
            download_dir=args.download_dir,
            download_timeout=args.download_timeout,
            upload_endpoint=args.upload_endpoint,
            skip_upload=args.skip_upload,
            keep_browser_open=args.keep_browser_open,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
