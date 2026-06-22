"""图片转 PDF / PDF 合并图形界面。"""

from __future__ import annotations

import os
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from folder_picker import pick_folders, pick_subfolders
from processor import (
    convert_folders_to_pdf,
    merge_pdfs,
    resolve_folder_output,
    resolve_merge_output,
)

PDF_TYPES = [
    ("PDF 文件", "*.pdf"),
    ("所有文件", "*.*"),
]


class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("图片转 PDF")
        self.geometry("600x520")
        self.minsize(520, 420)
        self.resizable(True, True)

        self.output_preview = tk.StringVar(value="添加文件夹后显示输出位置")
        self._busy = False

        self._folder_paths: list[Path] = []
        self._pdf_paths: list[Path] = []
        self.merge_output_preview = tk.StringVar(value="添加 PDF 文件后显示输出位置")

        self._build_ui()

    def _build_ui(self) -> None:
        padding = {"padx": 16, "pady": 6}

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=16, pady=(16, 0))

        image_tab = ttk.Frame(notebook, padding=4)
        merge_tab = ttk.Frame(notebook, padding=4)
        notebook.add(image_tab, text="图片转 PDF")
        notebook.add(merge_tab, text="PDF 合并")

        self._build_image_tab(image_tab, padding)
        self._build_merge_tab(merge_tab, padding)

        status_frame = ttk.LabelFrame(self, text="状态", padding=12)
        status_frame.pack(fill="both", expand=True, **padding)

        self.log = tk.Text(status_frame, height=8, wrap="word", state="disabled")
        self.log.pack(fill="both", expand=True)
        self._append_log("欢迎使用。可在「图片转 PDF」或「PDF 合并」标签页中操作。")

    def _build_image_tab(self, parent: ttk.Frame, padding: dict) -> None:
        hint = ttk.Label(
            parent,
            text="可一次多选多个文件夹；也可选择上级目录批量添加其下全部子文件夹。每个文件夹内的图片合并为一个 PDF，保存在各文件夹的上级目录；文件夹中的 PDF 文件会自动忽略。",
            wraplength=520,
        )
        hint.pack(anchor="w", pady=(0, 8))

        list_frame = ttk.LabelFrame(parent, text="待转换文件夹", padding=12)
        list_frame.pack(fill="both", expand=True, pady=6)

        list_container = ttk.Frame(list_frame)
        list_container.pack(fill="both", expand=True)

        scrollbar = ttk.Scrollbar(list_container)
        scrollbar.pack(side="right", fill="y")

        self.folder_listbox = tk.Listbox(list_container, height=6, yscrollcommand=scrollbar.set)
        self.folder_listbox.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.folder_listbox.yview)

        btn_row = ttk.Frame(list_frame)
        btn_row.pack(fill="x", pady=(8, 0))

        ttk.Button(btn_row, text="添加文件夹", command=self._add_folders, width=10).pack(side="left")
        ttk.Button(btn_row, text="添加上级目录", command=self._add_parent_subfolders, width=10).pack(
            side="left", padx=(4, 0)
        )
        ttk.Button(btn_row, text="移除", command=self._remove_selected_folder, width=8).pack(
            side="left", padx=(4, 0)
        )
        ttk.Button(btn_row, text="清空", command=self._clear_folders, width=6).pack(side="left", padx=(4, 0))

        output_frame = ttk.LabelFrame(parent, text="输出", padding=12)
        output_frame.pack(fill="x", pady=6)

        ttk.Label(output_frame, textvariable=self.output_preview, wraplength=500).pack(anchor="w")

        action_frame = ttk.Frame(parent)
        action_frame.pack(fill="x", pady=6)

        self.convert_btn = ttk.Button(action_frame, text="开始转换", command=self._start_convert, width=12)
        self.convert_btn.pack(side="left")

        ttk.Button(action_frame, text="打开输出目录", command=self._open_image_output_dir, width=12).pack(
            side="left", padx=(8, 0)
        )

    def _build_merge_tab(self, parent: ttk.Frame, padding: dict) -> None:
        hint = ttk.Label(
            parent,
            text="添加多个 PDF 文件，按列表顺序合并为一个 PDF。可调整顺序后一键合并。",
            wraplength=520,
        )
        hint.pack(anchor="w", pady=(0, 8))

        list_frame = ttk.LabelFrame(parent, text="待合并 PDF（按顺序）", padding=12)
        list_frame.pack(fill="both", expand=True, pady=6)

        list_container = ttk.Frame(list_frame)
        list_container.pack(fill="both", expand=True)

        scrollbar = ttk.Scrollbar(list_container)
        scrollbar.pack(side="right", fill="y")

        self.pdf_listbox = tk.Listbox(list_container, height=6, yscrollcommand=scrollbar.set)
        self.pdf_listbox.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.pdf_listbox.yview)

        btn_row = ttk.Frame(list_frame)
        btn_row.pack(fill="x", pady=(8, 0))

        ttk.Button(btn_row, text="添加 PDF", command=self._add_pdfs, width=10).pack(side="left")
        ttk.Button(btn_row, text="移除", command=self._remove_selected_pdf, width=8).pack(side="left", padx=(4, 0))
        ttk.Button(btn_row, text="上移", command=lambda: self._move_pdf(-1), width=6).pack(side="left", padx=(4, 0))
        ttk.Button(btn_row, text="下移", command=lambda: self._move_pdf(1), width=6).pack(side="left", padx=(4, 0))
        ttk.Button(btn_row, text="清空", command=self._clear_pdfs, width=6).pack(side="left", padx=(4, 0))

        output_frame = ttk.LabelFrame(parent, text="输出", padding=12)
        output_frame.pack(fill="x", pady=6)

        ttk.Label(output_frame, textvariable=self.merge_output_preview, wraplength=500).pack(anchor="w")

        action_frame = ttk.Frame(parent)
        action_frame.pack(fill="x", pady=6)

        self.merge_btn = ttk.Button(action_frame, text="开始合并", command=self._start_merge, width=12)
        self.merge_btn.pack(side="left")

        ttk.Button(action_frame, text="打开输出目录", command=self._open_merge_output_dir, width=12).pack(
            side="left", padx=(8, 0)
        )

    def _append_folders(self, folders: list[Path]) -> None:
        existing = {path.resolve() for path in self._folder_paths}
        added = 0
        for folder in folders:
            resolved = folder.resolve()
            if resolved in existing:
                continue
            self._folder_paths.append(folder)
            existing.add(resolved)
            added += 1

        if added:
            self._refresh_folder_listbox()
            self._append_log(f"已添加 {added} 个文件夹。")

    def _add_folders(self) -> None:
        folders = pick_folders("选择文件夹（可多选，按住 Cmd/Ctrl 或 Shift）")
        if not folders:
            return
        self._append_folders(folders)

    def _add_parent_subfolders(self) -> None:
        folders = pick_subfolders("选择上级目录")
        if folders is None:
            return
        if not folders:
            messagebox.showinfo("提示", "该目录下没有子文件夹。")
            return
        self._append_folders(folders)

    def _remove_selected_folder(self) -> None:
        selection = self.folder_listbox.curselection()
        if not selection:
            return
        index = selection[0]
        removed = self._folder_paths.pop(index)
        self._refresh_folder_listbox()
        self._append_log(f"已移除：{removed.name}")

    def _clear_folders(self) -> None:
        if not self._folder_paths:
            return
        self._folder_paths.clear()
        self._refresh_folder_listbox()
        self._append_log("已清空文件夹列表。")

    def _refresh_folder_listbox(self) -> None:
        self.folder_listbox.delete(0, "end")
        for path in self._folder_paths:
            self.folder_listbox.insert("end", str(path))
        self._update_image_output_preview()

    def _update_image_output_preview(self) -> None:
        if not self._folder_paths:
            self.output_preview.set("添加文件夹后显示输出位置")
            return

        lines = [str(resolve_folder_output(folder).resolve()) for folder in self._folder_paths]
        if len(lines) == 1:
            self.output_preview.set(lines[0])
        else:
            self.output_preview.set("\n".join(lines))

    def _refresh_pdf_listbox(self) -> None:
        self.pdf_listbox.delete(0, "end")
        for path in self._pdf_paths:
            self.pdf_listbox.insert("end", path.name)
        self._update_merge_output_preview()

    def _update_merge_output_preview(self) -> None:
        if not self._pdf_paths:
            self.merge_output_preview.set("添加 PDF 文件后显示输出位置")
            return

        output = resolve_merge_output(self._pdf_paths, None)
        self.merge_output_preview.set(str(output.resolve()))

    def _add_pdfs(self) -> None:
        paths = filedialog.askopenfilenames(title="选择 PDF 文件", filetypes=PDF_TYPES)
        if not paths:
            return

        existing = {path.resolve() for path in self._pdf_paths}
        added = 0
        for raw in paths:
            path = Path(raw)
            resolved = path.resolve()
            if resolved in existing:
                continue
            self._pdf_paths.append(path)
            existing.add(resolved)
            added += 1

        if added:
            self._refresh_pdf_listbox()
            self._append_log(f"已添加 {added} 个 PDF 文件。")

    def _remove_selected_pdf(self) -> None:
        selection = self.pdf_listbox.curselection()
        if not selection:
            return
        index = selection[0]
        removed = self._pdf_paths.pop(index)
        self._refresh_pdf_listbox()
        self._append_log(f"已移除：{removed.name}")

    def _move_pdf(self, direction: int) -> None:
        selection = self.pdf_listbox.curselection()
        if not selection:
            return

        index = selection[0]
        new_index = index + direction
        if new_index < 0 or new_index >= len(self._pdf_paths):
            return

        self._pdf_paths[index], self._pdf_paths[new_index] = (
            self._pdf_paths[new_index],
            self._pdf_paths[index],
        )
        self._refresh_pdf_listbox()
        self.pdf_listbox.selection_set(new_index)

    def _clear_pdfs(self) -> None:
        if not self._pdf_paths:
            return
        self._pdf_paths.clear()
        self._refresh_pdf_listbox()
        self._append_log("已清空 PDF 列表。")

    def _append_log(self, message: str) -> None:
        self.log.configure(state="normal")
        self.log.insert("end", message + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def _set_busy(self, busy: bool) -> None:
        self._busy = busy
        state = "disabled" if busy else "normal"
        self.convert_btn.configure(state=state)
        self.merge_btn.configure(state=state)

    def _start_convert(self) -> None:
        if self._busy:
            return

        if not self._folder_paths:
            messagebox.showwarning("提示", "请先添加至少一个文件夹。")
            return

        for path in self._folder_paths:
            if not path.exists():
                messagebox.showerror("错误", f"路径不存在：\n{path}")
                return
            if not path.is_dir():
                messagebox.showerror("错误", f"不是文件夹：\n{path}")
                return

        folders = list(self._folder_paths)
        self._set_busy(True)
        self._append_log(f"共 {len(folders)} 个文件夹，开始转换...")

        thread = threading.Thread(
            target=self._run_convert,
            args=(folders,),
            daemon=True,
        )
        thread.start()

    def _run_convert(self, folders: list[Path]) -> None:
        try:
            folder_count, image_count, errors, outputs = convert_folders_to_pdf(folders)
            self.after(0, lambda: self._on_convert_done(folder_count, image_count, errors, outputs))
        except Exception as exc:  # noqa: BLE001
            self.after(0, lambda: self._on_convert_failed(str(exc)))

    def _on_convert_done(
        self,
        folder_count: int,
        image_count: int,
        errors: list[str],
        outputs: list[Path],
    ) -> None:
        self._set_busy(False)
        if folder_count == 0:
            self._append_log("转换失败。")
            for err in errors:
                self._append_log(f"  - {err}")
            messagebox.showerror("转换失败", "\n".join(errors) if errors else "未知错误")
            return

        self._append_log(f"完成：{folder_count} 个文件夹，共 {image_count} 张图片")
        for output in outputs:
            self._append_log(f"  输出：{output.resolve()}")
        for err in errors:
            self._append_log(f"警告：{err}")

        msg = f"已成功转换 {folder_count} 个文件夹，共 {image_count} 张图片。"
        if len(outputs) == 1:
            msg += f"\n\n输出文件：\n{outputs[0].resolve()}"
        elif outputs:
            msg += "\n\n输出文件：\n" + "\n".join(str(p.resolve()) for p in outputs)
        if errors:
            msg += f"\n\n有 {len(errors)} 条警告，详见状态栏。"
        messagebox.showinfo("转换完成", msg)

    def _on_convert_failed(self, message: str) -> None:
        self._set_busy(False)
        self._append_log(f"错误：{message}")
        messagebox.showerror("错误", message)

    def _start_merge(self) -> None:
        if self._busy:
            return

        if len(self._pdf_paths) < 2:
            messagebox.showwarning("提示", "请至少添加 2 个 PDF 文件后再合并。")
            return

        for path in self._pdf_paths:
            if not path.exists():
                messagebox.showerror("错误", f"文件不存在：\n{path}")
                return

        output = resolve_merge_output(self._pdf_paths, None)
        self._set_busy(True)
        self._append_log(f"共 {len(self._pdf_paths)} 个 PDF，开始合并...")
        self._append_log(f"输出：{output.resolve()}")

        pdf_paths = list(self._pdf_paths)
        thread = threading.Thread(
            target=self._run_merge,
            args=(pdf_paths, output),
            daemon=True,
        )
        thread.start()

    def _run_merge(self, pdf_paths: list[Path], output: Path) -> None:
        try:
            count, errors = merge_pdfs(pdf_paths, output)
            self.after(0, lambda: self._on_merge_done(count, errors, output))
        except Exception as exc:  # noqa: BLE001
            self.after(0, lambda: self._on_merge_failed(str(exc)))

    def _on_merge_done(self, count: int, errors: list[str], output: Path) -> None:
        self._set_busy(False)
        if count == 0:
            self._append_log("合并失败。")
            for err in errors:
                self._append_log(f"  - {err}")
            messagebox.showerror("合并失败", "\n".join(errors) if errors else "未知错误")
            return

        self._append_log(f"完成：成功合并 {count} 个 PDF")
        for err in errors:
            self._append_log(f"警告：{err}")

        msg = f"已成功合并 {count} 个 PDF。\n\n输出文件：\n{output.resolve()}"
        if errors:
            msg += f"\n\n有 {len(errors)} 个文件失败，详见状态栏。"
        messagebox.showinfo("合并完成", msg)

    def _on_merge_failed(self, message: str) -> None:
        self._set_busy(False)
        self._append_log(f"错误：{message}")
        messagebox.showerror("错误", message)

    def _open_directory(self, target_dir: Path) -> None:
        if not target_dir.exists():
            messagebox.showwarning("提示", "输出目录尚不存在，请先完成一次操作。")
            return

        try:
            if sys.platform == "darwin":
                subprocess.run(["open", str(target_dir)], check=False)
            elif sys.platform == "win32":
                os.startfile(str(target_dir))  # noqa: S606
            else:
                subprocess.run(["xdg-open", str(target_dir)], check=False)
        except OSError as exc:
            messagebox.showerror("错误", f"无法打开目录：{exc}")

    def _open_image_output_dir(self) -> None:
        if not self._folder_paths:
            messagebox.showwarning("提示", "请先添加文件夹。")
            return

        selection = self.folder_listbox.curselection()
        index = selection[0] if selection else 0
        folder = self._folder_paths[index]
        if not folder.exists():
            messagebox.showerror("错误", f"路径不存在：\n{folder}")
            return

        self._open_directory(resolve_folder_output(folder).parent)

    def _open_merge_output_dir(self) -> None:
        if not self._pdf_paths:
            messagebox.showwarning("提示", "请先添加 PDF 文件。")
            return

        output = resolve_merge_output(self._pdf_paths, None)
        self._open_directory(output.parent)


def main() -> None:
    app = App()
    app.mainloop()
