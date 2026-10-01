#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import io
import csv
import os
import re
import struct
import pandas as pd
from pathlib import Path

# Windows下解决中文打印乱码
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# 配置路径
VIDEO_DIR = r"E:\00 视频\Up主\有何高见9527"
OCR_DIR = r"D:\workspace\video-crawl-download-ocr-doc-rag\doc\有何高见9527"
EXCEL_FILE = r"D:\workspace\video-crawl-download-ocr-doc-rag\output\有何高见9527.xlsx"


# ============================================================
# MP4 时长解析
# ============================================================

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


# ============================================================
# 原有逻辑
# ============================================================

def rename_files_in_folder(folder_path):
    """扫描文件夹，重命名符合格式的文件"""
    renamed_files = []

    for root, dirs, files in os.walk(folder_path):
        print(f"dirs: {dirs}")
        for filename in files:
            # 匹配格式: 第00001期_20230215_剩余名字.类型
            pattern = r"^第(\d{5})期_(\d{8})_(.+?)(\.\w+)$"
            match = re.match(pattern, filename)

            if match:
                episode_num = match.group(1)
                date_str = match.group(2)
                rest_name = match.group(3)
                ext = match.group(4)

                try:
                    year = int(date_str[:4])
                    if year < 2000 or year > 2100:
                        continue
                except:
                    continue

                new_date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
                new_filename = f"{new_date} 第{episode_num}期 {rest_name}{ext}"

                old_path = os.path.join(root, filename)
                new_path = os.path.join(root, new_filename)

                if old_path != new_path:
                    try:
                        os.rename(old_path, new_path)
                        renamed_files.append((old_path, new_path))
                        print(f"重命名: {filename} -> {new_filename}")
                    except Exception as e:
                        print(f"重命名失败 {filename}: {e}")

    return renamed_files


def convert_title_format(title):
    """转换标题格式"""
    if pd.isna(title):
        return title, False

    pattern = r"^第(\d{5})期_(\d{8})_(.+)$"
    match = re.match(pattern, str(title))

    if match:
        episode_num = match.group(1)
        date_str = match.group(2)

        try:
            year = int(date_str[:4])
            if year < 2000 or year > 2100:
                return title, False
        except:
            return title, False

        rest_name = match.group(3)

        new_date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
        new_title = f"{new_date} 第{episode_num}期 {rest_name}"
        return new_title, True

    return title, False


def find_file_in_directory(directory, filename_pattern):
    """在目录中查找文件"""
    if not os.path.exists(directory):
        return None

    dir_path = Path(directory)

    for file_path in dir_path.rglob(filename_pattern):
        return str(file_path)

    return None


# ============================================================
# 主流程
# ============================================================

def main():
    print("=" * 60)
    print("Step 1: 重命名文件夹中的文件")
    print("=" * 60)

    print(f"\n扫描目录: {VIDEO_DIR}")
    rename_files_in_folder(VIDEO_DIR)

    print(f"\n扫描目录: {OCR_DIR}")
    rename_files_in_folder(OCR_DIR)

    print("\n" + "=" * 60)
    print("Step 2: 处理Excel文件")
    print("=" * 60)

    # 读取Excel
    df = pd.read_excel(EXCEL_FILE)

    print(f"\nExcel列名: {df.columns.tolist()}")

    # 查找output_file和转文字列
    output_file_col = None
    ocr_col = None

    for col in df.columns:
        if "output_file" in col.lower() or "output" in col.lower():
            output_file_col = col
        if "转文字" in col or "ocr" in col.lower():
            ocr_col = col

    print(f"output_file列: {output_file_col}")
    print(f"转文字列: {ocr_col}")

    # 确保新增列存在
    if "时长" not in df.columns:
        df["时长"] = pd.NA
    if "文字行数" not in df.columns:
        df["文字行数"] = pd.NA
    df["时长"] = df["时长"].astype(object)
    df["文字行数"] = df["文字行数"].astype(object)

    short_video_count = 0

    # 更新每一行
    for idx, row in df.iterrows():
        new_title = row["new_title"]

        # 1. 转换标题格式
        converted_title, was_converted = convert_title_format(new_title)
        if was_converted:
            df.at[idx, "new_title"] = converted_title
            new_title = converted_title
            print(f"行 {idx}: 转换标题 -> {new_title}")

        # 2. 查找mp4文件
        if output_file_col and pd.notna(new_title):
            mp4_pattern = f"{new_title}.mp4"
            mp4_path = find_file_in_directory(VIDEO_DIR, mp4_pattern)

            if mp4_path:
                df.at[idx, output_file_col] = mp4_path
                print(f"  找到MP4: {mp4_path}")
            else:
                # 尝试其他扩展名
                for ext in [".m4a", ".mkv", ".avi"]:
                    mp4_pattern = f"{new_title}{ext}"
                    mp4_path = find_file_in_directory(VIDEO_DIR, mp4_pattern)
                    if mp4_path:
                        df.at[idx, output_file_col] = mp4_path
                        print(f"  找到MP4: {mp4_path}")
                        break

        # 3. 查找ocr csv文件
        if ocr_col and pd.notna(new_title):
            csv_pattern = f"{new_title}_ocr.csv"
            csv_path = find_file_in_directory(OCR_DIR, csv_pattern)

            if csv_path:
                df.at[idx, ocr_col] = csv_path
                print(f"  找到OCR: {csv_path}")

        # 4. 判断视频时长，< 10分钟删除视频和csv
        output_file = df.at[idx, output_file_col] if output_file_col else ""
        if pd.notna(output_file) and str(output_file).strip():
            seconds = get_mp4_duration_seconds(str(output_file).strip())
            if seconds is not None and seconds < 600:  # < 10分钟
                print(f"  视频时长 < 10分钟 ({int(seconds)}s)，删除: {output_file}")
                # 删除视频文件
                try:
                    os.remove(str(output_file).strip())
                except Exception as e:
                    print(f"  删除视频失败: {e}")
                # 删除对应的csv文件
                if ocr_col:
                    ocr_val = df.at[idx, ocr_col]
                    if pd.notna(ocr_val) and str(ocr_val).strip():
                        try:
                            os.remove(str(ocr_val).strip())
                            print(f"  删除CSV: {ocr_val}")
                        except Exception as e:
                            print(f"  删除CSV失败: {e}")
                # 设置标记
                df.at[idx, output_file_col] = "会员视频"
                if ocr_col:
                    df.at[idx, ocr_col] = ""
                short_video_count += 1

    print(f"\n短视频删除: {short_video_count} 条")

    print("\n" + "=" * 60)
    print("Step 3: 计算时长和文字行数")
    print("=" * 60)

    # 计算时长和文字行数
    for idx, row in df.iterrows():
        output_file = df.at[idx, output_file_col] if output_file_col else ""
        zhuan_file = df.at[idx, ocr_col] if ocr_col else ""

        # 时长
        if pd.isna(output_file) or not str(output_file).strip():
            df.at[idx, "时长"] = 0
        elif str(output_file).strip() == "会员视频":
            df.at[idx, "时长"] = 0
        else:
            seconds = get_mp4_duration_seconds(str(output_file).strip())
            if seconds is not None:
                df.at[idx, "时长"] = int(seconds // 60)
            else:
                df.at[idx, "时长"] = 0

        # 文字行数
        duration_min = df.at[idx, "时长"]

        if pd.isna(zhuan_file) or not str(zhuan_file).strip() or str(zhuan_file).strip() == "无字幕":
            df.at[idx, "文字行数"] = 0
        else:
            zhuan_path = Path(str(zhuan_file).strip())
            if not zhuan_path.exists():
                # 转文字 非空但文件不存在 → 清空
                df.at[idx, ocr_col] = ""
                df.at[idx, "文字行数"] = 0
            else:
                line_count = count_csv_data_rows(str(zhuan_file).strip())
                if line_count is not None:
                    # if 文字行数 < 10 * 时长 → 文字行数 = -1
                    if line_count < 10 * int(duration_min):
                        df.at[idx, "文字行数"] = -1
                    else:
                        df.at[idx, "文字行数"] = line_count
                else:
                    df.at[idx, "文字行数"] = 0

    # 统计
    duration_zero = (df["时长"] == 0).sum()
    line_neg = (df["文字行数"] == -1).sum()
    print(f"时长 = 0: {duration_zero} 条")
    print(f"文字行数 = -1 (异常): {line_neg} 条")

    # 保存Excel
    output_excel = EXCEL_FILE
    df.to_excel(output_excel, index=False)
    print(f"\n已保存更新后的Excel到: {output_excel}")


if __name__ == "__main__":
    main()
