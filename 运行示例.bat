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
    echo 未指定文件，启动图形界面...
    "%EXE%"
    echo.
    pause
    exit /b 0
)

"%EXE%" %*
echo.
pause
