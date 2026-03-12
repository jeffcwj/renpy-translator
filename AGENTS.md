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

### 2026-03-12: hook 模板优化 & 一键翻译特殊符号替换开关

#### 文件变更

- `src/hook_add_change_language_entrance.rpy` — 恢复 screen replacement（preferences→my_preferences），用 `renpy.known_languages()` 替代 `os.listdir('game/tl')` + `traverse_first_dir()`
- `src/one_key_translate.py` — 新增 replaceSpecialSymbolsCheckBox 控件（默认勾选），调整下方控件坐标
- `src/one_key_translate_form.py` — 翻译线程的 `is_replace_special_symbols` 参数从硬编码 True 改为读取 checkbox 状态
- `migrate_to_apk.py` — 修复 `sys.exit(0)` 缩进错误

#### hook 模板优化详情

- 删除 `traverse_first_dir()` 函数（手动遍历 game/tl 目录 + `renpy.game.script.translator.languages`）
- 改用 `renpy.known_languages()` 内置 API，代码从 21 行缩减为 5 行
- 保留 screen replacement 机制（preferences→my_preferences），适用于通用游戏的语言切换覆盖

#### 一键翻译特殊符号替换开关

- 新增 "Enable replace special symbols" checkbox，位于右侧 Translate 和 Error Repair 之间
- 默认勾选（与普通翻译页面行为一致）
- 关闭后翻译时不再对 `[]` `{}` `<>` 内容进行编码/解码，避免某些场景下特殊符号丢失

### 2026-03-12: hook 模板 overlay 重构（修复 tab 切换）

#### 文件变更

- `src/hook_add_change_language_entrance.rpy` — 从 screen replacement 改为 overlay 方式，修复 preferences 页面 tab 切换失效

#### 重构详情

- **问题根因**：screen replacement（`preferences` → `my_preferences`）导致 `SetScreenVariable("tab", ...)` 无法穿透屏幕边界，tab 点击无效
- **新方案**：hook `renpy.show_screen`，当 `show_screen('preferences')` 被调用后，额外调用 `show_screen('language_overlay')`
- **`language_overlay` screen**：`zorder 100` 置顶，右下角显示语言列表；通过 `renpy.get_screen("preferences")` 检测 preferences 是否存在，不存在时 `timer 0 action Hide` 自动隐藏
- **不使用 `config.overlay_screens`**：Ren'Py 在 game menu 中会 `suppress_overlay=True`，overlay screens 会被隐藏，因此不适用
- 删除了无用的调试注释

### 2026-03-12: hook overlay 条件渲染修复 & prompt 括号类型保护

#### 文件变更

- `src/hook_add_change_language_entrance.rpy` — 修复 timer 0 错误，改为条件渲染
- `src/openai_template.json` — 新增 Rule 3 括号类型严格保护，新增 c_mc_name 示例

#### hook overlay 修复详情

- Ren'Py 要求 timer delay 大于 0，timer 0 报错
- 移除 timer + if not 分支，改为 if renpy.get_screen("preferences") 条件渲染
- preferences 不存在时整个 vbox 不渲染，无需显式 Hide

#### prompt 模板更新详情

- 新增 Rule 3（最高优先级）：方括号和花括号严禁互相转换，违反导致游戏崩溃
- 新增示例 6：Earth to [c_mc_name] 的翻译示例
- 规则从 8 条增至 9 条，示例从 5 条增至 6 条

### 2026-03-12: .gitignore 添加

#### 文件变更

- `.gitignore` — 新增，排除游戏目录、__pycache__、*.pyc、log.txt、构建产物等

### 2026-03-12: prompt 模板迭代（语气词翻译 & 占位符邻近保护）

#### 文件变更

- `src/openai_template.json` — Rule 5 和 Rule 7 更新

#### 详情

- **Rule 5（保留英文原名）**：新增语气词翻译示例，明确 No→不、Oh→哦、Ok→好的、So→所以、Ah→啊、Hi→嗨、Yo→哟、Hmm→嗯、I-→我- 等必须翻译
- **Rule 7（占位符保护）**：新增「占位符仅是临时替代符号，占位符前后紧邻的文字必须正常翻译，不得遗漏或改变大小写」
- 解决：AI 偶尔跳过占位符旁边单词不翻译、首字母变小写的问题

### 2026-03-12: 翻译结果防错乱 & 安全性修复

#### 文件变更

- `src/openai_translate.py` — 并发顺序保证 + 截断修复安全化
- `src/renpy_translate.py` — safe pop/get + 双花括号还原参数传递
- `src/string_tool.py` — sanitize_translated_text 新增双花括号还原
- `src/openai_template.json` — Rule 1/3 精化 + 新增示例 7

#### openai_translate.py 修复详情

1. **`as_completed` → 顺序遍历**：`concurrent.futures.as_completed(to_do)` 改为 `for future in to_do:`，保证多批次翻译结果按原始顺序拼接
2. **禁用 `_try_fix_truncated_json` 策略 2**：直接在截断处补 `"}` 可能闭合不完整的 value 导致翻译内容错乱，改为无法修复时放弃、走 `spilt_half_and_re_translate` 重试

#### renpy_translate.py 修复详情

1. **safe pop**：`rpy_info_dic.pop(self.p)` → `pop(self.p, None)`，防止异常处理时二次 KeyError
2. **safe get**：`trans_dic[target]` → `trans_dic.get(target, None)`，防止禁用特殊符号替换时 KeyError
3. **双花括号还原**：`sanitize_translated_text(translated)` → `sanitize_translated_text(translated, target)`，传入原文供 `{{` 还原

#### string_tool.py 修复详情

- `sanitize_translated_text(text, original=None)`：新增 `{{` 双花括号还原逻辑——当原文含 `{{tag}}` 但译文被 AI 简化为 `{tag}` 时，自动还原

#### prompt 模板更新详情

- **Rule 1**：仅当原文存在 `\"` 时才用「」替代，`{i}{/i}` 等是标签不是引号
- **Rule 3**：新增 `{{` `}}` 双花括号保护
- **新增示例 7**：`{{color=[event_hint_location_color]}}Visit the hospital.{{/color}}`

#### 错位调查结论

- 代码逻辑层面不存在系统性错位 bug：`TranslateToList` 用原文作字典 key（内容映射），不依赖返回顺序
- `as_completed` 乱序不影响字典映射，但改为保序更安全
- 用户观察到的「错位」更可能是 AI 模型本身混淆序号、或截断修复产生残缺内容

### 2026-03-12: 一键翻译 tl 目录备份 & prompt 模板防繁体/防补全

#### 文件变更

- `src/one_key_translate_form.py` — 翻译前自动备份 tl 目录为 zip
- `src/openai_template.json` — Rule 4 强制简体中文、Rule 7 严禁自行补全/删除标签

#### 一键翻译备份详情

- 在 `translate()` 方法的 `else` 分支（确认 `select_dir` 存在后），翻译开始前调用 `shutil.make_archive()` 将 tl 目录打包为 zip
- 备份文件命名：`{tl_name}_backup_{YYYYMMDD_HHMMSS}.zip`，存放在 `game/tl/` 目录下
- 备份失败不阻断翻译流程（try/except + log_print）

#### prompt 模板更新详情

- **Rule 4**：标题从「风格与人设高度适配」改为「简体中文 & 风格适配」，新增「必须使用简体中文，严禁输出繁体中文」
- **Rule 7**：末尾新增「严禁自行补全或删除标签——即使原文标签看起来不完整（如缺少闭合标签），也必须严格按原文输出，不得擅自增删」

### 2026-03-12: API 错误重试 & 截断日志增强 & markdown 剥离

#### 文件变更

- `src/openai_translate.py` — 500/429 错误对半拆分重试、截断时打印输入/输出内容、剥离 markdown 代码块标记
- `src/openai_template.json` — Rule 9 禁止 markdown 包裹

#### openai_translate.py 修复详情

1. **500/429 错误重试**：`APIStatusError`、`RateLimitError` 不再直接 `return None`，改为 `spilt_half_and_re_translate()` 对半拆分重试（batch >= 2 时），再失败才放弃
2. **截断详细日志**：`finish_reason=length` 时额外打印输入批次前 3 条内容、返回内容前 500 字符和末尾 200 字符，方便排查异常截断
3. **markdown 剥离**：`json.loads` 前自动剥离 AI 返回的 ` ```json ... ``` ` 标记

#### prompt 模板更新

- **Rule 9**：新增「直接返回纯 JSON，严禁用 markdown 代码块包裹」
