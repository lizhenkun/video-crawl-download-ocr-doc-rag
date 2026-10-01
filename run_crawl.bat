@REM call "D:\workspace\VideoCrawlOcrSummary\.venv\Scripts\activate.bat"
python -c "import sys; print(sys.executable)"
@REM pause

cd D:\workspace\video-crawl-download-ocr-doc-rag\video_crawl_download_ocr_doc_rag\app\skills\
@REM @REM 爬取up主的视频信息
python .\bilibili_crawler\scripts\crawl_uper_videos.py
@REM @REM 下载视频文件
python .\bilibili_crawler\scripts\download_uper_videos.py

@REM 把视频、csv移动到相关地方
python .\mv_bilibili_videos\scripts\mv_bilibili_videos.py
@REM 更新Excel里 视频、csv的位置信息
python .\mv_bilibili_videos\scripts\更新视频路径.py

@REM 把E盘里的CSV移动到D盘 python .\mv_bilibili_videos\scripts\更新视频路径.py

@REM @REM  视频最终转文字
python .\video_2_pic_2_text\scripts\batch_video_2_pic_2_text.py -u 有何高见9527 -y
@REM  python .\video_2_pic_2_text\scripts\batch_video_2_pic_2_text.py -u 珍大户 -y

@REM 老的脚本
@REM cd video_crawl_download_ocr_doc_rag
@REM python -m app.tools.crawl_uper_videos
@REM @REM start "C:\Program Files (x86)\Kingsoft\WPS Office\ksolaunch.exe"
@REM @echo "回车继续执行..."
@REM pause
@REM python -m app.tools.download_videos_from_excel
