#!/usr/bin/env bash
# 找出创建时间在指定分钟数内的 CSV 文件，把绝对路径输出到 recent_csv.log
# 用法: ./find_recent_csv.sh [分钟数=1440] [搜索目录=.]
set -u

MINUTES="${1:-1440}"
SEARCH_DIR="${2:-.}"
OUT_FILE="recent_csv.log"

# 先把搜索目录转成绝对路径，find 输出自然就是绝对路径
SEARCH_ABS="$(cd "$SEARCH_DIR" && pwd)" || exit 1

# 兼容 GNU stat(Linux, -c) 和 BSD stat(macOS, -f)
if stat -c '%W' . >/dev/null 2>&1; then
    get_birth() { stat -c '%W' "$1" 2>/dev/null; }
    get_mtime() { stat -c '%Y' "$1" 2>/dev/null; }
else
    get_birth() { stat -f '%B' "$1" 2>/dev/null; }
    get_mtime() { stat -f '%m' "$1" 2>/dev/null; }
fi

now=$(date +%s)
cutoff=$((now - MINUTES * 60))

count=0
: > "$OUT_FILE"
while IFS= read -r -d '' f; do
    birth="$(get_birth "$f")"
    # 文件系统不支持创建时间（值为 0 或空）时，退回到修改时间
    if [ -z "$birth" ] || [ "$birth" -le 0 ] 2>/dev/null; then
        birth="$(get_mtime "$f")"
    fi
    if [ -n "$birth" ] && [ "$birth" -ge "$cutoff" ] 2>/dev/null; then
        printf '%s\n' "$f" >> "$OUT_FILE"
        count=$((count + 1))
    fi
done < <(find "$SEARCH_ABS" -type f -iname '*.csv' -print0 2>/dev/null)

out_abs="$(pwd)/$OUT_FILE"
echo "搜索目录: $SEARCH_ABS"
echo "时间范围: 最近 $MINUTES 分钟"
echo "共找到 $count 个 csv 文件"
echo "已输出: $out_abs"
