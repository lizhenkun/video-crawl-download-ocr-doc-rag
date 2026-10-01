# !/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将视频 转 图片
"""
import os
import traceback
import pandas
from pathlib import Path
from moviepy import VideoFileClip

from app.config import config
from app.logger import logger


def picture_all():
    """下载所有配置的up主 在Excel中未下载且需要下载的视频"""
    for uploader_id, uper_info in config.bilibili_up_info.items():
        if uper_info.get("video_2_txt"):
            uper_info['id'] = uploader_id
            picture_up_videos(uper_info)


def picture_up_videos(uper_info):
    """将up主的视频转成图片"""
    uploader = uper_info['uploader']
    uploader_dir = os.path.join(config.output_root, uploader)

    excel_file = os.path.join(config.output_root, f'{uploader}.xlsx')
    df = pandas.read_excel(excel_file)
    if "转文字" not in df:
        df["转文字"] = ""

    # 兼容性
    df[["转文字"]] = df[["转文字"]].astype(str)
    df.fillna({"转文字": ""}, inplace=True)
        
    entries = os.listdir(uploader_dir)
    video_map = {}

    for file_name in entries:
        file_path = os.path.join(uploader_dir, file_name)
        file_type = file_path.rsplit('.', 1)[-1]
        logger.info(
            f'file type: {file_type}'
            f'\nfile path: {file_path}')

        if os.path.isfile(file_path) and file_type in ["mp4"]:
            file_name = os.path.basename(file_path).replace(f".{file_type}", "")
            sub_df = df[df.new_title == file_name]
            if not sub_df.empty and sub_df.iloc[0]["转文字"]:
                print("已经转图片了， 本次不再转了", sub_df.iloc[0]["转文字"])
                continue
            
            video_map[file_name] = file_path

    logger.info(f"需要转图片的: {video_map.keys()}")

    for title_name, video_file in video_map.items():
        try:
            pic_dir = audio_2_pictures(video_file, uper_info["cropped_kwargs"])
            df.loc[df.new_title == title_name, "转文字"] = pic_dir
        except:
            logger.warning(traceback.format_exc())
    
    # 更新转文字结果
    for i in range(3):
        try:
            df.to_excel(excel_file, index=False)
            logger.info(f"保存成功 : {excel_file}")
            break
        except:
            if i == 0:
                input(f"EXCEL {excel_file} 写入失败, 请关闭Excel, 然后按回车键继续...")
            else:
                raise
    return


def audio_2_pictures(video_file_path: str, cropped_kwargs, interval: float=0.5):
    """
    将 audio(例如: mp4) 以 每X秒 截取一张图片
    """
    file_dir = Path(video_file_path).parent
    file_name = os.path.basename(video_file_path).rsplit(".", 1)[0]

    logger.info(file_dir)

    pic_dir = file_dir / file_name
    if not os.path.exists(pic_dir):
        os.mkdir(pic_dir)

    record_list = []
    
    cliper = VideoFileClip(video_file_path)
    # 
    cliper = cliper.cropped(
        y1=cliper.h + cropped_kwargs["y1"],
        y2=cliper.h + cropped_kwargs["y2"]
    )

    movie_total_seconds = cliper.duration

    movie_total_second_str = str(int(movie_total_seconds))
    _len = len(movie_total_second_str) + 1

    logger.info(
        f"开始转video: {video_file_path}"
        f"\n视频时长(秒): {movie_total_second_str}"
        f"\n截图数量: {_len / interval} "
    )

    cur_second = 0
    index = 0
    while cur_second < movie_total_seconds:
        cur_second_str = str(cur_second).zfill(_len + 1)
        index_str = str(index).zfill(_len)

        png_file = Path(pic_dir) / f"{index_str}.png"

        cliper.save_frame(png_file, t=cur_second)

        record_list.append({
            "index": index,
            "cur_second": cur_second,
            "png_file": f"{index_str}.png",
            "text": ""
        })
        
        if index % 100 == 0:
            logger.info(f"{cur_second_str}s : {png_file}")

        cur_second += interval
        index += 1

    df = pandas.DataFrame(record_list)
    csv_file = pic_dir / f"{file_name}.csv"
    df.to_csv(csv_file)
    
    return pic_dir


def _test():
    # video_file_path = Path("D:\\") / "demo" / "2026-01-14 595 特朗普2025年经济政策如何影响世界经济？.mp4"
    video_file_path = "D:/demo/2026-01-14 595 特朗普2025年经济政策如何影响世界经济？.mp4"
    logger.info(video_file_path, type(video_file_path))
    audio_2_pictures(video_file_path)


if __name__ == '__main__':
    # python -m app.tools.picture_video
    # _test()
    picture_all()