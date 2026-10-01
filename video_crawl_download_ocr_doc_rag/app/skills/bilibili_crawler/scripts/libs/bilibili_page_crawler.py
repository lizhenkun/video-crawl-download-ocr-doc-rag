# !/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Authors: 坤叔(1292746975@qq.com)
参考:
DrissionPage的使用
https://baijiahao.baidu.com/s?id=1801556183340018772&wfr=spider&for=pc

python bilibili_up_crawler_by_drission_page.py
"""
import os
import re
import json
import time
import subprocess
import traceback
import requests
from typing import Optional, Dict
from urllib.parse import urlparse, parse_qs

import pandas
from DrissionPage import ChromiumPage, ChromiumOptions

import sys
from pathlib import Path
SCRIPT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPT_DIR))

from libs import config, logger, StdResponse
from libs.rename_video import replace_unsuitable_letter


LEMONDL_KEY = 'https://lemondl.com/'


class BilibiliPageCrawler(object):
    """
    bilibili 页面爬虫器
    """
    @classmethod
    def create_webdriver(cls, **kwargs) -> ChromiumPage:
        """
        create_webdriver
        """
        if not kwargs:
            kwargs = {}
        kwargs.update(config.brower_config)
        
        if kwargs.get('auto_port'):
            options = ChromiumOptions().auto_port()
        else:
            port = kwargs.get('port')
            if port:
                options = ChromiumOptions().set_local_port(port)
            else:
                options = ChromiumOptions()

        if kwargs.get('brower_path'):
            options.set_paths(browser_path=kwargs["brower_path"])
        
        if kwargs.get('headless'):
            options.headless(kwargs["brower_path"])
        
        if kwargs.get('incognito'):
            options.incognito(kwargs["incognito"])

        driver = ChromiumPage(options)
        return driver
    
    @classmethod
    def extract_bvid(cls, url: str) -> Optional[str]:
        """从URL提取bvid"""
        if url.startswith("BV") and len(url) == 12:
            return url
        
        patterns = [
            r'bilibili\.com/video/(BV[\w]+)',
            r'BV[\w]{10}',
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1) if match.lastindex else match.group(0)
        return None

    @classmethod
    def crawl_video_page(cls, url: str, **kwargs):
        """"""
        bvid = cls.extract_bvid(url)
        if not bvid:
            logger.warning("无法提取bvid")
            return None
        
        # 构建完整URL
        if not url.startswith("http"):
            url = f"https://www.bilibili.com/video/{bvid}/"

        logger.debug(f"正在访问: {url}")

        driver = cls.create_webdriver(**kwargs)

        try:
            # 访问页面
            driver.get(url)
            
            # 等待页面加载
            logger.debug("等待页面加载...")
            driver.wait.load_start()
            
            # 等待一段时间确保内容加载完成
            time.sleep(3)
            
            html = driver.html

            # 获取页面HTML (尝试多种属性)
            # try:
            #     html = driver.html
            # except AttributeError:
            #     try:
            #         html = driver.get_tab(0).html
            #     except AttributeError:
            #         html = driver.page_html

            title = driver.title.strip()
            
            return {
                "html": html,
                "bvid": bvid,
                "title": title
            }
        
        except:
            logger.warning(traceback.format_exc())

        finally:
            driver.quit()

    @classmethod
    def crawl_space_page(cls, web_driver, uploader_id, page_count=1, special_type=''):
        """
        https://space.bilibili.com/290663424/upload/video

        Space Url = f'https://space.bilibili.com/{uploader_id}/video'
        """
        std_resp = StdResponse()

        # 最新发布: space_url = f'https://space.bilibili.com/{uploader_id}/video?tid=0&special_type=&pn={pn}&keyword=&order=pubdate'
        # 充电专属: space_url = f'https://space.bilibili.com/{uploader_id}/video?tid=0&special_type=charging&pn={pn}&keyword=&order=pubdate'
        # space_url eg. https://space.bilibili.com/290663424/video?tid=0&special_type=&pn=2&keyword=&order=pubdate
        # 已经被 B站屏蔽了
        # space_url = f'https://space.bilibili.com/{uploader_id}/video?tid=0&special_type={special_type}&pn={pn}&keyword=&order=pubdate'
        # https://space.bilibili.com/290663424/upload/video
        space_url = f'https://space.bilibili.com/{uploader_id}/upload/video'
        logger.info(f'space_url: {space_url}')

        # search_url_pattern = f'https://api.bilibili.com/x/space/wbi/arc/search?mid={uploader_id}'
        search_url_pattern = f'https://api.bilibili.com/x/space/wbi/arc/search'
        
        logger.info('crawling...')

        web_driver.listen.start(search_url_pattern) # 开始监听，指定获取包含该文本的数据包(部分url)
        web_driver.get(space_url)
        
        total_video_list = []

        cur_pn = 0
        while page_count < 0 or cur_pn < page_count:
            cur_pn += 1
            
            # web_driver.wait.load_start()

            video_list = []
            for retry in range(5):
                try:
                    # res 是拦截到的接口的响应体
                    res = web_driver.listen.wait()

                    # res.response.body: dict
                    video_list = cls.get_video_info_list(res.response.body)
                    logger.info(
                        f'当前页 {cur_pn}'
                        f'\n本页视频数量: {len(video_list)}'
                        f'\n第一个视频: {video_list[0]['title']}'
                        f'\n监听的url: {res.url}'
                        f'\nheaders: {res.response.headers}'
                    )
                    break
                except Exception as e:
                    logger.info(f'第 {retry + 1} 次抓取失败: {e}')
                    if retry < 4:
                        logger.info('尝试刷新页面...')
                        web_driver.get(space_url)
                        web_driver.listen.start(search_url_pattern)
                        time.sleep(2)
                    else:
                        print('已达到最大重试次数 (5次)')
                        logger.warning(traceback.format_exc())

            if video_list:
                total_video_list.extend(video_list)

            time.sleep(3)
            try:
                # page: ChromiumPage
                # btn: DrissionPage._elements.chromium_element
                # from DrissionPage._elements.chromium_element import ChromiumElement
                btn = web_driver('下一页')
                # logger.info(btn , {btn.html})
                # help(btn)
                # AttributeError: 'ChromiumElement' object has no attribute 'exists'
                if btn.states.has_rect:
                    # input('回车 ， 自动点击下一页')
                    btn.click()
                    continue
                else:
                    logger.info('没有下一页了 , break')
                    break
            except:
                logger.info('没有下一页了 , break')
                break

        std_resp.data['uploader_id'] = uploader_id
        std_resp.data['space_url'] = space_url
        std_resp.data['search_url'] = res.url
        std_resp.data['pn'] = cur_pn
        std_resp.data['video_list'] = total_video_list

        return std_resp

    @classmethod
    def get_video_info_list(cls, ajax_data):
        """
        get video info list
        """
        # 处理字符串类型的响应
        import json as json_module
        if isinstance(ajax_data, str):
            ajax_data = json_module.loads(ajax_data)
        
        # write to json for test
        # with open(f'{uploader_id}_response.json', mode='w', encoding='utf-8') as writer:
        #     json.dump(ajax_data, writer)

        # test
        # with open(f'{uploader_id}_response.json', mode='r', encoding='utf-8') as reader:
        #     ajax_data = json.load(reader)

        vlist = ajax_data['data']['list']['vlist']
        logger.info(f'vlist len: {len(vlist)}')

        new_list = []
        for v_info in vlist:
            bvid = v_info['bvid']
            v_item = {
                'title': v_info['title'],
                'created': v_info['created'], # 创建时间
                'bvid': bvid, # video id
                'bvUrl': f'https://www.bilibili.com/video/{bvid}/',
                'description':v_info['description']
            }
            new_list.append(v_item)
        
        return new_list

    @classmethod
    def download_videos(cls, space_page_resp):
        """
        download videos
        """
        output_dir = space_page_resp.get('output', 'output')
        uploader = space_page_resp['uploader']
        excel_file = os.path.join(output_dir, f'{uploader}.xlsx')

        df = pandas.read_excel(excel_file)

        for index, row in df.iterrows():
            title = row.new_title
            if not title:
                title = row.title

            if not isinstance(row.lemonUrl, str):
                continue

            download_url = row.lemonUrl.strip()

            if download_url[:len(LEMONDL_KEY)] == LEMONDL_KEY:
                parsed_url = urlparse(download_url)
                query_params = parsed_url.query
                params = parse_qs(query_params)
                # logger.info(params)

                params = json.loads(params['data'][0])
                bvid = params['bvid']
                
                if row.bvid != bvid:
                    logger.warning(f'row: {bvid} , {row.bvid == bvid}')
                    df.loc[index, 'bvid_error'] = '是'
                    continue

                download_url = params['url']

                output_file = download_file(output_dir, download_url, title)
                df.loc[index, 'download_url'] = download_url
                df.loc[index, 'output_file'] = output_file

        df.to_excel(excel_file, index=False)

    # ============ B站 API 相关方法 ============

    @classmethod
    def get_video_info(cls, bvid: str) -> Optional[Dict]:
        """
        获取视频基本信息
        返回是大 dict ， 具体内容参考 试试执行: _test_get_video_info()
        """
        headers = config.headers_config
        url = f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}"
        resp = requests.get(url, headers=headers)
        data = resp.json()
        
        if data.get("code") != 0:
            logger.error(f"Error: {data.get('message')}")
            return None
        
        return data.get("data")

    @classmethod
    def get_playurl_mp4(
        cls, video_info: dict,
        quality: int = 64) -> Optional[Dict]:
        """
        尝试获取mp4格式的下载链接
        video_info : 视频信息

        quality : 视频清晰度，192=1080P, 80=1080P, 64=720P
        """
        avid = video_info["aid"]
        cid = int(video_info["cid"])
        headers = config.headers_config
        
        # 方法1: fnval=0 (durl格式，mp4)
        logger.info("尝试获取mp4格式...")
        
        url = "https://api.bilibili.com/x/player/playurl"
        params = {
            "avid": avid,
            "cid": cid,
            "qn": quality,  # 192 = 1080P
            "fnval": 0,     # 不使用fnval，获取durl
            "fourk": 1,
        }
        
        resp = requests.get(url, params=params, headers=headers)
        logger.info(
            f"\nrequest: {resp.url}"
            f"\nheaders: {json.dumps(headers, indent=2)}\n"
        )
        data = resp.json()
        
        if data.get("code") != 0:
            logger.error(f"Error: {data.get('message')}")
            return None
        
        play_data = data.get("data", {})
        
        # 尝试durl格式（mp4）
        durls = play_data.get("durl", [])
        if durls:
            logger.info(f"找到durl格式，共 {len(durls)} 个分段")
            first_durl = durls[0]
            video_url = first_durl.get("url", "")
            
            if video_url and ".mp4" in video_url:
                return {
                    "format": "mp4 (durl)",
                    "video_url": video_url,
                    "audio_url": "",
                    "quality": quality,
                    "durl": durls,
                }
        
        # 方法2: 尝试fnval=8 (mp4格式)
        logger.info("尝试 fnval=8 (mp4格式)...")
        params["fnval"] = 8
        resp = requests.get(url, params=params, headers=headers)
        data = resp.json()
        
        if data.get("code") == 0:
            play_data = data.get("data", {})
            durls = play_data.get("durl", [])
            if durls:
                logger.info(f"找到durl格式(fnval=8)，共 {len(durls)} 个分段")
                first_durl = durls[0]
                video_url = first_durl.get("url", "")
                if video_url:
                    return {
                        "format": "mp4 (fnval=8)",
                        "video_url": video_url,
                        "audio_url": "",
                        "quality": quality,
                        "durl": durls,
                    }
        
        # 方法3: 尝试fnval=16 (dash格式)
        logger.info("尝试 fnval=16 (dash格式)...")
        params["fnval"] = 16
        resp = requests.get(url, params=params, headers=headers)
        data = resp.json()
        
        if data.get("code") == 0:
            play_data = data.get("data", {})
            dash = play_data.get("dash", {})
            if dash:
                video_list = dash.get("video", [])
                audio_list = dash.get("audio", [])
                
                if video_list:
                    video_url = video_list[0].get("baseUrl", "")
                    audio_url = audio_list[0].get("baseUrl", "") if audio_list else ""
                    
                    is_mp4 = ".mp4" in video_url
                    logger.info(f"dash格式 - 视频: {'mp4' if is_mp4 else 'm4s'}")
                    
                    return {
                        "format": "dash (mp4)" if is_mp4 else "dash (m4s)",
                        "video_url": video_url,
                        "audio_url": audio_url,
                        "quality": quality,
                        "dash": dash,
                    }
        
        return None

    @classmethod
    def get_video_download_url(cls, video_url: str, quality: int = 64) -> Optional[Dict]:
        """获取B站视频的下载URL
        
        Args:
            video_url: B站视频URL或bvid
            quality: 视频清晰度 (192=1080P, 80=1080P, 64=720P , 默认 64)
            
        Returns:
            包含 bvid, title, format, download_url, audio_url 的字典
        """
        bvid = cls.extract_bvid(video_url)
        if not bvid:
            logger.error("无法提取bvid")
            return None
        
        logger.info(f"bvid: {bvid}")

        video_info = cls.get_video_info(bvid)
        
        title = video_info.get("title", "")
        logger.info(f"标题: {title}")
        
        play_data = cls.get_playurl_mp4(video_info, quality)
        if not play_data:
            logger.error("无法获取下载链接")
            return None
        
        result = {
            "bvid": bvid,
            "title": title,
            "format": play_data.get("format", ""),
            "download_url": play_data.get("video_url", ""),
            "audio_url": play_data.get("audio_url", ""),
        }
        
        logger.info(f"格式: {result['format']}")
        logger.info(f"视频地址: {'已获取' if result['download_url'] else '无'}")
        logger.info(f"音频地址: {'已获取' if result['audio_url'] else '无'}")
        
        return result

    @classmethod
    def download_video_file(cls, download_url: str, output_path: str, show_progress: bool=False) -> bool:
        """下载文件到本地
        
        Args:
            download_url: 下载链接
            output_path: 输出文件路径
            
        Returns:
            是否下载成功
        """
        headers = config.headers_config
        logger.info(f"正在下载: {output_path}")
        
        try:
            resp = requests.get(download_url, headers=headers, stream=True, timeout=60)
            resp.raise_for_status()
            
            total_size = int(resp.headers.get('content-length', 0))
            logger.info(f"文件大小: {total_size / 1024 / 1024:.2f} MB")
            
            downloaded = 0
            os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
            with open(output_path, 'wb') as f:
                for chunk in resp.iter_content(chunk_size=1024*1024):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if show_progress:
                            if total_size:
                                pct = downloaded / total_size * 100
                                print(f"\r下载进度: {pct:.1f}%", end="", flush=True)
            
            if show_progress:
                print()
                
            logger.success("下载完成!")
            return True
        except Exception as e:
            logger.error(f"下载失败: {e}")
            return False


def download_file(output_dir, download_url, title):
    """
    download
    """
    parts = download_url.split('?')
    file_type = parts[0].strip().rsplit('.', 1)[-1]
    logger.info(f'download file type: {file_type}')
    if not file_type:
        file_type = 'mp4'

    target = f'{output_dir}/{title}.{file_type}'
    if os.path.exists(target):
        return target

    cmd = f'wget "{download_url}" -O "{target}"'
    logger.info(cmd)
    p = subprocess.run(cmd, shell=True)
    return target


def _test_get_video_info():
    url = "https://www.bilibili.com/video/BV1QGXABxEbq/"
    bvid = BilibiliPageCrawler.extract_bvid(url)
    result = BilibiliPageCrawler.get_video_info(bvid)

    logger.info(json.dumps(result))


if __name__ == '__main__':
    """
    python ./scripts/libs/bilibili_page_crawler.py
    python -m scripts.libs.bilibili_page_crawler
    """
    _test_get_video_info()
