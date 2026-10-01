#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 此文件由 李总助手 创建，版权归属：513483905@qq.com
"""

使用示例：
    python update_text_path.py -u "有何高见9527"
"""
import argparse

import pandas as pd
from pandas import DataFrame

# 导入项目config获取output目录
import io
import sys
from pathlib import Path
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
# 设置UTF-8输出
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


from libs import config, logger


def get_excel_path(uploader: str) -> Path:
    """获取UP主的Excel文件路径"""
    output_dir = Path(config.excel_root)
    excel_path = output_dir / f"{uploader}.xlsx"
    if not excel_path.exists():
        raise FileNotFoundError(f"Excel文件不存在: {excel_path}")
    return excel_path


def update_text_path(uploader, excel_file):
    """更新Excel中转文字的路径（CSV文件）"""
    df = pd.read_excel(excel_file)
    update_count = 0
    fail_count = 0
    not_find_list = []  # 记录未找到的文本

    for index, row in df.iterrows():
        text_path = row.get('转文字', '')
        title = row.title
        new_title = row.new_title

        # 处理空值或NaN
        if pd.isna(text_path) or text_path == "":
            text_path = "NOT_FOUND"

        if text_path != "NOT_FOUND":
            csv_path = Path(text_path)
            if csv_path.exists():
                continue

        item = {
            "original_path": text_path,
            "title": title,
            "new_title": new_title
        }

        real_path = find_text_real_path(uploader, item)

        # 更新到 dataframe
        if real_path:
            df.loc[index, '转文字'] = real_path
            update_count += 1
            logger.success(f"[{title}] 更新路径: {real_path}")
        else:
            df.loc[index, '转文字'] = "NOT_FOUND"
            fail_count += 1
            not_find_list.append(f"{title}|{new_title}")
            logger.warning(f"[{title}] 未找到文本")

    save_excel(df, excel_file)

    # 输出未找到的文本到文件
    if not_find_list:
        not_find_file = Path(excel_file).parent / "not_find_text.txt"
        with open(not_find_file, "w", encoding="utf-8") as f:
            for item in not_find_list:
                f.write(item + "\n")
        logger.info(f"未找到的文本已保存到: {not_find_file}")

    logger.info(f"更新完成: 成功 {update_count} 个, 失败 {fail_count} 个")


def find_text_real_path(uploader, item):
    """找到文本（CSV）新的真实地址"""
    from pathlib import Path

    # 视频目录
    video_dir = Path(f"E:\\00 视频\\Up主\\{uploader}")

    # 尝试查找 CSV 文件
    new_title = item['new_title']
    title = item['title']

    csv_name_1 = f"{new_title}_ocr.csv"
    csv_name_2 = f"{title}_ocr.csv"

    print("\nI want to find:")
    print(csv_name_1)
    print(csv_name_2)

    if not video_dir.exists():
        logger.warning(f"目录不存在: {video_dir}")
        return None

    # 遍历目录查找CSV文件（精确匹配）
    for csv_file in video_dir.rglob("*_ocr.csv"):
        print(csv_file)
        print(csv_file.name)
        if csv_file.name == csv_name_1 or csv_file.name == csv_name_2:
            logger.info(f"找到文本: {csv_file}")
            return str(csv_file)

    logger.warning(f"未找到文本: {csv_name_1} 或 {csv_name_2}")
    return None


def save_excel(df: DataFrame, excel_file: str):
    """保存Excel文件"""
    for i in range(3):
        try:
            df.to_excel(excel_file, index=False)
            logger.success(f"Excel已保存: {excel_file}")
            return
        except Exception as e:
            if i == 0:
                input(f"Excel {excel_file} 写入失败, 请关闭Excel, 按回车继续...")
            else:
                logger.error(f"保存失败: {e}")
                raise


def main():
    # 项目根目录
    parser = argparse.ArgumentParser(
        description="找到转文字CSV位置，更新Excel里的【转文字】列",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
    python update_text_path.py -u "有何高见9527"
        """
    )

    parser.add_argument("-u", "--uploader", help="UP主名称")
    parser.add_argument("--all", action="store_true", help="处理所有UP主的视频")

    args = parser.parse_args()

    uploader = args.uploader

    logger.info("=" * 60)
    logger.info(f"批量更新转文字路径")
    logger.info(f"UP主: {uploader}")
    logger.info(f"Excel目录: {config.excel_root}")
    logger.info("=" * 60)

    if args.uploader:
        uloader_dict = {}
        if args.uploader in config.bilibili_up_dict:
            uloader_dict[args.uploader] = config.bilibili_up_dict[args.uploader]
        else:
            for uloader_id, info in config.bilibili_up_dict.items():
                if args.uploader == info['uploader']:
                    uloader_dict[uloader_id] = info
    elif args.all:
        uloader_dict = config.bilibili_up_dict
    else:
        logger.error("请提供UP主名称 -u up主名字/id 或使用 --all 参数")
        return

    for uploader_id, uploader_item in uloader_dict.items():
        uploader = uploader_item['uploader']
        logger.info(f"\n\n开始处理: {uploader}")

        logger.info(f"Processing UP主: {uploader_item['uploader']}")

        # 获取Excel路径
        try:
            excel_path = get_excel_path(uploader)
        except FileNotFoundError as e:
            logger.info(f"[ERROR] {e}")
            continue

        logger.info(f"\n[INFO] Excel文件: {excel_path}")

        # 找出需要更新路径的转文字
        update_text_path(uploader, excel_path)



if __name__ == "__main__":
    main()
