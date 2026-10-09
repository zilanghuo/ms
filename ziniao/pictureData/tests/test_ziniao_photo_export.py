import sys
import unittest
import json
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock, patch


PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))

import ziniao_photo_export as exporter
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys


class FixedDate(date):
    @classmethod
    def today(cls):
        return cls(2026, 10, 5)


class DateParsingTests(unittest.TestCase):
    def test_parse_date_defaults_to_two_days_ago(self):
        with patch.object(exporter, "date", FixedDate):
            self.assertEqual(exporter.parse_date(None).isoformat(), "2026-10-03")

    def test_parse_date_accepts_iso_date(self):
        self.assertEqual(exporter.parse_date("2026-10-04").isoformat(), "2026-10-04")

    def test_iter_dates_includes_both_endpoints(self):
        self.assertEqual(
            [value.isoformat() for value in exporter.iter_dates(date(2026, 10, 2), date(2026, 10, 4))],
            ["2026-10-02", "2026-10-03", "2026-10-04"],
        )

    def test_iter_dates_rejects_reversed_range(self):
        with self.assertRaisesRegex(ValueError, "开始日期"):
            list(exporter.iter_dates(date(2026, 10, 4), date(2026, 10, 2)))

    def test_calendar_month_offset_moves_to_the_previous_month(self):
        self.assertEqual(
            exporter.calendar_month_offset("2026年10月", date(2026, 9, 1)),
            -1,
        )
        self.assertEqual(
            exporter.calendar_month_offset("2026 10月", date(2026, 9, 1)),
            -1,
        )
        self.assertEqual(
            exporter.calendar_month_offset("2026年-10月", date(2026, 9, 1)),
            -1,
        )

    def test_calendar_month_offset_rejects_missing_header_text(self):
        with self.assertRaises(ValueError):
            exporter.calendar_month_offset(None, date(2026, 9, 1))

    def test_date_panel_locator_targets_the_range_popup_container(self):
        self.assertIn("arco-picker-range", exporter.DATE_PANEL_XPATH)

    def test_calendar_navigation_uses_month_buttons_not_year_buttons(self):
        self.assertEqual(exporter.calendar_month_button_index(-1), 1)
        self.assertEqual(exporter.calendar_month_button_index(1), 2)

    @patch.object(exporter, "WebDriverWait")
    def test_click_visible_date_cell_skips_hidden_calendar_cells(self, mock_wait):
        driver = MagicMock()
        hidden_cell = MagicMock()
        hidden_cell.is_displayed.return_value = False
        visible_cell = MagicMock()
        visible_cell.is_displayed.return_value = True
        driver.find_elements.return_value = [hidden_cell, visible_cell]
        mock_wait.return_value.until.side_effect = lambda condition: condition(driver)

        exporter.click_visible_date_cell(driver, ("xpath", "//date-cell"), 30)

        driver.execute_script.assert_called_once_with("arguments[0].click()", visible_cell)


class ZiniaoResponseTests(unittest.TestCase):
    def test_extract_debug_port_accepts_nested_response(self):
        response = {
            "statusCode": 0,
            "data": {"debuggingPort": 39350},
        }
        self.assertEqual(exporter.extract_debug_port(response), 39350)

    def test_extract_debug_port_rejects_missing_port(self):
        with self.assertRaisesRegex(RuntimeError, "调试端口"):
            exporter.extract_debug_port({"statusCode": 0, "data": {}})

    def test_extract_core_major_reads_nested_core_version(self):
        self.assertEqual(exporter.extract_core_major({"data": {"core_version": "131.0.6778.76"}}), 131)

    @patch.object(exporter, "ziniao_call")
    def test_stop_browser_uses_official_stop_action(self, mock_ziniao_call):
        credentials = {"company": "company", "username": "user", "password": "password"}
        exporter.stop_browser("http://127.0.0.1:18888", credentials, "shop-1")
        mock_ziniao_call.assert_called_once_with(
            "http://127.0.0.1:18888", credentials, "stopBrowser", browserId="shop-1"
        )

    @patch.object(exporter, "extract_core_major", return_value=131)
    @patch.object(exporter, "extract_debug_port", return_value=9222)
    @patch.object(exporter, "ziniao_call")
    def test_start_browser_uses_headless_mode(
        self, mock_ziniao_call, mock_extract_debug_port, mock_extract_core_major
    ):
        credentials = {"company": "company", "username": "user", "password": "password"}
        mock_ziniao_call.return_value = {"data": {"debuggingPort": 9222, "core_version": "131.0"}}

        exporter.start_browser("http://127.0.0.1:18888", credentials, "shop-1")

        self.assertEqual(mock_ziniao_call.call_args_list[1].kwargs["isHeadless"], True)


class DownloadNamingTests(unittest.TestCase):
    def test_build_export_filename_uses_shop_account_and_compact_date(self):
        self.assertEqual(
            exporter.build_export_filename("美国TK-艾斯特尼-美区跨境1店", "已绑定账号", date(2026, 10, 4)),
            "商品照片详情_已绑定账号_美国TK-艾斯特尼-美区跨境1店_2026-10-04.xlsx",
        )


class ShopSelectionTests(unittest.TestCase):
    def test_select_shops_returns_configured_three_shop_sequence(self):
        shops = exporter.select_shops(all_shops=True, browser_id=None, browser_name=None, shop_label=None)
        self.assertEqual(
            [(shop.label, shop.browser_name) for shop in shops],
            [
                ("1店", "美国TK-艾斯特尼-美区跨境1店"),
                ("3店", "美国TK-艾斯特尼-美区跨境3店（原大魔王）"),
                ("英国直邮店", "美国TK-艾斯特尼-英国直邮店"),
            ],
        )

    def test_select_shops_reuses_uk_page_config_for_exact_single_shop_name(self):
        shops = exporter.select_shops(
            all_shops=False,
            browser_id=None,
            browser_name="美国TK-艾斯特尼-英国直邮店",
            shop_label="英国直邮店",
        )
        self.assertEqual(shops[0].page_url, exporter.UK_PHOTO_DETAILS_URL)

    def test_uk_shop_uses_gb_photo_details_page(self):
        shops = exporter.select_shops(all_shops=True, browser_id=None, browser_name=None, shop_label=None)
        uk_shop = next(shop for shop in shops if shop.label == "英国直邮店")
        self.assertEqual(
            uk_shop.page_url,
            "https://seller.eu.tiktokshopglobalselling.com/compass/video-analytics/"
            "photo-details?shop_region=GB",
        )
        self.assertEqual(uk_shop.navigation_labels, ())

    @patch.object(exporter, "click_navigation_label")
    def test_open_shop_report_opens_uk_photo_details_url_directly(self, mock_click_navigation_label):
        driver = MagicMock()
        shop = next(shop for shop in exporter.SHOP_CONFIGS if shop.label == "英国直邮店")

        exporter.open_shop_report(driver, shop, 30)

        driver.get.assert_called_once_with(
            "https://seller.eu.tiktokshopglobalselling.com/compass/video-analytics/"
            "photo-details?shop_region=GB"
        )
        mock_click_navigation_label.assert_not_called()

    def test_open_shop_report_allows_page_load_timeout_after_url_is_set(self):
        driver = MagicMock()
        driver.get.side_effect = TimeoutException()
        shop = next(shop for shop in exporter.SHOP_CONFIGS if shop.label == "英国直邮店")

        exporter.open_shop_report(driver, shop, 30)

        driver.set_page_load_timeout.assert_called_once_with(30)

    def test_ensure_shop_report_url_rejects_navigation_away_from_uk_page(self):
        driver = MagicMock()
        driver.current_url = "https://seller.eu.tiktokshopglobalselling.com/home"
        shop = next(shop for shop in exporter.SHOP_CONFIGS if shop.label == "英国直邮店")

        with self.assertRaisesRegex(RuntimeError, "页面地址异常"):
            exporter.ensure_shop_report_url(driver, shop)

    def test_ensure_shop_report_url_converts_empty_url_to_webdriver_error(self):
        driver = MagicMock()
        driver.current_url = None
        shop = next(shop for shop in exporter.SHOP_CONFIGS if shop.label == "英国直邮店")

        with self.assertRaises(WebDriverException):
            exporter.ensure_shop_report_url(driver, shop)

    @patch.object(exporter, "WebDriverWait")
    def test_click_navigation_label_uses_dom_click_for_text_container(self, mock_wait):
        driver = MagicMock()
        menu_text = MagicMock()
        mock_wait.return_value.until.return_value = menu_text

        exporter.click_navigation_label(driver, "数据分析", 30)

        driver.execute_script.assert_called_once_with("arguments[0].click()", menu_text)

    @patch.object(exporter, "WebDriverWait")
    def test_click_download_closes_popup_and_uses_dom_click(self, mock_wait):
        driver = MagicMock()
        button = MagicMock()
        button.is_enabled.return_value = True
        button.get_attribute.return_value = ""
        mock_wait.return_value.until.return_value = button

        self.assertTrue(exporter.click_download(driver, 30))

        driver.find_element.assert_called_once_with(By.TAG_NAME, "body")
        driver.find_element.return_value.send_keys.assert_called_once_with(Keys.ESCAPE)
        driver.execute_script.assert_called_once_with("arguments[0].click()", button)

    @patch.object(exporter, "WebDriverWait")
    def test_click_download_skips_disabled_official_export_button(self, mock_wait):
        driver = MagicMock()
        button = MagicMock()
        button.is_enabled.return_value = False
        button.get_attribute.return_value = "disabled"
        mock_wait.return_value.until.return_value = button

        self.assertFalse(exporter.click_download(driver, 30))
        driver.execute_script.assert_not_called()

    def test_all_shops_rejects_single_shop_arguments(self):
        with self.assertRaisesRegex(ValueError, "--all-shops"):
            exporter.validate_shop_arguments(True, "shop-id", None, None)

    @patch.object(exporter, "stop_browser")
    @patch.object(exporter, "set_date_range", side_effect=RuntimeError("导出失败"))
    @patch.object(exporter, "attach_driver")
    @patch.object(exporter, "start_browser", return_value=(9222, None))
    @patch.object(exporter, "resolve_browser_id", return_value="shop-id")
    def test_export_shop_closes_browser_when_export_fails(
        self,
        mock_resolve_browser_id,
        mock_start_browser,
        mock_attach_driver,
        mock_set_date_range,
        mock_stop_browser,
    ):
        driver = MagicMock()
        mock_attach_driver.return_value = driver
        credentials = {"company": "company", "username": "user", "password": "password"}
        shop = exporter.ShopConfig("1店", browser_name="美国TK-艾斯特尼-美区跨境1店")

        with self.assertRaisesRegex(RuntimeError, "导出失败"):
            exporter.export_shop(
                api_base="http://127.0.0.1:18888",
                credentials=credentials,
                browser_list=[],
                shop=shop,
                chrome_driver_path="/tmp/chromedriver",
                target_dates=[date(2026, 10, 7)],
                timeout=30,
                download_dir=Path("/tmp"),
                download_timeout=120,
                upload_endpoint="http://example.test/upload",
                skip_upload=True,
                keep_browser_open=False,
            )

        driver.quit.assert_called_once_with()
        mock_stop_browser.assert_called_once_with("http://127.0.0.1:18888", credentials, "shop-id")


class ChromeDriverSelectionTests(unittest.TestCase):
    def test_resolve_chrome_driver_uses_matching_major_version(self):
        with TemporaryDirectory() as temporary_directory:
            driver_dir = Path(temporary_directory)
            fallback_driver = driver_dir / "chromedriver129"
            matching_driver = driver_dir / "chromedriver131"
            fallback_driver.touch()
            matching_driver.touch()

            self.assertEqual(
                exporter.resolve_chrome_driver(str(fallback_driver), 131),
                str(matching_driver),
            )


class DriverRecoveryTests(unittest.TestCase):
    def test_detects_lost_webdriver_connection(self):
        self.assertTrue(exporter.is_webdriver_connection_lost(WebDriverException("connection lost")))
        self.assertFalse(exporter.is_webdriver_connection_lost(RuntimeError("other error")))

    def test_reconnect_delays_use_bounded_backoff(self):
        self.assertEqual(exporter.RECONNECT_DELAYS, (2, 5, 10))


class UploadResponseTests(unittest.TestCase):
    def test_parse_upload_response_accepts_success_code(self):
        self.assertEqual(
            exporter.parse_upload_response('{"code":200,"msg":"success"}'),
            {"code": 200, "msg": "success"},
        )


class AllShopsLauncherTests(unittest.TestCase):
    def test_launcher_runs_all_shops_for_the_interactively_entered_range(self):
        launcher = PROJECT_DIR / "run_all_shops.sh"

        self.assertTrue(launcher.is_file())
        content = launcher.read_text(encoding="utf-8")
        self.assertIn("ziniao_photo_export.py", content)
        self.assertIn("--all-shops", content)
        self.assertIn('--start-date "$START_DATE"', content)
        self.assertIn('--end-date "$END_DATE"', content)


if __name__ == "__main__":
    unittest.main()
