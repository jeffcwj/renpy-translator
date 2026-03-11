# -*- coding: utf-8 -*-
"""
清理解包后的重复资源文件，减少游戏包体大小。
这些文件已经存在于 .rpa 压缩包中，解包后产生了重复副本。

用法：
    python cleanup_unpacked.py <game目录路径>

示例：
    python cleanup_unpacked.py "E:\Download\CS\renpy-translator\LostInYou-0.15.1-pc"

注意：
    - 不会删除翻译文件（game/tl/）
    - 不会删除字体文件（game/fonts/）
    - 不会删除 .rpa 压缩包
    - 不会删除 hook 文件
    - 执行前会显示将要删除的内容，需确认后才执行
"""
import os
import sys
import shutil

# 需要删除的目录（解包产生的资源副本，原件在 .rpa 中）
CLEANUP_DIRS = [
    'images',   # 图片素材（已在 .rpa 中）
    'audio',    # 音频素材（已在 .rpa 中）
    'gui',      # GUI 素材（已在 gui.rpa 中）
]

# 需要删除的根目录 .rpy/.rpyc 文件（已在 scripts.rpa 中）
# 但保留 hook 文件和 screens.rpy（我们修改过的）
KEEP_FILES = {
    'hook_add_change_language_entrance.rpy',
    'hook_add_change_language_entrance.rpyc',
    'screens.rpy',
    'screens.rpyc',
}


def get_dir_size(path):
    total = 0
    for dp, dn, fns in os.walk(path):
        for f in fns:
            fp = os.path.join(dp, f)
            try:
                total += os.path.getsize(fp)
            except OSError:
                pass
    return total


def format_size(size_bytes):
    if size_bytes >= 1073741824:
        return '{:.1f} GB'.format(size_bytes / 1073741824)
    elif size_bytes >= 1048576:
        return '{:.1f} MB'.format(size_bytes / 1048576)
    elif size_bytes >= 1024:
        return '{:.1f} KB'.format(size_bytes / 1024)
    return '{} B'.format(size_bytes)


def main():
    if len(sys.argv) < 2:
        print('用法: python cleanup_unpacked.py <游戏根目录>')
        print('示例: python cleanup_unpacked.py "LostInYou-0.15.1-pc"')
        sys.exit(1)

    game_root = sys.argv[1]
    game_dir = os.path.join(game_root, 'game')

    if not os.path.isdir(game_dir):
        print('错误: 找不到 game 目录: {}'.format(game_dir))
        sys.exit(1)

    # 检查 .rpa 文件是否存在（确保资源有备份）
    rpa_files = [f for f in os.listdir(game_dir) if f.endswith('.rpa')]
    if not rpa_files:
        print('警告: game 目录下没有 .rpa 文件！')
        print('删除解包文件后游戏可能无法运行。')
        ans = input('是否继续？(y/N): ').strip().lower()
        if ans != 'y':
            print('已取消。')
            sys.exit(0)

    print('=' * 60)
    print('解包资源清理工具')
    print('游戏目录: {}'.format(game_dir))
    print('=' * 60)

    total_size = 0
    cleanup_items = []

    # 检查目录
    for dirname in CLEANUP_DIRS:
        dirpath = os.path.join(game_dir, dirname)
        if os.path.isdir(dirpath):
            size = get_dir_size(dirpath)
            total_size += size
            cleanup_items.append(('dir', dirpath, size))
            print('[目录] {} - {}'.format(dirname, format_size(size)))
        else:
            print('[跳过] {} - 不存在'.format(dirname))

    # 检查根目录 .rpy/.rpyc 文件（排除保留文件）
    root_files_size = 0
    root_files = []
    for f in sorted(os.listdir(game_dir)):
        if f in KEEP_FILES:
            continue
        fp = os.path.join(game_dir, f)
        if os.path.isfile(fp) and (f.endswith('.rpy') or f.endswith('.rpyc')):
            fsize = os.path.getsize(fp)
            root_files_size += fsize
            root_files.append(fp)

    if root_files:
        total_size += root_files_size
        cleanup_items.append(('files', root_files, root_files_size))
        print('[文件] 根目录 .rpy/.rpyc ({} 个) - {}'.format(
            len(root_files), format_size(root_files_size)))
        print('       保留: {}'.format(', '.join(sorted(KEEP_FILES))))

    print('-' * 60)
    print('总计可释放: {}'.format(format_size(total_size)))
    print()

    if not cleanup_items:
        print('没有需要清理的内容。')
        sys.exit(0)

    # 确认
    ans = input('确认删除以上内容？此操作不可撤销！(y/N): ').strip().lower()
    if ans != 'y':
        print('已取消。')
        sys.exit(0)

    # 执行删除
    deleted_size = 0
    for item_type, item_path, item_size in cleanup_items:
        if item_type == 'dir':
            print('删除目录: {} ...'.format(item_path), end='')
            try:
                shutil.rmtree(item_path)
                deleted_size += item_size
                print(' 完成')
            except Exception as e:
                print(' 失败: {}'.format(e))
        elif item_type == 'files':
            for fp in item_path:
                fname = os.path.basename(fp)
                try:
                    fsize = os.path.getsize(fp)
                    os.remove(fp)
                    deleted_size += fsize
                except Exception as e:
                    print('删除失败: {} - {}'.format(fname, e))
            print('删除根目录 .rpy/.rpyc 文件: {} 个'.format(len(item_path)))

    print()
    print('清理完成！释放空间: {}'.format(format_size(deleted_size)))


if __name__ == '__main__':
    main()
