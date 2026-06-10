"""图片转 PDF 处理核心。"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable, List, Tuple

import img2pdf

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}


def is_supported_image(path: Path) -> bool:
    return path.suffix.lower() in SUPPORTED_EXTENSIONS


def _natural_sort_key(path: Path) -> list:
    """自然排序：个人xxx1 < 个人xxx2 < 个人xxx10"""
    parts = re.split(r"(\d+)", path.name)
    return [int(part) if part.isdigit() else part.lower() for part in parts]


def collect_images(paths: Iterable[Path]) -> List[Path]:
    images: List[Path] = []
    for path in paths:
        if path.is_dir():
            for child in path.iterdir():
                if child.is_file() and is_supported_image(child):
                    images.append(child)
        elif path.is_file() and is_supported_image(path):
            images.append(path)
    images.sort(key=_natural_sort_key)
    return images


def save_images_as_pdf(image_paths: List[Path], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    pdf_bytes = img2pdf.convert([str(path) for path in image_paths])
    output_path.write_bytes(pdf_bytes)


def convert_files_to_pdf(
    input_paths: Iterable[Path],
    output_path: Path,
    merge: bool = True,
) -> Tuple[int, List[str]]:
    image_paths = collect_images(input_paths)
    if not image_paths:
        return 0, ["未找到可处理的图片文件"]

    errors: List[str] = []
    success = 0

    if merge:
        valid_paths: List[Path] = []
        for path in image_paths:
            try:
                # 提前验证可读性，避免部分成功时难以排查
                path.read_bytes()
                valid_paths.append(path)
                success += 1
            except OSError as exc:
                errors.append(f"{path.name}: {exc}")
        if valid_paths:
            save_images_as_pdf(valid_paths, output_path)
        return success, errors

    output_dir = output_path if output_path.suffix.lower() != ".pdf" else output_path.parent
    output_dir.mkdir(parents=True, exist_ok=True)

    for path in image_paths:
        try:
            target = output_dir / f"{path.stem}.pdf"
            save_images_as_pdf([path], target)
            success += 1
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{path.name}: {exc}")

    return success, errors
