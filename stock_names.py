"""Code-keyed stock names. Network lookup is for data updates, never page loads."""

import json
from pathlib import Path
import re
from urllib.request import Request, urlopen


CNINFO_NAMES_URL = "https://www.cninfo.com.cn/new/data/szse_stock.json"
MISSING_NAME = "待补充"
EMPTY_NAMES = {"", "none", "nan", "null", "<na>", "nat", "—", "--", MISSING_NAME}


def clean_stock_name(value):
    if value is None:
        return ""
    text = str(value).strip()
    return "" if text.lower() in EMPTY_NAMES else text


def normalize_stock_code(value):
    text = str(value).strip().upper()
    match = re.fullmatch(r"([036]\d{5})(?:\.(SH|SZ))?", text)
    if not match:
        return ""
    digits, suffix = match.groups()
    exchange = "SH" if digits.startswith("6") else "SZ"
    if suffix and suffix != exchange:
        return ""
    return f"{digits}.{exchange}"


def read_name_cache(path):
    path = Path(path)
    if not path.exists():
        return {}
    entries = json.loads(path.read_text(encoding="utf-8")).get("names", {})
    return {
        code: name
        for raw_code, raw_name in entries.items()
        if (code := normalize_stock_code(raw_code))
        and (name := clean_stock_name(raw_name))
    }


def parse_cninfo_names(payload):
    rows = payload.get("stockList")
    if not isinstance(rows, list) or not rows:
        raise ValueError("巨潮证券名称接口未返回有效列表")
    names = {}
    for row in rows:
        if row.get("category") != "A股":
            continue
        code = normalize_stock_code(row.get("code"))
        name = clean_stock_name(row.get("zwjc"))
        if code and name:
            if code in names and names[code] != name:
                raise ValueError(f"巨潮同一证券代码返回不同名称：{code}")
            names[code] = name
    if not names:
        raise ValueError("巨潮列表未包含可用 A 股代码与名称")
    return names


def fetch_cninfo_names():
    request = Request(CNINFO_NAMES_URL, headers={"User-Agent": "HuataiCB-data-update/1.0"})
    with urlopen(request, timeout=15) as response:
        payload = json.load(response)
    return parse_cninfo_names(payload)


def resolve_stock_names(bonds, known_names, fetcher=None):
    """Preserve known names and fill only missing code matches; never guess by bond name."""
    names = dict(known_names)
    for bond in bonds:
        code = normalize_stock_code(bond.get("stock_code"))
        name = clean_stock_name(bond.get("stock_name"))
        if code and name:
            names[code] = name
    missing = {
        normalize_stock_code(bond.get("stock_code"))
        for bond in bonds
        if not names.get(normalize_stock_code(bond.get("stock_code")))
    }
    resolved = {}
    warning = ""
    if missing and fetcher is not None:
        try:
            remote = fetcher()
            resolved = {code: remote[code] for code in missing if code and remote.get(code)}
            names.update(resolved)
        except (OSError, ValueError, TimeoutError) as error:
            warning = f"正股名称在线补全失败（{type(error).__name__}），已保留原映射并列出缺失项。"
    for bond in bonds:
        bond["stock_name"] = names.get(normalize_stock_code(bond.get("stock_code")), "")
    return names, resolved, warning
