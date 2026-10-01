# Skill: video_2_pic_2_text

> 将视频转换为图片，再通过OCR识别图片中的文字，最终输出文本内容。

## 快速开始

```bash
cd D:\workspace\video-crawl-download-ocr-doc-rag\video_crawl_download_ocr_doc_rag\app\skills\video_2_pic_2_text\scripts

# 一键完成（推荐）- 流水线模式，截图+OCR并行执行
D:\workspace\video-crawl-download-ocr-doc-rag\.venv\Scripts\python.exe video_2_pic_2_text.py -i "video.mp4"

# 分步执行
D:\workspace\video-crawl-download-ocr-doc-rag\.venv\Scripts\python.exe video_2_pic.py -i "video.mp4"
D:\workspace\video-crawl-download-ocr-doc-rag\.venv\Scripts\python.exe pic_2_text.py -d "video_pics_dir"
```

## 功能概述

| 脚本 | 功能 | 特性 |
|------|------|------|
| `video_2_pic.py` | 视频转图片 | 按固定间隔截取视频帧 |
| `pic_2_text.py` | 图片转文字 | 批量OCR识别，支持断点续传 |
| `video_2_pic_2_text.py` | 一键流水线 | 截图+OCR并行执行，支持断点续传，实时写入CSV |

## 🏗️ 架构设计

```
┌─────────────────┐    Queue     ┌─────────────────┐
│  截图进程       │  ──────────► │   OCR进程       │
│ (ScreenshotWorker)│  (帧队列)  │ (OcrWorker)     │
│                 │              │                 │
│ - 从视频截帧    │              │ - 从队列取帧    │
│ - 放入队列      │              │ - PaddleOCR识别 │
│ - 记录进度     │              │ - 写入CSV      │
└─────────────────┘              └─────────────────┘
```

**核心特性：**
- 流水线模式：截图和OCR并行执行，大幅提升效率
- 断点续传：使用 `.progress.json` 记录进度，中断后可继续
- 实时写入：每识别完立即写入CSV，无需等待全部完成

## 批量处理

### batch_video_2_pic_2_text.py

扫描UP主的Excel文件，找出"转文字"列为空的视频，批量进行OCR处理。

```bash
cd D:\workspace\video-crawl-download-ocr-doc-rag\video_crawl_download_ocr_doc_rag\app\skills\video_2_pic_2_text\scripts

# 扫描并处理（先显示待处理列表，确认后执行）
D:\workspace\video-crawl-download-ocr-doc-rag\.venv\Scripts\python.exe batch_video_2_pic_2_text.py -u "有何高见9527"

# 模拟运行（仅显示待处理视频，不实际执行）
D:\workspace\video-crawl-download-ocr-doc-rag\.venv\Scripts\python.exe batch_video_2_pic_2_text.py -u "有何高见9527" --dry-run

# 限制处理数量
D:\workspace\video-crawl-download-ocr-doc-rag\.venv\Scripts\python.exe batch_video_2_pic_2_text.py -u "有何高见9527" --limit 5
```

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `-u, --uploader` | UP主名称（Excel文件名） | 必需 |
| `--dry-run` | 仅显示待处理视频，不执行 | False |
| `-l, --limit` | 限制处理数量，0表示全部 | 0（全部） |

**工作流程：**
1. 读取UP主的Excel文件（如 `有何高见9527.xlsx`）
2. 筛选"转文字"列为空的视频
3. 检查视频文件是否存在
4. 逐个调用 `video_2_pic_2_text.py` 进行OCR处理
5. 自动更新Excel的"转文字"列

编辑 `config/config.toml`：

```toml
[sys]
log_level = "INFO"
output_root = "D:\\workspace\\video-crawl-download-ocr-doc-rag\\output"

[video]
interval = 0.5      # 截图间隔（秒）
crop_y1 = -200     # 裁剪起始Y坐标
crop_y2 = -30      # 裁剪结束Y坐标

[ocr]
probability_threshold = 0.93  # 置信度阈值

# UP主配置
[BILIBILI_UP_INFO.290663424]
uploader = "有何高见9527"
skip_line_pattern = "^\\d+$"
probability_threshold = 0.90
```

## 参数说明

### video_2_pic_2_text.py（推荐）

```bash
python video_2_pic_2_text.py -i "video.mp4" [options]
```

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `-i, --input` | 输入视频文件路径 | 必需 |
| `-d, --dir` | 输出目录路径 | 视频所在文件夹 |
| `--interval` | 截图间隔（秒） | 0.5 |
| `--crop-y1` | 裁剪起始Y坐标 | -200 |
| `--crop-y2` | 裁剪结束Y坐标 | -30 |
| `--skip-pattern` | 跳过匹配该正则的行 | '' |
| `--threshold` | 识别置信度阈值 | 0.93 |
| `--no-resume` | 禁用断点续传 | False |

## 输出结果

- 图片目录：`{output_root}/{UP主名}/{视频名}/`
- 进度文件：`{图片目录}/.progress.json`
- OCR结果：`{图片目录}/{视频名}_ocr.csv`

CSV格式：
```
movie_cur_seconds,probability,line
10.5,0.95,识别到的文字内容
```

## 详细文档

详细说明请参阅 [README.md](./README.md)

## 目录结构

```
video_2_pic_2_text/
├── config/
│   └── config.toml
├── scripts/
│   ├── libs/
│   │   ├── config.py
│   │   └── logger.py
│   ├── video_2_pic.py
│   ├── pic_2_text.py
│   └── video_2_pic_2_text.py   # 推荐使用
├── output/
├── logs/
├── requirements.txt
├── SKILL.md
└── README.md                     # 详细文档
```
