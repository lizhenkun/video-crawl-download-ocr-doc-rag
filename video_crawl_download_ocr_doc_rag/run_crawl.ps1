# 视频爬取 -> 下载 -> 移动 -> 转文字 全流程脚本
# 由 run_crawl.bat 转换而来，run_crawl.bat 保持不变

$ErrorActionPreference = "Stop"

# 脚本自身所在目录（...\video_crawl_download_ocr_doc_rag）
$ScriptDir = $PSScriptRoot
$ParentDir = Split-Path -Parent $ScriptDir

# 1. 先判断上一层目录或当前目录是否存在 .venv，存在则先加载（优先上一层）
$venvActivate = $null
foreach ($candidate in @(
    (Join-Path $ParentDir ".venv"),
    (Join-Path $ScriptDir ".venv")
)) {
    $activatePs1 = Join-Path $candidate "Scripts\Activate.ps1"
    if (Test-Path -LiteralPath $activatePs1) {
        $venvActivate = $activatePs1
        break
    }
}

if ($venvActivate) {
    . $venvActivate
    Write-Host "已加载虚拟环境: $venvActivate"
} else {
    Write-Warning "上一层目录和当前目录均未找到 .venv，将使用系统 Python"
}

python -c "import sys; print(sys.executable)"

# 2. 基于脚本自身目录切换到 app\skills（不使用绝对路径硬编码）
$SkillsDir = Join-Path $ScriptDir "app\skills"
if (-not (Test-Path -LiteralPath $SkillsDir)) {
    throw "目录不存在: $SkillsDir"
}
Set-Location -LiteralPath $SkillsDir

# 爬取 up 主的视频信息
python .\bilibili_crawler\scripts\crawl_uper_videos.py
# 下载视频文件
python .\bilibili_crawler\scripts\download_uper_videos.py

# 把视频、csv 移动到相关地方
python .\mv_bilibili_videos\scripts\mv_bilibili_videos.py
# 更新 Excel 里 视频、csv 的位置信息
python .\mv_bilibili_videos\scripts\更新视频路径.py

# 视频最终转文字
python .\video_2_pic_2_text\scripts\batch_video_2_pic_2_text.py -u 有何高见9527 -y
# python .\video_2_pic_2_text\scripts\batch_video_2_pic_2_text.py -u 珍大户 -y
