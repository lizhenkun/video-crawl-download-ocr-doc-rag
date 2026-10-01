# compose_knowledge - 有何高见视频字幕整理技能

将有何高见9527的视频字幕CSV文件整理成结构化的Markdown知识文档。

## 功能说明

该技能读取视频OCR字幕CSV文件，通过理解内容并提取核心观点、分析逻辑和推理过程，输出标准化的Markdown知识文档。

## 输入

| 参数 | 类型 | 说明 |
|------|------|------|
| csv_file | str | CSV文件路径 |
| related_materials | str | 相关背景材料（可选） |

## 输出

Markdown文件，保存路径与CSV同级目录：
- 输入：`2026-06-16 699 流动性紧张趋势会得到改善吗？_ocr.csv`
- 输出：`2026-06-16 699 流动性紧张趋势会得到改善吗？.md`

## Markdown文档结构

```markdown
---
title: 视频标题
date: 视频日期
tags: [标签1, 标签2]
---

## 核心观点
[一句话概括核心观点]

## 背景/事件
[事件背景描述]

## 分析逻辑
### 维度1
[详细分析]

### 维度2
[详细分析]

## 推理过程
[未来发展趋势的推演]

## 涉及知识点
- 知识点1
- 知识点2
```

## 使用方式

### 方式一：命令行

```bash
cd D:\workspace\video-crawl-download-ocr-doc-rag\.venv\Scripts

# 处理单个CSV文件
python.exe -m app.skills.compose_knowledge.main --csv "D:\workspace\video-crawl-download-ocr-doc-rag\doc\有何高见9527\2026.01-06\2026-06-16 699 流动性紧张趋势会得到改善吗？近期市场情绪修复是否昙花一现？_ocr.csv"

# 批量处理整个目录
python.exe -m app.skills.compose_knowledge.main --dir "D:\workspace\video-crawl-download-ocr-doc-rag\doc\有何高见9527\2026.01-06"

# 带相关材料
python.exe -m app.skills.compose_knowledge.main --csv "<path>" --materials "<相关材料>"
```

### 方式二：Python调用

```python
from app.skills.compose_knowledge import compose_knowledge

# 处理单个文件
result = compose_knowledge(
    csv_file="D:\\workspace\\video-crawl-download-ocr-doc-rag\\doc\\有何高见9527\\2026.01-06\\2026-06-16 699 流动性紧张趋势会得到改善吗？_ocr.csv",
    related_materials="相关背景材料（可选）"
)

# 批量处理目录
results = compose_knowledge_from_dir(
    dir_path="D:\\workspace\\video-crawl-download-ocr-doc-rag\\doc\\有何高见9527\\2026.01-06"
)
```

## 处理逻辑

1. **CSV读取**：解析OCR字幕文件（movie_cur_seconds, probability, line）
2. **内容理解**：
   - 识别视频主题
   - 提取核心观点
   - 梳理分析维度
   - 总结推理过程
3. **结构化输出**：按照标准Markdown模板生成文档

## 涉及分析维度

参考"有何高见9527"的分析特点：

| 维度 | 示例 |
|------|------|
| 全球宏观政策 | 美联储利率、QE印钱、流动性 |
| 地缘政治 | 中东冲突（美伊）、中美关系 |
| 经济数据 | 进出口、社零、房地产、贸易顺差 |
| 产业趋势 | AI、电动车、芯片 |

## 注意事项

- 去除口语化表达，保留核心内容
- 保持UP主分析逻辑的完整性
- 提取关键数据和结论
- 梳理事件之间的逻辑关系
