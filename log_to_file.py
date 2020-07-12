import time
import hangul
from jamo import h2j, j2hcj, j2h


def extract_paragraph_from_log(report_chunk):
    report_list = report_chunk.split(
        '--------------------------------------------------------\n' +
        '--------------------------------------------------------\n' +
        '--------------------------------------------------------\n' +
        '\n' +
        '****************************\n')

    start0 = time.time()
    for i, report in enumerate(report_list):
        file_nm = ''
        file_text = ''
        paragraph_list = report.split(
            '--------------------------------------------------------\n' +
            '--------------------------------------------------------\n')

        # 리스트 인덱스 하나씩 다. 갯수세기
        start1 = time.time()
        for j, paragraph in enumerate(paragraph_list):
            if j == 0:
                file_nm = paragraph.split('\n')[0]

            if '다.' in paragraph or len(paragraph.split(' ')) > 20:
                file_text += paragraph + ' \n'

        save_to_txt(file_nm, file_text)
        end4 = time.time()

        print(f'{i + 1}/{len(report_list)}')
        print(f"for this task : {end4 - start1}")
        print(f"total time : {end4 - start0}")

    return


def save_to_txt(file_nm, file_text):
    root_dir = '/Users/daniel/Desktop/test_2/txt_2/'
    path = root_dir + file_nm
    path = hangul.join_jamos(j2hcj(h2j(path)))
    print(file_nm)

    with open(path, 'w') as out_file:
        out_file.write(file_text)


log_file_path = '/Users/daniel/Desktop/test_2/log/log_2.txt'
f = open(log_file_path)
extract_paragraph_from_log(f.read())
f.close()
