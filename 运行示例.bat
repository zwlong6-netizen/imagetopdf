@echo off
chcp 65001 >nul
cd /d "%~dp0"

if not exist "ImageToPDF.exe" (
    if exist "dist\ImageToPDF.exe" (
        set "EXE=dist\ImageToPDF.exe"
    ) else (
        echo 未找到 ImageToPDF.exe，请先运行 build.bat 打包
        pause
        exit /b 1
    )
) else (
    set "EXE=ImageToPDF.exe"
)

if "%~1"=="" (
    echo 用法: 把图片拖到此 bat 文件上，或:
    echo   运行示例.bat 图片.jpg
    echo   运行示例.bat 图片.jpg -o 输出.pdf
    pause
    exit /b 1
)

"%EXE%" %*
echo.
pause
