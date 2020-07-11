#!/usr/bin/python
# -*- coding: utf-8 -*-

from io import StringIO, BytesIO

from finance_converter import FinanceConverter
from pdfminer.pdfdocument import PDFDocument, PDFStream
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfparser import PDFParser
from pdfminer.layout import LAParams, LTTextBox, LTTextLine
from pdfminer.pdfdevice import PDFDevice, TagExtractor

from os import listdir
from os.path import isfile, join

class ExtractText():

    def __init__(self):
        self.finance_words = list()
        self.finance_words_count = dict()
        self.report_pdf_dir = '/Users/eunbyul/Desktop/git/pdf-miner-finance/report/'
        self.report_pdf_list  = [f for f in listdir(self.report_pdf_dir) if isfile(join(self.report_pdf_dir, f))]

    def convert_pdf_to_txt(self, pdf_file):
        """PDF파일을 텍스트로 변환해주는 함수

        Args:
            pdf ([PDF]): PDF파일

        Returns:
            [dict]: PDF에서 텍스트로 변환된 결과물
        """
        report_text = dict()
        output_string = StringIO()
        file_nm = pdf_file.split(".")[0]
        file_ex = pdf_file.split(".")[1]

        pdf_path = self.report_pdf_dir + pdf_file
        out_path = self.report_pdf_dir + 'out/' + file_nm + '.txt'

        laparams = LAParams(line_overlap=.5,
                            char_margin=.38,
                            line_margin=1.1,
                            word_margin=0.01,
                            boxes_flow=.8,
                            detect_vertical=False,
                            all_texts=False)

        rsrcmgr = PDFResourceManager()
        device = FinanceConverter(rsrcmgr, output_string, laparams=laparams)
        interpreter = PDFPageInterpreter(rsrcmgr, device)

        # Extract text
        with open(pdf_path, 'rb') as in_file:

            for page_num, page in enumerate(PDFPage.get_pages(in_file, check_extractable=True)):
                interpreter.process_page(page)
                report_text = output_string.getvalue()
        
        with open(out_path, 'w') as out_file:

            out_file.write(file_nm + '\n')
            out_file.write(report_text)
        return

    def detect_finance_page(self, text):
        """텍스트로 변환된 스트링을 받아서, 재무 분석 의견이 있는 페이지를 찾는 함수

        Args:
            text (string): [description]

        Returns:
            [list]: 재무 분석 문단이 있는 페이지
        """
        # '1_185_2018-12-20_LG유플러스_A032640_최남곤_유안타증권'
        # if '제목' in page_num:
        #     print(value)

        page_num = 0

        return page_num

    def detect_finance_paragraph(self, text, page_num):
        """문단과 제목의 분리

        Args:
            text ([string]): 텍스트로 변환된 재무 문서
            page_num ([list]): 재무 분석 문단이 있는 페이지

        Returns:
            [dict]: 문단 텍스트
        """
        paragraph = ''

        # 문단과 제묵 분리 인식
        return paragraph

    def extract_finance_words(self):

        pass

    def match_finance_words(self):
        pass

    def save_to_csv(self):
        pass

    def main(self):
        # 이게 먼저 #input pdf output text
        for pdf_file in self.report_pdf_list:
            text = self.convert_pdf_to_txt(pdf_file)
            # paragraph = self.detect_finance_paragraph(text)
            # mined_words = self.extract_finance_words(paragraph)
            # self.match_finance_words()
            # self.save_to_csv()


if __name__ == "__main__":
    extract = ExtractText()
    extract.main()
