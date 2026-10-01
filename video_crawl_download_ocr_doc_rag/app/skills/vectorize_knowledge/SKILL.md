# vectorize_knowledge - 知识向量化技能

将Markdown知识文档向量化，存入向量知识库，支持增量更新。

## 功能说明

将已整理的Markdown知识文档通过embedding模型向量化，存储到向量数据库（Chroma）中，支持增量添加、更新和同步。

## 输入

| 参数 | 类型 | 说明 |
|------|------|------|
| doc_path | str | Markdown文件路径或目录路径 |
| mode | str | "add"=添加, "update"=更新, "sync"=同步 |

## 输出

向量数据库中的文档向量存储

## 使用方式

### 方式一：命令行

```bash
cd D:\workspace\video-crawl-download-ocr-doc-rag\.venv\Scripts

# 添加单个文档到知识库
python.exe -m app.skills.vectorize_knowledge.main --add "D:\workspace\video-crawl-download-ocr-doc-rag\doc\有何高见9527\2026.01-06\2026-06-16 699 流动性紧张趋势会得到改善吗？.md"

# 批量添加目录下所有文档
python.exe -m app.skills.vectorize_knowledge.main --add-dir "D:\workspace\video-crawl-download-ocr-doc-rag\doc\有何高见9527\2026.01-06"

# 同步整个目录
python.exe -m app.skills.vectorize_knowledge.main --sync "D:\workspace\video-crawl-download-ocr-doc-rag\doc\有何高见9527"

# 查询知识库
python.exe -m app.skills.vectorize_knowledge.main --query "美国印钱"
```

### 方式二：Python调用

```python
from app.skills.vectorize_knowledge import VectorizeKnowledge

vk = VectorizeKnowledge()

# 添加文档
vk.add_document("path/to/doc.md")

# 批量添加
vk.add_from_directory("path/to/docs/")

# 相似度查询
results = vk.query("美国印钱", top_k=5)

# 删除文档
vk.delete_document("doc_id")
```

## 向量存储配置

### 默认配置

```toml
[vector_store]
type = "chroma"  # chroma 或 pgvector
persist_dir = "D:\\workspace\\video-crawl-download-ocr-doc-rag\\vector_store"

[embedding]
model = "BAAI/bge-m3"  # 中文优化embedding模型
```

### Metadata设计

每个文档存储以下metadata：

```json
{
  "source": "有何高见9527",
  "date": "2026-06-16",
  "title": "流动性紧张趋势会得到改善吗？",
  "tags": ["流动性", "美联储", "特朗普"],
  "file_path": "原始CSV路径"
}
```

## 增量处理逻辑

1. **添加模式(add)**：新增文档，忽略已存在的
2. **更新模式(update)**：根据文件hash判断是否有更新
3. **同步模式(sync)**：
   - 检测新增文档 → 添加
   - 检测更新文档 → 更新
   - 标记已删除文档 → 软删除

## 注意事项

- 首次使用需确保embedding模型已下载
- 大量文档建议分批处理
- 定期备份向量数据库
