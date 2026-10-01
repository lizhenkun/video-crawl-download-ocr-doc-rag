# Video 2 Pic 2 Text

> 将视频转换为图片，再通过OCR识别图片中的文字，最终输出文本内容。

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

## 功能概述

本技能实现以下功能：
1. **视频转图片** - 按固定时间间隔截取视频帧
2. **图片OCR识别** - 使用PaddleOCR识别图片中的文字
3. **文本输出** - 将识别结果保存为CSV文件

## 🏗️ 架构设计

### 流水线模式

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

### 核心特性

| 特性 | 说明 |
|------|------|
| **流水线模式** | 截图和OCR并行执行，用多进程替代串行处理，大幅提升效率 |
| **断点续传** | 使用 `.progress.json` 记录进度，中断后可继续 |
| **实时写入** | 每识别完一张立即写入CSV，无需等待全部完成 |
| **去重机制** | 记录已识别文字，避免重复识别 |

### 断点续传流程

```
1. 检查输出目录是否存在 .progress.json
2. 读取最后处理的时间戳
3. 从该时间戳继续截图和OCR
4. 每次处理完更新进度文件
```

## 环境准备

```bash
pip install -r requirements.txt
```

依赖包括：
- moviepy - 视频处理
- paddleocr / paddlepaddle - OCR文字识别
- pandas - 数据处理

## 配置说明

编辑 `config/config.toml`：

```toml
[sys]
log_level = "INFO"
output_root = "D:\\workspace\\video-crawl-download-ocr-doc-rag\\output"

[video]
# 截图间隔（秒）
interval = 0.5
# 视频裁剪参数（用于去掉水印等）
# y1, y2 为负数表示从底部向上裁剪
crop_y1 = -200
crop_y2 = -30

[ocr]
# 置信度阈值
probability_threshold = 0.93
```

### UP主配置示例

```toml
[BILIBILI_UP_INFO.290663424]
uploader = "有何高见9527"
skip_line_pattern = "^\\d+$"
probability_threshold = 0.90
```

## 使用方法

### 命令行方式

#### 方式一：直接使用 .venv Python（推荐）

```bash
cd D:\workspace\video-crawl-download-ocr-doc-rag\video_crawl_download_ocr_doc_rag\app\skills\video_2_pic_2_text\scripts

# 视频转图片（分步执行）
D:\workspace\video-crawl-download-ocr-doc-rag\.venv\Scripts\python.exe video_2_pic.py -i "video.mp4"

# 图片转文字（分步执行）
D:\workspace\video-crawl-download-ocr-doc-rag\.venv\Scripts\python.exe pic_2_text.py -d "video_pics_dir"

# 一键完成（视频 -> 图片 -> 文字，流水线模式）
D:\workspace\video-crawl-download-ocr-doc-rag\.venv\Scripts\python.exe video_2_pic_2_text.py -i "video.mp4"
```

#### 方式二：激活虚拟环境后使用

```bash
cd D:\workspace\video-crawl-download-ocr-doc-rag\video_crawl_download_ocr_doc_rag

# 激活虚拟环境
.venv\Scripts\activate

cd app\skills\video_2_pic_2_text\scripts

# 视频转图片
python video_2_pic.py -i "video.mp4"

# 图片转文字
python pic_2_text.py -d "video_pics_dir"

# 一键完成
python video_2_pic_2_text.py -i "video.mp4"
```

### 脚本说明

| 脚本 | 功能 | 说明 |
|------|------|------|
| `video_2_pic.py` | 视频转图片 | 按固定间隔截取视频帧 |
| `pic_2_text.py` | 图片转文字 | 批量OCR识别图片 |
| `video_2_pic_2_text.py` | 一键流水线 | 截图+OCR并行执行，支持断点续传 |

### 参数说明

#### video_2_pic.py
```bash
python video_2_pic.py -i "video.mp4" [-d output_dir] [--interval 0.5] [--crop-y1 -200] [--crop-y2 -30]
```

| 参数 | 说明 |
|------|------|
| `-i, --input` | 输入视频文件路径（必需） |
| `-d, --dir` | 输出目录路径 |
| `--interval` | 截图间隔（秒），默认0.5 |
| `--crop-y1` | 裁剪起始Y坐标，默认-200 |
| `--crop-y2` | 裁剪结束Y坐标，默认-30 |

#### pic_2_text.py
```bash
python pic_2_text.py -d "pics_dir" [-o output_dir] [--interval 0.5]
```

| 参数 | 说明 |
|------|------|
| `-d, --dir` | 图片目录路径（必需） |
| `-o, --output` | 输出目录路径 |
| `-i, --interval` | 时间间隔（秒） |

#### video_2_pic_2_text.py（推荐）
```bash
python video_2_pic_2_text.py -i "video.mp4" [-d output_dir] [options]
```

| 参数 | 说明 |
|------|------|
| `-i, --input` | 输入视频文件路径（必需） |
| `-d, --dir` | 输出目录路径 |
| `--interval` | 截图间隔（秒） |
| `--crop-y1` | 裁剪起始Y坐标 |
| `--crop-y2` | 裁剪结束Y坐标 |
| `--skip-pattern` | 跳过匹配该正则表达式的行 |
| `--threshold` | 识别置信度阈值 |
| `--no-resume` | 禁用断点续传 |

## 输出结果

- 图片目录：`{output_root}/{UP主名}/{视频名}/`
- 进度文件：`{图片目录}/.progress.json`（断点续传用）
- OCR结果：`{图片目录}/{视频名}_ocr.csv`

### CSV格式

```
movie_cur_seconds,probability,line
10.5,0.95,识别到的文字内容
15.0,0.92,另一段文字
```

## 目录结构

```
video_2_pic_2_text/
├── config/
│   └── config.toml          # 配置文件
├── scripts/
│   ├── libs/
│   │   ├── __init__.py
│   │   ├── config.py       # 配置加载模块
│   │   └── logger.py       # 日志模块
│   ├── video_2_pic.py      # 视频转图片
│   ├── pic_2_text.py       # 图片转文字
│   └── video_2_pic_2_text.py  # 一键流水线（推荐）
├── output/                  # 输出目录
├── logs/                   # 日志目录
├── requirements.txt
├── SKILL.md
└── README.md
```

## 常见问题

### Q: 如何跳过某些文字？
A: 使用 `--skip-pattern` 参数指定正则表达式，如 `--skip-pattern "^\\d+$"` 跳过纯数字行

### Q: 如何调整识别阈值？
A: 使用 `--threshold` 参数，如 `--threshold 0.9` 降低阈值

### Q: 中途停止后如何继续？
A: 脚本会自动检测 `.progress.json`，下次运行会自动从断点继续

### Q: 截图和OCR可以分开执行吗？
A: 可以，先运行 `video_2_pic.py` 再运行 `pic_2_text.py`
