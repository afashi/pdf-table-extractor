# src/pdf_extractor/services/parser_service.py

import fitz  # PyMuPDF
from typing import List, Dict, Any

from ..core.logger import logger


class PDFParserService:
    """
    一个专门用于解析和从PDF文件中提取信息的服务类。
    """

    def get_toc(self, pdf_path: str) -> List[Dict[str, Any]]:
        """
        从给定的PDF文件中提取目录 (Table of Contents, TOC)。

        此方法会处理文件打开、TOC提取以及格式化输出的整个流程。

        Args:
            pdf_path (str): PDF文件的绝对路径。

        Returns:
            一个字典列表，每个字典代表一个TOC条目。
            示例:
            [
                {"level": 1, "title": "第一章", "page": 5},
                {"level": 2, "title": "1.1 节", "page": 6},
                ...
            ]
            如果PDF没有目录或发生错误，则返回一个空列表。

        Raises:
            ValueError: 如果文件路径无法作为有效的PDF打开。
        """
        logger.info(f"尝试从 '{pdf_path}' 提取目录...")
        try:
            # 使用 fitz.open() 打开 PDF 文件
            doc = fitz.open(pdf_path)
        except Exception as e:
            logger.error(f"无法打开或读取PDF文件 '{pdf_path}': {e}", exc_info=True)
            # 抛出一个更具体的异常，以便上层调用者可以捕获
            raise ValueError(f"无法打开PDF文件: {pdf_path}") from e

        # 检查文档是否为有效的PDF
        if not doc.is_pdf:
            logger.warning(f"文件 '{pdf_path}' 不是一个有效的PDF文档。")
            doc.close()
            return []

        # 获取原始目录信息
        # fitz 返回一个列表，每个元素是 [level, title, page, ...]
        toc_raw = doc.get_toc()
        doc.close()  # 操作完成后务必关闭文档

        if not toc_raw:
            logger.info(f"在 '{pdf_path}' 中未找到目录。")
            return []

        # 将原始TOC格式化为更友好的字典列表
        formatted_toc = []
        for level, title, page in toc_raw:
            formatted_toc.append({
                "level": level,
                "title": title.strip(),  # 去除标题前后的空白
                "page": page
            })

        logger.info(f"成功从 '{pdf_path}' 提取了 {len(formatted_toc)} 个目录条目。")
        return formatted_toc