# AGENTS.md — Renpy Translator

## 语言规范

- **语言**：文档、文档名称、注释、回答均用中文
- 
## 每次必读注意事项！！！
- 写入超过2000字符时，请分段写入，否则可能永远卡住
- 有阶段性成果时提交 git、更新AGENTS.md、docs里相关文档（技术性文档、PRD或教程等）和相关README.md
- CSMOS v338只是用了部分CSSO 1.0的代码甚至有修改，可以用作参考但不要滥用CSSO 1.0源码而不检查动态库

## Project Overview

Renpy Translator is a free, open-source GUI tool for translating Ren'Py visual novel games.
Python 3.8 desktop app (Windows-only) using PySide6 (Qt6) with qt-material theming.
All source lives in `src/` (flat structure, ~74 .py files). MIT License.

## Build & Run Commands

```bash
# Install dependencies
pip install -r src/requirements.txt

# Run the application
python src/main.py

# Build with PyInstaller
pyinstaller src/main.spec

# Build with Nuitka (used in CI, targets Python 3.8 x64)
# See .github/workflows/Nuitak-publish.yml for full flags
```

### CI Workflows

- `.github/workflows/Pyinstaller-publish.yml` — PyInstaller release build
- `.github/workflows/Nuitak-publish.yml` — Nuitka release build

### Tests & Linting

**None.** No test framework, no test files, no linter config, no type checking, no
`pyproject.toml`, `setup.py`, `setup.cfg`, `tox.ini`, or `Makefile` exist.
When adding new code, manual testing via the GUI is the only verification path.

## Architecture

### Entry Point

`src/main.py` — creates QApplication, applies qt-material theme, shows MainWindow.

### Key Modules

| Module | Purpose |
|---|---|
| `main.py` | App entry, MainWindow, menu/toolbar, orchestration |
| `renpy_translate.py` | Core translation logic (RPY file processing) |
| `renpy_extract.py` | String extraction from RPY files |
| `string_tool.py` | Bracket encoding/decoding for translation safety |
| `openai_translate.py` | OpenAI/ChatGPT translation engine |
| `deepl_translate.py` | DeepL translation engine |
| `html_util.py` | HTML tag preservation during translation |
| `my_log.py` | Thread-safe logging to `log.txt` via `log_print()` |
| `ui.py` | Auto-generated Qt UI code (DO NOT EDIT — regenerate from .ui) |

### UI Pattern

- `*.ui` files — Qt Designer XML layouts
- `ui.py` — auto-generated from `.ui` files (do not hand-edit)
- `*_form.py` — form logic classes inheriting both QDialog and Ui_*Dialog
- Dialogs are modal, launched from MainWindow

### Custom Translation Engines

Plugin directory: `src/custom_engine/`

Each plugin must expose one of:
- `tranlate_single(text, from_lang, to_lang)` — translate one string (note: typo is intentional)
- `tranlate_queue(text_list, from_lang, to_lang)` — translate a batch

See `src/custom_engine/_caiyun.py` for a reference implementation.

### Config Storage

JSON config files in working directory (not `.json` extension):
- `engine.txt` — selected translation engine settings
- `proxy.txt` — proxy configuration
- `custom.txt` — custom engine settings
- `language.txt` — language preferences

Read/write pattern: `json.load()` / `json.dump()` with `io.open(path, 'r', encoding='utf-8')`.

### Threading Model

- `threading.Thread` subclasses with `threading.Lock` for shared state
- `_thread.start_new_thread` for fire-and-forget background work
- `concurrent.futures.ThreadPoolExecutor` for batch translation
- UI updates from threads must go through Qt signals (PySide6)

## Code Style

### Naming Conventions

- **Classes**: PascalCase (`MainWindow`, `TranslateThread`, `OpenaiTranslate`)
- **Functions/methods**: inconsistent — mixedCase and snake_case both used
  (`TranslateFile`, `EncodeBrackets`, `get_rpy_info`, `log_print`)
- **Variables**: mostly snake_case (`file_path`, `translate_list`)
- **Constants**: not distinguished from variables (no UPPER_CASE convention)
- **When adding code**: match the style of the file you're editing

### Imports

Loosely ordered: stdlib → third-party → local. No strict enforcement.
Wildcard imports are used (`from string_tool import *`). Follow existing patterns per file.

### Type Hints

**Not used anywhere.** Do not introduce type hints unless explicitly asked —
they would be inconsistent with the entire codebase.

### Docstrings

**Not used.** Functions have no docstrings. Add comments only when logic is non-obvious.

### Error Handling

```python
try:
    # operation
except Exception:
    msg = traceback.format_exc()
    log_print(msg)
```

- Broad `except Exception` or bare `except:` is the norm
- Always log with `traceback.format_exc()` → `log_print(msg)`
- Never silently swallow exceptions

### Logging

Use `log_print(msg)` from `my_log.py`. Thread-safe, timestamps, writes to `log.txt`.
Do NOT use `print()` or the `logging` module.

### File I/O

Always use explicit encoding:
```python
import io
f = io.open(file_path, 'r', encoding='utf-8')
```

### String Safety

Translation-safe bracket encoding in `string_tool.py`:
- `EncodeBrackets(text)` before sending to translation API
- `DecodeBrackets(text)` after receiving translated text
- Preserves `[]`, `{}`, `<>` content through translation round-trips

## Platform Notes

- **Windows-only**: uses `pywin32`, `ctypes.windll`, Windows subprocess flags
- **Python 3.8**: target version in CI builds — do not use 3.9+ syntax
  (no `match`, no `dict | dict`, no `list` as generic type, etc.)
- **PySide6 6.6.3**: pinned version — do not upgrade without testing

## Dependencies

All in `src/requirements.txt`:
PySide6, pygtrans, deepl, openai, translators, pyperclip, openpyxl,
qt-material, beautifulsoup4, pywin32, ping3, pyinstaller, httpx.

## Quick Reference

```
src/main.py          → start here for app flow
src/renpy_translate.py → core translation pipeline
src/string_tool.py   → bracket encoding (critical for correctness)
src/custom_engine/   → add new translation engines here
src/my_log.py        → logging (use log_print, not print)
src/*.ui             → Qt Designer files (edit in Designer, not by hand)
src/ui.py            → auto-generated (DO NOT EDIT)
```

## 变更记录

### 2026-03-10: OpenAI 翻译引擎优化 & 教程文档

#### 文件变更

- `src/openai_translate.py` — 修复多个错误处理问题（见下方详细说明）
- `src/openai_template.json` — 替换为 Galgame 优化版翻译提示词
- `src/openai_template.default.json` — 新增，原始默认模板备份
- `docs/一键翻译教程.md` — 新增，OpenAI/AI 引擎一键翻译完整教程
- `docs/构建与启动教程.md` — 新增，项目构建与运行教程
- `build_pyinstaller.bat` — 新增，PyInstaller 一键构建脚本
- `build_nuitka.bat` — 新增，Nuitka 一键构建脚本

#### openai_translate.py 修复详情

1. **`len(l) < 0` bug**：原条件永远不成立，改为 `len(l) == 0`
2. **输出截断检测**：检查 `finish_reason == 'length'`，警告用户降低 max_length
3. **截断 JSON 修复**：`_try_fix_truncated_json()` 尝试修复不完整的 JSON 响应
4. **部分结果恢复**：截断时保留已翻译的部分，只重试未翻译的行
5. **日志改进**：记录丢失的行号和内容、原始响应文本、期望/实际数量
6. **模板缓存**：`_load_template_cached()` 避免每次 API 调用都读取文件
7. **f-string 兼容性**：将 f-string 改为 `.format()` 确保 Python 3.8 兼容（虽然 3.8 支持 f-string，保持与代码库风格一致）

#### 关键发现

- `max_length` 参数过大（如 50000）是翻译大量失败的根本原因，推荐 3000-5000
- 游戏卡顿主要因 CJK 字体过大和 Ren'Py 文字渲染开销
- 文件夹膨胀因解包 .rpa 释放的素材文件，翻译后可清理

### 2026-03-10: Android APK 汉化补丁教程

#### 文件变更

- `docs/Android-APK汉化补丁教程.md` — 新增，面向终端用户的中文教程，指导如何将 PC 版 Ren'Py 翻译补丁移植到 Android APK

#### 教程内容

1. APK 内部结构解析（`assets/x-game/` 与 `x-` 前缀规则）
2. 方案A：直接修改 APK（7-Zip + uber-apk-signer）
3. 方案B：Ren'Py SDK 重新打包（适合有 .rpy 源文件的用户）
4. APK 重签名（uber-apk-signer，内置 debug keystore）
5. CJK 字体处理
6. 安装与常见问题（翻译不生效、签名冲突、批量重命名脚本）

#### 关键发现

- Ren'Py APK 内所有文件名和目录名必须加 `x-` 前缀（如 `assets/x-game/x-tl/x-chinese/x-script.rpyc`）
- Android 版 Ren'Py 只加载 `.rpyc`，不编译 `.rpy`
- 修改 APK 后必须删除 `META-INF/` 并重签名，用户须卸载原版才能安装
- 打包时必须用"仅存储（Store）"模式，否则媒体文件无法读取
