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
        self.root_dir = '/Users/eunbyul/Desktop/증권회사/10_유안타증권_배은별_2/10_유안타증권_배은별_2/'
        self.report_pdf_dir = self.root_dir + 'pdf/'
        self.output_txt_dir = self.root_dir + 'txt/'
        self.temp_img_dir = self.root_dir + 'tmp/'
        self.log_dir = self.root_dir + 'log/'

        self.report_pdf_list = [f for f in listdir(
            self.report_pdf_dir) if isfile(join(self.report_pdf_dir, f))]
        self.file_nm = ''
        self.pdf_path = ''

        for dirs in [self.output_txt_dir, self.temp_img_dir, self.log_dir]:
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
                            char_margin=1.38,
                            line_margin=1.1,
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
                report_text, found = self.page_text_finder(page_text)
                if found:
                    break

            if not found:
                report_text = None

        return report_text

    def page_text_finder(self, report_text):
        """텍스트로 변환된 스트링을 받아서, 재무 분석 의견이 있는 페이지를 찾는 함수

        Args:
            report_text (string): [description]

        Returns:
            [list]: 재무 분석 문단이 있는 페이지
        """
        page_text = ''
        text = ''
        i = 0
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

        return page_text, found

    def extract_paragraph(self, page_text):
        """문단과 제목의 분리

        Args:
            text ([string]): 텍스트로 변환된 재무 문서
            page_num ([list]): 재무 분석 문단이 있는 페이지

        Returns:
            [dict]: 문단 텍스트
        """
        text = ''
        # page_text = page_text[58:-58]
        paragraph_list = page_text.split(
            '--------------------------------------------------------\n--------------------------------------------------------\n')

        # 리스트 인덱스 하나씩 다. 갯수세기

        for paragraph in paragraph_list:
            if '다.' in paragraph:
                text += paragraph + ' \n'
            if "--------------------------------------------------------\n" in text:
                text = text.replace(
                    "--------------------------------------------------------\n", '')

        return text

    def convert_pdf_to_img_to_txt(self):
        pages = convert_from_path(self.pdf_path, 500)
        self.temp_img_dir = self.root_dir + 'tmp/'

        converted_text = ''
        for i, page in enumerate(pages):
            img_path = self.temp_img_dir + self.file_nm + f'-{i}' + '.jpg'
            page.save(img_path, 'JPEG')
            text = pytesseract.image_to_string(
                Image.open(img_path), lang='kor+eng')
            converted_text += text

        return converted_text

    def create_log_txt(self):
        with open(self.log_dir + 'log.txt', 'a') as out_file:
            out_file.write(self.file_nm + '.txt \n')

    def save_to_txt(self, txt):
        output_path = self.output_txt_dir + self.file_nm + '.txt'
        output_path = hangul.join_jamos(j2hcj(h2j(output_path)))

        with open(output_path, 'w') as out_file:
            out_file.write(txt)

    def main(self):
        # 이게 먼저 #input pdf output text
        # print(self.report_pdf_list)
        start0 = time.time()
        for i, pdf_file in enumerate(sorted(self.report_pdf_list)):
            start1 = time.time()
            report_text = self.convert_pdf_to_txt(pdf_file)

            if report_text:
                txt = self.extract_paragraph(report_text)
            else:
                txt = self.convert_pdf_to_img_to_txt()
                self.create_log_txt()
            self.save_to_txt(txt)
            end4 = time.time()

            print(f'{i + 1}/{len(self.report_pdf_list)}')
            print(f"for this task : {end4 - start1}")
            print(f"total time : {end4 - start0}")


if __name__ == "__main__":
    extract = ExtractText()
    extract.main()
