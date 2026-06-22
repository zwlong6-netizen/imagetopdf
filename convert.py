#!/usr/bin/env python3
"""图片转 PDF：无参数启动图形界面，有参数走命令行。"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from processor import (
    collect_images,
    convert_files_to_pdf,
    convert_folders_to_pdf,
    merge_pdfs,
    resolve_merge_output,
    resolve_output,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="将图片转换为 PDF，或合并多个 PDF",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  ImageToPDF.exe
  ImageToPDF.exe 图片.jpg
  ImageToPDF.exe 图片.jpg -o 输出.pdf
  ImageToPDF.exe ./照片文件夹 -o 合并.pdf
  ImageToPDF.exe ./照片文件夹 --separate -o ./输出目录
  ImageToPDF.exe ./文件夹A ./文件夹B ./文件夹C
  ImageToPDF.exe --merge-pdf 文件1.pdf 文件2.pdf -o 合并.pdf
        """,
    )
    parser.add_argument("input", nargs="*", help="输入图片、文件夹或 PDF 文件")
    parser.add_argument("-o", "--output", help="输出 PDF 路径或输出目录")
    parser.add_argument("--separate", action="store_true", help="每张图单独输出 PDF")
    parser.add_argument("--merge-pdf", action="store_true", help="合并多个 PDF 文件")
    return parser


def cli_main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.merge_pdf:
        return _cli_merge_pdfs(args)

    inputs = [Path(p) for p in args.input]
    for path in inputs:
        if not path.exists():
            print(f"错误: 路径不存在 -> {path}", file=sys.stderr)
            return 1

    all_dirs = all(path.is_dir() for path in inputs)
    if all_dirs and len(inputs) >= 1 and not args.output and not args.separate:
        return _cli_convert_folders(inputs)

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


def _cli_convert_folders(folders: list[Path]) -> int:
    print(f"共 {len(folders)} 个文件夹，开始转换...")
    folder_count, image_count, errors, outputs = convert_folders_to_pdf(folders)

    if folder_count == 0:
        print("转换失败:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        if not sys.stdout.isatty():
            _show_cli_error_dialog(errors)
        return 1

    print(f"完成: 成功 {folder_count} 个文件夹，共 {image_count} 张图片")
    for output in outputs:
        print(f"  输出: {output.resolve()}")

    if errors:
        print(f"警告: {len(errors)} 条", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)

    if not sys.stdout.isatty():
        _show_cli_folders_result_dialog(folder_count, image_count, errors, outputs)

    return 0


def _cli_merge_pdfs(args: argparse.Namespace) -> int:
    inputs = [Path(p) for p in args.input]
    if len(inputs) < 2:
        print("错误: 合并 PDF 至少需要 2 个文件", file=sys.stderr)
        return 1

    for path in inputs:
        if not path.exists():
            print(f"错误: 路径不存在 -> {path}", file=sys.stderr)
            return 1
        if path.suffix.lower() != ".pdf":
            print(f"错误: 不是 PDF 文件 -> {path}", file=sys.stderr)
            return 1

    output = resolve_merge_output(inputs, args.output)
    print(f"共 {len(inputs)} 个 PDF，开始合并...")
    count, errors = merge_pdfs(inputs, output)

    if count == 0:
        print("合并失败:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        if not sys.stdout.isatty():
            _show_cli_error_dialog(errors)
        return 1

    print(f"完成: 成功合并 {count} 个 PDF")
    print(f"输出文件: {output.resolve()}")

    if errors:
        print(f"警告: {len(errors)} 个文件失败", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)

    if not sys.stdout.isatty():
        _show_cli_merge_result_dialog(count, errors, output)

    return 0


def _show_cli_folders_result_dialog(
    folder_count: int,
    image_count: int,
    errors: list[str],
    outputs: list[Path],
) -> None:
    import tkinter as tk
    from tkinter import messagebox

    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)

    detail = ""
    if len(outputs) == 1:
        detail = f"输出文件：\n{outputs[0].resolve()}"
    elif outputs:
        detail = "输出文件：\n" + "\n".join(str(p.resolve()) for p in outputs)
    if errors:
        detail += f"\n\n有 {len(errors)} 条警告。"

    messagebox.showinfo(
        "转换完成",
        f"已成功转换 {folder_count} 个文件夹，共 {image_count} 张图片。\n\n{detail}",
    )
    root.destroy()


def _show_cli_merge_result_dialog(count: int, errors: list[str], output: Path) -> None:
    import tkinter as tk
    from tkinter import messagebox

    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)

    detail = f"输出文件：\n{output.resolve()}"
    if errors:
        detail += f"\n\n有 {len(errors)} 个 PDF 失败。"

    messagebox.showinfo("合并完成", f"已成功合并 {count} 个 PDF。\n\n{detail}")
    root.destroy()


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
