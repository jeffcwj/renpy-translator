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

### 2026-03-10: 一键翻译技术文档

#### 文件变更

- `docs/一键翻译技术文档.md` — 新增，完整的一键翻译流程技术文档（17个章节）

#### 文档内容

1. 一键翻译概述与调度机制（MyQueue + qDic）
2. 全部 9 个步骤的详细调用链、文件 I/O、完成检测
3. 文件产物总览（按步骤汇总所有生成文件）
4. 解包机制详解（SCRIPT_ONLY 选择性解包）
5. 必要文件与非必要文件分类
6. 翻译后清理建议（按优先级）
7. 信号文件与完成检测机制
8. 关键源文件索引（核心模块、翻译引擎、Hook 脚本、工具模块、配置文件）

### 2026-03-11: UI 卡死修复 & 提示词精简

#### 文件变更

- `src/engine_form.py` — 修复打开提示词模板/模型列表时 UI 卡死（`subprocess.Popen().wait()` → `os.startfile()`）
- `src/openai_template.json` — 精简提示词（820字→380字），占位符保护提升为最高优先级规则

#### engine_form.py 修复详情

- `custom_prompt()`: 用 `os.startfile()` 异步打开模板文件，不阻塞 UI 线程
- `on_custom_button_clicked()`: 同理修复模型列表编辑按钮

#### openai_template.json 精简详情

1. **占位符保护提升为第一条规则**：标记为「最高优先级」，AI 对开头规则遵从度更高
2. **删除 H-Scene 词汇穷举表**：约 200 字的具体词汇列表删除，改为一句话概括（AI 自行根据语境选词）
3. **示例从 1→4 条含占位符**：增加 `{0}{1}{2}{3}` 多占位符示例，强化 AI 对占位符的记忆
4. **总长度减少 54%**：减少 AI 注意力分散，提高占位符保留率

### 2026-03-11: 设置界面 tab 修复 & 清理/迁移脚本

#### 文件变更

- `LostInYou-0.15.1-pc/game/screens.rpy` — 在 preferences 屏幕内新增 Language tab（自动扫描 game/tl/ 下的语言目录）
- `LostInYou-0.15.1-pc/game/hook_add_change_language_entrance.rpy` — 注释掉 preferences→my_preferences 的 screen 替换，修复 tab 切换失效
- `cleanup_unpacked.py` — 新增，解包资源清理脚本（删除 images/audio/gui/saves 等重复目录）
- `migrate_to_apk.py` — 新增，PC→Android APK 翻译迁移脚本（处理 x- 前缀、字体、hook 文件）

#### tab 切换修复详情

- **根因**：hook 文件拦截 `renpy.show_screen`，将 `'preferences'` 替换为 `'my_preferences'`。`my_preferences` 用 `use preferences` 嵌套原始屏幕，但 `SetScreenVariable("tab", ...)` 无法穿透屏幕边界，导致 tab 点击无效
- **修复**：在原生 preferences 屏幕内直接添加 Language tab（第5个 tab），移除 hook 的 screen 替换
- Language tab 使用 `os.listdir('game/tl')` 自动发现可用语言，通过 `Language()` action 切换

#### 清理脚本 (cleanup_unpacked.py)

- 删除解包产生的重复资源（images/audio/gui/saves），释放约 3.2 GB
- 保留 .rpa 压缩包、tl/ 翻译目录、fonts/、hook 文件、screens.rpy
- 执行前显示将要删除的内容和大小，需用户确认

#### 迁移脚本 (migrate_to_apk.py)

- 6 个步骤：检查 rpyc 编译状态 → 复制翻译 .rpyc → 复制 hook → 复制 screens.rpyc → 复制字体 → 复制 hook 翻译文件
- 自动处理 x- 前缀规则（文件名和目录名都加 x-）
- 支持 --dry-run 试运行、--font 指定 CJK 字体、--lang 指定语言
- 检测 .rpyc 是否过期，提醒用户先启动 PC 游戏重新编译
