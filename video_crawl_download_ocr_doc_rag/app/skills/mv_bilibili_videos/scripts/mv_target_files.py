#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
mv_target_files skill
将指定类型的文件从源目录移动到目标目录，保持目录层级结构

例如：
  SRC: E:\00 视频\Up主\XXX\2024\abc.csv
  DEST: D:\workspace\video-crawl-download-ocr-doc-rag\doc\XXX\abc.csv
"""
import os
import sys
import shutil
import argparse
from pathlib import Path


SRC_DIR = r"E:\00 视频\Up主"
DEST_DIR = r"D:\workspace\video-crawl-download-ocr-doc-rag\doc"
TARGET_TYPE = "csv"  # csv, xlsx, xls, mp4, all


def get_target_extensions(target_type):
    """根据目标类型返回文件扩展名列表"""
    if target_type == 'csv':
        return ['.csv']
    elif target_type == 'xlsx':
        return ['.xlsx', '.xls']
    elif target_type == 'excel':
        return ['.xlsx', '.xls']
    elif target_type == 'mp4':
        return ['.mp4']
    elif target_type == 'all':
        return ['.csv', '.xlsx', '.xls', '.mp4']
    else:
        return [f'.{target_type}']


def find_target_files(src_dir, target_type):
    """查找源目录下所有目标类型的文件"""
    src_path = Path(src_dir)
    target_extensions = get_target_extensions(target_type)
    target_files = []

    for ext in target_extensions:
        # 递归查找所有匹配的文件
        for file_path in src_path.rglob(f'*{ext}'):
            if file_path.is_file():
                # 获取相对于源目录的路径
                rel_path = file_path.relative_to(src_path)
                target_files.append({
                    'src_path': file_path,
                    'rel_path': rel_path,
                    'up_name': rel_path.parts[0] if rel_path.parts else None
                })

    return target_files


def get_dest_path(rel_path, dest_dir, up_name):
    """计算目标文件路径

    例如：
      rel_path = "XXX/2024/abc.csv", up_name = "XXX"
      -> dest_dir / "XXX" / "abc.csv"
    """
    dest_base = Path(dest_dir)

    # 只保留UP主名和文件名，去掉中间层级（如年份）
    if up_name and len(rel_path.parts) >= 2:
        # "XXX/2024/abc.csv" -> "XXX/abc.csv"
        filename = rel_path.parts[-1]
        return dest_base / up_name / filename
    else:
        # 保持原层级结构
        return dest_base / rel_path


def move_target_files(src_dir, dest_dir, target_type, dry_run=False, up_name=None):
    """移动目标文件到目标目录"""
    print(f"源目录: {src_dir}")
    print(f"目标目录: {dest_dir}")
    print(f"目标类型: {target_type}")
    print(f"模拟运行: {dry_run}")
    if up_name:
        print(f"只处理UP主: {up_name}")
    print()

    # 查找所有目标文件
    all_files = find_target_files(src_dir, target_type)

    # 过滤UP主（如果指定了）
    if up_name:
        all_files = [f for f in all_files if f['up_name'] == up_name]

    if not all_files:
        print("未找到目标文件")
        return {'moved': 0, 'skipped': 0, 'failed': 0}

    print(f"找到 {len(all_files)} 个目标文件")

    # 统计
    moved = 0
    skipped = 0
    failed = 0

    for file_info in all_files:
        src_path = file_info['src_path']
        rel_path = file_info['rel_path']
        up_name = file_info['up_name']

        # 计算目标路径
        dest_path = get_dest_path(rel_path, dest_dir, up_name)

        # 确保目标目录存在
        dest_path.parent.mkdir(parents=True, exist_ok=True)

        # 检查目标文件是否已存在
        if dest_path.exists():
            print(f"  跳过（已存在）: {src_path.name} -> {dest_path}")
            skipped += 1
            continue

        if dry_run:
            print(f"  移动（模拟）: {src_path} -> {dest_path}")
            moved += 1
        else:
            try:
                shutil.move(str(src_path), str(dest_path))
                print(f"  移动: {src_path} -> {dest_path}")
                moved += 1
            except Exception as e:
                print(f"  错误: {src_path} -> {e}")
                failed += 1

    return {'moved': moved, 'skipped': skipped, 'failed': failed}


def main():
    parser = argparse.ArgumentParser(description='将指定类型的文件从源目录移动到目标目录')
    parser.add_argument('--src', default=SRC_DIR, help='源目录路径')
    parser.add_argument('--dest', default=DEST_DIR, help='目标目录路径')
    parser.add_argument('--type', '--target-type', dest='target_type', default=TARGET_TYPE,
                        help='目标文件类型: csv, xlsx, excel, mp4, all (默认: csv)')
    parser.add_argument('--up', help='只处理指定的UP主')
    parser.add_argument('--dry-run', action='store_true', help='模拟运行，不实际移动文件')

    args = parser.parse_args()

    # 检查源目录
    if not Path(args.src).exists():
        print(f"错误: 源目录不存在: {args.src}")
        return 1

    # 移动文件
    stats = move_target_files(
        args.src,
        args.dest,
        args.target_type,
        args.dry_run,
        args.up
    )

    # 打印总结
    print("\n" + "="*50)
    print("总结:")
    print(f"  文件移动: {stats['moved']} 个")
    print(f"  文件跳过: {stats['skipped']} 个")
    print(f"  文件失败: {stats['failed']} 个")

    if args.dry_run:
        print("\n注意: 这是模拟运行，没有实际移动文件。")

    return 0


if __name__ == '__main__':
    sys.exit(main())
