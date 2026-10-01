# mv_bilibili_videos Skill

移动B站视频文件到目标目录，按年份归档。

## 虚拟环境

Python解释器: `D:\workspace\video-crawl-download-ocr-doc-rag\.venv\Scripts\python.exe`

## 功能
- 从 `D:\workspace\video-crawl-download-ocr-doc-rag\output` 读取视频和CSV/Excel文件
- 将视频文件(.mp4)移动到 `E:\00 视频\Up主\{UP主名}\{年份}\` 目录
- 将CSV和Excel文件复制到 `D:\workspace\video-crawl-download-ocr-doc-rag\doc\{UP主名}\` 目录
- 对于"有何高见9527"UP主的特殊处理：
  - 以 `yyyy-mm-dd 数字` 开头的视频 → `E:\00 视频\Up主\有何高见9527\充电专属\{年份}\` 目录
  - 以 `第xxxx期_yyyyMMdd_` 开头的视频 → 
    如果 MM 属于 01 02 03 , 放入
    `E:\00 视频\Up主\有何高见9527\{年份}\01-03` 目录
    如果 MM 属于 04 05 06 , 放入
    `E:\00 视频\Up主\有何高见9527\{年份}\04-06` 目录
    如果 MM 属于 07 08 09 , 放入
    `E:\00 视频\Up主\有何高见9527\{年份}\07-09` 目录
    如果 MM 属于 10 11 12 , 放入
    `E:\00 视频\Up主\有何高见9527\{年份}\10-12` 目录

## 使用方法

方式一：直接使用 .venv Python（推荐）
```bash
cd D:\workspace\video-crawl-download-ocr-doc-rag

# 模拟运行所有UP主
D:\workspace\video-crawl-download-ocr-doc-rag\.venv\Scripts\python.exe -m video_crawl_download_ocr_doc_rag.app.skills.mv_bilibili_videos.scripts.mv_bilibili_videos --dry-run

# 实际运行
D:\workspace\video-crawl-download-ocr-doc-rag\.venv\Scripts\python.exe -m video_crawl_download_ocr_doc_rag.app.skills.mv_bilibili_videos.scripts.mv_bilibili_videos

# 只处理"有何高见9527"
D:\workspace\video-crawl-download-ocr-doc-rag\.venv\Scripts\python.exe -m video_crawl_download_ocr_doc_rag.app.skills.mv_bilibili_videos.scripts.mv_bilibili_videos --up "有何高见9527"
```

方式二：激活虚拟环境后使用
```bash
cd D:\workspace\video-crawl-download-ocr-doc-rag

# 激活虚拟环境
.venv\Scripts\activate

# 模拟运行所有UP主
python -m video_crawl_download_ocr_doc_rag.app.skills.mv_bilibili_videos.scripts.mv_bilibili_videos --dry-run

# 实际运行
python -m video_crawl_download_ocr_doc_rag.app.skills.mv_bilibili_videos.scripts.mv_bilibili_videos

# 只处理"有何高见9527"
python -m video_crawl_download_ocr_doc_rag.app.skills.mv_bilibili_videos.scripts.mv_bilibili_videos --up "有何高见9527"
```

## 参数
- `--source`: 源目录路径 (默认: `D:\workspace\video-crawl-download-ocr-doc-rag\output`)
- `--video-target`: 视频目标目录路径 (默认: `E:\00 视频\Up主`)
- `--csv-target`: CSV目标目录路径 (默认: `D:\workspace\video-crawl-download-ocr-doc-rag\doc`)
- `--dry-run`: 模拟运行，不实际移动文件
- `--up`: 只处理指定的UP主 (默认处理所有)

## 示例
```bash
# 模拟运行所有UP主
python -m video_crawl_download_ocr_doc_rag.app.skills.mv_bilibili_videos.scripts.mv_bilibili_videos --dry-run

# 实际运行
python -m video_crawl_download_ocr_doc_rag.app.skills.mv_bilibili_videos.scripts.mv_bilibili_videos

# 只处理"有何高见9527"
python -m video_crawl_download_ocr_doc_rag.app.skills.mv_bilibili_videos.scripts.mv_bilibili_videos --up "有何高见9527"

# 指定视频和CSV目标目录
python -m video_crawl_download_ocr_doc_rag.app.skills.mv_bilibili_videos.scripts.mv_bilibili_videos --video-target "E:\00 视频\Up主" --csv-target "D:\workspace\video-crawl-download-ocr-doc-rag\doc"
```
