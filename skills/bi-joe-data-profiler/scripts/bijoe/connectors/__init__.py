"""Connector registry.

Built-in connectors register themselves with @register. Third-party packages can
add connectors without touching this repo by declaring an entry point:

    [project.entry-points."bijoe.connectors"]
    oracle = "my_package.oracle:OracleConnector"
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Type

from .base import ColumnInfo, Connector, ConnectorError, TableInfo

__all__ = [
    "ColumnInfo",
    "Connector",
    "ConnectorError",
    "TableInfo",
    "register",
    "available",
    "get",
    "resolve",
    "open_connector",
    "plugin_errors",
]

_REGISTRY: Dict[str, Type[Connector]] = {}
_PLUGIN_ERRORS: Dict[str, str] = {}
_loaded = False


def register(cls: Type[Connector]) -> Type[Connector]:
    if not cls.name:
        raise ValueError(f"{cls.__name__} must set a `name`")
    _REGISTRY[cls.name] = cls
    return cls


def _entry_points():
    try:
        from importlib.metadata import entry_points
    except ImportError:  # pragma: no cover
        return []
    try:
        return list(entry_points(group="bijoe.connectors"))
    except TypeError:  # Python 3.9
        return list(entry_points().get("bijoe.connectors", []))


def _ensure_loaded() -> None:
    global _loaded
    if _loaded:
        return
    _loaded = True
    from . import csv_files, excel, sqlalchemy_db, sqlite  # noqa: F401  (registers built-ins)

    for ep in _entry_points():
        try:
            register(ep.load())
        except Exception as exc:  # a broken plugin must not break the tool
            _PLUGIN_ERRORS[ep.name] = f"{type(exc).__name__}: {exc}"


def available() -> List[Type[Connector]]:
    _ensure_loaded()
    return sorted(_REGISTRY.values(), key=lambda c: (c.priority, c.name))


def plugin_errors() -> Dict[str, str]:
    _ensure_loaded()
    return dict(_PLUGIN_ERRORS)


def get(name: str) -> Type[Connector]:
    _ensure_loaded()
    try:
        return _REGISTRY[name]
    except KeyError:
        names = ", ".join(sorted(_REGISTRY))
        raise ConnectorError(f"Unknown connector '{name}'. Available: {names}") from None


def resolve(source: str, name: Optional[str] = None) -> Type[Connector]:
    if name:
        return get(name)
    for cls in available():
        try:
            if cls.can_handle(source):
                return cls
        except Exception:
            continue
    raise ConnectorError(
        f"No connector recognises '{source}'. Give a CSV file or folder, an .xlsx file, "
        "a SQLite file, or a database URL. Run `bijoe connectors` to see what is supported."
    )


def open_connector(source: str, name: Optional[str] = None, **options: Any) -> Connector:
    cls = resolve(source, name)
    missing = cls.missing_requirements()
    if missing:
        hint = cls.install_hint or " ".join(missing)
        raise ConnectorError(f"The '{cls.name}' connector needs extra packages: pip install {hint}")
    return cls(source, **options)
