#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频转图片再转文字 - 流水线处理

特性：
- 流水线模式：截图和OCR并行执行，大幅提升效率
- 断点续传：支持中断后继续处理
- 实时写入：每识别完立即写入CSV，无需等待全部完成
- 多进程：使用多进程充分利用多核CPU
- 时间范围：支持指定开始和结束时间，只处理指定区间的视频

使用示例：
    python video_2_pic_2_text.py -i "视频文件.mp4" -d "输出目录"
    # 处理指定时间范围
    python video_2_pic_2_text.py -i "视频文件.mp4" --start 60 --end 120
"""
import argparse
import os
import sys
import re
import csv
import json
import shutil
import threading
import multiprocessing
from pathlib import Path
import traceback
from typing import Tuple
from queue import Empty
from dataclasses import dataclass

import pandas as pd

# 添加项目根目录到路径
SCRIPT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPT_DIR))

from libs import config, logger

# 全局OCR实例（在子进程中初始化）
_ocr_instance = None


def get_ocr_instance():
    """获取PaddleOCR实例（延迟初始化）"""
    global _ocr_instance

    # 使用 PaddleOCR
    from paddleocr import PaddleOCR
    if _ocr_instance is None:
        logger.info("初始化 PaddleOCR...")
        _ocr_instance = PaddleOCR(
            ocr_version="PP-OCRv4",
            precision='fp16',
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
            use_textline_orientation=False,
        )
        logger.info("PaddleOCR 初始化完成")
    return _ocr_instance


@dataclass
class FrameInfo:
    """帧信息数据类"""
    index: int
    timestamp: float
    image_path: str


def _screenshot_worker(
    video_path: str,
    start_timestamp: float,
    queue: multiprocessing.Queue,
    progress_file: Path,
    stop_event: multiprocessing.Event,
    **kwargs
):
    """
    截图工作进程（生产者）
    
    从视频中按时间间隔截取帧，放入队列
    """
    from moviepy import VideoFileClip
    
    video_path = Path(video_path)
    pic_dir = Path(kwargs["pic_dir"])
    pic_dir.mkdir(parents=True, exist_ok=True)

    interval = kwargs["interval"]
    crop_y1 = kwargs["crop_y1"]
    crop_y2 = kwargs["crop_y2"]
    start_time = kwargs.get("start_time")
    end_time = kwargs.get("end_time")
    
    logger.info(f"[Screenshot] 开始截图: {video_path}")
    logger.info(f"[Screenshot] 输出目录: {pic_dir}")
    logger.info(f"[Screenshot] 截图间隔: {interval}秒")
    logger.info(f"[Screenshot] 起始时间戳: {start_timestamp}")
    if start_time is not None or end_time is not None:
        logger.info(f"[Screenshot] 时间范围: {start_time or 0}s ~ {end_time or '结束'}s")
    
    try:
        clip = VideoFileClip(str(video_path))
        
        # 裁剪视频（用于去掉水印）
        if crop_y1 != 0 or crop_y2 != 0:
            clip = clip.cropped(
                y1=clip.h + crop_y1,
                y2=clip.h + crop_y2
            )
        
        duration = clip.duration
        
        # 确定实际处理的时间范围
        actual_start = start_timestamp if start_timestamp > 0 else (start_time if start_time else 0)
        actual_end = end_time if end_time else duration
        
        # 确保范围有效
        if actual_end > duration:
            actual_end = duration
        if actual_start < 0:
            actual_start = 0
            
        logger.info(f"[Screenshot] 视频时长: {duration}秒")
        logger.info(f"[Screenshot] 实际处理范围: {actual_start:.2f}s ~ {actual_end:.2f}s")
        
        # 计算时间格式化宽度
        time_width = len(str(int(duration))) + 1
        
        # 从起始时间戳开始
        cur_time = actual_start
        index = int(actual_start / interval)
        
        while cur_time < actual_end and not stop_event.is_set():
            # 生成文件名
            index_str = str(index).zfill(time_width + 1)
            image_path = pic_dir / f"{index_str}.png"
            
            # 保存帧
            clip.save_frame(str(image_path), t=cur_time)
            
            # 放入队列
            frame_info = FrameInfo(
                index=index,
                timestamp=cur_time,
                image_path=str(image_path)
            )
            queue.put(frame_info)
            
            logger.info(f"[Screenshot] 已截图: {cur_time:.2f}s -> {image_path.name}")
            
            # 更新进度
            save_progress(progress_file, cur_time, index, video_path)
            
            cur_time += interval
            index += 1
        
        clip.close()
        
        # 发送结束信号
        queue.put(None)
        
        logger.info(f"[Screenshot] 截图完成，共 {index} 张")
        
    except Exception as e:
        logger.error(f"[Screenshot] 截图失败: {e}")
        queue.put(None)
        raise


def _ocr_worker(
    queue: multiprocessing.Queue,
    stop_event: multiprocessing.Event,
    **kwargs
):
    """
    OCR工作进程（消费者）
    
    从队列中取出图片，识别文字，写入CSV
    """
    global _ocr_instance

    csv_file: Path = Path(kwargs["csv_file"])
    skip_line_pattern: str = kwargs["skip_line_pattern"]
    probability_threshold: float = kwargs["probability_threshold"]
    
    # 延迟初始化OCR
    ocr = get_ocr_instance()
    
    # 用于去重
    prev_lines = []
    
    logger.info(f"[OCR] 开始OCR识别")
    
    # CSV写入锁
    csv_lock = threading.Lock()
    
    processed_count = 0
    
    # 编译跳过模式正则
    if skip_line_pattern:
        skip_regex = re.compile(skip_line_pattern)
    else:
        skip_regex = re.compile(r'^$')
    
    while not stop_event.is_set():
        try:
            # 从队列获取任务，设置超时
            frame_info = queue.get(timeout=1)
            
            # 收到结束信号
            if frame_info is None:
                logger.info(f"[OCR] 收到结束信号，处理完成")
                break
            
            image_path = frame_info.image_path
            timestamp = frame_info.timestamp
            
            logger.debug(f"[OCR] 开始识别: {image_path}")
            
            try:
                # 执行OCR识别（参考 pic_2_text.py 的实现）
                ocr_result_list = ocr.predict(image_path)
                
                new_items = []
                new_lines = []
                
                for item in ocr_result_list:
                    for index, line in enumerate(item["rec_texts"]):
                        probability = item["rec_scores"][index]
                        
                        # 跳过已存在的
                        if line in prev_lines:
                            continue
                        # 跳过低置信度
                        if probability < probability_threshold:
                            continue
                        # 跳过匹配模式的行
                        if skip_regex.search(line):
                            continue
                        
                        new_lines.append(line)
                        new_items.append({
                            'movie_cur_seconds': timestamp,
                            'probability': probability,
                            'line': line
                        })
                        break  # 只取第一行
                
                # 更新已识别行记录（只保留最近100条）
                if new_lines:
                    prev_lines = new_lines + prev_lines
                    prev_lines = prev_lines[:100]
                
                # 立即写入CSV（线程安全）
                if new_items:
                    with csv_lock:
                        write_header = not csv_file.exists()
                        with open(csv_file, 'a', newline='', encoding='utf-8') as f:
                            fieldnames = ['movie_cur_seconds', 'probability', 'line']
                            writer = csv.DictWriter(f, fieldnames=fieldnames)
                            if write_header:
                                writer.writeheader()
                            writer.writerows(new_items)
                    
                    logger.info(f"[OCR] 识别到 {len(new_items)} 条文本: {new_items[0]['line'][:30]}...")
                else:
                    # 没有识别到文字，删除图片以节省空间
                    try:
                        os.remove(image_path)
                    except Exception:
                        pass
                
                processed_count += 1
                if processed_count % 50 == 0:
                    logger.info(f"[OCR] 已处理: {processed_count} 张")
                
            except Exception as e:
                logger.warning(f"[OCR] 识别失败 {image_path}: {e}")
                continue
                
        except Empty:
            # 队列为空，继续等待
            continue
        except Exception as e:
            logger.error(f"[OCR] 处理异常: {e}")
            continue
    
    logger.info(f"[OCR] OCR处理完成，共处理 {processed_count} 张图片")


def load_progress(progress_file: Path) -> Tuple[float, int]:
    """
    加载进度文件
    
    Returns:
        Tuple[float, int]: (最后时间戳, 最后索引)
    """
    if not progress_file.exists():
        return 0.0, 0
    
    try:
        with open(progress_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data.get('last_timestamp', 0.0), data.get('last_index', 0)
    except Exception as e:
        logger.warning(f"读取进度文件失败: {e}")
        return 0.0, 0


def save_progress(progress_file: Path, timestamp: float, index: int, video_path: Path):
    """保存进度"""
    progress_data = {
        "last_timestamp": timestamp,
        "last_index": index,
        "video_path": str(video_path)
    }
    with open(progress_file, 'w', encoding='utf-8') as f:
        json.dump(progress_data, f)


def video_2_pic_2_text(
    video_path: str,
    resume: bool = True,
    **kwargs
) -> str:
    """
    视频转图片再转文字（流水线模式）
    
    Args:
        video_path: 视频文件路径
        output_dir: 输出目录（默认: 视频所在文件夹/视频名/）

        config:
            interval: 截图间隔（秒）
            crop_y1: 裁剪起始Y坐标
            crop_y2: 裁剪结束Y坐标
            skip_line_pattern: 跳过匹配该正则表达式的行
            probability_threshold: 识别置信度阈值
            resume: 是否断点续传
        
    Returns:
        str: CSV文件路径
    """
    video_path = Path(video_path)
    if not video_path.exists():
        raise FileNotFoundError(f"视频文件不存在: {video_path}")
    
    video_dir = Path(os.path.dirname(video_path))
    pic_dir = video_dir / video_path.stem

    # 进度文件
    progress_file = pic_dir / ".progress.json"
    # CSV文件
    csv_file = video_dir / f"{video_path.stem}_ocr.csv"
    if os.path.exists(csv_file):
        return csv_file

    kwargs["video_dir"] = str(video_dir)
    kwargs["pic_dir"] = str(pic_dir)
    kwargs["csv_file"] = str(csv_file)
    
    # 添加时间范围参数
    logger.info(f"="*50)
    logger.info(f"开始处理: {video_path.name}")
    logger.info(f"截图输出目录: {pic_dir}")
    logger.info(f"="*50)
    
    # 断点续传 -- 有bug， 用不了
    start_timestamp = 0.0
    # if resume and progress_file.exists():
    #     start_timestamp, last_index = load_progress(progress_file)
    #     if start_timestamp > 0:
    #         logger.info(f"检测到已有进度，从 {start_timestamp:.2f}秒 处继续")
    
    # 创建队列和事件
    queue = multiprocessing.Queue(maxsize=100)
    stop_event = multiprocessing.Event()
    
    # 启动截图进程（生产者）
    screenshot_process = multiprocessing.Process(
        target=_screenshot_worker,
        args=(
            str(video_path),
            start_timestamp,
            queue,
            progress_file,
            stop_event
        ),
        name="ScreenshotWorker",
        kwargs=kwargs
    )
    screenshot_process.start()
    
    # 启动OCR进程（消费者）
    ocr_process = multiprocessing.Process(
        target=_ocr_worker,
        args=(
            queue,
            stop_event,
        ),
        name="OcrWorker",
        kwargs=kwargs,
    )
    ocr_process.start()
    
    # 等待截图进程完成
    screenshot_process.join()
    
    # 等待OCR进程完成
    ocr_process.join()
    
    # OCR处理完成后，删除截图目录，只保留CSV结果
    try:
        if pic_dir.exists() and pic_dir.is_dir():
            shutil.rmtree(pic_dir)
            logger.info(f"已删除截图目录: {pic_dir}")
        # 删除进度文件
        if progress_file.exists():
            progress_file.unlink()
            logger.info(f"已删除进度文件: {progress_file}")
    except Exception as e:
        logger.warning(f"清理截图目录失败: {e}")
    
    logger.info(f"="*50)
    logger.info(f"处理完成!")
    logger.info(f"结果保存至: {csv_file}")
    logger.info(f"="*50)
    
    return str(csv_file)


def _update_excel_with_csv_path(video_path: str, csv_file: str, uploader: str):
    """
    更新 uploader 的 Excel 文件的【转文字】列为 csv_file 路径
    
    Args:
        video_path: 视频文件路径
        csv_file: CSV文件路径
        uploader: UP主名称
    """
    video_path = Path(video_path)
    video_name = video_path.stem  # 去掉扩展名后的文件名
    
    # Excel 文件路径（在 output 目录下）
    excel_file = Path(config.excel_root) / f"{uploader}.xlsx"
    logger.info(f"uploader Excel 文件: {excel_file}")
    
    if not excel_file.exists():
        logger.warning(f"Excel 文件不存在: {excel_file}")
        return
    
    try:
        # 读取 Excel
        df = pd.read_excel(excel_file)

        df['转文字'] = df['转文字'].astype(str)
        
        # 查找对应的视频行
        updated = False
        for idx, row in df.iterrows():
            # 检查 title 或 output_file 是否包含视频名
            title = str(row.get('new_title', ''))
            output_file = str(row.get('output_file', ''))
            
            if video_name in title or video_name in output_file:
                # 更新【转文字】列
                df.at[idx, 'output_file'] = str(video_path)
                df.at[idx, '转文字'] = str(csv_file)
                updated = True
                logger.info(f"已更新 Excel 行 {idx}: {title[:30]}...")
                break
        
        if updated:
            # 保存 Excel

            for i in range(4):
                try:
                    df.to_excel(excel_file, index=False)
                except Exception as e:
                    logger.warning(f'{excel_file} 保存失败 , 请关闭文件后再试, Exception : {e}')
                    enter = input("按任意键继续重试 , 输入 [break] 结束")
                    if enter == "break":
                        break

            logger.info(f"Excel 已更新: {excel_file}")
        else:
            logger.warning(f"未找到对应的视频行: {video_name}")
            
    except Exception as e:
        logger.error(f"更新 Excel 失败: {e}\n{traceback.format_exc()}")


def main():
    parser = argparse.ArgumentParser(
        description="视频转图片再转文字 - 流水线处理",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
    python video_2_pic_2_text.py -i "视频文件.mp4"
    python video_2_pic_2_text.py -i "视频文件.mp4" -d "输出目录"
    python video_2_pic_2_text.py -i "视频文件.mp4" --interval 1.0
    python video_2_pic_2_text.py -i "视频文件.mp4" --no-resume
    python video_2_pic_2_text.py -i "视频文件.mp4" --start 60 --end 120
        """
    )
    parser.add_argument("-i", "--input", required=True, help="输入视频文件路径")
    parser.add_argument("--no-resume", action="store_true", help="禁用断点续传")
    parser.add_argument("-d", "--dir", help="输出目录路径（默认: 视频所在文件夹/视频名/）")
    parser.add_argument("--interval", type=float, help="截图间隔（秒）")
    parser.add_argument("--crop-y1", type=int, help="裁剪起始Y坐标")
    parser.add_argument("--crop-y2", type=int, help="裁剪结束Y坐标")
    parser.add_argument("--skip-pattern", type=str, default='', help="跳过匹配该正则表达式的行")
    parser.add_argument("--threshold", type=float, help="识别置信度阈值")
    parser.add_argument("--start", type=float, help="开始时间（秒），例如: 60 表示从第60秒开始")
    parser.add_argument("--end", type=float, help="结束时间（秒），例如: 120 表示处理到第120秒结束")

    args = parser.parse_args()

    kwargs = None

    video_path = args.input.replace('\\', '/')

    for up_config in config.bilibili_up_dict.values():
        # logger.info(up_config)
        uploader = up_config["uploader"]
        if video_path.find(f"/{uploader}/") != -1:
            kwargs = up_config
            break

    if kwargs is None:
        kwargs = config.bilibili_up_dict["default"]

    uploader = kwargs["uploader"]

    kwargs = kwargs.copy()
    if args.interval:
        kwargs["interval"] = args.interval
    if args.crop_y1:
        kwargs["crop_y1"] = args.crop_y1
    if args.crop_y2:
        kwargs["crop_y2"] = args.crop_y2
    if args.skip_pattern:
        kwargs["skip_line_pattern"] = args.skip_pattern
    if args.threshold:
        kwargs["probability_threshold"] = args.threshold
    if not kwargs.get("probability_threshold"):
        kwargs["probability_threshold"] = 0.93
    # 处理时间范围参数
    if args.start is not None:
        kwargs["start_time"] = args.start
    if args.end is not None:
        kwargs["end_time"] = args.end

    # input(f"开始处理: {args} , 回车继续:")

    csv_file = video_2_pic_2_text(
        video_path=args.input,
        resume=not args.no_resume,
        **kwargs
    )
    logger.info(f"csv file: {csv_file}")

    csv_file = mv_csv_file(csv_file)
    
    # 如果 uploader 不是 default，更新 Excel 的【转文字】列
    if uploader != "default":
        _update_excel_with_csv_path(
            video_path=args.input,
            csv_file=csv_file,
            uploader=uploader
        )

    return csv_file


def extract_year_month_from_filename(filename):
    """从文件名中提取年份, 月份"""
    # 尝试匹配 yyyy-mm-dd 模式
    date_pattern1 = r'(\d{4})-(\d{2})-\d{2}'
    match1 = re.search(date_pattern1, filename)
    if match1:
        print(filename)
        print(match1.group(1))
        print(match1.group(2))
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


def mv_csv_file(csv_file):
    logger.info("将csv 文件移动到 指定位置 D:\\workspace\\video-crawl-download-ocr-doc-rag\\doc")
    ocr_root_dir = Path("D:\\workspace\\video-crawl-download-ocr-doc-rag\\doc")

    # D:\\workspace\\video-crawl-download-ocr-doc-rag\\output\\有何高见9527
    dir_name = os.path.dirname(csv_file)
    basename = os.path.basename(dir_name)
    target_path = ocr_root_dir / basename

    filename = os.path.basename(csv_file)
    year, month = extract_year_month_from_filename(filename)
    if year:
        if int(month) < 7:
            target_path = target_path / f"{year}.01-06"
        else:
            target_path = target_path / f"{year}.07-12"

    os.makedirs(target_path, exist_ok=True)

    new_csv_file = target_path / filename
    logger.info(f"mv csv_file : {csv_file} to {new_csv_file}")

    if not os.path.exists(new_csv_file):
        shutil.move(str(csv_file), str(target_path))

    return str(new_csv_file)


if __name__ == "__main__":
    main()
    # _test_mv_csv_file()
