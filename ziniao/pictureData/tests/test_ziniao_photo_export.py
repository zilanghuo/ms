import sys
import unittest
import json
from datetime import date
from pathlib import Path
from unittest.mock import patch


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


class DownloadNamingTests(unittest.TestCase):
    def test_build_export_filename_uses_shop_account_and_compact_date(self):
        self.assertEqual(
            exporter.build_export_filename("1店", "已绑定账号", date(2026, 10, 4)),
            "1店-已绑定账号-20261004.xlsx",
        )


class UploadResponseTests(unittest.TestCase):
    def test_parse_upload_response_accepts_success_code(self):
        self.assertEqual(
            exporter.parse_upload_response('{"code":200,"msg":"success"}'),
            {"code": 200, "msg": "success"},
        )


if __name__ == "__main__":
    unittest.main()
