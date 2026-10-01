#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 此文件由 李总助手 创建，版权归属：513483905@qq.com
"""


使用示例：
    python update_output_file.py -u "有何高见9527"
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


def update_video_path(uploader, excel_file):
    """更新Excel中视频的路径"""
    df = pd.read_excel(excel_file)
    update_count = 0
    fail_count = 0
    not_find_list = []  # 记录未找到的视频

    for index, row in df.iterrows():
        output_file = row.output_file
        title = row.title
        new_title = row.new_title

        # 处理空值或NaN
        if pd.isna(output_file) or output_file == "":
            output_file = "NOT_FOUND"
        video_path = Path(output_file) if output_file != "NOT_FOUND" else None
        if video_path and video_path.exists():
            continue

        item = {
            "original_path": output_file,
            "title": title,
            "new_title": new_title
        }

        real_path = find_video_real_path(uploader, item)
        
        # 更新到 dataframe
        if real_path:
            df.loc[index, "output_file"] = real_path
            update_count += 1
            logger.success(f"[{title}] 更新路径: {real_path}")
        else:
            df.loc[index, "output_file"] = "DOWNLOAD FAIL"
            fail_count += 1
            not_find_list.append(f"{title}|{new_title}")
            logger.warning(f"[{title}] 未找到视频")

    save_excel(df, excel_file)
    
    # 输出未找到的视频到文件
    if not_find_list:
        not_find_file = Path(excel_file).parent / "not_find.txt"
        with open(not_find_file, "w", encoding="utf-8") as f:
            for item in not_find_list:
                f.write(item + "\n")
        logger.info(f"未找到的视频已保存到: {not_find_file}")
    
    logger.info(f"更新完成: 成功 {update_count} 个, 失败 {fail_count} 个")


def find_video_real_path(uploader, item):
    """找到视频新的真实地址"""
    from pathlib import Path
    
    new_dir = Path(f"E:\\00 视频\\Up主\\{uploader}")
    video_name_1 = f"{item['new_title']}.mp4"
    video_name_2 = f"{item['title']}.mp4"

    print("\nI want to find:")
    print(video_name_1)
    print(video_name_2)
    # input(f"excel output_path: {item['original_path']}")


    if not new_dir.exists():
        logger.warning(f"目录不存在: {new_dir}")
        return None
    
    __all_mp4 = new_dir.rglob("*.mp4")
    # print(__all_mp4)
    # input("回车继续")

    # 遍历目录查找视频文件（精确匹配）
    for video_file in __all_mp4:
        print(video_file)
        print(video_file.name)
        if video_file.name == video_name_1 or video_file.name == video_name_2:
            logger.info(f"找到视频: {video_file}")
            return str(video_file)

    logger.warning(f"未找到视频: {video_name_1} 或 {video_name_2}")
    # input(f"not found excel output_path: {item['original_path']} \n {video_name_1} \n {video_name_2}\n")
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
        description="找到视频位置，更新Excel里的output_file",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
    python update_video_path.py -u "有何高见9527"
        """
    )
    
    parser.add_argument("-u", "--uploader", help="UP主名称")
    parser.add_argument("--all", action="store_true", help="处理所有UP主的视频")
    
    args = parser.parse_args()
    
    uploader = args.uploader
    
    logger.info("=" * 60)
    logger.info(f"批量转文字处理")
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
        
        # 找出需要OCR的视频
        update_video_path(uploader, excel_path)
        


if __name__ == "__main__":
    main()
