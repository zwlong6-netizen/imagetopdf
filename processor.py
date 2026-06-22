"""图片转 PDF 与 PDF 合并处理核心。"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable, List, Tuple

import img2pdf
from pypdf import PdfReader, PdfWriter

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}


def is_supported_image(path: Path) -> bool:
    return path.suffix.lower() in SUPPORTED_EXTENSIONS


def should_collect_file(path: Path) -> bool:
    """文件夹扫描时只收集图片，PDF 等非图片文件直接忽略。"""
    if path.suffix.lower() == ".pdf":
        return False
    return is_supported_image(path)


def _natural_sort_key(path: Path) -> list:
    """自然排序：个人xxx1 < 个人xxx2 < 个人xxx10"""
    parts = re.split(r"(\d+)", path.name)
    return [int(part) if part.isdigit() else part.lower() for part in parts]


def collect_images(paths: Iterable[Path]) -> List[Path]:
    images: List[Path] = []
    for path in paths:
        if path.is_dir():
            for child in path.iterdir():
                if child.is_file() and should_collect_file(child):
                    images.append(child)
        elif path.is_file() and should_collect_file(path):
            images.append(path)
    images.sort(key=_natural_sort_key)
    return images


def save_images_as_pdf(image_paths: List[Path], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    pdf_bytes = img2pdf.convert([str(path) for path in image_paths])
    output_path.write_bytes(pdf_bytes)


def resolve_folder_output(folder: Path) -> Path:
    """单个文件夹的输出 PDF 路径（保存在文件夹的上级目录）。"""
    return folder.parent / f"{folder.name}.pdf"


def resolve_output(inputs: list[Path], output: str | None, separate: bool) -> Path:
    if output:
        return Path(output)
    if len(inputs) == 1 and inputs[0].is_file():
        return inputs[0].with_suffix(".pdf")
    if len(inputs) == 1 and inputs[0].is_dir():
        folder = inputs[0]
        if separate:
            return folder
        return resolve_folder_output(folder)
    if separate:
        return Path.cwd()
    return Path.cwd() / "输出.pdf"


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


def convert_folders_to_pdf(
    folders: Iterable[Path],
) -> Tuple[int, int, List[str], List[Path]]:
    """将多个文件夹各自合并为 PDF，保存在各文件夹的上级目录。

    Returns:
        (成功文件夹数, 总图片数, 错误列表, 输出文件列表)
    """
    folder_success = 0
    total_images = 0
    errors: List[str] = []
    outputs: List[Path] = []

    for folder in folders:
        if not folder.is_dir():
            errors.append(f"{folder}: 不是文件夹")
            continue

        images = collect_images([folder])
        if not images:
            errors.append(f"{folder.name}: 未找到图片")
            continue

        output = resolve_folder_output(folder)
        count, folder_errors = convert_files_to_pdf([folder], output, merge=True)
        if count == 0:
            for err in folder_errors:
                errors.append(f"{folder.name}: {err}")
            continue

        folder_success += 1
        total_images += count
        outputs.append(output)
        for err in folder_errors:
            errors.append(f"{folder.name}: {err}")

    return folder_success, total_images, errors, outputs


def is_pdf(path: Path) -> bool:
    return path.suffix.lower() == ".pdf"


def resolve_merge_output(pdf_paths: list[Path], output: str | None) -> Path:
    if output:
        return Path(output)
    if len(pdf_paths) == 1:
        return pdf_paths[0].with_name(f"{pdf_paths[0].stem}_合并.pdf")
    return pdf_paths[0].parent / "合并.pdf"


def merge_pdfs(pdf_paths: List[Path], output_path: Path) -> Tuple[int, List[str]]:
    writer = PdfWriter()
    success = 0
    errors: List[str] = []

    for path in pdf_paths:
        try:
            reader = PdfReader(str(path))
            for page in reader.pages:
                writer.add_page(page)
            success += 1
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{path.name}: {exc}")

    if success == 0:
        return 0, errors

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("wb") as handle:
        writer.write(handle)

    return success, errors
