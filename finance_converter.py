import logging
import re
import sys
from pdfminer.pdfdevice import PDFTextDevice
from pdfminer.pdffont import PDFUnicodeNotDefined
from pdfminer.layout import LTContainer
from pdfminer.layout import LTPage
from pdfminer.layout import LTAnno
from pdfminer.layout import LTText
from pdfminer.layout import LTLine
from pdfminer.layout import LTRect
from pdfminer.layout import LTCurve
from pdfminer.layout import LTFigure
from pdfminer.layout import LTImage
from pdfminer.layout import LTChar
from pdfminer.layout import LTTextLine
from pdfminer.layout import LTTextLineHorizontal
from pdfminer.layout import LTTextBox
from pdfminer.layout import LTTextBoxVertical
from pdfminer.layout import LTTextBoxHorizontal
from pdfminer.layout import LTTextGroup
from pdfminer.utils import apply_matrix_pt
from pdfminer.utils import mult_matrix
from pdfminer.utils import enc
from pdfminer.utils import bbox2str
from pdfminer import utils
import hangul
from jamo import h2j, j2hcj, j2h

log = logging.getLogger(__name__)


class PDFLayoutAnalyzer(PDFTextDevice):
    def __init__(self, rsrcmgr, pageno=1, laparams=None):
        PDFTextDevice.__init__(self, rsrcmgr)
        self.pageno = pageno
        self.laparams = laparams
        self._stack = []
        return

    def begin_page(self, page, ctm):
        (x0, y0, x1, y1) = page.mediabox
        (x0, y0) = apply_matrix_pt(ctm, (x0, y0))
        (x1, y1) = apply_matrix_pt(ctm, (x1, y1))
        mediabox = (0, 0, abs(x0-x1), abs(y0-y1))
        self.cur_item = LTPage(self.pageno, mediabox)
        return

    def end_page(self, page):
        assert not self._stack, str(len(self._stack))
        assert isinstance(self.cur_item, LTPage), str(type(self.cur_item))
        if self.laparams is not None:
            self.cur_item.analyze(self.laparams)
        self.pageno += 1
        self.receive_layout(self.cur_item)
        # print(self.test[:500])
        return

    def begin_figure(self, name, bbox, matrix):
        self._stack.append(self.cur_item)
        self.cur_item = LTFigure(name, bbox, mult_matrix(matrix, self.ctm))
        return

    def end_figure(self, _):
        fig = self.cur_item
        assert isinstance(self.cur_item, LTFigure), str(type(self.cur_item))
        self.cur_item = self._stack.pop()
        self.cur_item.add(fig)
        return

    def render_image(self, name, stream):
        assert isinstance(self.cur_item, LTFigure), str(type(self.cur_item))
        item = LTImage(name, stream,
                       (self.cur_item.x0, self.cur_item.y0,
                        self.cur_item.x1, self.cur_item.y1))
        self.cur_item.add(item)
        return

    def paint_path(self, gstate, stroke, fill, evenodd, path):
        shape = ''.join(x[0] for x in path)
        if shape == 'ml':
            # horizontal/vertical line
            (_, x0, y0) = path[0]
            (_, x1, y1) = path[1]
            (x0, y0) = apply_matrix_pt(self.ctm, (x0, y0))
            (x1, y1) = apply_matrix_pt(self.ctm, (x1, y1))
            if x0 == x1 or y0 == y1:
                self.cur_item.add(LTLine(gstate.linewidth, (x0, y0), (x1, y1),
                                         stroke, fill, evenodd, gstate.scolor,
                                         gstate.ncolor))
                return
        if shape == 'mlllh':
            # rectangle
            (_, x0, y0) = path[0]
            (_, x1, y1) = path[1]
            (_, x2, y2) = path[2]
            (_, x3, y3) = path[3]
            (x0, y0) = apply_matrix_pt(self.ctm, (x0, y0))
            (x1, y1) = apply_matrix_pt(self.ctm, (x1, y1))
            (x2, y2) = apply_matrix_pt(self.ctm, (x2, y2))
            (x3, y3) = apply_matrix_pt(self.ctm, (x3, y3))
            if (x0 == x1 and y1 == y2 and x2 == x3 and y3 == y0) or \
                    (y0 == y1 and x1 == x2 and y2 == y3 and x3 == x0):
                self.cur_item.add(LTRect(gstate.linewidth, (x0, y0, x2, y2),
                                         stroke, fill, evenodd, gstate.scolor,
                                         gstate.ncolor))
                return
        # other shapes
        pts = []
        for p in path:
            for i in range(1, len(p), 2):
                pts.append(apply_matrix_pt(self.ctm, (p[i], p[i+1])))
        self.cur_item.add(LTCurve(gstate.linewidth, pts, stroke, fill, evenodd,
                                  gstate.scolor, gstate.ncolor))
        return

    def render_char(self, matrix, font, fontsize, scaling, rise, cid, ncs,
                    graphicstate):
        try:
            text = font.to_unichr(cid)
            assert isinstance(text, str), str(type(text))
        except PDFUnicodeNotDefined:
            text = self.handle_undefined_char(font, cid)
        textwidth = font.char_width(cid)
        textdisp = font.char_disp(cid)
        item = LTChar(matrix, font, fontsize, scaling, rise, text, textwidth,
                      textdisp, ncs, graphicstate)
        self.cur_item.add(item)
        return item.adv

    def handle_undefined_char(self, font, cid):
        import codecs

        def slashescape(err):
            """ codecs error handler. err is UnicodeDecode instance. return
            a tuple with a replacement for the unencodable part of the input
            and a position where encoding should continue"""
            # print err, dir(err), err.start, err.end, err.object[:err.start]
            thebyte = err.object[err.start:err.end]
            repl = u'\\x'+hex(ord(thebyte))[2:]
            return (repl, err.end)

        # codecs.register_error('slashescape', slashescape)
        log.info('undefined: %r, %r', font, cid)
        # cid = hangul.join_jamos(j2hcj(h2j(cid)))
        # print(font.basefont)
        # print(font.basefont.decode('utf-8', 'slashescape'))
        return '(cid:%d)' % cid

    def receive_layout(self, ltpage):
        return


class PDFConverter(PDFLayoutAnalyzer):
    def __init__(self, rsrcmgr, outfp, codec='utf-8', pageno=1,
                 laparams=None):
        PDFLayoutAnalyzer.__init__(self, rsrcmgr, pageno=pageno,
                                   laparams=laparams)
        self.outfp = outfp
        self.codec = codec
        if hasattr(self.outfp, 'mode'):
            if 'b' in self.outfp.mode:
                self.outfp_binary = True
            else:
                self.outfp_binary = False
        else:
            import io
            if isinstance(self.outfp, io.BytesIO):
                self.outfp_binary = True
            elif isinstance(self.outfp, io.StringIO):
                self.outfp_binary = False
            else:
                try:
                    self.outfp.write("é")
                    self.outfp_binary = False
                except TypeError:
                    self.outfp_binary = True
        return


class FinanceConverter(PDFConverter):

    CONTROL = re.compile('[\x00-\x08\x0b-\x0c\x0e-\x1f]')

    def __init__(self, rsrcmgr, outfp, codec='utf-8', pageno=1, laparams=None,
                 imagewriter=None, stripcontrol=False):
        PDFConverter.__init__(self, rsrcmgr, outfp, codec=codec, pageno=pageno,
                              laparams=laparams)
        self.imagewriter = imagewriter
        self.stripcontrol = stripcontrol
        self.write_header()
        self.count = 0
        self.space_check = []
        self.need_space = False
        self.need_enter = False
        self.large_char = 30
        self.small_char = 9
        self.test = []
        return

    def is_all_continous_spaces(self, li):
        space_count = 0
        enter_count = 0
        for el in li:
            if not el.strip():
                space_count += 1
            if el == '\n':
                enter_count += 1
        if space_count == 3 or enter_count == 3:
            return True
        else:
            return False

    def write(self, text):
        if self.codec:
            text = text.encode(self.codec)
        self.outfp.write(text.decode('UTF-8'))
        return

    def write_header(self):
        if self.codec:
            pass
            # self.write('<?xml version="1.0" encoding="%s" ?>\n' % self.codec)
        # else:
        #     self.write('<?xml version="1.0" ?>\n')
        # self.write('==pages====\n')
        return

    def write_footer(self):
        # self.write('==pages====\n')
        return

    def write_text(self, text):
        if self.stripcontrol:
            text = self.CONTROL.sub('', text)
        self.write(enc(text))
        return

    def receive_layout(self, ltpage):
        def show_group(item):
            if isinstance(item, LTTextBox):
                # self.write(item)
                # self.write('<textbox id="%d" bbox="%s" />\n' %
                #            (item.index, bbox2str(item.bbox)))
                pass
            elif isinstance(item, LTTextGroup):
                # self.write(item)
                # self.write('<textgroup bbox="%s">\n' % bbox2str(item.bbox))
                # self.write('textgroup\n')
                for child in item:
                    show_group(child)
                # self.write('</textgroup>\n')
            return

        def render(item, box_id=None):
            # if not isinstance(item, LTPage):
            #     pass
            self.test.append(item)
            if isinstance(item, LTPage):
                # s = '<page id="%s" bbox="%s" rotate="%d">\n' % \
                #     (item.pageid, bbox2str(item.bbox), item.rotate)
                self.write(f'==page_id={item.pageid}==== \n')
                for child in item:
                    render(child)
                if item.groups is not None:
                    # self.write('<layout>\n')
                    for group in item.groups:
                        show_group(group)
                    # self.write('</layout>\n')
                # self.write('</page>\n')
            elif isinstance(item, LTLine):
                s = '<line linewidth="%d" bbox="%s" />\n' % \
                    (item.linewidth, bbox2str(item.bbox))
                # self.write(s)
            elif isinstance(item, LTRect):
                s = '<rect linewidth="%d" bbox="%s" />\n' % \
                    (item.linewidth, bbox2str(item.bbox))
                # self.write(s)
            elif isinstance(item, LTCurve):
                s = '<curve linewidth="%d" bbox="%s" pts="%s"/>\n' % \
                    (item.linewidth, bbox2str(item.bbox), item.get_pts())
                # self.write(s)
            elif isinstance(item, LTFigure):
                s = '<figure name="%s" bbox="%s">\n' % \
                    (item.name, bbox2str(item.bbox))
                # self.write(s)
                for child in item:
                    render(child)
                # self.write('</figure>\n')

            # 문장
            elif isinstance(item, LTTextLine):
                large_char = 0
                count_char = 0
                for child in item:
                    if isinstance(child, LTChar) and child.size > self.large_char:
                        large_char += 1

                if isinstance(item, LTTextLineHorizontal):
                    # print(item)

                    # if large_char > 1 and box_id:
                    #     self.write('==' + 'id=' + box_id + '=' * large_char * 2 + '\n')
                    if large_char > 1:
                        self.write('||Title||  ')

                    for child in item:
                        if (hasattr(child, 'size') and child.size < self.small_char):
                            pass
                        else:
                            render(child)

                    # if large_char > 1:
                    #     self.write('\n' + '=' * large_char * 2 + '=======' '\n')
                    #     self.need_enter = False

                    if self.need_enter:
                        self.write('\n')
                        self.need_enter = False

            # 문단 (글자 박스)
            elif isinstance(item, LTTextBox):
                count = 0
                grand_count = 0
                small_child_count = 0
                small_grand_count = 0

                for child in item:

                    if child.get_text().strip() is not '' and child.get_text().strip() is not '\n':
                        count += 1

                    if (hasattr(child, 'size') and child.size > self.large_char):
                        large_char = True

                    if (hasattr(child, 'size') and child.size > self.small_char):
                        small_child_count += 1

                    for grand in child:
                        if grand.get_text().strip() is not '' and grand.get_text().strip() is not '\n':
                            grand_count += 1

                        if (hasattr(grand, 'size') and grand.size > self.large_char):
                            large_char = True

                        if (hasattr(grand, 'size') and grand.size > self.small_char):
                            small_grand_count += 1

                # 버티컬 글자 박스
                # print(item)
                if isinstance(item, LTTextBoxVertical):
                    if grand_count > 0:
                        if count > 0 and (small_child_count > 0 or small_grand_count > 0):
                            self.write(
                                '--start--------------------------------------------------\n')

                        for child in item:
                            render(child)

                        if count > 0 and (small_child_count > 0 or small_grand_count > 0):
                            self.write(
                                '--end----------------------------------------------------\n')

                        large_char = False

                if isinstance(item, LTTextBoxHorizontal):
                    if grand_count > 0:
                        if count > 0 and (small_child_count > 0 or small_grand_count > 0):
                            self.write(
                                '--start--------------------------------------------------\n')

                        for child in item:
                            render(child)

                        if count > 0 and (small_child_count > 0 or small_grand_count > 0):
                            self.write(
                                '--end----------------------------------------------------\n')

                        large_char = False

            # 글자
            elif isinstance(item, LTChar):
                self.a = False
                if self.count < 3 or len(self.space_check) < 3:
                    self.space_check.append(item.get_text())
                else:
                    self.space_check.append(item.get_text())
                    self.space_check.pop(0)

                if self.count < 3 and (not item.get_text().strip() or item.get_text() == '\n'):
                    pass

                elif self.is_all_continous_spaces(self.space_check):
                    pass
                else:
                    if not item.get_text().strip() or item.get_text().strip() == '\n':
                        pass
                    else:
                        self.write_text(item.get_text())
                        self.need_space = True
                self.count += 1

            # 단어
            elif isinstance(item, LTText):
                if item.get_text().strip():
                    self.write_text(item.get_text())
                    print(item.get_text())
                elif self.need_space:
                    # 단어 띄어 쓰기
                    self.write(' ')
                    self.need_enter = True
                    self.need_space = False

            # 이미지
            elif isinstance(item, LTImage):
                if self.imagewriter is not None:
                    name = self.imagewriter.export_image(item)
                    # self.write('<image src="%s" width="%d" height="%d" />\n' %
                    #            (enc(name), item.width, item.height))
                # else:
                #     self.write('<image width="%d" height="%d" />\n' %
                #                (item.width, item.height))

            else:
                assert False, str(('Unhandled', item))
            return

            # 이미지

        render(ltpage)
        return

    def close(self):
        self.write_footer()
        return
