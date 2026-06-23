"""跨平台文件夹选择对话框。"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from tkinter import filedialog
from typing import Any


def pick_folders(title: str = "选择文件夹", parent: Any | None = None) -> list[Path]:
    if sys.platform == "win32":
        paths = _pick_folders_windows(title, parent)
    elif sys.platform == "linux":
        paths = _pick_folders_linux(title, parent)
    else:
        paths = _pick_folders_tk(title, parent)

    return [Path(p) for p in paths if p]


def pick_subfolders(title: str = "选择上级目录", parent: Any | None = None) -> list[Path] | None:
    """选择上级目录，返回其下所有直接子文件夹；取消选择时返回 None。"""
    selected = _pick_single_folder(title, parent)
    if selected is None:
        return None

    return sorted(
        [path for path in selected.iterdir() if path.is_dir()],
        key=lambda path: path.name.lower(),
    )


def _pick_single_folder(title: str, parent: Any | None = None) -> Path | None:
    selected = filedialog.askdirectory(title=title, parent=parent)
    return Path(selected) if selected else None


def _pick_folders_tk(title: str, parent: Any | None = None) -> list[str]:
    selected = _pick_single_folder(title, parent)
    return [str(selected)] if selected else []


def _pick_folders_linux(title: str, parent: Any | None = None) -> list[str]:
    try:
        result = subprocess.run(
            ["zenity", "--file-selection", "--directory", "--multiple", f"--title={title}"],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        return _pick_folders_tk(title, parent)

    if result.returncode != 0:
        return []
    return [part for part in result.stdout.strip().split("|") if part]


def _pick_folders_windows(title: str, parent: Any | None = None) -> list[str]:
    try:
        paths = _pick_folders_windows_dialog(title, parent)
        if paths:
            return paths
    except Exception:
        pass
    return _pick_folders_tk(title, parent)


def _pick_folders_windows_dialog(title: str, parent: Any | None = None) -> list[str]:
    import ctypes
    from ctypes import POINTER, Structure, byref, c_int, c_uint, c_void_p, cast, windll
    from ctypes.wintypes import HWND, LPWSTR

    class GUID(Structure):
        _fields_ = [
            ("Data1", c_uint),
            ("Data2", c_uint),
            ("Data3", c_uint),
            ("Data4", c_uint * 2),
        ]

    def guid_from_string(value: str) -> GUID:
        import uuid

        u = uuid.UUID(value)
        data4 = (c_uint * 2)(int.from_bytes(u.bytes[8:12], "little"), int.from_bytes(u.bytes[12:16], "little"))
        return GUID(u.time_low, u.time_mid, u.time_hi_version, data4)

    CLSID_FileOpenDialog = guid_from_string("{DC1C5A9C-E88A-4dde-B5A1-60F82A20AEF7}")
    IID_IFileOpenDialog = guid_from_string("{D57C7288-D4AD-4768-BE02-9D96953223E6}")

    CLSCTX_INPROC_SERVER = 0x1
    FOS_PICKFOLDERS = 0x20
    FOS_ALLOWMULTISELECT = 0x200
    FOS_PATHMUSTEXIST = 0x800
    SIGDN_FILESYSPATH = 0x80058000
    S_OK = 0

    ole32 = windll.ole32
    ole32.CoInitialize(None)

    dialog = c_void_p()
    try:
        hr = ole32.CoCreateInstance(
            byref(CLSID_FileOpenDialog),
            None,
            CLSCTX_INPROC_SERVER,
            byref(IID_IFileOpenDialog),
            byref(dialog),
        )
        if hr != S_OK:
            return []

        vtable = cast(dialog, POINTER(c_void_p))[0]
        methods = cast(vtable, POINTER(c_void_p))

        SetOptions = ctypes.WINFUNCTYPE(c_int, c_void_p, c_uint)(methods[10])
        Show = ctypes.WINFUNCTYPE(c_int, c_void_p, HWND)(methods[3])
        GetResults = ctypes.WINFUNCTYPE(c_int, c_void_p, POINTER(c_void_p))(methods[27])
        SetTitle = ctypes.WINFUNCTYPE(c_int, c_void_p, LPWSTR)(methods[17])

        options = FOS_PICKFOLDERS | FOS_ALLOWMULTISELECT | FOS_PATHMUSTEXIST
        if SetOptions(dialog, options) != S_OK:
            return []
        if title:
            SetTitle(dialog, title)

        owner = HWND(parent.winfo_id()) if parent is not None else HWND(0)
        if Show(dialog, owner) != S_OK:
            return []

        items = c_void_p()
        if GetResults(dialog, byref(items)) != S_OK:
            return []

        items_vtable = cast(items, POINTER(c_void_p))[0]
        items_methods = cast(items_vtable, POINTER(c_void_p))
        GetCount = ctypes.WINFUNCTYPE(c_int, c_void_p, POINTER(c_uint))(items_methods[3])
        GetItemAt = ctypes.WINFUNCTYPE(c_int, c_void_p, c_uint, POINTER(c_void_p))(items_methods[4])

        count = c_uint()
        if GetCount(items, byref(count)) != S_OK:
            return []

        paths: list[str] = []
        for index in range(count.value):
            item = c_void_p()
            if GetItemAt(items, index, byref(item)) != S_OK:
                continue

            item_vtable = cast(item, POINTER(c_void_p))[0]
            item_methods = cast(item_vtable, POINTER(c_void_p))
            GetDisplayName = ctypes.WINFUNCTYPE(c_int, c_void_p, c_uint, POINTER(LPWSTR))(item_methods[5])

            name = LPWSTR()
            if GetDisplayName(item, SIGDN_FILESYSPATH, byref(name)) != S_OK:
                continue
            if name.value:
                paths.append(name.value)
            windll.ole32.CoTaskMemFree(name)

        return paths
    finally:
        ole32.CoUninitialize()
