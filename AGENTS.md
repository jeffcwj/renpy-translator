# AGENTS.md — Renpy Translator

## 语言规范

- **语言**：文档、文档名称、注释、回答均用中文
- 
## 每次必读注意事项！！！
- 写入超过2000字符时，请分段写入，否则可能永远卡住
- 有阶段性成果时提交 git、更新AGENTS.md、docs里相关文档（技术性文档、PRD或教程等）和相关README.md

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

## 当前的自定义修改概要

详细变更记录见 git log。以下仅列出当前相对于上游的主要修改领域：

- **OpenAI 翻译引擎** (`openai_translate.py`)：截断检测/修复、对半拆分重试、markdown 剥离、并发保序、详细日志
- **翻译安全处理** (`string_tool.py`)：`sanitize_translated_text()` 写入时兆底（换行符、双引号、双花括号还原）
- **提示词模板** (`openai_template.json`)：Galgame 专用 9 条规则 + 7 个示例
- **Hook 模板** (`hook_add_change_language_entrance.rpy`)：overlay 方式注入语言切换，不破坏原生 tab
- **一键翻译** (`one_key_translate*.py`)：特殊符号替换开关、翻译前 tl 目录自动备份
- **UI 修复** (`engine_form.py`)：打开模板文件不再卡死 UI
- **工具脚本**：`cleanup_unpacked.py`、`migrate_to_apk.py`、构建脚本
- **文档**：一键翻译教程、技术文档、Android APK 汉化教程、构建教程
