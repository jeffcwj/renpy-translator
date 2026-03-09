@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ============================================
echo   Renpy Translator - PyInstaller 编译脚本
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
set "DIST=%SRC%\dist\main"

:: 第一步：安装依赖
echo [1/3] 安装依赖...
pip install -r "%SRC%\requirements.txt"
if errorlevel 1 (
    echo [错误] 依赖安装失败
    pause
    exit /b 1
)
echo [1/3] 依赖安装完成
echo.

:: 第二步：PyInstaller 编译
echo [2/3] 开始 PyInstaller 编译...
pushd "%SRC%"
pyinstaller main.spec
if errorlevel 1 (
    popd
    echo [错误] PyInstaller 编译失败
    pause
    exit /b 1
)
popd
echo [2/3] PyInstaller 编译完成
echo.

:: 第三步：复制资源文件
echo [3/3] 复制资源文件...

:: 目录资源
xcopy /E /I /Y "%SRC%\supported_language" "%DIST%\supported_language"
xcopy /E /I /Y "%SRC%\resource" "%DIST%\resource"
xcopy /E /I /Y "%SRC%\qm" "%DIST%\qm"
xcopy /E /I /Y "%SRC%\custom_engine" "%DIST%\custom_engine"

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
copy /Y "%SRC%\main.ico" "%DIST%\main.ico"
copy /Y "%SRC%\cacert.pem" "%DIST%\cacert.pem"

echo [3/3] 资源文件复制完成
echo.

echo ============================================
echo   编译完成！
echo   产物目录: %DIST%
echo   启动程序: %DIST%\main.exe
echo ============================================
pause
