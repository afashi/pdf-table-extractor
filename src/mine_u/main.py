import os
from io import BytesIO

import fitz
from magic_pdf.data.data_reader_writer import FileBasedDataWriter, FileBasedDataReader
from magic_pdf.data.dataset import PymuDocDataset
from magic_pdf.model.doc_analyze_by_custom_model import doc_analyze
from magic_pdf.config.enums import SupportedPdfParseMethod

def doc_parse(pdf_path, output_path, page_start=None, page_end=None):
    filename = os.path.basename(pdf_path)
    # prepare env
    local_image_dir, local_md_dir = (output_path + "/images", output_path)
    os.makedirs(local_image_dir, exist_ok=True)
    image_writer, md_writer = FileBasedDataWriter(local_image_dir), FileBasedDataWriter(local_md_dir)
    name_without_suff = filename.split(".")[0]
    reader = FileBasedDataReader()
    if page_start is not None and page_end is not None:
        name_without_suff = name_without_suff + f"_{page_start}-{page_end}"
        pdf_bytes = split_pdf_by_range_fitz(pdf_path, page_start, page_end)
        ds = PymuDocDataset(pdf_bytes)
    else:
        pdf_bytes = reader.read(pdf_path)
        ds = PymuDocDataset(pdf_bytes)

    if ds.classify() == SupportedPdfParseMethod.OCR:
        infer_result = ds.apply(doc_analyze, ocr=True, lang="ch")
        ## pipeline
        pipe_result = infer_result.pipe_ocr_mode(image_writer)
    else:
        infer_result = ds.apply(doc_analyze, ocr=False, lang="ch")
        ## pipeline
        pipe_result = infer_result.pipe_txt_mode(image_writer)
    pipe_result.get_middle_json()
    pipe_result.dump_middle_json(md_writer, f"{name_without_suff}_middle.json")


def split_pdf_by_range_fitz(input_path, start_page, end_page):
    """
    根据页码范围切分 PDF，返回二进制数据
    :param input_path: PDF 文件路径
    :param start_page: 起始页码（从 0 开始）
    :param end_page: 结束页码（包含，从 0 开始）
    :return: 切分后的二进制数据 (bytes)
    """
    doc = fitz.open(input_path)
    new_doc = fitz.open()  # 创建空文档
    # 插入指定页码范围（PyMuPDF 的页码从 0 开始）
    new_doc.insert_pdf(doc, from_page=start_page, to_page=end_page)
    # 将结果保存到内存中的字节流
    buffer = BytesIO()
    new_doc.save(buffer)  # 写入二进制流
    buffer.seek(0)
    doc.close()
    new_doc.close()
    return buffer.getvalue()  # 返回二进制数组


if __name__ == "__main__":
    input_path_ = "C:\\Code\\MyWorkspace\\table-extract\\input\\安徽国风新材料股份有限公司_2024-12-31_年度报告_2025-03-15-2-19.pdf"
    output_path_ = "C:\\Code\\MyWorkspace\\table-extract\\output\\"
    doc_parse(input_path_, output_path_, 1, 4)
