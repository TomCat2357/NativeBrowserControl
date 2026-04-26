"""JSON Schema generation helpers for NativeBrowserDriver methods.

server.py から import される関心分離モジュール。inspect.Signature を
JSON Schema (object 型) に変換し、動的 MCP ツール登録に利用する。
"""

from __future__ import annotations

import inspect
import json
import logging
import typing
from collections.abc import Callable, Iterator
from typing import Any

logger = logging.getLogger(__name__)


_PRIMITIVE_MAP: dict[type, dict[str, Any]] = {
    str: {"type": "string"},
    int: {"type": "integer"},
    float: {"type": "number"},
    bool: {"type": "boolean"},
    bytes: {"type": "string", "contentEncoding": "base64"},
    type(None): {"type": "null"},
}


_STRING_ANNOTATION_FALLBACK: dict[str, type] = {
    "str": str,
    "int": int,
    "float": float,
    "bool": bool,
    "bytes": bytes,
    "None": type(None),
}


def python_type_to_json_schema(annotation: Any) -> dict[str, Any]:
    """Python の型注釈を JSON Schema 断片に変換する。

    解決不能/未注釈の場合は ``{}`` (= 任意型) を返す。
    """
    if annotation is inspect.Parameter.empty or annotation is Any:
        return {}

    if isinstance(annotation, str):
        fallback = _STRING_ANNOTATION_FALLBACK.get(annotation.strip())
        if fallback is not None:
            return python_type_to_json_schema(fallback)
        return {}

    if isinstance(annotation, type) and annotation in _PRIMITIVE_MAP:
        return dict(_PRIMITIVE_MAP[annotation])

    origin = typing.get_origin(annotation)
    args = typing.get_args(annotation)

    if origin is None:
        return {}

    if origin is typing.Union:
        non_none = [a for a in args if a is not type(None)]
        has_none = len(non_none) != len(args)
        if len(non_none) == 1:
            sub = python_type_to_json_schema(non_none[0])
            if has_none and sub:
                return {"oneOf": [sub, {"type": "null"}]}
            return sub
        sub_schemas = [python_type_to_json_schema(a) for a in non_none]
        sub_schemas = [s for s in sub_schemas if s]
        if has_none:
            sub_schemas.append({"type": "null"})
        return {"oneOf": sub_schemas} if sub_schemas else {}

    origin_name = getattr(origin, "__name__", "")
    if origin in (list, tuple, set, frozenset) or origin_name in {
        "Iterable",
        "Sequence",
        "Collection",
        "MutableSequence",
        "List",
        "Tuple",
        "Set",
        "FrozenSet",
    }:
        out: dict[str, Any] = {"type": "array"}
        if args:
            item_schema = python_type_to_json_schema(args[0])
            if item_schema:
                out["items"] = item_schema
        return out

    if origin is dict or origin_name in {"Dict", "Mapping", "MutableMapping"}:
        return {"type": "object"}

    if origin is typing.Literal:
        if all(isinstance(a, str) for a in args):
            return {"type": "string", "enum": list(args)}
        if all(isinstance(a, bool) for a in args):
            return {"type": "boolean", "enum": list(args)}
        if all(isinstance(a, int) for a in args):
            return {"type": "integer", "enum": list(args)}
        return {"enum": list(args)}

    return {}


def signature_to_input_schema(
    sig: inspect.Signature,
    *,
    type_hints: dict[str, Any] | None = None,
    inject: dict[str, dict[str, Any]] | None = None,
    inject_required: list[str] | None = None,
    drop_params: set[str] | None = None,
) -> dict[str, Any]:
    """``inspect.Signature`` を JSON Schema (object) に変換する。

    Parameters
    ----------
    sig:
        対象シグネチャ。
    type_hints:
        ``typing.get_type_hints`` で解決済みの型ヒント辞書。指定時は
        ``param.annotation`` よりも優先する。``from __future__ import annotations``
        で文字列化された注釈に対処するために使用する。
    inject:
        ``properties`` に追加注入するエントリ (例: ``session_id`` / ``browser``)。
        既に同名の実引数があれば上書きしない。
    inject_required:
        ``required`` に追加するキー名のリスト。``properties`` に含まれているもののみ採用。
    drop_params:
        無視するパラメータ名 (通常 ``{"self"}``)。
    """

    drop = drop_params or set()
    hints = type_hints or {}
    properties: dict[str, Any] = {}
    required: list[str] = []

    for name, param in sig.parameters.items():
        if name in drop:
            continue
        if param.kind in (
            inspect.Parameter.VAR_POSITIONAL,
            inspect.Parameter.VAR_KEYWORD,
        ):
            continue

        annotation = hints.get(name, param.annotation)
        prop_schema = python_type_to_json_schema(annotation)

        if param.default is inspect.Parameter.empty:
            required.append(name)
        else:
            try:
                json.dumps(param.default)
                prop_schema = dict(prop_schema)
                prop_schema["default"] = param.default
            except (TypeError, ValueError):
                pass

        properties[name] = prop_schema

    if inject:
        for k, v in inject.items():
            if k not in properties:
                properties[k] = v

    if inject_required:
        for k in inject_required:
            if k in properties and k not in required:
                required.append(k)

    schema: dict[str, Any] = {"type": "object", "properties": properties}
    if required:
        schema["required"] = required
    return schema


def iter_driver_methods(cls: type) -> Iterator[tuple[str, Callable[..., Any]]]:
    """``NativeBrowserDriver.tool_info`` と同じ規約で公開メソッドを列挙する。

    private prefix / property / classmethod を除外する。
    """
    for name in sorted(dir(cls)):
        if name.startswith("_"):
            continue
        raw = inspect.getattr_static(cls, name)
        if isinstance(raw, (property, classmethod)):
            continue
        member = getattr(cls, name)
        if not callable(member):
            continue
        yield name, member
