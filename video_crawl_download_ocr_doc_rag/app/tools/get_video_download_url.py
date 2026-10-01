#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
获取B站视频下载地址（带音频）

用法:
    python get_video_download_url.py -u "https://www.bilibili.com/video/BV1jTX8ByEq7/"
    python get_video_download_url.py -u "BV1jTX8ByEq7"
    python get_video_download_url.py -u "BV15fXpBdE1d" -d
    python get_video_download_url.py -u "BV15fXpBdE1d" -d -n "UP主名称"
"""
import re
import os
import json
import argparse
import requests
from pathlib import Path
from typing import Optional, Dict

# 获取项目根目录
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent

# 配置文件路径（使用skill的配置）
CONFIG_FILE = PROJECT_ROOT / "app" / "skills" / "bilibili_crawler" / "config.toml"


def load_config() -> Dict:
    """加载配置文件"""
    config = {"bilibili": {"cookie": ""}, "output": {"root": ""}}
    
    if CONFIG_FILE.exists():
        try:
            import tomli as toml
            with open(CONFIG_FILE, "rb") as f:
                config = toml.load(f)
        except ImportError:
            # 如果没有 tomli，尝试手动解析
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("cookie") and "=" in line:
                        _, value = line.split("=", 1)
                        config["bilibili"]["cookie"] = value.strip().strip('"').strip("'")
                    elif line.startswith("root") and "=" in line:
                        _, value = line.split("=", 1)
                        config["output"]["root"] = value.strip().strip('"').strip("'")
        except Exception as e:
            print(f"配置文件加载失败: {e}")
    
    return config


# 加载配置
CONFIG = load_config()
BILIBILI_COOKIE = CONFIG.get("bilibili", {}).get("cookie", "")

# 输出目录：从配置读取，默认为工程output目录
_config_output_root = CONFIG.get("output", {}).get("root", "")
DEFAULT_OUTPUT_ROOT = _config_output_root if _config_output_root else str(PROJECT_ROOT / "output")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.bilibili.com/",
}

# 添加Cookie（如果有配置）
if BILIBILI_COOKIE:
    HEADERS["Cookie"] = BILIBILI_COOKIE


def extract_bvid(url: str) -> Optional[str]:
    """从URL提取bvid，如果是bvid直接返回"""
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


def get_video_info(bvid: str) -> Optional[Dict]:
    """获取视频基本信息"""
    url = f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}"
    resp = requests.get(url, headers=HEADERS)
    data = resp.json()
    
    if data.get("code") != 0:
        print(f"Error: {data.get('message')}")
        return None
    
    return data.get("data")


def get_playurl(bvid: str, cid: int, quality: int = 80) -> Optional[Dict]:
    """获取下载链接（尝试多种格式）"""
    info = get_video_info(bvid)
    if not info:
        return None
    
    avid = info["aid"]
    
    # 尝试fnval=16 (dash格式)
    for fnval in [16, 4048, 8]:
        url = "https://api.bilibili.com/x/player/playurl"
        params = {
            "avid": avid,
            "cid": cid,
            "qn": quality,
            "fnval": fnval,
            "fourk": 1,
        }
        
        resp = requests.get(url, params=params, headers=HEADERS)
        data = resp.json()
        
        if data.get("code") != 0:
            continue
        
        play_data = data.get("data", {})
        dash = play_data.get("dash", {})
        
        if dash:
            video_list = dash.get("video", [])
            audio_list = dash.get("audio", [])
            
            if video_list:
                return {
                    "dash": dash,
                    "video_url": video_list[0].get("baseUrl", ""),
                    "audio_url": audio_list[0].get("baseUrl", "") if audio_list else "",
                }
        
        # 尝试durl格式
        durls = play_data.get("durl", [])
        if durls:
            return {
                "durl": durls,
                "video_url": durls[0].get("url", ""),
                "audio_url": "",
            }
    
    return None


def get_video_download_url(video_url: str, quality: int = 80) -> Optional[Dict]:
    """获取B站视频的下载URL"""
    bvid = extract_bvid(video_url)
    if not bvid:
        print("无法提取bvid")
        return None
    
    print(f"bvid: {bvid}")
    
    info = get_video_info(bvid)
    if not info:
        return None
    
    title = info.get("title", "")
    cid = info.get("cid")
    print(f"标题: {title}")
    print(f"cid: {cid}")
    
    play_data = get_playurl(bvid, cid, quality)
    if not play_data:
        print("无法获取下载链接")
        return None
    
    video_url = play_data.get("video_url", "")
    audio_url = play_data.get("audio_url", "")
    
    print(f"视频地址: {'已获取' if video_url else '无'}")
    print(f"音频地址: {'已获取' if audio_url else '无'}")
    
    result = {
        "bvid": bvid,
        "title": title,
        "download_url": video_url,
        "audio_url": audio_url,
    }
    
    return result


def save_json(result: Dict, output_dir: str = "output") -> str:
    """保存结果到JSON文件"""
    bvid = result.get("bvid", "unknown")
    json_file = os.path.join(output_dir, f"{bvid}.json")
    
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"JSON已保存: {json_file}")
    return json_file


def sanitize_filename(name: str) -> str:
    """清理文件名中的非法字符"""
    return re.sub(r'[\\/:*?"<>|]', '_', name)


def download_file(url: str, output_path: str) -> bool:
    """下载文件"""
    print(f"正在下载: {output_path}")
    
    try:
        resp = requests.get(url, headers=HEADERS, stream=True, timeout=60)
        resp.raise_for_status()
        
        total_size = int(resp.headers.get('content-length', 0))
        print(f"文件大小: {total_size / 1024 / 1024:.2f} MB")
        
        downloaded = 0
        with open(output_path, 'wb') as f:
            for chunk in resp.iter_content(chunk_size=1024*1024):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size:
                        pct = downloaded / total_size * 100
                        print(f"\r下载进度: {pct:.1f}%", end="", flush=True)
        
        print(f"\n下载完成!")
        return True
    except Exception as e:
        print(f"下载失败: {e}")
        return False


def download_video(video_url: str, quality: int = 80, output_dir: str = None, uploader: str = None) -> Optional[Dict]:
    """下载视频主函数
    
    Args:
        video_url: B站视频URL或bvid
        quality: 视频清晰度
        output_dir: 输出目录（默认为工程output目录）
        uploader: UP主名称（可选，指定后会创建UP主文件夹）
    """
    result = get_video_download_url(video_url, quality)
    if not result:
        return None
    
    # 确定输出目录
    if output_dir is None:
        output_dir = str(DEFAULT_OUTPUT_ROOT)
    
    # 如果指定了UP主，创建UP主子文件夹
    if uploader:
        output_dir = os.path.join(output_dir, uploader)
    
    # 保存JSON
    save_json(result, output_dir)
    
    os.makedirs(output_dir, exist_ok=True)
    safe_title = sanitize_filename(result["title"])
    
    video_path = None
    if result["download_url"]:
        ext = ".mp4" if result["download_url"].endswith(".mp4") else ".m4s"
        video_path = os.path.join(output_dir, f"{safe_title}_video{ext}")
        download_file(result["download_url"], video_path)
    
    audio_path = None
    if result["audio_url"]:
        audio_path = os.path.join(output_dir, f"{safe_title}_audio.m4s")
        download_file(result["audio_url"], audio_path)
    
    result["video_path"] = video_path
    result["audio_path"] = audio_path
    
    return result


def main():
    """主入口"""
    parser = argparse.ArgumentParser(description="获取B站视频下载地址")
    parser.add_argument("-u", "--url", type=str, required=True, help="B站视频URL或bvid")
    parser.add_argument("-q", "--quality", type=int, default=80, help="视频清晰度: 80=1080P, 64=720P, 32=480P, 16=360P (默认80)")
    parser.add_argument("-d", "--download", action="store_true", help="下载视频")
    parser.add_argument("-o", "--output", type=str, default=None, help=f"输出目录 (默认: {DEFAULT_OUTPUT_ROOT})")
    parser.add_argument("-n", "--uploader", type=str, default=None, help="UP主名称（可选，指定后会创建UP主文件夹）")
    
    args = parser.parse_args()
    
    # 确定输出目录
    output_dir = args.output if args.output else str(DEFAULT_OUTPUT_ROOT)
    
    print(f"\n{'='*60}")
    print(f"输入: {args.url}")
    print(f"输出目录: {output_dir}")
    if args.uploader:
        print(f"UP主文件夹: {args.uploader}")
    print('='*60)
    
    if args.download:
        result = download_video(args.url, args.quality, output_dir, args.uploader)
        if result:
            print(f"\n=== 下载完成 ===")
            print(f"视频: {result['video_path']}")
            print(f"音频: {result['audio_path']}")
            if result['video_path'] and result['audio_path']:
                print(f"\n提示: 合并视频和音频:")
                print(f"ffmpeg -i \"{result['video_path']}\" -i \"{result['audio_path']}\" -c copy \"{output_dir}/{result['title']}.mp4\"")
    else:
        result = get_video_download_url(args.url, args.quality)
        if result:
            # 保存JSON
            save_json(result, output_dir)
            
            print(f"标题: {result['title']}")
            print(f"视频地址: {result['download_url']}")
            print(f"音频地址: {result['audio_url']}")


if __name__ == "__main__":
    main()
