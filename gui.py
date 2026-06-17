"""图片转 PDF 图形界面。"""

from __future__ import annotations

import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from processor import collect_images, convert_files_to_pdf, resolve_output

IMAGE_TYPES = [
    ("图片文件", "*.jpg *.jpeg *.png *.bmp *.tif *.tiff *.webp"),
    ("所有文件", "*.*"),
]


class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("图片转 PDF")
        self.geometry("560x380")
        self.minsize(480, 320)
        self.resizable(True, True)

        self.input_path = tk.StringVar()
        self.output_preview = tk.StringVar(value="选择图片或文件夹后显示输出位置")
        self.status_text = tk.StringVar(value="就绪")
        self._busy = False
        self.input_path.trace_add("write", lambda *_: self._update_output_preview())

        self._build_ui()

    def _build_ui(self) -> None:
        padding = {"padx": 16, "pady": 6}

        header = ttk.Label(self, text="图片转 PDF", font=("Microsoft YaHei UI", 16, "bold"))
        header.pack(anchor="w", padx=16, pady=(16, 8))

        hint = ttk.Label(
            self,
            text="支持单张图片或整个文件夹；文件夹会按文件名顺序合并为一个 PDF。",
            wraplength=520,
        )
        hint.pack(anchor="w", **padding)

        input_frame = ttk.LabelFrame(self, text="输入", padding=12)
        input_frame.pack(fill="x", **padding)

        entry = ttk.Entry(input_frame, textvariable=self.input_path)
        entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        ttk.Button(input_frame, text="选图片", command=self._pick_file, width=8).pack(side="left", padx=(0, 4))
        ttk.Button(input_frame, text="选文件夹", command=self._pick_folder, width=8).pack(side="left")

        output_frame = ttk.LabelFrame(self, text="输出", padding=12)
        output_frame.pack(fill="x", **padding)

        ttk.Label(output_frame, textvariable=self.output_preview, wraplength=500).pack(anchor="w")

        action_frame = ttk.Frame(self)
        action_frame.pack(fill="x", **padding)

        self.convert_btn = ttk.Button(action_frame, text="开始转换", command=self._start_convert, width=12)
        self.convert_btn.pack(side="left")

        ttk.Button(action_frame, text="打开输出目录", command=self._open_output_dir, width=12).pack(side="left", padx=(8, 0))

        status_frame = ttk.LabelFrame(self, text="状态", padding=12)
        status_frame.pack(fill="both", expand=True, **padding)

        self.log = tk.Text(status_frame, height=8, wrap="word", state="disabled")
        self.log.pack(fill="both", expand=True)
        self._append_log("欢迎使用。请选择图片或文件夹，然后点击「开始转换」。")

    def _pick_file(self) -> None:
        path = filedialog.askopenfilename(title="选择图片", filetypes=IMAGE_TYPES)
        if path:
            self.input_path.set(path)
            self._update_output_preview()

    def _pick_folder(self) -> None:
        path = filedialog.askdirectory(title="选择文件夹")
        if path:
            self.input_path.set(path)
            self._update_output_preview()

    def _update_output_preview(self) -> None:
        raw = self.input_path.get().strip()
        if not raw:
            self.output_preview.set("选择图片或文件夹后显示输出位置")
            return

        path = Path(raw)
        if not path.exists():
            self.output_preview.set("路径不存在")
            return

        output = resolve_output([path], None, separate=False)
        self.output_preview.set(str(output.resolve()))

    def _append_log(self, message: str) -> None:
        self.log.configure(state="normal")
        self.log.insert("end", message + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def _set_busy(self, busy: bool) -> None:
        self._busy = busy
        state = "disabled" if busy else "normal"
        self.convert_btn.configure(state=state)

    def _start_convert(self) -> None:
        if self._busy:
            return

        raw = self.input_path.get().strip()
        if not raw:
            messagebox.showwarning("提示", "请先选择图片或文件夹。")
            return

        path = Path(raw)
        if not path.exists():
            messagebox.showerror("错误", f"路径不存在：\n{path}")
            return

        images = collect_images([path])
        if not images:
            messagebox.showerror("错误", "未找到可处理的图片文件。")
            return

        output = resolve_output([path], None, separate=False)
        self._set_busy(True)
        self.status_text.set("转换中...")
        self._append_log(f"共 {len(images)} 张图片，开始转换...")
        self._append_log(f"输出：{output.resolve()}")

        thread = threading.Thread(
            target=self._run_convert,
            args=([path], output),
            daemon=True,
        )
        thread.start()

    def _run_convert(self, inputs: list[Path], output: Path) -> None:
        try:
            count, errors = convert_files_to_pdf(inputs, output, merge=True)
            self.after(0, lambda: self._on_convert_done(count, errors, output))
        except Exception as exc:  # noqa: BLE001
            self.after(0, lambda: self._on_convert_failed(str(exc)))

    def _on_convert_done(self, count: int, errors: list[str], output: Path) -> None:
        self._set_busy(False)
        if count == 0:
            self._append_log("转换失败。")
            for err in errors:
                self._append_log(f"  - {err}")
            messagebox.showerror("转换失败", "\n".join(errors) if errors else "未知错误")
            return

        self._append_log(f"完成：成功 {count} 张")
        for err in errors:
            self._append_log(f"警告：{err}")

        msg = f"已成功转换 {count} 张图片。\n\n输出文件：\n{output.resolve()}"
        if errors:
            msg += f"\n\n有 {len(errors)} 张图片失败，详见状态栏。"
        messagebox.showinfo("转换完成", msg)

    def _on_convert_failed(self, message: str) -> None:
        self._set_busy(False)
        self._append_log(f"错误：{message}")
        messagebox.showerror("错误", message)

    def _open_output_dir(self) -> None:
        raw = self.input_path.get().strip()
        if not raw:
            messagebox.showwarning("提示", "请先选择图片或文件夹。")
            return

        path = Path(raw)
        if not path.exists():
            messagebox.showerror("错误", f"路径不存在：\n{path}")
            return

        output = resolve_output([path], None, separate=False)
        target_dir = output.parent if output.suffix.lower() == ".pdf" else output
        if not target_dir.exists():
            messagebox.showwarning("提示", "输出目录尚不存在，请先完成一次转换。")
            return

        import os
        import subprocess
        import sys

        try:
            if sys.platform == "darwin":
                subprocess.run(["open", str(target_dir)], check=False)
            elif sys.platform == "win32":
                os.startfile(str(target_dir))  # noqa: S606
            else:
                subprocess.run(["xdg-open", str(target_dir)], check=False)
        except OSError as exc:
            messagebox.showerror("错误", f"无法打开目录：{exc}")


def main() -> None:
    app = App()
    app.mainloop()
