@echo off
chcp 65001 >nul
echo ========================================
echo   图片转 PDF - Windows 打包
echo ========================================
echo.

where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [错误] 未找到 Python，请先安装 Python 3.8（兼容 Windows 7）
    echo 下载: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [1/3] 安装依赖...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [错误] 依赖安装失败
    pause
    exit /b 1
)

echo.
echo [2/3] 开始打包 exe...
python -m PyInstaller build_win.spec --noconfirm
if %errorlevel% neq 0 (
    echo [错误] 打包失败
    pause
    exit /b 1
)

echo.
echo [3/3] 完成!
echo.
echo 可执行文件: dist\ImageToPDF.exe
echo.
echo 用法示例:
echo   ImageToPDF.exe 图片.jpg
echo   ImageToPDF.exe 图片.jpg -o 输出.pdf
echo   ImageToPDF.exe 文件夹 -o 合并.pdf
echo.
pause
