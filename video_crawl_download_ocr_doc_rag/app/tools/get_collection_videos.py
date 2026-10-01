# !/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Authors: 坤叔(1292746975@qq.com)
更新up主的视频列表
获取 up主的视频列表并保存(更新)到 Excel里 ( resources/up主名.xlsx )

python -m app.tools.update_uper_list
"""
import os
import time

import pandas
from pandas import DataFrame

from app.libs import BilibiliPageCrawler
from app.tools.rename_video import replace_unsuitable_letter

from app.config import config
from app.logger import logger, print_caller_stack


def get_collection_videos(collection_template, total_page):
    """
    Docstring for get_collection_videos
    
    :param collection_last_url: Description
    """
    video_title_list = []
    title = ''

    crawler = BilibiliPageCrawler()

    page = crawler.driver

    last_url = collection_template.format(page=total_page)
    page.get(last_url)

    # 等待元素加载
    # page.wait.ele_displayed('@class:video-pod__list', timeout=1)

    """
    <h1 data-title="【公开课】温铁军：中国经济研究（33讲）" title="【公开课】温铁军：中国经济研究（33讲）" class="video-title special-text-indent" data-v-fe6ec38e="">【公开课】温铁军：中国经济研究（33讲）</h1>

    h1_eles = page.eles('tag:h1@data-title')
    print(f"lens: {len(h1_eles)}")
    for ele in h1_eles:
        print(ele)
        print(ele.attr("data-title"))
        print(ele.text)
    """
    h1_ele = page.ele('tag:h1@data-title')
    title = h1_ele.text
    
    # 获取div元素
    parent_div = page.ele('@class:video-pod__list')
    if parent_div:
        
        video_title_elements = parent_div.eles('.title-txt')
        for index, video_title_ele in enumerate(video_title_elements):
            pn = index + 1
            video_title_list.append(
                {"pn": pn, "title": video_title_ele.text, "bvUrl": collection_template.format(page=pn)}
            )
            # print(video_title_ele.text)
        # print(div_element.html)
    else:
        print("未找到元素")

    crawler.driver.quit()
    return video_title_list, title


def save_2_excel(title, video_list):
    collection_dir = os.path.join(config.output_root, title)
    if not os.path.exists(collection_dir):
        os.makedirs(collection_dir)

    __OUTPUT_EXCEL = os.path.join(collection_dir, f'{title}.xlsx')
    total_df = DataFrame(video_list)

    if os.path.exists(__OUTPUT_EXCEL):
        df = total_df
        total_df = DataFrame()

        old_df = pandas.read_excel(__OUTPUT_EXCEL)
        logger.info(f'old_df : {old_df.shape} , columns : {old_df.columns}')
        logger.info(f'new_df : {df.shape} , columns : {df.columns}')

        new_df = df[~df.url.isin(old_df.url)]
        total_df = pandas.concat([new_df, old_df], ignore_index=True)
        total_df = total_df.drop_duplicates(subset=['url'], keep='first')
    else:
        total_df['new_title'] = total_df['title'].apply(replace_unsuitable_letter)
        total_df['lemonUrl'] = ''
        total_df['download_url'] = ''
        total_df['output_file'] = ''
        total_df['bvid_error'] = ''

    for i in range(2):
        try:
            total_df.to_excel(__OUTPUT_EXCEL, index=False)
            logger.info(f'OUTPUT TO EXCEL SUCCESS: {__OUTPUT_EXCEL}')
            break
        except:
            logger.error(f'{__OUTPUT_EXCEL} 保存失败 , 请关闭文件后再试')
            if i == 0:
                input("按任意键继续重试...")
                
    return __OUTPUT_EXCEL

if __name__ == '__main__':
    # python -m app.tools.get_collection_videos
    collection_template = "https://www.bilibili.com/video/BV1kp4y1W7u8/?spm_id_from=333.788.videopod.episodes&vd_source=2e3e55ec052ee4f3928dff1d7db3f3c0&p={page}"
    video_title_list, title = get_collection_videos(collection_template, total_page=32)
    output_excel = save_2_excel(title, video_title_list)
    
    input(f"collection info: {output_excel}, 请准备好下载连接")