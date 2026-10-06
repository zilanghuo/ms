#!/usr/bin/env python3
"""通过紫鸟本地 WebDriver 启动店铺并导出 TikTok Shop 照片详情数据。"""

from __future__ import annotations

import argparse
import json
import time
import uuid
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


def parse_date(value: str | None) -> date:
    """返回指定的 ISO 日期；未指定时返回本机前两天。"""
    if value is None:
        return date.today() - timedelta(days=2)
    return date.fromisoformat(value)


def build_export_filename(shop_label: str, account_label: str, target_date: date) -> str:
    """生成稳定且便于归档的 Excel 文件名。"""
    return f"{shop_label}-{account_label}-{target_date:%Y%m%d}.xlsx"


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
    if destination.exists():
        raise RuntimeError(f"目标文件已存在，拒绝覆盖：{destination}")
    deadline = time.monotonic() + timeout
    download_clicked = False
    while time.monotonic() < deadline:
        partial = list(download_dir.glob("*.crdownload"))
        candidates = [path for path in download_dir.glob("*.xlsx") if path not in existing_files]
        if candidates and not partial:
            source = max(candidates, key=lambda path: path.stat().st_mtime)
            source.rename(destination)
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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--credentials-file", required=True, type=Path)
    parser.add_argument("--browser-id")
    parser.add_argument("--browser-name")
    parser.add_argument("--date", help="YYYY-MM-DD；默认前一天")
    parser.add_argument("--api-base", default="http://127.0.0.1:18888")
    parser.add_argument("--chrome-driver", required=True)
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--download-dir", type=Path, default=Path.home() / "Downloads")
    parser.add_argument("--download-timeout", type=int, default=120)
    parser.add_argument("--shop-label", default="1店")
    parser.add_argument("--upload-endpoint", default=DEFAULT_UPLOAD_ENDPOINT)
    parser.add_argument("--skip-upload", action="store_true")
    args = parser.parse_args()
    target_date = parse_date(args.date)
    credentials = read_credentials(args.credentials_file)
    browser_list = ziniao_call(args.api_base, credentials, "getBrowserList").get("browserList", [])
    browser_id = resolve_browser_id(browser_list, args.browser_id, args.browser_name)
    debug_port = start_browser(args.api_base, credentials, browser_id)
    driver = attach_driver(debug_port, args.chrome_driver)
    try:
        args.download_dir.mkdir(parents=True, exist_ok=True)
        try:
            driver.execute_cdp_cmd(
                "Browser.setDownloadBehavior",
                {"behavior": "allow", "downloadPath": str(args.download_dir), "eventsEnabled": True},
            )
        except Exception:
            driver.execute_cdp_cmd("Page.setDownloadBehavior", {"behavior": "allow", "downloadPath": str(args.download_dir)})
        driver.get(PHOTO_DETAILS_URL)
        set_date_range(driver, target_date, args.timeout)
        for account_label in ("已绑定账号", "联盟账号"):
            existing_files = set(args.download_dir.glob("*.xlsx"))
            export_account_type(driver, account_label, target_date, args.timeout)
            saved_path = wait_and_rename_download(
                driver,
                args.download_dir,
                existing_files,
                build_export_filename(args.shop_label, account_label, target_date),
                args.download_timeout,
            )
            print(f"已导出并重命名：{saved_path}")
            if not args.skip_upload:
                upload_excel(args.upload_endpoint, saved_path)
                print(f"已上传：{saved_path.name}")
    finally:
        driver.quit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
