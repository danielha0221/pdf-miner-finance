import time
import hangul
from jamo import h2j, j2hcj, j2h


def extract_paragraph_from_log(report_chunk):
    end = '--end----------------------------------------------------\n'
    start = '--start--------------------------------------------------\n'
    report_list = report_chunk.split('****************************\n')

    start0 = time.time()
    for i, report in enumerate(report_list):
        file_nm = ''
        file_text = ''
        paragraph_list = report.split(end + start)

        # 리스트 인덱스 하나씩 다. 갯수세기
        start1 = time.time()
        for j, paragraph in enumerate(paragraph_list):
            if j == 0:
                file_nm = paragraph.split('\n')[0]

            if start in paragraph:
                for para in paragraph.split(start):
                    if end in para:
                        for pa in para.split(end):
                            if '다.' in pa or len(pa.split(' ')) > 20:
                                file_text += pa + ' \n'

                    elif '다.' in para or len(para.split(' ')) > 20:
                        file_text += para + ' \n'

            elif '다.' in paragraph or len(paragraph.split(' ')) > 20:
                file_text += paragraph + ' \n'

        save_to_txt(file_nm, file_text)
        end4 = time.time()

        print(f'{i + 1}/{len(report_list)}')
        print(f"for this task : {end4 - start1}")
        print(f"total time : {end4 - start0}")

    return


def save_to_txt(file_nm, file_text):
    root_dir = '/Users/daniel/Desktop/test_2/after_inspec_txt/'
    path = root_dir + file_nm
    path = hangul.join_jamos(j2hcj(h2j(path)))
    print(file_nm)

    with open(path, 'w') as out_file:
        out_file.write(file_text)


log_file_path = '/Users/daniel/Desktop/test_2/log/log_2.txt'
f = open(log_file_path)
extract_paragraph_from_log(f.read())
f.close()
