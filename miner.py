#!/usr/bin/python
# -*- coding: utf-8 -*-

# pip install pytesseract pdf2image jamo hangul pdfminer.six
# brew install poppler tesseract tesseract-lang

from io import StringIO, BytesIO
import os
from os import listdir
from os.path import isfile, join
import time

from finance_converter import FinanceConverter
from pdfminer.pdfdocument import PDFDocument, PDFStream
from pdfminer.converter import TextConverter
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfparser import PDFParser
from pdfminer.layout import LAParams, LTTextBox, LTTextLine
from pdfminer.pdfdevice import PDFDevice, TagExtractor
import hangul
from jamo import h2j, j2hcj, j2h
from pdf2image import convert_from_path
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter


class ExtractText():

    def __init__(self):
        self.finance_words = list()
        self.finance_words_count = dict()
        self.root_dir = '/Users/daniel/Desktop/test_2/'
        self.report_pdf_dir = self.root_dir + 'pdf/'
        self.output_txt_dir = self.root_dir + 'txt/'
        self.after_inspec_dir = self.root_dir + 'after_inspec_txt/'
        self.log_dir = self.root_dir + 'log/'

        self.report_pdf_list = [f for f in listdir(
            self.report_pdf_dir) if isfile(join(self.report_pdf_dir, f))]
        self.file_nm = ''
        self.pdf_path = ''

        for dirs in [self.output_txt_dir, self.after_inspec_dir, self.log_dir]:
            if not os.path.exists(dirs):
                os.makedirs(dirs)

        if '.DS_Store' in self.report_pdf_list:
            self.report_pdf_list.pop(self.report_pdf_list.index('.DS_Store'))

    def convert_pdf_to_txt(self, pdf_file):
        """PDF파일을 텍스트로 변환해주는 함수

        Args:
            pdf ([PDF]): PDF파일

        Returns:
            [dict]: PDF에서 텍스트로 변환된 결과물
        """

        output_string = StringIO()
        self.file_nm = pdf_file.split(".")[0]
        file_ex = pdf_file.split(".")[1]

        self.pdf_path = self.report_pdf_dir + pdf_file
        self.pdf_path = hangul.join_jamos(j2hcj(h2j(self.pdf_path)))

        laparams = LAParams(line_overlap=.5,
                            char_margin=1.35,
                            line_margin=1.0,
                            word_margin=0.01,
                            boxes_flow=.5,
                            detect_vertical=False,
                            all_texts=False)

        rsrcmgr = PDFResourceManager()
        device = FinanceConverter(rsrcmgr, output_string, laparams=laparams)
        interpreter = PDFPageInterpreter(rsrcmgr, device)

        # Extract text
        found = False
        with open(self.pdf_path, 'rb') as in_file:

            for page_num, page in enumerate(PDFPage.get_pages(in_file, check_extractable=True)):
                interpreter.process_page(page)
                page_text = output_string.getvalue()
                report_text, found, company_nm, company_num = self.page_text_finder(
                    page_text)
                if found:
                    break

            if not found:
                report_text = None

        return report_text, company_nm, company_num

    def page_text_finder(self, report_text):
        page_text = ''
        text = ''
        found = False

        company_name = self.file_nm.split('_')[3]
        company_num = self.file_nm.split('_')[4][1:]

        company_dict = {'LG상사': 'LG 상사'}

        # To resolve hangul encoding issue
        company_name = hangul.join_jamos(j2hcj(h2j(company_name)))

        if company_name in company_dict.keys():
            company_name = company_dict[company_name]

        for line in report_text.split('\n'):
            if "page_id" in line and '||Title||  ' + company_name in text and company_num in text:
                page_text = text
                found = True
                break

            elif "page_id" in line:
                text = ''
            else:
                text += line + '\n'

        return page_text, found, company_name, company_num

    def extract_paragraph(self, page_text):
        text = ''
        end = '--end----------------------------------------------------\n'
        start = '--start--------------------------------------------------\n'
        paragraph_list = page_text.split(end + start)

        # 리스트 인덱스 하나씩 다. 갯수세기
        for paragraph in paragraph_list:
            if start in paragraph:
                for para in paragraph.split(start):
                    if end in para:
                        for pa in para.split(end):
                            if '다.' in pa or len(pa.split(' ')) > 20:
                                text += pa + ' \n'

                    elif '다.' in para or len(para.split(' ')) > 20:
                        text += para + ' \n'

            elif '다.' in paragraph or len(paragraph.split(' ')) > 20:
                text += paragraph + ' \n'

        return text

    def convert_pdf_to_img_to_txt(self):
        pages = convert_from_path(self.pdf_path, 500)
        self.temp_img_dir = self.root_dir + 'tmp/'

        converted_text = ''
        for i, page in enumerate(pages):
            img_path = self.temp_img_dir + self.file_nm + f'-{i}' + '.jpg'
            page.save(img_path, 'JPEG')

            im = Image.open(img_path)
            text = pytesseract.image_to_string(
                im, lang='kor')
            converted_text += text

        return converted_text

    def create_log_txt(self, txt, company_nm, company_num):
        with open(self.log_dir + 'log.txt', 'a') as out_file:
            out_file.write(self.file_nm + '.txt \n')
            out_file.write(company_nm + ' ' + company_num + '\n')
            txt = txt.split('\n')[1:-1]
            txt = '\n'.join(txt)
            out_file.write(txt + '\n')
            out_file.write('****************************\n')

    def save_to_txt(self, txt):
        output_path = self.output_txt_dir + self.file_nm + '.txt'
        output_path = hangul.join_jamos(j2hcj(h2j(output_path)))

        with open(output_path, 'w') as out_file:
            out_file.write(txt)

    def main(self):
        start0 = time.time()
        for i, pdf_file in enumerate(sorted(self.report_pdf_list)):
            start1 = time.time()
            report_text, company_nm, company_num = self.convert_pdf_to_txt(
                pdf_file)

            if report_text:
                txt = self.extract_paragraph(report_text)
                self.create_log_txt(report_text, company_nm, company_num)
                self.save_to_txt(txt)

            end4 = time.time()

            print(f'{i + 1}/{len(self.report_pdf_list)}')
            print(f"for this task : {end4 - start1}")
            print(f"total time : {end4 - start0}")


if __name__ == "__main__":
    extract = ExtractText()
    extract.main()
