# !/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将 audio(例如: mp4) 文件转换为图片
"""
import os
from pathlib import Path
from moviepy import VideoFileClip


def audio_2_pictures(file_path: str, interval: float=0.5):
    """
    将 audio(例如: mp4) 以 每X秒 截取一张图片
    """
    file_dir = Path(file_path).parent
    print(file_dir)

    pic_dir = file_dir / "pics"
    if not os.path.exists(pic_dir):
        os.mkdir(pic_dir)

    cliper = VideoFileClip(file_path)
    movie_total_seconds = cliper.duration
    print(movie_total_seconds)

    movie_total_second_str = str(int(movie_total_seconds))
    _len = len(movie_total_second_str) + 1
    print(_len)

    cur_second = 1
    index = 1
    while cur_second < movie_total_seconds:
        cur_second_str = str(cur_second).zfill(_len + 1)
        index_str = str(index).zfill(_len)

        png_file = Path(pic_dir) / f"{index_str}.png"
        cliper.save_frame(png_file, t=cur_second)
        
        print(f"{cur_second_str}s : {png_file}")

        cur_second += interval
        index += 1

    return 


def _test():
    # file_path = Path("D:\\") / "demo" / "2026-01-14 595 特朗普2025年经济政策如何影响世界经济？.mp4"
    file_path = "D:/demo/2026-01-14 595 特朗普2025年经济政策如何影响世界经济？.mp4"
    print(file_path, type(file_path))
    audio_2_pictures(file_path)


if __name__ == '__main__':
    # python -m skills.audio_2_pictures.scripts.audio_2_pictures
    _test()
