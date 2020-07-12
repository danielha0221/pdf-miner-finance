import ocrmypdf


ocrmypdf.ocr('/Users/daniel/Desktop/test_2/pdf/105_9393_2018-07-20_현대해상_A001450_정준섭_유안타증권-1.jpg',
             '/Users/daniel/Desktop/test_2/pdf/105_9393_2018-07-20_현대해상_A001450_정준섭_유안타증권-1.pdf', image_dpi=300, language=['kor+eng'], output_type='pdf', force_ocr=True, deskew=True)
