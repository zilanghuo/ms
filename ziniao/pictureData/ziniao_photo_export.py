#!/usr/bin/env python3
"""通过紫鸟本地 WebDriver 启动店铺并导出 TikTok Shop 照片详情数据。"""

from __future__ import annotations

import argparse
import json
import time
import uuid
from dataclasses import dataclass
from datetime import date, timedelta
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


PHOTO_DETAILS_URL = (
    "https://seller.us.tiktokshopglobalselling.com/compass/video-analytics/"
    "photo-details?shop_region=US"
)
DEFAULT_UPLOAD_ENDPOINT = "http://124.71.66.128:9210/tk/temp/excel/import/example"


@dataclass(frozen=True)
class ShopConfig:
    """一次导出任务对应的紫鸟店铺及归档文件名前缀。"""

    label: str
    browser_name: str | None = None
    browser_id: str | None = None


SHOP_CONFIGS = (
    ShopConfig("1店", browser_name="美国TK-艾斯特尼-美区跨境1店"),
    ShopConfig("3店", browser_name="美国TK-艾斯特尼-美区跨境3店（原大魔王）"),
    ShopConfig("英国直邮店", browser_name="美国TK-艾斯特尼-英国直邮店"),
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
    return f"{shop_label}-{account_label}-{target_date:%Y%m%d}.xlsx"


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


def start_browser(api_base: str, credentials: dict[str, str], browser_id: str) -> int:
    ziniao_call(api_base, credentials, "updateCore")
    response = ziniao_call(
        api_base,
        credentials,
        "startBrowser",
        browserId=browser_id,
        isHeadless=False,
        privacyMode=False,
    )
    return extract_debug_port(response)


def stop_browser(api_base: str, credentials: dict[str, str], browser_id: str) -> None:
    """调用紫鸟接口关闭本次启动的店铺窗口。"""
    ziniao_call(api_base, credentials, "stopBrowser", browserId=browser_id)


def attach_driver(debug_port: int, chrome_driver_path: str) -> webdriver.Chrome:
    options = Options()
    options.add_experimental_option("debuggerAddress", f"127.0.0.1:{debug_port}")
    return webdriver.Chrome(service=Service(chrome_driver_path), options=options)


def set_date_range(driver: webdriver.Chrome, target_date: date, timeout: int) -> None:
    wait = WebDriverWait(driver, timeout)
    date_text = target_date.strftime("%Y/%m/%d")
    date_cell = (
        By.XPATH,
        "//div[contains(@class, 'arco-panel-date')]"
        f"[.//div[contains(@class, 'arco-picker-header-value') and contains(., '{target_date.year}年') and contains(., '{target_date.month}月')]]"
        "//div[contains(@class, 'arco-picker-cell-in-view') and not(contains(@class, 'disabled'))]"
        f"[.//div[contains(@class, 'arco-picker-date-value') and normalize-space()='{target_date.day}']]",
    )
    start_field = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[placeholder='开始日期']")))
    start_field.click()
    wait.until(EC.element_to_be_clickable(date_cell)).click()
    wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[placeholder='结束日期']")))
    wait.until(EC.element_to_be_clickable(date_cell)).click()
    wait.until(
        lambda current: all(
            current.find_element(By.CSS_SELECTOR, f"input[placeholder='{placeholder}']").get_attribute("value") == date_text
            for placeholder in ("开始日期", "结束日期")
        )
    )


def click_account_tab(driver: webdriver.Chrome, account_label: str, timeout: int) -> None:
    locator = (By.XPATH, f"//*[(@role='tab' or self::button) and starts-with(normalize-space(.), '{account_label}')]")
    WebDriverWait(driver, timeout).until(EC.element_to_be_clickable(locator)).click()


def click_download(driver: webdriver.Chrome, timeout: int) -> None:
    direct = (By.CSS_SELECTOR, "button[data-uid^='asyncexport:button_handleexport']")
    try:
        WebDriverWait(driver, 3).until(EC.element_to_be_clickable(direct)).click()
        return
    except Exception:
        pass
    fallback = (By.XPATH, "(//table/preceding::button[not(@disabled)])[last()-1]")
    WebDriverWait(driver, timeout).until(EC.element_to_be_clickable(fallback)).click()


def export_account_type(driver: webdriver.Chrome, account_label: str, target_date: date, timeout: int = 30) -> None:
    click_account_tab(driver, account_label, timeout)
    WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.TAG_NAME, "table")))
    click_download(driver, timeout)


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
            if download_buttons:
                try:
                    driver.execute_script("arguments[0].click()", download_buttons[0])
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
    debug_port = start_browser(api_base, credentials, browser_id)
    driver: webdriver.Chrome | None = None
    try:
        driver = attach_driver(debug_port, chrome_driver_path)
        download_dir.mkdir(parents=True, exist_ok=True)
        try:
            driver.execute_cdp_cmd(
                "Browser.setDownloadBehavior",
                {"behavior": "allow", "downloadPath": str(download_dir), "eventsEnabled": True},
            )
        except Exception:
            driver.execute_cdp_cmd("Page.setDownloadBehavior", {"behavior": "allow", "downloadPath": str(download_dir)})
        for target_date in target_dates:
            driver.get(PHOTO_DETAILS_URL)
            set_date_range(driver, target_date, timeout)
            for account_label in ("已绑定账号", "联盟账号"):
                existing_files = set(download_dir.glob("*.xlsx"))
                export_account_type(driver, account_label, target_date, timeout)
                saved_path = wait_and_rename_download(
                    driver,
                    download_dir,
                    existing_files,
                    build_export_filename(shop.label, account_label, target_date),
                    download_timeout,
                )
                print(f"[{shop.label}] 已导出并重命名：{saved_path}")
                if not skip_upload:
                    upload_excel(upload_endpoint, saved_path)
                    print(f"[{shop.label}] 已上传：{saved_path.name}")
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
    parser.add_argument("--download-timeout", type=int, default=120)
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
