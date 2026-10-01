#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
vectorize_knowledge - 知识向量化技能

将Markdown知识文档向量化，存入向量知识库，支持增量更新
"""

import argparse
import os
import sys
from pathlib import Path
from typing import Optional
import hashlib
import json
from datetime import datetime

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class VectorizeKnowledge:
    """知识向量化处理类"""

    def __init__(self, persist_dir: Optional[str] = None):
        """
        初始化向量知识库

        Args:
            persist_dir: 向量数据库持久化目录
        """
        self.persist_dir = persist_dir or str(PROJECT_ROOT / "vector_store")
        self.chunks_dir = os.path.join(self.persist_dir, "chunks")

        # 确保目录存在
        os.makedirs(self.persist_dir, exist_ok=True)
        os.makedirs(self.chunks_dir, exist_ok=True)

        # 初始化向量存储（简化版：使用文件存储+内存索引）
        self.documents = {}  # doc_id -> document
        self.metadata_store = {}  # doc_id -> metadata

        # 加载已存在的文档
        self._load_existing()

    def _load_existing(self):
        """加载已存在的文档"""
        metadata_file = os.path.join(self.persist_dir, "metadata.json")
        if os.path.exists(metadata_file):
            with open(metadata_file, 'r', encoding='utf-8') as f:
                self.metadata_store = json.load(f)

        # 加载文档内容
        if os.path.exists(self.chunks_dir):
            for filename in os.listdir(self.chunks_dir):
                if filename.endswith('.txt'):
                    doc_id = filename.replace('.txt', '')
                    doc_file = os.path.join(self.chunks_dir, filename)
                    with open(doc_file, 'r', encoding='utf-8') as f:
                        self.documents[doc_id] = f.read()

    def _save_metadata(self):
        """保存metadata"""
        metadata_file = os.path.join(self.persist_dir, "metadata.json")
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(self.metadata_store, f, ensure_ascii=False, indent=2)

    def _compute_file_hash(self, file_path: str) -> str:
        """计算文件hash"""
        hasher = hashlib.md5()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

    def _extract_frontmatter(self, content: str) -> dict:
        """提取Markdown frontmatter"""
        frontmatter = {}
        if content.startswith('---'):
            end_idx = content.find('---', 3)
            if end_idx > 0:
                fm_text = content[3:end_idx].strip()
                for line in fm_text.split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        frontmatter[key.strip()] = value.strip()
        return frontmatter

    def _generate_doc_id(self, file_path: str) -> str:
        """生成文档ID"""
        return hashlib.md5(file_path.encode()).hexdigest()[:12]

    def _read_markdown(self, file_path: str) -> tuple[str, dict]:
        """读取Markdown文件内容"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 提取frontmatter
        frontmatter = self._extract_frontmatter(content)

        # 提取正文（去掉frontmatter）
        if content.startswith('---'):
            end_idx = content.find('---', 3)
            if end_idx > 0:
                body = content[end_idx+3:].strip()
            else:
                body = content
        else:
            body = content

        return body, frontmatter

    def add_document(self, file_path: str) -> str:
        """
        添加单个文档到知识库

        Args:
            file_path: Markdown文件路径

        Returns:
            生成的doc_id
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")

        doc_id = self._generate_doc_id(file_path)
        file_hash = self._compute_file_hash(file_path)

        # 检查是否已存在且未更新
        if doc_id in self.metadata_store:
            if self.metadata_store[doc_id].get('hash') == file_hash:
                print(f"文档未更新，跳过: {file_path}")
                return doc_id

        # 读取内容
        body, frontmatter = self._read_markdown(file_path)

        # 创建文档记录
        metadata = {
            'doc_id': doc_id,
            'file_path': file_path,
            'hash': file_hash,
            'title': frontmatter.get('title', Path(file_path).stem),
            'date': frontmatter.get('date', datetime.now().strftime('%Y-%m-%d')),
            'tags': frontmatter.get('tags', '').replace('[', '').replace(']', '').split(','),
            'source': frontmatter.get('source', '有何高见9527'),
            'added_at': datetime.now().isoformat(),
            'content_preview': body[:500]  # 保存预览
        }

        # 存储文档（简化版：存储文本内容）
        self.documents[doc_id] = body
        self.metadata_store[doc_id] = metadata

        # 保存到文件
        doc_file = os.path.join(self.chunks_dir, f"{doc_id}.txt")
        with open(doc_file, 'w', encoding='utf-8') as f:
            f.write(body)

        self._save_metadata()

        print(f"✓ 已添加文档: {metadata['title']} (doc_id: {doc_id})")

        return doc_id

    def add_from_directory(self, dir_path: str) -> list[str]:
        """
        批量添加目录下所有Markdown文档

        Args:
            dir_path: 目录路径

        Returns:
            添加的doc_id列表
        """
        results = []

        for root, dirs, files in os.walk(dir_path):
            for file in files:
                if file.endswith('.md'):
                    file_path = os.path.join(root, file)
                    try:
                        doc_id = self.add_document(file_path)
                        results.append(doc_id)
                    except Exception as e:
                        print(f"✗ 处理失败 {file_path}: {e}")

        return results

    def query(self, query_text: str, top_k: int = 5) -> list[dict]:
        """
        查询知识库（简化版：基于关键词匹配）

        Args:
            query_text: 查询文本
            top_k: 返回前k个结果

        Returns:
            匹配的文档列表
        """
        results = []

        # 简化版：使用关键词匹配
        query_keywords = query_text.lower().split()

        for doc_id, content in self.documents.items():
            content_lower = content.lower()

            # 计算匹配分数
            score = 0
            for kw in query_keywords:
                if kw in content_lower:
                    score += 1

            if score > 0:
                metadata = self.metadata_store.get(doc_id, {})
                results.append({
                    'doc_id': doc_id,
                    'score': score,
                    'title': metadata.get('title', 'Unknown'),
                    'date': metadata.get('date', ''),
                    'content_preview': content[:500]
                })

        # 按分数排序
        results.sort(key=lambda x: x['score'], reverse=True)

        return results[:top_k]

    def delete_document(self, doc_id: str) -> bool:
        """
        删除文档

        Args:
            doc_id: 文档ID

        Returns:
            是否成功
        """
        if doc_id in self.documents:
            del self.documents[doc_id]

            # 删除文件
            doc_file = os.path.join(self.chunks_dir, f"{doc_id}.txt")
            if os.path.exists(doc_file):
                os.remove(doc_file)

            # 更新metadata
            if doc_id in self.metadata_store:
                del self.metadata_store[doc_id]
                self._save_metadata()

            print(f"✓ 已删除文档: {doc_id}")
            return True

        return False

    def list_documents(self) -> list[dict]:
        """
        列出所有文档

        Returns:
            文档列表
        """
        results = []
        for doc_id, metadata in self.metadata_store.items():
            results.append({
                'doc_id': doc_id,
                'title': metadata.get('title', 'Unknown'),
                'date': metadata.get('date', ''),
                'tags': metadata.get('tags', [])
            })
        return results


def add_documents(path: str, is_directory: bool = False) -> list[str]:
    """
    添加文档到知识库

    Args:
        path: 文件或目录路径
        is_directory: 是否为目录

    Returns:
        添加的doc_id列表
    """
    vk = VectorizeKnowledge()

    if is_directory:
        return vk.add_from_directory(path)
    else:
        return [vk.add_document(path)]


def query_knowledge(query_text: str, top_k: int = 5) -> list[dict]:
    """
    查询知识库

    Args:
        query_text: 查询文本
        top_k: 返回前k个结果

    Returns:
        匹配的文档列表
    """
    vk = VectorizeKnowledge()
    return vk.query(query_text, top_k)


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(description='知识向量化技能')
    parser.add_argument('--add', help='添加单个文档')
    parser.add_argument('--add-dir', help='批量添加目录')
    parser.add_argument('--sync', help='同步目录')
    parser.add_argument('--query', help='查询知识库')
    parser.add_argument('--list', action='store_true', help='列出所有文档')
    parser.add_argument('--delete', help='删除文档')
    parser.add_argument('--top-k', type=int, default=5, help='查询返回数量')

    args = parser.parse_args()

    vk = VectorizeKnowledge()

    if args.add:
        vk.add_document(args.add)
    elif args.add_dir:
        results = vk.add_from_directory(args.add_dir)
        print(f"\n共添加 {len(results)} 个文档")
    elif args.query:
        results = vk.query(args.query, args.top_k)
        print(f"\n找到 {len(results)} 个匹配结果:\n")
        for r in results:
            print(f"- {r['title']} (分数: {r['score']})")
            print(f"  {r['content_preview'][:200]}...")
            print()
    elif args.list:
        docs = vk.list_documents()
        print(f"\n知识库共有 {len(docs)} 个文档:\n")
        for doc in docs:
            print(f"- {doc['title']} ({doc['date']}) - {', '.join(doc['tags'])}")
    elif args.delete:
        vk.delete_document(args.delete)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
