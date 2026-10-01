# !/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Authors: 坤叔(1292746975@qq.com)
"""

from moviepy import VideoFileClip



def cut_video(video_file, end_second: int, start_second=0):
    """
    剪切视频

    end_second: 例如 想剪切视频，保留前5分10秒, end_second = 310
    """
    cliper = VideoFileClip(video_file)
    # 加载视频文件
    cliper = cliper.subclip(start_second, end_second)

    # 输出剪切后的视频
    cliper.write_videofile("trimmed_video.mp4", codec="libx264", audio_codec="aac")

