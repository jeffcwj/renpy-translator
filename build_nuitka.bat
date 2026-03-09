@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ============================================
echo   Renpy Translator - Nuitka 编译脚本
echo ============================================
echo.

:: 检查 Python 是否可用
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python，请确保 Python 3.8 已安装并加入 PATH
    pause
    exit /b 1
)

:: 项目根目录（脚本所在目录）
set "ROOT=%~dp0"
set "SRC=%ROOT%src"
set "BUILD=%ROOT%build"
set "DIST=%ROOT%dist\windows"

:: 第一步：安装依赖
echo [1/4] 安装依赖...
pip install -r "%SRC%\requirements.txt"
pip install nuitka
if errorlevel 1 (
    echo [错误] 依赖安装失败
    pause
    exit /b 1
)
echo [1/4] 依赖安装完成
echo.

:: 第二步：Nuitka 编译
echo [2/4] 开始 Nuitka 编译（这可能需要较长时间）...
python -m nuitka ^
    --standalone ^
    --disable-console ^
    --enable-plugin=pyside6 ^
    --windows-icon-from-ico="%SRC%\main.ico" ^
    --noinclude-data-files="%SRC%\resource" ^
    --output-dir="%BUILD%" ^
    "%SRC%\main.py"
if errorlevel 1 (
    echo [错误] Nuitka 编译失败
    pause
    exit /b 1
)
echo [2/4] Nuitka 编译完成
echo.

:: 第三步：组装发布目录
echo [3/4] 组装发布目录...
if exist "%DIST%" rmdir /S /Q "%DIST%"
mkdir "%DIST%"

:: 复制 Nuitka 产物
xcopy /E /I /Y "%BUILD%\main.dist" "%DIST%"

echo [3/4] 产物复制完成
echo.

:: 第四步：复制资源文件
echo [4/4] 复制资源文件...

:: 目录资源
xcopy /E /I /Y "%SRC%\resource" "%DIST%\resource"
xcopy /I /Y "%SRC%\supported_language" "%DIST%\supported_language"
xcopy /I /Y "%SRC%\qm" "%DIST%\qm"
xcopy /I /Y "%SRC%\custom_engine" "%DIST%\custom_engine"

:: 文件资源
copy /Y "%SRC%\custom.txt" "%DIST%\custom.txt"
copy /Y "%SRC%\hook_unrpa.rpy" "%DIST%\hook_unrpa.rpy"
copy /Y "%SRC%\openai_model.txt" "%DIST%\openai_model.txt"
copy /Y "%SRC%\openai_template.json" "%DIST%\openai_template.json"
copy /Y "%SRC%\hook_extract.rpy" "%DIST%\hook_extract.rpy"
copy /Y "%SRC%\hook_add_change_language_entrance.rpy" "%DIST%\hook_add_change_language_entrance.rpy"
copy /Y "%SRC%\default_langauge_template.txt" "%DIST%\default_langauge_template.txt"
copy /Y "%SRC%\rpatool" "%DIST%\rpatool"
copy /Y "%SRC%\font_style_template.txt" "%DIST%\font_style_template.txt"
copy /Y "%SRC%\cacert.pem" "%DIST%\cacert.pem"
copy /Y "%SRC%\main.ico" "%DIST%\main.ico"

echo [4/4] 资源文件复制完成
echo.

echo ============================================
echo   编译完成！
echo   产物目录: %DIST%
echo   启动程序: %DIST%\main.exe
echo ============================================
pause
