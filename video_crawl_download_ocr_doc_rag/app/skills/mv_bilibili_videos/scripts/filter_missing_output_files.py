#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
filter_missing_output_files

用 pandas 读取 Excel，只增加两列：时长、文字行数。

逻辑（对齐 更新视频路径.py）：
- 时长：
  - output_file 为空 或 = "会员视频" → 时长 = 0
  - 否则读取 mp4 时长（分钟，向下取整）
- 文字行数：
  - 转文字 为空 或 = "无字幕" → 文字行数 = 0
  - 转文字 非空但文件不存在 → 清空转文字，文字行数 = 0
  - 转文字 非空且文件存在 → 读取行数
  - 如果 文字行数 < 10 * 时长 → 文字行数 = -1
"""
import csv
import struct
import sys
import argparse
from pathlib import Path
import pandas as pd

DEFAULT_XLSX_PATH = r"D:\workspace\video-crawl-download-ocr-doc-rag\output\有何高见9527.xlsx"


def is_empty(val):
    """判断单元格是否为空"""
    if pd.isna(val):
        return True
    return str(val).strip() == ""


def _read_box_header(f):
    """读取 MP4 box 的头部，返回 (size, box_type, header_size)"""
    header = f.read(8)
    if len(header) < 8:
        return None, None, None
    size, box_type = struct.unpack(">I4s", header)
    box_type = box_type.decode("ascii", errors="replace")
    header_size = 8
    if size == 1:
        ext = f.read(8)
        if len(ext) < 8:
            return None, None, None
        size = struct.unpack(">Q", ext)[0]
        header_size = 16
    elif size == 0:
        size = None
    return size, box_type, header_size


def get_mp4_duration_seconds(file_path):
    """解析 MP4 文件，返回时长（秒）。失败返回 None"""
    try:
        with open(file_path, "rb") as f:
            file_size = f.seek(0, 2)
            f.seek(0)
            moov_start = None
            moov_size = None
            while f.tell() < file_size:
                pos = f.tell()
                size, box_type, header_size = _read_box_header(f)
                if box_type is None:
                    break
                if box_type == "moov":
                    moov_start = pos
                    moov_size = size
                    break
                if size is not None:
                    f.seek(pos + size)
                else:
                    break
            if moov_start is None:
                return None
            f.seek(moov_start + 8)
            moov_end = moov_start + moov_size if moov_size else file_size
            while f.tell() < moov_end:
                pos = f.tell()
                size, box_type, header_size = _read_box_header(f)
                if box_type is None:
                    break
                if box_type == "mvhd":
                    version = struct.unpack(">B", f.read(1))[0]
                    f.read(3)
                    if version == 0:
                        f.read(8)
                        timescale = struct.unpack(">I", f.read(4))[0]
                        duration = struct.unpack(">I", f.read(4))[0]
                    else:
                        f.read(16)
                        timescale = struct.unpack(">I", f.read(4))[0]
                        duration = struct.unpack(">Q", f.read(8))[0]
                    if timescale == 0:
                        return None
                    return duration / timescale
                if size is not None:
                    f.seek(pos + size)
                else:
                    break
            return None
    except Exception:
        return None


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


def process_excel(xlsx_path):
    print(f"Excel 路径: {xlsx_path}")

    if not Path(xlsx_path).exists():
        print(f"错误: Excel 文件不存在: {xlsx_path}")
        return 1

    df = pd.read_excel(xlsx_path, sheet_name="Sheet1")
    print(f"Sheet1 总行数: {len(df)}")

    # 确保新增列存在
    if "时长" not in df.columns:
        df["时长"] = pd.NA
    if "文字行数" not in df.columns:
        df["文字行数"] = pd.NA
    df["时长"] = df["时长"].astype(object)
    df["文字行数"] = df["文字行数"].astype(object)

    duration_zero_count = 0
    line_negative_count = 0
    zhuan_cleared_count = 0

    for idx in df.index:
        output_file = df.at[idx, "output_file"]
        zhuan_file = df.at[idx, "转文字"]

        # ---- 时长 ----
        if is_empty(output_file) or str(output_file).strip() == "会员视频":
            df.at[idx, "时长"] = 0
            duration_zero_count += 1
        else:
            seconds = get_mp4_duration_seconds(str(output_file).strip())
            if seconds is not None:
                df.at[idx, "时长"] = int(seconds // 60)
            else:
                df.at[idx, "时长"] = 0
                duration_zero_count += 1

        # ---- 文字行数 ----
        duration_min = df.at[idx, "时长"]

        if is_empty(zhuan_file) or str(zhuan_file).strip() == "无字幕":
            df.at[idx, "文字行数"] = 0
        else:
            zhuan_path = Path(str(zhuan_file).strip())
            if not zhuan_path.exists():
                # 转文字 非空但文件不存在 → 清空
                df.at[idx, "转文字"] = ""
                df.at[idx, "文字行数"] = 0
                zhuan_cleared_count += 1
            else:
                line_count = count_csv_data_rows(str(zhuan_file).strip())
                if line_count is not None:
                    # if 文字行数 < 10 * 时长 → 文字行数 = -1
                    if line_count < 10 * int(duration_min):
                        df.at[idx, "文字行数"] = -1
                        line_negative_count += 1
                    else:
                        df.at[idx, "文字行数"] = line_count
                else:
                    df.at[idx, "文字行数"] = 0

    print(f"时长 = 0: {duration_zero_count} 条")
    print(f"文字行数 = -1 (异常): {line_negative_count} 条")
    print(f"清理转文字（文件不存在）: {zhuan_cleared_count} 条")

    # 保存
    df.to_excel(xlsx_path, sheet_name="Sheet1", index=False)
    print(f"\n已保存: {xlsx_path}")
    return 0


def main():
    parser = argparse.ArgumentParser(description="只增加 时长、文字行数 两列")
    parser.add_argument("--xlsx", default=DEFAULT_XLSX_PATH, help="Excel 文件路径")
    args = parser.parse_args()
    return process_excel(args.xlsx)


if __name__ == "__main__":
    sys.exit(main())
