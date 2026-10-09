import sys
import unittest
import json
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, patch


PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))

import ziniao_photo_export as exporter


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

    @patch.object(exporter, "ziniao_call")
    def test_stop_browser_uses_official_stop_action(self, mock_ziniao_call):
        credentials = {"company": "company", "username": "user", "password": "password"}
        exporter.stop_browser("http://127.0.0.1:18888", credentials, "shop-1")
        mock_ziniao_call.assert_called_once_with(
            "http://127.0.0.1:18888", credentials, "stopBrowser", browserId="shop-1"
        )


class DownloadNamingTests(unittest.TestCase):
    def test_build_export_filename_uses_shop_account_and_compact_date(self):
        self.assertEqual(
            exporter.build_export_filename("1店", "已绑定账号", date(2026, 10, 4)),
            "1店-已绑定账号-20261004.xlsx",
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

    def test_all_shops_rejects_single_shop_arguments(self):
        with self.assertRaisesRegex(ValueError, "--all-shops"):
            exporter.validate_shop_arguments(True, "shop-id", None, None)

    @patch.object(exporter, "stop_browser")
    @patch.object(exporter, "set_date_range", side_effect=RuntimeError("导出失败"))
    @patch.object(exporter, "attach_driver")
    @patch.object(exporter, "start_browser", return_value=9222)
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


class UploadResponseTests(unittest.TestCase):
    def test_parse_upload_response_accepts_success_code(self):
        self.assertEqual(
            exporter.parse_upload_response('{"code":200,"msg":"success"}'),
            {"code": 200, "msg": "success"},
        )


if __name__ == "__main__":
    unittest.main()
