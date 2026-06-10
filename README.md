# 图片转 PDF

将图片直接转换为 PDF，支持单张图片或文件夹批量合并。

**使用方式：** Mac 上传代码到 GitHub → Actions 自动打包 → Windows 下载 exe 运行。

## 打包 exe（GitHub Actions）

1. 把代码 push 到 GitHub 仓库的 `main` 分支
2. 打开仓库 **Actions** →「打包 Windows 版本」（push 后自动触发，也可手动运行）
3. 构建完成后，在 **Artifacts** 下载 `ImageToPDF-Windows`
4. 解压得到 `ImageToPDF.exe`，在 Windows x86 电脑使用

GitHub Actions 在 `windows-latest`（x86_64）上构建，Mac ARM 只需负责上传代码。

## 系统要求

| 系统 | 是否支持 |
|------|----------|
| Windows 10 / 11 | ✓ |
| Windows 7 SP1（64 位） | ✓（需安装 [KB2999226 更新补丁](https://www.microsoft.com/en-us/download/details.aspx?id=49093)） |
| Windows 7 32 位 | ✗ 当前仅打包 64 位 exe |

> 使用 **Python 3.8** 打包，以兼容 Windows 7。Windows 8 及以上无特殊要求。

## exe 用法

```cmd
ImageToPDF.exe 图片.jpg
ImageToPDF.exe 图片.jpg -o 输出.pdf
ImageToPDF.exe 文件夹 -o 合并.pdf
ImageToPDF.exe 文件夹 --separate -o 输出目录
```

- 单张图片：生成同名的 PDF（或通过 `-o` 指定路径）
- 文件夹：按文件名中的**数字顺序**合并为一份 PDF（如 `个人xxx1.jpg` → `个人xxx2.jpg` → `个人xxx10.jpg`）

也可把图片拖到 **`运行示例.bat`** 上。

## 参数

| 参数 | 说明 |
|------|------|
| `-o` | 输出 PDF 或目录 |
| `--separate` | 每张图单独 PDF |

## 文件说明

| 文件 | 作用 |
|------|------|
| `convert.py` | 命令行入口 |
| `processor.py` | 转换核心 |
| `build_win.spec` | PyInstaller 配置 |
| `version_info.txt` | exe 版本信息 |
| `.github/workflows/build.yml` | GitHub 自动打包 |
| `requirements.txt` | 打包时依赖清单（给 GitHub Actions 用，Mac 无需安装） |
| `build.bat` | Windows 本地打包（可选） |
