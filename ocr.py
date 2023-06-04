import ddddocr
import re

"""
代码两种选择模式
普通模式：直接输入数字
分块模式：利用正表达将数据分块，可进行运算（目前对运算符号识别不友好）
"""


class Ocr_d:
    def __init__(self, png):
        self.png = png

    def rec(self):
        ocr = ddddocr.DdddOcr()
        with open(self.png, 'rb') as f:
            img_bytes = f.read()
        res = ocr.classification(img_bytes)
        return res

    def rec_sum(self):
        pattern = re.compile(r"\d+")
        res = list(map(int, pattern.findall(Ocr_d.rec(self))))
        return res
