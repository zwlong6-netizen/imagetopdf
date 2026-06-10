#!/usr/bin/env python3
"""命令行：图片转 PDF。"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from processor import collect_images, convert_files_to_pdf


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="将图片直接转换为 PDF",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  ImageToPDF.exe 图片.jpg
  ImageToPDF.exe 图片.jpg -o 输出.pdf
  ImageToPDF.exe ./照片文件夹 -o 合并.pdf
  ImageToPDF.exe ./照片文件夹 --separate -o ./输出目录
        """,
    )
    parser.add_argument("input", nargs="+", help="输入图片或文件夹，可多个")
    parser.add_argument("-o", "--output", help="输出 PDF 路径或输出目录")
    parser.add_argument("--separate", action="store_true", help="每张图单独输出 PDF")
    return parser


def resolve_output(inputs: list[Path], output: str | None, separate: bool) -> Path:
    if output:
        return Path(output)
    if separate:
        if len(inputs) == 1 and inputs[0].is_dir():
            return inputs[0]
        return Path.cwd()
    if len(inputs) == 1 and inputs[0].is_file():
        return inputs[0].with_suffix(".pdf")
    return Path.cwd() / "输出.pdf"


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

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

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
