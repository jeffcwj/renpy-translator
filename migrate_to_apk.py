# -*- coding: utf-8 -*-
"""
将 PC 版 Ren'Py 翻译迁移到 Android APK（解压后的目录）。

用法：
    python migrate_to_apk.py <PC游戏目录> <APK解压目录> [选项]

示例：
    python migrate_to_apk.py "LostInYou-0.15.1-pc" "com.atrx.lostinyou-0.15.1.apk.unziped"
    python migrate_to_apk.py "LostInYou-0.15.1-pc" "com.atrx.lostinyou-0.15.1.apk.unziped" --font "ChillReunion_Sans.otf"
    python migrate_to_apk.py "LostInYou-0.15.1-pc" "com.atrx.lostinyou-0.15.1.apk.unziped" --lang chinese

注意：
    - Android Ren'Py 只读 .rpyc 文件，不会编译 .rpy
    - 所有文件和目录必须加 x- 前缀
    - 执行前请先在 PC 端启动一次游戏，确保 .rpyc 已重新编译
    - 修改 APK 后需要重新打包和签名
"""
import os
import sys
import shutil
import argparse


def add_x_prefix(name):
    """给文件名添加 x- 前缀"""
    if name.startswith('x-'):
        return name
    return 'x-' + name


def check_rpyc_freshness(rpy_path, rpyc_path):
    """检查 .rpyc 是否比 .rpy 新"""
    if not os.path.exists(rpyc_path):
        return False
    if not os.path.exists(rpy_path):
        return True
    return os.path.getmtime(rpyc_path) >= os.path.getmtime(rpy_path)


def copy_with_x_prefix(src_dir, dst_dir, ext_filter='.rpyc'):
    """递归复制文件，添加 x- 前缀，只复制指定扩展名"""
    copied = 0
    skipped = 0

    for item in sorted(os.listdir(src_dir)):
        src_path = os.path.join(src_dir, item)

        if os.path.isdir(src_path):
            # 递归处理子目录
            dst_subdir = os.path.join(dst_dir, add_x_prefix(item))
            sub_copied, sub_skipped = copy_with_x_prefix(
                src_path, dst_subdir, ext_filter)
            copied += sub_copied
            skipped += sub_skipped

        elif os.path.isfile(src_path):
            if ext_filter and not item.endswith(ext_filter):
                skipped += 1
                continue

            dst_path = os.path.join(dst_dir, add_x_prefix(item))
            os.makedirs(dst_dir, exist_ok=True)
            shutil.copy2(src_path, dst_path)
            copied += 1

    return copied, skipped


def main():
    parser = argparse.ArgumentParser(
        description='将 PC 版翻译迁移到 Android APK')
    parser.add_argument('pc_dir', help='PC 游戏根目录')
    parser.add_argument('apk_dir', help='APK 解压后的根目录')
    parser.add_argument('--lang', default='chinese',
                        help='翻译语言目录名 (默认: chinese)')
    parser.add_argument('--font', default=None,
                        help='CJK 字体文件路径 (可选)')
    parser.add_argument('--dry-run', action='store_true',
                        help='只显示将要执行的操作，不实际复制')
    args = parser.parse_args()

    pc_game = os.path.join(args.pc_dir, 'game')
    apk_game = os.path.join(args.apk_dir, 'assets', 'x-game')

    # 验证目录
    if not os.path.isdir(pc_game):
        print('错误: 找不到 PC game 目录: {}'.format(pc_game))
        sys.exit(1)
    if not os.path.isdir(apk_game):
        print('错误: 找不到 APK game 目录: {}'.format(apk_game))
        sys.exit(1)

    pc_tl = os.path.join(pc_game, 'tl', args.lang)
    if not os.path.isdir(pc_tl):
        print('错误: 找不到翻译目录: {}'.format(pc_tl))
        avail = [d for d in os.listdir(os.path.join(pc_game, 'tl'))
                 if os.path.isdir(os.path.join(pc_game, 'tl', d))]
        print('可用语言: {}'.format(', '.join(avail)))
        sys.exit(1)

    apk_tl = os.path.join(apk_game, 'x-tl')
    apk_lang = os.path.join(apk_tl, add_x_prefix(args.lang))

    print('=' * 60)
    print('PC -> Android APK 翻译迁移工具')
    print('=' * 60)
    print('PC 翻译目录:  {}'.format(pc_tl))
    print('APK 目标目录: {}'.format(apk_lang))
    print('语言: {}'.format(args.lang))
    if args.font:
        print('字体: {}'.format(args.font))
    if args.dry_run:
        print('[试运行模式 - 不会实际复制]')
    print()

    # 步骤 1: 检查 .rpyc 文件是否为最新
    print('--- 步骤 1: 检查 .rpyc 编译状态 ---')
    stale_files = []
    for dp, dn, fns in os.walk(pc_tl):
        for f in fns:
            if f.endswith('.rpy'):
                rpy_path = os.path.join(dp, f)
                rpyc_path = rpy_path + 'c'
                if not check_rpyc_freshness(rpy_path, rpyc_path):
                    rel = os.path.relpath(rpy_path, pc_tl)
                    stale_files.append(rel)

    # 也检查 hook 和 screens
    hook_rpy = os.path.join(pc_game,
                            'hook_add_change_language_entrance.rpy')
    hook_rpyc = hook_rpy + 'c'
    screens_rpy = os.path.join(pc_game, 'screens.rpy')
    screens_rpyc = screens_rpy + 'c'

    extra_stale = []
    if os.path.exists(hook_rpy):
        if not check_rpyc_freshness(hook_rpy, hook_rpyc):
            extra_stale.append('hook_add_change_language_entrance')
    if os.path.exists(screens_rpy):
        if not check_rpyc_freshness(screens_rpy, screens_rpyc):
            extra_stale.append('screens')

    if stale_files or extra_stale:
        print('警告: 以下 .rpyc 文件可能过期（.rpy 比 .rpyc 新）:')
        for f in stale_files[:10]:
            print('  翻译: {}'.format(f))
        if len(stale_files) > 10:
            print('  ... 还有 {} 个'.format(len(stale_files) - 10))
        for f in extra_stale:
            print('  游戏: {}.rpy'.format(f))
        print()
        print('请先在 PC 端启动一次游戏，让 Ren\'Py 重新编译 .rpyc 文件。')
        print('然后重新运行此脚本。')
        if not args.dry_run:
            ans = input('是否忽略警告继续？(y/N): ').strip().lower()
            if ans != 'y':
                print('已取消。请先启动 PC 游戏后重试。')
            sys.exit(0)
    else:
        print('.rpyc 文件状态正常。')
    print()

    # 步骤 2: 复制翻译文件
    print('--- 步骤 2: 复制翻译文件 (.rpyc) ---')
    if args.dry_run:
        # 统计文件
        rpyc_count = 0
        for dp, dn, fns in os.walk(pc_tl):
            rpyc_count += len([f for f in fns if f.endswith('.rpyc')])
        print('[试运行] 将复制 {} 个 .rpyc 文件到 {}'.format(
            rpyc_count, apk_lang))
    else:
        if os.path.exists(apk_lang):
            print('目标目录已存在，将覆盖: {}'.format(apk_lang))
            shutil.rmtree(apk_lang)
        copied, skipped = copy_with_x_prefix(pc_tl, apk_lang, '.rpyc')
        print('已复制 {} 个 .rpyc 文件（跳过 {} 个非 .rpyc 文件）'.format(
            copied, skipped))
    print()

    # 步骤 3: 复制 hook 文件
    print('--- 步骤 3: 复制 hook 文件 ---')
    if os.path.exists(hook_rpyc):
        dst_hook = os.path.join(
            apk_game,
            add_x_prefix('hook_add_change_language_entrance.rpyc'))
        if args.dry_run:
            print('[试运行] 将复制 hook_add_change_language_entrance.rpyc')
            print('  -> {}'.format(dst_hook))
        else:
            shutil.copy2(hook_rpyc, dst_hook)
            print('已复制 hook 文件: {}'.format(
                os.path.basename(dst_hook)))
    else:
        print('警告: hook .rpyc 文件不存在: {}'.format(hook_rpyc))
    print()

    # 步骤 4: 复制 screens.rpyc（含 Language tab 修复）
    print('--- 步骤 4: 复制 screens.rpyc ---')
    if os.path.exists(screens_rpyc):
        dst_screens = os.path.join(apk_game, 'x-screens.rpyc')
        if args.dry_run:
            print('[试运行] 将复制 screens.rpyc -> {}'.format(dst_screens))
        else:
            # 备份原 APK 的 screens.rpyc
            if os.path.exists(dst_screens):
                backup = dst_screens + '.bak'
                if not os.path.exists(backup):
                    shutil.copy2(dst_screens, backup)
                    print('已备份原始 screens: {}'.format(
                        os.path.basename(backup)))
            shutil.copy2(screens_rpyc, dst_screens)
            print('已复制 screens.rpyc（含 Language tab 和 tab 切换修复）')
    else:
        print('警告: screens.rpyc 不存在: {}'.format(screens_rpyc))
    print()

    # 步骤 5: 复制字体文件
    print('--- 步骤 5: 处理字体 ---')
    apk_fonts = os.path.join(apk_game, 'x-fonts')
    if args.font:
        if not os.path.isfile(args.font):
            print('警告: 字体文件不存在: {}'.format(args.font))
        else:
            font_name = os.path.basename(args.font)
            dst_font = os.path.join(apk_fonts, add_x_prefix(font_name))
            if args.dry_run:
                print('[试运行] 将复制字体 {} -> {}'.format(
                    font_name, dst_font))
            else:
                os.makedirs(apk_fonts, exist_ok=True)
                shutil.copy2(args.font, dst_font)
                print('已复制字体: {}'.format(os.path.basename(dst_font)))
    else:
        # 检查 PC 游戏的 fonts 目录是否有额外字体
        pc_fonts = os.path.join(pc_game, 'fonts')
        if os.path.isdir(pc_fonts):
            # 找出 PC 有但 APK 没有的字体
            pc_font_files = set(os.listdir(pc_fonts))
            apk_font_files = set()
            if os.path.isdir(apk_fonts):
                apk_font_files = set(
                    f[2:] if f.startswith('x-') else f
                    for f in os.listdir(apk_fonts))
            new_fonts = pc_font_files - apk_font_files
            if new_fonts:
                print('发现 PC 端新增字体:')
                for f in sorted(new_fonts):
                    src = os.path.join(pc_fonts, f)
                    dst = os.path.join(apk_fonts, add_x_prefix(f))
                    if args.dry_run:
                        print('  [试运行] {} -> {}'.format(
                            f, add_x_prefix(f)))
                    else:
                        os.makedirs(apk_fonts, exist_ok=True)
                        shutil.copy2(src, dst)
                        print('  已复制: {}'.format(add_x_prefix(f)))
            else:
                print('无新增字体需要复制。')
        else:
            print('未指定字体，且 PC 无 fonts 目录。如需 CJK 字体，'
                  '请用 --font 参数指定。')
    print()

    # 步骤 6: 复制 hook 翻译文件
    print('--- 步骤 6: 复制 hook 翻译文件 ---')
    hook_tl_rpyc = os.path.join(
        pc_game, 'tl', args.lang,
        'hook_add_change_language_entrance.rpyc')
    if os.path.exists(hook_tl_rpyc):
        dst_hook_tl = os.path.join(
            apk_lang,
            add_x_prefix('hook_add_change_language_entrance.rpyc'))
        if args.dry_run:
            print('[试运行] 将复制 hook 翻译文件')
        else:
            os.makedirs(apk_lang, exist_ok=True)
            shutil.copy2(hook_tl_rpyc, dst_hook_tl)
            print('已复制 hook 翻译文件')
    else:
        print('hook 翻译文件不存在（可选），跳过。')
    print()

    # 完成
    print('=' * 60)
    if args.dry_run:
        print('试运行完成。使用不带 --dry-run 参数重新运行以执行实际操作。')
    else:
        print('迁移完成！')
        print()
        print('后续步骤:')
        print('1. 删除 APK 中的 META-INF/ 目录（签名文件）')
        print('2. 重新打包为 ZIP（存储模式，不压缩）：')
        print('   cd <APK解压目录>')
        print('   7z a -tzip -mx=0 "../patched.apk" .')
        print('3. 签名 APK：')
        print('   java -jar uber-apk-signer.jar -a patched.apk')
        print('4. 安装签名后的 APK（需先卸载原版）')
    print('=' * 60)


if __name__ == '__main__':
    main()
