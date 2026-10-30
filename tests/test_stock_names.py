import csv
from pathlib import Path
import sys
import unittest

from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from stock_names import (
    clean_stock_name, normalize_stock_code, parse_cninfo_names,
    read_name_cache, resolve_stock_names,
)


class StockNamesTest(unittest.TestCase):
    def test_missing_markers_and_code_matching(self):
        for value in (None, float("nan"), "None", " null ", "<NA>", "待补充", ""):
            self.assertEqual(clean_stock_name(value), "")
        self.assertEqual(clean_stock_name(" 奥士康 "), "奥士康")
        self.assertEqual(normalize_stock_code("002913"), "002913.SZ")
        self.assertEqual(normalize_stock_code(" 688686.sh "), "688686.SH")
        self.assertEqual(normalize_stock_code("002913.SH"), "")
        self.assertEqual(normalize_stock_code("123"), "")

    def test_official_payload_validated(self):
        payload = {"stockList": [
            {"code": "688686", "zwjc": "奥普特", "category": "A股"},
            {"code": "002913", "zwjc": "奥士康", "category": "A股"},
            {"code": "111026", "zwjc": "派克转债", "category": "债券"},
        ]}
        self.assertEqual(parse_cninfo_names(payload), {"688686.SH": "奥普特", "002913.SZ": "奥士康"})
        with self.assertRaises(ValueError):
            parse_cninfo_names({"stockList": []})
        with self.assertRaises(ValueError):
            parse_cninfo_names({"stockList": [
                {"code": "002913", "zwjc": name, "category": "A股"}
                for name in ("奥士康", "错误名称")
            ]})

    def test_new_stock_resolved_only_by_code(self):
        rows = [
            {"name": "不能凭券名推测", "stock_code": "002913.SZ", "stock_name": "None"},
            {"stock_code": "688686.SH", "stock_name": "奥普特"},
        ]
        names, added, warning = resolve_stock_names(rows, {}, lambda: {"002913.SZ": "奥士康"})
        self.assertEqual(rows[0]["stock_name"], "奥士康")
        self.assertEqual(added, {"002913.SZ": "奥士康"})
        self.assertEqual(names["688686.SH"], "奥普特")
        self.assertFalse(warning)

    def test_complete_cache_skips_network_and_failure_stays_missing(self):
        def no_network():
            raise AssertionError("Complete cache must not use the network")
        rows = [{"stock_code": "002913.SZ", "stock_name": ""}]
        resolve_stock_names(rows, {"002913.SZ": "奥士康"}, no_network)
        self.assertEqual(rows[0]["stock_name"], "奥士康")
        def unavailable():
            raise OSError("offline")
        rows = [{"stock_code": "301571.SZ", "stock_name": ""}]
        _, added, warning = resolve_stock_names(rows, {}, unavailable)
        self.assertEqual(rows[0]["stock_name"], "")
        self.assertFalse(added)
        self.assertIn("补全失败", warning)
        _, _, warning = resolve_stock_names(rows, {}, None)
        self.assertFalse(warning)

    def test_published_data_has_no_missing_names(self):
        names = read_name_cache(ROOT / "data/stock_names.json")
        with (ROOT / "data/bonds.csv").open(encoding="utf-8-sig") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(len(rows), 312)
        for row in rows:
            self.assertTrue(clean_stock_name(row["stock_name"]), row["code"])
            self.assertEqual(row["stock_name"], names[row["stock_code"]])

    def test_missing_before_now_searchable_on_desktop_and_mobile(self):
        for mobile, stock_name, bond_code in (
            (False, "奥士康", "127117.SZ"),
            (True, "国科天成", "123286.SZ"),
        ):
            with self.subTest(mobile=mobile):
                app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=30)
                if mobile:
                    app.query_params["view"] = "mobile"
                app.run()
                app.text_input(key="mobile_query_filter" if mobile else "query_filter").set_value(stock_name).run()
                self.assertFalse(app.exception, [e.message for e in app.exception])
                tables = [table.value for table in app.dataframe if "正股名称" in table.value.columns]
                self.assertTrue(tables)
                table = tables[0]
                self.assertEqual(table["正股名称"].tolist(), [stock_name])
                if "转债代码" in table.columns:
                    self.assertEqual(table["转债代码"].tolist(), [bond_code])
                self.assertTrue(app.get("download_button"))
                if mobile:
                    next(r for r in app.radio if r.label == "明细展示").set_value("双列卡片").run()
                    self.assertFalse(app.exception)
                    self.assertTrue(any(stock_name in m.value and "mobile-bond-card" in m.value for m in app.markdown))


if __name__ == "__main__":
    unittest.main()
