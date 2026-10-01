#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
delete_source_when_target_exists skill

根据 dest_already_exists_source_paths.csv，
如果目标文件已存在，则删除对应的源文件。

CSV 列：up_name, file_type, source_path, target_path
"""
import os
import csv
import sys
import argparse
from pathlib import Path

DEFAULT_CSV_PATH = r"D:\workspace\video-crawl-download-ocr-doc-rag\output\dest_already_exists_source_paths.csv"


def read_csv_records(csv_path):
    """读取 CSV 记录"""
    records = []
    with open(csv_path, 'r', newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            records.append(row)
    return records


def delete_source_when_target_exists(csv_path, dry_run=False, up_name=None):
    """根据 CSV 删除目标已存在的源文件"""
    print(f"CSV 路径: {csv_path}")
    print(f"模拟运行: {dry_run}")
    if up_name:
        print(f"只处理UP主: {up_name}")
    print()

    # 检查 CSV 是否存在
    if not Path(csv_path).exists():
        print(f"错误: CSV 文件不存在: {csv_path}")
        return {'deleted': 0, 'target_not_exist': 0, 'source_not_found': 0, 'failed': 0}

    # 读取记录
    records = read_csv_records(csv_path)

    # 过滤 UP 主
    if up_name:
        records = [r for r in records if r.get('up_name') == up_name]

    if not records:
        print("CSV 中没有记录")
        return {'deleted': 0, 'target_not_exist': 0, 'source_not_found': 0, 'failed': 0}

    print(f"共读取 {len(records)} 条记录")

    deleted = 0
    target_not_exist = 0
    source_not_found = 0
    failed = 0

    for i, record in enumerate(records, 1):
        source_path = Path(record['source_path'])
        target_path = Path(record['target_path'])
        up = record.get('up_name', '')
        ftype = record.get('file_type', '')

        print(f"[{i}/{len(records)}] {up} ({ftype})")
        print(f"  源文件: {source_path}")
        print(f"  目标文件: {target_path}")

        # 检查目标文件是否存在
        if not target_path.exists():
            print(f"  跳过：目标文件不存在")
            target_not_exist += 1
            continue

        # 检查源文件是否存在
        if not source_path.exists():
            print(f"  跳过：源文件不存在")
            source_not_found += 1
            continue

        if dry_run:
            print(f"  删除（模拟）: {source_path.name}")
            deleted += 1
        else:
            try:
                os.remove(str(source_path))
                print(f"  已删除源文件: {source_path.name}")
                deleted += 1
            except Exception as e:
                print(f"  错误删除 {source_path.name}: {e}")
                failed += 1

    return {
        'deleted': deleted,
        'target_not_exist': target_not_exist,
        'source_not_found': source_not_found,
        'failed': failed
    }


def main():
    parser = argparse.ArgumentParser(description='根据 CSV 删除目标已存在的源文件')
    parser.add_argument('--csv', default=DEFAULT_CSV_PATH, help='CSV 文件路径')
    parser.add_argument('--up', help='只处理指定的UP主')
    parser.add_argument('--dry-run', action='store_true', help='模拟运行，不实际删除文件')

    args = parser.parse_args()

    stats = delete_source_when_target_exists(
        args.csv,
        dry_run=args.dry_run,
        up_name=args.up
    )

    # 打印总结
    print("\n" + "="*50)
    print("总结:")
    print(f"  已删除源文件: {stats['deleted']} 个")
    print(f"  目标不存在（跳过）: {stats['target_not_exist']} 个")
    print(f"  源文件不存在（跳过）: {stats['source_not_found']} 个")
    print(f"  删除失败: {stats['failed']} 个")

    if args.dry_run:
        print("\n注意: 这是模拟运行，没有实际删除文件。")

    return 0


if __name__ == '__main__':
    sys.exit(main())
