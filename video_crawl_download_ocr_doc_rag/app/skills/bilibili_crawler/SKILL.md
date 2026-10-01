# bilibili_crawler - B站UP主视频爬虫

从B站抓取UP主的视频列表、获取视频下载链接、爬取视频页面。

## 虚拟环境

Python解释器: `D:\workspace\video-crawl-download-ocr-doc-rag\.venv\Scripts\python.exe`

激活虚拟环境:
```bash
# CMD
D:\workspace\video-crawl-download-ocr-doc-rag\.venv\Scripts\activate.bat

# PowerShell
D:\workspace\video-crawl-download-ocr-doc-rag\.venv\Scripts\Activate.ps1

# 或直接使用完整路径
D:\workspace\video-crawl-download-ocr-doc-rag\.venv\Scripts\python.exe script.py
```

## 功能

| 脚本 | 功能 |
|------|------|
| `crawl_uper_videos.py` | 抓取UP主视频列表并保存Excel |
| `get_video_download_url.py` | 获取视频下载URL和JSON信息 |
| `crawl_bilibili_page.py` | 爬取视频页面HTML |

## 使用方式

方式一：直接使用 .venv Python（推荐）
```bash
# 进入skill目录
cd D:\workspace\video-crawl-download-ocr-doc-rag\video_crawl_download_ocr_doc_rag\app\skills\bilibili_crawler\scripts

# 1. 根据配置文件抓取所有UP主最新视频列表
D:\workspace\video-crawl-download-ocr-doc-rag\.venv\Scripts\python.exe crawl_uper_videos.py

# 2. 获取视频下载URL + 保存JSON
D:\workspace\video-crawl-download-ocr-doc-rag\.venv\Scripts\python.exe get_video_download_url.py -u "BV15fXpBdE1d"
D:\workspace\video-crawl-download-ocr-doc-rag\.venv\Scripts\python.exe get_video_download_url.py -u "https://www.bilibili.com/video/BV15fXpBdE1d/"

# 3. 爬取视频页面HTML
D:\workspace\video-crawl-download-ocr-doc-rag\.venv\Scripts\python.exe crawl_bilibili_page.py -u "BV15fXpBdE1d"
D:\workspace\video-crawl-download-ocr-doc-rag\.venv\Scripts\python.exe crawl_bilibili_page.py -u "https://www.bilibili.com/video/BV15fXpBdE1d/"

# 4. 获取视频URL + 下载视频 + 保存JSON
D:\workspace\video-crawl-download-ocr-doc-rag\.venv\Scripts\python.exe get_video_download_url.py -u "BV15fXpBdE1d" -d

# 5. 下载视频到指定UP主文件夹
D:\workspace\video-crawl-download-ocr-doc-rag\.venv\Scripts\python.exe get_video_download_url.py -u "BV15fXpBdE1d" -d -n "UP主名称"
```

方式二：激活虚拟环境后使用
```bash
cd D:\workspace\video-crawl-download-ocr-doc-rag\video_crawl_download_ocr_doc_rag

# 激活虚拟环境
.venv\Scripts\activate

# 进入skill目录
cd app\skills\bilibili_crawler\scripts

# 1. 根据配置文件抓取所有UP主最新视频列表
python crawl_uper_videos.py

# 2. 获取视频下载URL + 保存JSON
python get_video_download_url.py -u "BV15fXpBdE1d"
```

## 输出

默认输出目录: `D:\workspace\video-crawl-download-ocr-doc-rag\output\`

| 文件类型 | 命名规则 |
|----------|----------|
| Excel | `{UP主名}.xlsx` |
| CSV | `{UP主名}.csv` |
| JSON | `{bvid}.json` |
| HTML | `{bvid}.html` |

### 下载视频输出结构

```
output/
├── (默认根目录)
│   └── {bvid}.json
├── {UP主名称}/          (当指定 -n 参数时)
│   ├── {bvid}.json
│   ├── {标题}_video.m4s
│   └── {标题}_audio.m4s
```

## 命令行参数

### get_video_download_url.py

| 参数 | 说明 |
|------|------|
| `-u, --url` | B站视频URL或bvid (必填) |
| `-q, --quality` | 视频清晰度: 80=1080P, 64=720P, 32=480P, 16=360P (默认80) |
| `-d, --download` | 是否下载视频 |
| `-o, --output` | 输出目录 (默认: `D:\workspace\video-crawl-download-ocr-doc-rag\output`) |
| `-n, --uploader` | UP主名称 (可选，指定后会在output下创建UP主文件夹) |

## 配置

配置文件: `app/skills/bilibili_crawler/config.toml`

```toml
# B站爬虫配置
[bilibili]
# B站Cookie（用于获取更多视频资源，可从浏览器F12获取）
cookie = ""

# 输出配置
[output]
# 输出根目录（支持绝对路径或相对路径）
root = "D:\\workspace\\video-crawl-download-ocr-doc-rag\\output"
```

### 获取Cookie方法
1. 登录B站
2. 按F12打开开发者工具
3. 切换到 Application/Application -> Cookies -> bilibili.com
4. 复制Cookie值填入配置
