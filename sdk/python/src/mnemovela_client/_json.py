from __future__ import annotations

from typing import Any

from mnemovela_client._generated import mnemovela_v1_pb2 as pb


def to_value(obj: Any) -> "pb.Value":
    v = pb.Value()
    if isinstance(obj, bool):
        v.bool_value = obj
    elif isinstance(obj, (int, float)):
        v.number_value = float(obj)
    elif isinstance(obj, str):
        v.string_value = obj
    elif isinstance(obj, dict):
        for k, item in obj.items():
            v.struct_value.fields[k].CopyFrom(to_value(item))
    elif isinstance(obj, (list, tuple)):
        for item in obj:
            v.list_value.values.add().CopyFrom(to_value(item))
    elif obj is None:
        v.string_value = ""
    else:
        raise TypeError(f"unsupported payload type: {type(obj)!r}")
    return v


def from_value(v: "pb.Value") -> Any:
    kind = v.WhichOneof("kind")
    if kind == "string_value":
        return v.string_value
    if kind == "number_value":
        return v.number_value
    if kind == "bool_value":
        return v.bool_value
    if kind == "struct_value":
        return {k: from_value(val) for k, val in v.struct_value.fields.items()}
    if kind == "list_value":
        return [from_value(item) for item in v.list_value.values]
    return None


def to_value_map(d: dict[str, Any]) -> dict[str, "pb.Value"]:
    return {k: to_value(val) for k, val in d.items()}


def from_value_map(m) -> dict[str, Any]:
    return {k: from_value(v) for k, v in m.items()}
