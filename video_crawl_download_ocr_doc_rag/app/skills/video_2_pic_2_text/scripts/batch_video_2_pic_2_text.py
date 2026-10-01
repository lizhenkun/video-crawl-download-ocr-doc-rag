#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 此文件由 李总助手 创建，版权归属：513483905@qq.com
"""
批量转文字处理脚本

功能：
- 扫描UP主的Excel文件
- 找出"转文字"列为空或为"NOT_FOUND"的视频
- 跳过 output_file = "会员视频" / 时长 = 0 / 转文字 = "无字幕" 的行
- 对存在的视频进行批量转文字处理
- 转换完成后更新"文字行数"到Excel

使用示例：
    python batch_video_2_pic_2_text.py -u "有何高见9527"
    python batch_video_2_pic_2_text.py -u "有何高见9527" --dry-run
"""
import argparse
import csv
import pandas as pd
import subprocess
from pathlib import Path
from typing import List, Dict

# 导入项目config获取output目录
import io
import sys
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
# 设置UTF-8输出
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")


from libs import config, logger


def is_empty(val):
    """判断单元格是否为空"""
    if pd.isna(val):
        return True
    return str(val).strip() == ""


def count_csv_data_rows(file_path):
    """统计 CSV 文件的数据行数（不含表头）。失败返回 None"""
    try:
        with open(file_path, "r", encoding="utf-8-sig", newline="") as f:
            reader = csv.reader(f)
            rows = list(reader)
        data_rows = [r for r in rows[1:] if any(cell.strip() for cell in r)]
        return len(data_rows)
    except Exception:
        return None


def get_excel_path(uploader: str) -> Path:
    """获取UP主的Excel文件路径"""
    output_dir = Path(config.excel_root)
    excel_path = output_dir / f"{uploader}.xlsx"
    if not excel_path.exists():
        raise FileNotFoundError(f"Excel文件不存在: {excel_path}")
    return excel_path


def find_videos_need_ocr(excel_path: Path) -> List[Dict]:
    """
    找出需要OCR处理的视频

    跳过条件：
    - output_file = "会员视频"
    - 时长 = 0
    - 转文字 = "无字幕"

    筛选条件：转文字 为空 或 NOT_FOUND
    """
    df = pd.read_excel(excel_path, sheet_name="Sheet1")
    if "转文字" not in df.columns:
        df["转文字"] = ""

    videos = []
    __skip_no_video = 0
    __skip_member = 0
    __skip_duration_zero = 0
    __skip_wuzimu = 0
    __found_count = 0

    # 筛选：转文字 为空 或 NOT_FOUND
    need_ocr = df[(df["转文字"].isna()) | (df["转文字"].astype(str).str.strip() == "NOT_FOUND")].copy()

    logger.info(f"\n扫描 {len(need_ocr)} 个\"转文字\"为空或为NOT_FOUND的视频...")

    for _, row in need_ocr.iterrows():
        output_file = row.get("output_file", "")
        new_title = row.get("new_title", "")
        title = row.get("title", "")
        duration = row.get("时长", None)
        bvid = row.get("bvid", "")
        idx_in_df = row.name  # 原始 DataFrame index

        # 跳过 会员视频
        if not is_empty(output_file) and str(output_file).strip() == "会员视频":
            __skip_member += 1
            continue

        # 跳过 时长 = 0
        if not is_empty(duration) and int(duration) == 0:
            __skip_duration_zero += 1
            continue

        # 跳过 无字幕（虽然此时转文字应该为空，但防御性检查）
        zhuan = row.get("转文字", "")
        if not is_empty(zhuan) and str(zhuan).strip() == "无字幕":
            __skip_wuzimu += 1
            continue

        # 检查是否有视频路径记录
        if is_empty(output_file):
            __skip_no_video += 1
            continue

        # 检查视频文件是否存在
        video_path = Path(str(output_file).strip())
        if not video_path.exists():
            __skip_no_video += 1
            continue

        __found_count += 1
        videos.append({
            "bvid": bvid,
            "title": title,
            "new_title": new_title,
            "output_file": str(output_file).strip(),
            "df_index": idx_in_df,
        })

    logger.info(f"  - 有效视频（待转换）: {__found_count}")
    logger.info(f"  - 跳过（会员视频）: {__skip_member}")
    logger.info(f"  - 跳过（时长=0）: {__skip_duration_zero}")
    logger.info(f"  - 跳过（无字幕）: {__skip_wuzimu}")
    logger.info(f"  - 跳过（无路径或文件不存在）: {__skip_no_video}")

    return videos


def process_video(video_info: Dict, python_exe: Path, script_path: Path, dry_run: bool = False) -> bool:
    """
    处理单个视频的OCR

    Returns:
        是否成功
    """
    video_path = video_info["output_file"]
    title = video_info["title"]
    bvid = video_info["bvid"]

    logger.info(f"\n处理: {title}")
    logger.info(f"  BV ID: {bvid}")
    logger.info(f"  视频路径: {video_path}")

    if dry_run:
        logger.info("  [DRY-RUN] 跳过实际处理")
        return True

    # 调用 video_2_pic_2_text.py 处理视频
    cmd = [
        str(python_exe),
        str(script_path),
        "-i", str(video_path),
    ]

    try:
        result = subprocess.run(
            cmd,
            text=True,
            timeout=3600 * 2,  # 2小时超时
        )

        if result.returncode == 0:
            logger.info("  [OK] 处理成功")
            return True
        else:
            logger.info(f"  [FAIL] 处理失败: {result.stderr[:200]}")
            return False

    except subprocess.TimeoutExpired:
        logger.info("  [FAIL] 处理超时")
        return False
    except Exception as e:
        logger.info(f"  [FAIL] 错误: {e}")
        return False


def find_csv_for_video(video_path: str, ocr_dir: str) -> str:
    """根据视频文件名找到对应的 _ocr.csv 文件"""
    video_name = Path(video_path).stem
    csv_pattern = f"{video_name}_ocr.csv"
    ocr_path = Path(ocr_dir)
    if ocr_path.exists():
        for f in ocr_path.rglob(csv_pattern):
            return str(f)
    return ""


def update_excel_row(excel_path: Path, df_index: int, csv_path: str, line_count: int):
    """更新Excel中指定行的 转文字 和 文字行数"""
    df = pd.read_excel(excel_path, sheet_name="Sheet1")

    # 更新 转文字
    df.at[df_index, "转文字"] = csv_path

    # 更新 文字行数
    duration = df.at[df_index, "时长"]
    if not is_empty(duration) and int(duration) > 0:
        if line_count < 10 * int(duration):
            df.at[df_index, "文字行数"] = -1
        else:
            df.at[df_index, "文字行数"] = line_count
    else:
        df.at[df_index, "文字行数"] = line_count

    df.to_excel(excel_path, sheet_name="Sheet1", index=False)


def main():
    parser = argparse.ArgumentParser(
        description="批量转文字处理 - 扫描Excel中未OCR的视频并处理",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
    python batch_video_2_pic_2_text.py -u "有何高见9527"
    python batch_video_2_pic_2_text.py -u "有何高见9527" --dry-run
    python batch_video_2_pic_2_text.py -u "有何高见9527" --limit 3
        """
    )

    parser.add_argument("-u", "--uploader", help="UP主名称")
    parser.add_argument("--all", action="store_true", help="处理所有UP主的视频")
    parser.add_argument("-y", action="store_true", help="自动确认")
    parser.add_argument("-d", "--dry-run", action="store_true", help="仅显示待处理视频，不实际执行")
    parser.add_argument("-l", "--limit", type=int, default=0, help="限制处理数量，0表示全部")

    args = parser.parse_args()

    uploader = args.uploader

    logger.info("=" * 60)
    logger.info("批量转文字处理")
    logger.info(f"UP主: {uploader}")
    logger.info(f"Excel目录: {config.excel_root}")
    logger.info("=" * 60)

    if args.uploader:
        uloader_dict = {}
        if args.uploader in config.bilibili_up_dict:
            uloader_dict[args.uploader] = config.bilibili_up_dict[args.uploader]
        else:
            for uloader_id, info in config.bilibili_up_dict.items():
                if args.uploader == info["uploader"]:
                    uloader_dict[uloader_id] = info
    elif args.all:
        uloader_dict = config.bilibili_up_dict
    else:
        logger.error("请提供UP主名称 -u up主名字/id 或使用 --all 参数")
        return

    for uploader_id, uploader_item in uloader_dict.items():
        uploader = uploader_item["uploader"]
        logger.info(f"\n\n开始处理: {uploader}")

        logger.info(f"Processing UP主: {uploader}")

        # 获取Excel路径
        try:
            excel_path = get_excel_path(uploader)
        except FileNotFoundError as e:
            logger.info(f"[ERROR] {e}")
            continue

        logger.info(f"\n[INFO] Excel文件: {excel_path}")

        # 找出需要OCR的视频
        videos = find_videos_need_ocr(excel_path)

        if not videos:
            logger.info("\n[OK] 没有需要处理的视频")
            continue

        logger.info(f"\n[INFO] 找到 {len(videos)} 个需要OCR的视频:")
        for i, v in enumerate(videos[:10], 1):
            v_title = v["title"]
            v_bvid = v["bvid"]
            logger.info(f"  {i}. {v_title[:50]}... (BV: {v_bvid})")

        if len(videos) > 10:
            logger.info(f"  ... 还有 {len(videos) - 10} 个")

        if args.limit > 0:
            videos = videos[:args.limit]
            logger.info(f"\n[INFO] 限制处理数量: {args.limit}")

        if args.dry_run:
            logger.info("\n[DRY-RUN] 跳过实际处理")
            continue

        # 确认是否继续
        if not args.y:
            logger.info(f"\n开始处理 {len(videos)} 个视频? (y/n)")
            response = input().strip().lower()
            if response != "y":
                logger.info("已取消")
                return

        # 准备脚本路径
        python_exe = "D:\\workspace\\video-crawl-download-ocr-doc-rag\\.venv\\Scripts\\python.exe"
        video_2_pic_2_text_script = SCRIPT_DIR / "video_2_pic_2_text.py"

        # OCR 目录
        ocr_dir = rf"D:\workspace\video-crawl-download-ocr-doc-rag\doc\{uploader}"

        logger.info(f"\n[INFO] Python: {python_exe}")
        logger.info(f"[INFO] 脚本: {video_2_pic_2_text_script}")

        # 逐个处理
        success_count = 0
        fail_count = 0

        for i, video in enumerate(videos, 1):
            print(f"\n[{i}/{len(videos)}] ", end="")
            if process_video(video, python_exe, video_2_pic_2_text_script, dry_run=args.dry_run):
                success_count += 1

                # 转换完成后，找到 CSV 并更新 Excel
                video_path = video["output_file"]
                csv_path = find_csv_for_video(video_path, ocr_dir)
                line_count = count_csv_data_rows(csv_path) if csv_path else 0

                logger.info(f"  视频路径: {video_path}")
                logger.info(f"  CSV 路径: {csv_path}")
                logger.info(f"  行数: {line_count}")

                # 更新 Excel
                update_excel_row(excel_path, video["df_index"], csv_path, line_count)
                logger.info("  Excel 已更新")
            else:
                fail_count += 1

        # 总结
        logger.info("\n" + "=" * 60)
        logger.info("处理完成!")
        logger.info(f"成功: {success_count}")
        logger.info(f"失败: {fail_count}")
        logger.info("=" * 60)


if __name__ == "__main__":
    main()
