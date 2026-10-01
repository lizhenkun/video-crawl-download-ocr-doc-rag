#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
mv_bilibili_videos skill
将output目录中的视频和CSV/Excel文件移动到目标目录

把 mp4（大文件）存放在 移动硬盘（大磁盘）下
把 csv（小文件）存放在 项目的 doc目录下

CSV
"""
import os
import re
import csv
import sys
import shutil
import argparse
from pathlib import Path
from datetime import datetime

SOURCE_ROOT_DIR = r'D:\workspace\video-crawl-download-ocr-doc-rag\output'
# SOURCE_ROOT_DIR = r"E:\00 视频\Up主"
VIDEO_DEST_ROOT_DIR = r"E:\00 视频\Up主"
CSV_DEST_ROOT_DIR = r"D:\workspace\video-crawl-download-ocr-doc-rag\doc"


def extract_year_month_from_filename(filename):
    """从文件名中提取年份, 月份"""
    # 尝试匹配 yyyy-mm-dd 模式
    date_pattern1 = r'(\d{4})-(\d{2})-\d{2}'
    match1 = re.search(date_pattern1, filename)
    if match1:
        return match1.group(1), match1.group(2)

    # 尝试匹配 yyyymmdd 模式
    date_pattern2 = r'(\d{4})(\d{2})\d{2}'
    match2 = re.search(date_pattern2, filename)
    if match2:
        return match2.group(1), match1.group(2)

    # 尝试匹配第xxxx期_yyyyMMdd 模式
    date_pattern3 = r'第\d+期_(\d{4})(\d{2})\d{2}'
    match3 = re.search(date_pattern3, filename)
    if match3:
        return match3.group(1), match1.group(2)

    return None, None

def classify_youhegaojian_file(filename):
    """分类有何高见9527的文件"""
    filename_str = filename.stem

    # 检查是否以 yyyy-mm-dd 数字 开头（充电专属）
    pattern_charging = r'^\d{4}-\d{2}-\d{2}\s+\d+'
    if re.match(pattern_charging, filename_str):
        return 'charging'

    # 检查是否以 第xxxx期_yyyyMMdd_ 开头（普通）
    pattern_normal = r'^第\d+期_\d{8}_'
    if re.match(pattern_normal, filename_str):
        return 'normal'

    # 检查是否以 第xxxxx期_yyyyMMdd_ 开头（可能是其他系列）
    pattern_other = r'^第\d{5}期_\d{8}_'
    if re.match(pattern_other, filename_str):
        return 'normal'

    return 'unknown'

def get_target_path(source_file, up_name, video_target_base_dir):
    """获取视频文件的目标路径"""
    target_base = Path(video_target_base_dir)

    # 提取年份
    year, month = extract_year_month_from_filename(source_file.name)

    if year:
        if up_name == '有何高见9527':
            if int(month) < 7:
                target_path = target_base / up_name / f"{year}.01-06" / source_file.name
            else:
                target_path = target_base / up_name / f"{year}.07-12" / source_file.name
        else:
            target_path = target_base / up_name / year / source_file.name
    else:
        target_path = target_base / up_name / source_file.name
    
    # # 对于视频文件
    # if up_name == '有何高见9527':
    #     classification = classify_youhegaojian_file(source_file)
    #     if classification == 'charging':
    #         # 充电专属/年份目录
    #         return target_base / up_name / '充电专属' / year / source_file.name
    #     else:
    #         # 普通年份目录
    #         return target_base / up_name / year / source_file.name
    # else:
    #     # 其他UP主：UP主名/年份目录
    #     return target_base / up_name / year / source_file.name
    
    return target_path

def ensure_directory_exists(directory_path):
    """确保目录存在，如果不存在则创建"""
    directory_path.mkdir(parents=True, exist_ok=True)

def analyze_source_directory(source_dir):
    """分析源目录结构"""
    source_path = Path(source_dir)
    up_dirs = {}

    # 遍历源目录
    for item in source_path.iterdir():
        if item.is_dir():
            up_name = item.name
            up_dirs[up_name] = {
                'path': item,
                'mp4_files': [],
                'csv_files': [],
                'excel_files': []
            }

            # 遍历UP主目录中的文件
            for file_item in item.iterdir():
                if file_item.is_file():
                    if file_item.suffix.lower() == '.mp4':
                        up_dirs[up_name]['mp4_files'].append(file_item)
                    elif file_item.suffix.lower() == '.csv':
                        up_dirs[up_name]['csv_files'].append(file_item)
                    elif file_item.suffix.lower() in ['.xlsx', '.xls']:
                        up_dirs[up_name]['excel_files'].append(file_item)

        elif item.is_file():
            # 根目录下的CSV和Excel文件
            if item.suffix.lower() == '.csv':
                # 从文件名提取UP主名（去掉.csv）
                up_name = item.stem
                if up_name not in up_dirs:
                    up_dirs[up_name] = {
                        'path': source_path / up_name,
                        'mp4_files': [],
                        'csv_files': [],
                        'excel_files': []
                    }
                up_dirs[up_name]['csv_files'].append(item)
            elif item.suffix.lower() in ['.xlsx', '.xls']:
                up_name = item.stem
                if up_name not in up_dirs:
                    up_dirs[up_name] = {
                        'path': source_path / up_name,
                        'mp4_files': [],
                        'csv_files': [],
                        'excel_files': []
                    }
                up_dirs[up_name]['excel_files'].append(item)

    return up_dirs

def process_up_files(up_name, up_data, video_target_dir, csv_target_dir, dry_run=False):
    """处理一个UP主的文件"""
    input(
        f"\n开始处理 UP主 【{up_name}】: "
        f"\n  MP4文件: {len(up_data['mp4_files'])} 个"
        f"\n  CSV文件: {len(up_data['csv_files'])} 个"
        f"\n  Excel文件: {len(up_data['excel_files'])} 个"
        f"\n按回车键继续..."
    )

    # 记录目标已存在的原始文件路径
    already_exists_source_paths = []

    # 处理MP4文件（移动）
    mp4_moved = 0
    mp4_skipped = 0
    for mp4_file in up_data['mp4_files']:
        target_path = get_target_path(mp4_file, up_name, video_target_dir)

        # 确保目标目录存在
        ensure_directory_exists(target_path.parent)

        # 检查目标文件是否已存在
        if target_path.exists():
            print(f"  跳过（已存在）: {mp4_file.name} -> {target_path}")
            already_exists_source_paths.append({
                'up_name': up_name,
                'file_type': 'mp4',
                'source_path': str(mp4_file),
                'target_path': str(target_path)
            })
            mp4_skipped += 1
            continue

        if dry_run:
            print(f"  移动（模拟）: {mp4_file.name} -> {target_path}")
        else:
            try:
                # 移动文件
                shutil.move(str(mp4_file), str(target_path))
                print(f"  移动: {mp4_file.name} -> {target_path}")
                mp4_moved += 1
            except Exception as e:
                print(f"  错误移动 {mp4_file.name}: {e}")

    # 处理CSV和Excel文件（复制）
    csv_copied = 0
    csv_skipped = 0
    for csv_file in up_data['csv_files'] + up_data['excel_files']:
        target_path = get_target_path(csv_file, up_name, csv_target_dir)

        # 确保目标目录存在
        ensure_directory_exists(target_path.parent)

        # 检查目标文件是否已存在
        if target_path.exists():
            print(f"  跳过（已存在）: {csv_file.name} -> {target_path}")
            csv_skipped += 1
            continue

        if dry_run:
            print(f"  复制（模拟）: {csv_file.name} -> {target_path}")
        else:
            try:
                # 复制文件
                shutil.copy2(str(csv_file), str(target_path))
                # shutil.move(str(csv_file), str(target_path))

                print(f"  复制: {csv_file.name} -> {target_path}")
                csv_copied += 1
            except Exception as e:
                print(f"  错误复制 {csv_file.name}: {e}")

    return {
        'mp4_moved': mp4_moved,
        'mp4_skipped': mp4_skipped,
        'csv_copied': csv_copied,
        'csv_skipped': csv_skipped,
        'already_exists_source_paths': already_exists_source_paths
    }

def main():
    parser = argparse.ArgumentParser(description='移动B站视频文件到目标目录')
    parser.add_argument('--up', help='只处理指定的UP主（默认处理所有）')
    parser.add_argument('--dry-run', action='store_true', help='模拟运行，不实际移动文件')

    parser.add_argument('--source', default=SOURCE_ROOT_DIR, help='源目录路径')
    parser.add_argument('--video-target', default=VIDEO_DEST_ROOT_DIR, help='视频目标目录路径')
    parser.add_argument('--csv-target', default=CSV_DEST_ROOT_DIR, help='CSV目标目录路径')

    args = parser.parse_args()

    print(f"源目录: {args.source}")
    print(f"视频目标目录: {args.video_target}")
    print(f"CSV目标目录: {args.csv_target}")
    print(f"模拟运行: {args.dry_run}")
    if args.up:
        print(f"只处理UP主: {args.up}")

    # 检查源目录是否存在
    if not Path(args.source).exists():
        print(f"错误: 源目录不存在: {args.source}")
        return 1

    # 分析源目录
    print(f"\n分析源目录 : {args.source} ")
    up_dirs = analyze_source_directory(args.source)

    if not up_dirs:
        print("错误: 源目录中没有找到UP主文件")
        return 1

    print(f"找到 {len(up_dirs)} 个UP主")

    # 过滤UP主（如果指定了--up参数）
    if args.up:
        if args.up not in up_dirs:
            print(f"错误: 找不到UP主 '{args.up}'")
            return 1
        up_dirs = {args.up: up_dirs[args.up]}

    print(up_dirs)

    # 处理每个UP主的文件
    total_stats = {
        'mp4_moved': 0,
        'mp4_skipped': 0,
        'csv_copied': 0,
        'csv_skipped': 0
    }

    # 收集所有目标已存在的原始文件路径
    all_already_exists_source_paths = []

    for up_name, up_data in up_dirs.items():
        stats = process_up_files(up_name, up_data, args.video_target, args.csv_target, args.dry_run)
        for key in total_stats:
            total_stats[key] += stats[key]
        all_already_exists_source_paths.extend(stats.get('already_exists_source_paths', []))

    # 打印总结
    print(
        "\n" + "="*50
        + "\n总结:"
        + f"\n  MP4文件移动: {total_stats['mp4_moved']} 个"
        + f"\n  MP4文件跳过: {total_stats['mp4_skipped']} 个"
        + f"\n  CSV/Excel文件复制: {total_stats['csv_copied']} 个"
        + f"\n  CSV/Excel文件跳过: {total_stats['csv_skipped']} 个"
    )

    if args.dry_run:
        print("\n注意: 这是模拟运行，没有实际移动文件。")
        print("使用 --dry-run 参数进行模拟运行。")

    # 输出所有目标已存在的原始文件路径到 CSV
    output_csv_path = Path(args.source) / "dest_already_exists_source_paths.csv"
    with open(output_csv_path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=['up_name', 'file_type', 'source_path', 'target_path'])
        writer.writeheader()
        writer.writerows(all_already_exists_source_paths)

    if all_already_exists_source_paths:
        print(f"\n目标已存在的原始文件路径已输出到: {output_csv_path}")
        print(f"共 {len(all_already_exists_source_paths)} 条记录")
    else:
        print("\n没有目标已存在的文件。")

    return 0

if __name__ == '__main__':
    sys.exit(main())
