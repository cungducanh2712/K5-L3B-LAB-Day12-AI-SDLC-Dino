"""File kho v1.2: {"items": [{"id": str, "kind": str, "fresh": float}]}.

Đọc: từ chối sai schema / id lạ / kind lạ / fresh ngoài [0, 100] / file kho đếm v1.0 (BadInput -> mã 2).
Ghi: qua file tạm cùng thư mục rồi thay thế nguyên tử, byte-ổn-định theo id.
"""

import json
import os
import tempfile

from .errors import BadInput
from .ids import sort_by_id

KINDS_P1 = ("ca_loc", "ca_linh", "bong_dien_dien", "bong_sung", "ca_keo", "keo_neo")


def validate_items(items, kinds=KINDS_P1):
    if not isinstance(items, dict):
        raise BadInput("items phải là object")
    out = {}
    for k, v in items.items():
        if k not in kinds:
            raise BadInput(f"nguyên liệu lạ: {k}")
        if isinstance(v, bool) or not isinstance(v, int) or v < 0:
            raise BadInput(f"số lượng không hợp lệ cho {k}: {v!r}")
        if v > 0:
            out[k] = v
    return out


def validate_item_list(items, kinds=KINDS_P1):
    """Kiểm tra và chuẩn hóa mảng cá thể."""
    if not isinstance(items, list):
        raise BadInput("items phải là mảng cá thể")
    seen_ids = set()
    out = []
    for it in items:
        if not isinstance(it, dict):
            raise BadInput("mỗi cá thể trong items phải là object")
        iid = it.get("id")
        kind = it.get("kind")
        fresh = it.get("fresh")
        if not isinstance(iid, str) or not iid:
            raise BadInput("id cá thể phải là chuỗi khác rỗng")
        if iid in seen_ids:
            raise BadInput(f"trùng id cá thể: {iid}")
        seen_ids.add(iid)
        if kind not in kinds:
            raise BadInput(f"nguyên liệu lạ: {kind}")
        if isinstance(fresh, bool) or not isinstance(fresh, (int, float)):
            raise BadInput(f"độ tươi không hợp lệ: {fresh!r}")
        if not (0.0 <= fresh <= 100.0):
            raise BadInput(f"độ tươi ngoài miền [0, 100]: {fresh}")
        out.append({
            "id": iid,
            "kind": kind,
            "fresh": float(fresh)
        })
    return sort_by_id(out)


def read_inventory(path: str, kinds=KINDS_P1) -> list:
    """Đọc file kho cá thể theo contract v1.2. Trả về list các dict {id, kind, fresh}."""
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError) as e:
        raise BadInput(f"không đọc được file kho {path}: {e}")
    if not isinstance(data, dict) or set(data.keys()) != {"items"}:
        raise BadInput("file kho chỉ được có khóa gốc 'items'")
    return validate_item_list(data["items"], kinds)


def write_inventory(path: str, items: list):
    """Ghi file kho cá thể theo contract v1.2 nguyên tử bằng file tạm."""
    if not isinstance(items, list):
        raise BadInput("items phải là list")
    clean_items = sort_by_id([
        {
            "id": it["id"],
            "kind": it["kind"],
            "fresh": float(it["fresh"])
        }
        for it in items
    ])
    d = os.path.dirname(os.path.abspath(path))
    fd, tmp = tempfile.mkstemp(prefix=".inv-", suffix=".tmp", dir=d)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            json.dump({"items": clean_items}, f, ensure_ascii=False, separators=(",", ":"))
            f.write("\n")
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise
