# Android APK 汉化补丁教程

> 本教程面向已完成 PC 版 Ren'Py 游戏汉化、希望将翻译补丁移植到 Android APK 的用户。

---

## 目录

1. [前置知识：APK 内部结构](#1-前置知识apk-内部结构)
2. [准备工具](#2-准备工具)
3. [方案A：直接修改 APK（推荐）](#3-方案a直接修改-apk推荐)
4. [方案B：Ren'Py SDK 重新打包](#4-方案brenpy-sdk-重新打包)
5. [APK 签名](#5-apk-签名)
6. [CJK 字体处理](#6-cjk-字体处理)
7. [安装到手机](#7-安装到手机)
8. [常见问题](#8-常见问题)

---

## 1. 前置知识：APK 内部结构

Ren'Py Android APK **不同于** PC 版目录结构。所有游戏文件都存放在 APK 的 `assets/x-game/` 目录下，且**每个文件名和文件夹名都带有 `x-` 前缀**。

### PC 版 vs APK 内部路径对照

| PC 版路径 | APK 内部路径 |
|-----------|-------------|
| `game/tl/chinese/` | `assets/x-game/x-tl/x-chinese/` |
| `game/tl/chinese/script.rpyc` | `assets/x-game/x-tl/x-chinese/x-script.rpyc` |
| `game/fonts/MyFont.ttf` | `assets/x-game/x-fonts/x-MyFont.ttf` |
| `game/script.rpyc` | `assets/x-game/x-script.rpyc` |

> **重要**：Android 版 Ren'Py **只加载 `.rpyc`（编译版）**，不会在运行时编译 `.rpy` 文件。因此你需要的是 `.rpyc` 文件，而非 `.rpy` 源文件。

---

## 2. 准备工具

### 必需工具

| 工具 | 用途 | 下载地址 |
|------|------|----------|
| **7-Zip** | 解包/重打包 APK | https://www.7-zip.org/ |
| **JDK 8+** | uber-apk-signer 运行环境 | https://adoptium.net/ |
| **uber-apk-signer** | APK 重签名（内置 debug keystore，无需配置） | https://github.com/patrickfav/uber-apk-signer/releases |

### 可选工具

| 工具 | 用途 | 说明 |
|------|------|------|
| **Ren'Py SDK** | 方案B重新打包 | 仅方案B需要 |
| **apktool** | 解析 APK 资源 | 可选，方案A不需要 |

### 前置条件

- 已有 PC 版汉化的 `.rpyc` 翻译文件（位于 `game/tl/你的语言名/` 目录）
- 如果只有 `.rpy` 文件，需要先用 Ren'Py SDK 编译为 `.rpyc`（见[第4节](#4-方案brenpy-sdk-重新打包)）

---

## 3. 方案A：直接修改 APK（推荐）

适合：**已有 `.rpyc` 文件**的用户，无需 Ren'Py SDK，操作简单。

### 步骤 1：解包 APK

APK 本质上是 ZIP 压缩包，直接用 7-Zip 解压：

1. 将 APK 文件**复制一份**（保留原版备用）
2. 右键 APK → 7-Zip → 解压到当前目录（或指定文件夹）

解压后你会看到类似结构：

```
游戏名_extracted/
  assets/
    x-game/
      x-tl/          ← 已有翻译时才存在
      x-script.rpyc
      ...
  lib/
  META-INF/          ← 签名信息，修改后必须删除
  AndroidManifest.xml
```

### 步骤 2：添加翻译文件

在 `assets/x-game/` 下创建对应的 `x-tl/x-你的语言名/` 目录结构，并将 `.rpyc` 文件放入，**每个文件名都要加 `x-` 前缀**。

**示例**（PC 版语言目录名为 `chinese`）：

```
# 在解压目录中创建：
assets/x-game/x-tl/x-chinese/

# 将 PC 版的翻译文件复制进去，并重命名加 x- 前缀：
PC 文件: game/tl/chinese/script.rpyc
APK 路径: assets/x-game/x-tl/x-chinese/x-script.rpyc

PC 文件: game/tl/chinese/common.rpyc
APK 路径: assets/x-game/x-tl/x-chinese/x-common.rpyc
```

> **批量重命名技巧**：可以用 PowerShell 批量加前缀（见[常见问题](#批量给文件加-x--前缀)）

### 步骤 3：删除 META-INF 目录

修改过内容的 APK **必须删除** `META-INF/` 目录，否则签名验证会失败：

```
解压目录/META-INF/   ← 整个目录全部删除
```

### 步骤 4：重新打包为 APK

1. 进入解压目录，全选所有文件（**不要选上级文件夹**）
2. 右键 → 7-Zip → 添加到压缩包
3. 压缩格式选 **zip**，压缩级别选 **仅存储（Store）**
4. 文件名改为 `游戏名_patched.zip`
5. 完成后将 `.zip` 后缀改为 `.apk`

> **为什么选"仅存储"？** Ren'Py 的媒体文件（图片、音频）必须以不压缩模式存储，否则游戏启动时会报错。

---

## 4. 方案B：Ren'Py SDK 重新打包

适合：**有完整 `.rpy` 源文件**，或希望生成正式签名 APK 的用户。此方案由 Ren'Py 官方工具处理所有 `x-` 前缀问题，更可靠但操作复杂。

### 步骤 1：安装 Ren'Py SDK

1. 从 https://www.renpy.org/latest.html 下载 Ren'Py SDK（Windows 版）
2. 解压到任意目录，运行 `renpy.exe`

### 步骤 2：配置 Android 打包环境（RAPT）

首次打包 Android 需要配置 RAPT（Ren'Py Android Package Tool）：

1. 在 Ren'Py SDK 主界面点击右下角 **Preferences**
2. 确认 Android SDK 路径已设置（需要 Android SDK + JDK）
3. 点击 **Install SDK & Create Keys**（会自动下载 Android SDK，需要较好网络）

> 此步骤较复杂，建议参考 Ren'Py 官方文档：https://www.renpy.org/doc/html/android.html

### 步骤 3：将翻译文件放入游戏目录

将汉化的 `.rpy` / `.rpyc` 文件放到 PC 版游戏的 `game/tl/语言名/` 目录下（**不需要**加 `x-` 前缀，SDK 会自动处理）。

### 步骤 4：在 Ren'Py SDK 中打包 APK

1. 在 Ren'Py SDK 中将 **Projects Directory** 设置为游戏的上级目录
2. 选择对应游戏
3. 点击 **Build Distributions**
4. 选择 **Android APK**
5. 等待打包完成

打包好的 APK 已包含翻译文件，无需额外签名步骤。

---

## 5. APK 签名

修改过的 APK 必须重新签名才能安装到 Android 设备。推荐使用 **uber-apk-signer**，内置 debug keystore，零配置。

### 下载 uber-apk-signer

从 GitHub Releases 下载最新版 jar 文件：
https://github.com/patrickfav/uber-apk-signer/releases

### 签名命令

确保已安装 JDK（`java` 命令可用），在 APK 所在目录运行：

```cmd
java -jar uber-apk-signer.jar --apks 游戏名_patched.apk
```

签名完成后会生成 `游戏名_patched-aligned-debugSigned.apk`，这个文件就是可安装的版本。

### 签名后的注意事项

> **重要**：由于签名密钥与原版不同，你**必须先卸载手机上的原版游戏**，再安装修改版。
> 卸载前请注意**备份存档**（存档通常在 `/Android/data/com.游戏包名/files/saves/` 目录）。

---

## 6. CJK 字体处理

如果汉化后游戏显示方块或乱码，需要将 CJK 字体文件一并打入 APK。

### 添加字体到 APK（方案A）

1. 准备字体文件（如 `SourceHanSansCN-Regular.otf`）
2. 在解压 APK 的 `assets/x-game/x-fonts/` 目录下放入字体文件，**加上 `x-` 前缀**：

```
assets/x-game/x-fonts/x-SourceHanSansCN-Regular.otf
```

3. 确认 PC 版的翻译 `.rpyc` 文件中已经正确引用了该字体路径（通常由 Renpy Translator 的「替换字体」功能自动处理）

### 推荐字体

- **中文**：[思源黑体 SourceHanSansCN](https://github.com/CyanoHao/WFM-Free-Font/tree/master/SourceHanSansCN) — 推荐 Regular 或 Medium 权重
- 字体文件越大，游戏启动越慢。建议使用子集化版本

---

## 7. 安装到手机

1. 将签名后的 APK 传输到手机（USB / 云盘 / 浏览器下载均可）
2. 在手机设置中**开启「允许安装未知来源应用」**
3. 点击 APK 文件进行安装
4. 如果提示「应用未安装」或「解析包时出现问题」：
   - 确认已卸载原版游戏
   - 确认 APK 已正确签名
   - 确认打包时使用了「仅存储」压缩模式

---

## 8. 常见问题

### 游戏启动后仍显示英文，翻译没有生效

**原因1**：游戏内语言设置未切换  
→ 进入游戏设置 → 语言，切换到汉化对应的语言名

**原因2**：`.rpyc` 文件路径不正确（`x-` 前缀缺失或多余）  
→ 检查 APK 内 `assets/x-game/x-tl/x-语言名/` 的路径是否与 PC 版 `game/tl/语言名/` 对应

**原因3**：只放了 `.rpy` 文件而没有 `.rpyc`  
→ Android 版不编译 `.rpy`，必须提供对应的 `.rpyc` 文件

---

### 安装时提示「解析包时出现问题」

- APK 打包时压缩模式设置有误：重新打包，确认选择**仅存储（Store）**
- APK 损坏：重新完成所有步骤

---

### 文字显示方块或乱码

- 字体文件未正确放入 APK 或路径错误
- 检查 `assets/x-game/x-fonts/x-字体文件名.otf` 路径是否正确
- 确认 rpyc 翻译文件中字体引用路径与 APK 内路径一致

---

### 批量给文件加 `x-` 前缀

在 PowerShell 中，进入需要重命名的目录，执行：

```powershell
Get-ChildItem -File | Rename-Item -NewName { "x-" + $_.Name }
```

如果需要递归处理子目录的所有文件：

```powershell
Get-ChildItem -Recurse -File | ForEach-Object {
    if (-not $_.Name.StartsWith("x-")) {
        Rename-Item $_.FullName ("x-" + $_.Name)
    }
}
```

子目录本身也需要重命名（从最深层开始）：

```powershell
Get-ChildItem -Recurse -Directory | Sort-Object FullName -Descending | ForEach-Object {
    if (-not $_.Name.StartsWith("x-")) {
        Rename-Item $_.FullName (Join-Path $_.Parent.FullName ("x-" + $_.Name))
    }
}
```

---

### 存档备份

卸载原版前备份存档（如果需要）：

```
/Android/data/com.游戏包名/files/saves/
```

用文件管理器（或 ADB）将此目录复制出来，安装修改版后再复制回去。

> **注意**：Android 13+ 对 `/Android/data/` 访问有限制，可能需要使用 ADB：
> ```cmd
> adb pull /sdcard/Android/data/com.游戏包名/files/saves/ ./saves_backup
> ```

---

## 参考资料

- [RenPy-UnAPK 工具（APK 结构解析）](https://github.com/drdrr/RenPy-UnAPK)
- [uber-apk-signer 签名工具](https://github.com/patrickfav/uber-apk-signer)
- [Ren'Py 官方 Android 文档](https://www.renpy.org/doc/html/android.html)
- [F95zone Android 移植教程（英文）](https://f95zone.to/threads/porting-renpy-games-to-android.255183/)
- [ctrl-freak APK 修改 Gist](https://gist.github.com/ctrl-freak/fdc93637711330d5da92a6b2f13cad04)
