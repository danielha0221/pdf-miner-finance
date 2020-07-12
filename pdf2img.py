from pdf2image import convert_from_path
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter


pages = convert_from_path(
    '/Users/daniel/Desktop/test_2/pdf/105_9393_2018-07-20_현대해상_A001450_정준섭_유안타증권.pdf', 500)


for i, page in enumerate(pages):
    img_path = f'/Users/daniel/Desktop/test_2/pdf/105_9393_2018-07-20_현대해상_A001450_정준섭_유안타증권-{i+1}.jpg'
    page.save(img_path, 'JPEG')
    text = pytesseract.image_to_string(
        Image.open(img_path), lang='kor+eng')
    f = open(f"/Users/daniel/Desktop/test_2/pdf/a-{i}.txt", "w")
    f.write(text)
    f.close()
