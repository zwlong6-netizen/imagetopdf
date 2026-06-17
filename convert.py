#!/usr/bin/env python3
"""图片转 PDF：无参数启动图形界面，有参数走命令行。"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from processor import collect_images, convert_files_to_pdf, resolve_output


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="将图片直接转换为 PDF",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  ImageToPDF.exe
  ImageToPDF.exe 图片.jpg
  ImageToPDF.exe 图片.jpg -o 输出.pdf
  ImageToPDF.exe ./照片文件夹 -o 合并.pdf
  ImageToPDF.exe ./照片文件夹 --separate -o ./输出目录
        """,
    )
    parser.add_argument("input", nargs="*", help="输入图片或文件夹，可多个")
    parser.add_argument("-o", "--output", help="输出 PDF 路径或输出目录")
    parser.add_argument("--separate", action="store_true", help="每张图单独输出 PDF")
    return parser


def cli_main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    inputs = [Path(p) for p in args.input]
    for path in inputs:
        if not path.exists():
            print(f"错误: 路径不存在 -> {path}", file=sys.stderr)
            return 1

    images = collect_images(inputs)
    if not images:
        print("错误: 未找到可处理的图片文件", file=sys.stderr)
        return 1

    output = resolve_output(inputs, args.output, args.separate)

    print(f"共 {len(images)} 张图片，开始转换...")
    count, errors = convert_files_to_pdf(inputs, output, merge=not args.separate)

    if count == 0:
        print("转换失败:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        if not sys.stdout.isatty():
            _show_cli_error_dialog(errors)
        return 1

    mode = "单独输出" if args.separate else "合并输出"
    print(f"完成: 成功 {count} 张 ({mode})")
    if args.separate:
        print(f"输出目录: {output.resolve()}")
    else:
        print(f"输出文件: {output.resolve()}")

    if errors:
        print(f"警告: {len(errors)} 张失败", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)

    if not sys.stdout.isatty():
        _show_cli_result_dialog(count, errors, output, args.separate)

    return 0


def _show_cli_error_dialog(errors: list[str]) -> None:
    import tkinter as tk
    from tkinter import messagebox

    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    messagebox.showerror("转换失败", "\n".join(errors) if errors else "未知错误")
    root.destroy()


def _show_cli_result_dialog(
    count: int,
    errors: list[str],
    output: Path,
    separate: bool,
) -> None:
    import tkinter as tk
    from tkinter import messagebox

    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)

    if separate:
        detail = f"输出目录：\n{output.resolve()}"
    else:
        detail = f"输出文件：\n{output.resolve()}"

    if errors:
        detail += f"\n\n有 {len(errors)} 张图片失败。"

    messagebox.showinfo("转换完成", f"已成功转换 {count} 张图片。\n\n{detail}")
    root.destroy()


def main() -> int:
    if len(sys.argv) == 1:
        from gui import main as gui_main

        gui_main()
        return 0
    return cli_main()


if __name__ == "__main__":
    raise SystemExit(main())
