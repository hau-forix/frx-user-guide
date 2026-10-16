"""Forix user-guide builder: raw OOXML on top of assets/forix-guide-template.docx.

The template carries the Forix look (A4 landscape, Montserrat everywhere, green #3C8A45,
grey header "<Product> · User guide · <Month Year>", "Page N" footer). Content is built with the
block helpers below and packed by `build()`.

Layout contract: one section = one page. `section()` starts with a page break, so a page that
overflows pushes every later page number off. `render_check.sh` catches that (page count must
equal len(sections) + 1 for the cover).

Text markup: `**bold**` inside any md string. Keep everything else plain.

Headings are real Word styles, so they show in Word's Navigation pane and the Google Docs outline,
and a Word TOC field could be built from them:
    Title / Subtitle  cover product name / "User Guide"
    Heading 1         page title            heading()
    Heading 2         green caps column label, cover subheading   label(), subheading()
    Heading 3         FAQ question          qa()
Eyebrows (BASICS, PAGES...) are plain paragraphs on purpose: they are categories, not headings.
"""
import os
import re
import shutil
import tempfile
import zipfile
from datetime import date
from xml.sax.saxutils import escape

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, '..', 'assets', 'forix-guide-template.docx')

GREEN, INK, GREY, RED = '3C8A45', '1B2420', '5A6761', 'E11D2A'
FONT = 'Montserrat'  # the whole document; ❶❷ captions keep Segoe UI Symbol (Montserrat has no such glyphs)
SP = '<w:spacing w:after="{a}" w:before="{b}" w:line="269" w:lineRule="auto"/>'
CIRCLED = '❶❷❸❹❺❻❼❽❾❿'

# Usable width of the landscape page in dxa (twips). Two-column layouts must sum to <= this.
FULL_W = 15309
# Common column splits (left, right): text-heavy left | screenshot right is the default.
SPLIT_DEFAULT = (6010, 9298)   # ~40 / 60: text left, screenshot right
SPLIT_HALF = (7371, 7938)      # cover page, FAQ, two text columns


# ------------------------------------------------------------------ runs and paragraphs
def font(name):
    return f'<w:rFonts w:ascii="{name}" w:hAnsi="{name}" w:eastAsia="{name}"/>'


def run(text, *, f=FONT, bold=False, color=INK, sz=20):
    b = '<w:b/>' if bold else '<w:b w:val="0"/>'
    return (f'<w:r><w:rPr>{font(f)}{b}<w:color w:val="{color}"/><w:sz w:val="{sz}"/></w:rPr>'
            f'<w:t xml:space="preserve">{escape(text)}</w:t></w:r>')


def runs(md, *, sz=20, color=INK, f=FONT):
    """`**bold**` markup -> runs."""
    out = []
    for i, part in enumerate(re.split(r'\*\*', md)):
        if part:
            out.append(run(part, f=f, bold=i % 2 == 1, color=color, sz=sz))
    return ''.join(out)


def para(inner, *, after=80, before=0, extra=''):
    style = ''.join(re.findall(r'<w:pStyle [^>]*/>', extra))
    rest = re.sub(r'<w:pStyle [^>]*/>', '', extra)
    return f'<w:p><w:pPr>{style}{SP.format(a=after, b=before)}{rest}</w:pPr>{inner}</w:p>'


def eyebrow(text, page_break=True):
    """Small green caps line above a page title (BASICS, PAGES, CLIENT PROFILE · 1 OF 6...)."""
    pb = '<w:pageBreakBefore/>' if page_break else '<w:pageBreakBefore w:val="0"/>'
    return f'<w:p><w:pPr>{pb}{SP.format(a=20, b=0)}</w:pPr>{run(text.upper(), bold=True, color=GREEN, sz=16)}</w:p>'


def heading(text, sz=36, after=120, color=INK):
    """Page title, style Heading 1."""
    return para(run(text, bold=True, color=color, sz=sz), after=after, extra='<w:pStyle w:val="Heading1"/>')


def subheading(text):
    """Bigger in-column title (e.g. 'Where the numbers come from' on the cover)."""
    r = run(text, bold=True, color=INK, sz=28).replace('<w:b/>', '<w:b/><w:caps w:val="0"/>', 1)  # Heading 2 is caps
    return para(r, after=80, extra='<w:pStyle w:val="Heading2"/>')


def p(md, sz=20):
    return para(runs(md, sz=sz))


def note(md):
    """Grey small print: permissions, edge cases, refresh times."""
    return para(runs(md, sz=19, color=GREY))


def label(text):
    """Green caps mini-heading inside a column (HOW TO USE, READ THE BADGES...)."""
    return para(run(text.upper(), bold=True, color=GREEN, sz=17), after=40, before=120, extra='<w:pStyle w:val="Heading2"/>')


def bullet(md):
    return para(runs(md), after=40, extra='<w:pStyle w:val="ListBullet"/>')


def numbered(n, md):
    return para(run(f'{n}.   ') + runs(md), after=40, extra='<w:ind w:left="312" w:hanging="255"/>')


def qa(q, a):
    return (para(runs(q, sz=20), after=20, before=100, extra='<w:pStyle w:val="Heading3"/>').replace('<w:b w:val="0"/>', '<w:b/>')
            + p(a, sz=19))


def cap(n, md):
    """Caption line for screenshot marker n (red ❶❷❸ matching annotate.py's numbered circles)."""
    return para(run(CIRCLED[n - 1] + '   ', f='Segoe UI Symbol', color=RED, sz=22).replace('<w:b w:val="0"/>', '')
                + runs(md, sz=19), after=40, extra='<w:ind w:left="340" w:hanging="340"/>')


_TINY = para('', after=0).replace('w:line="269" w:lineRule="auto"', 'w:line="40" w:lineRule="exact"')
SPACER = '<w:p/>' + _TINY


def _cell(blocks):
    """A cell must end with a paragraph. A full-height spacer line at the very bottom of a full page spills
    onto a blank next page, so the last block's SPACER shrinks to the 2pt paragraph."""
    x = ''.join(blocks)
    if x.endswith(SPACER):
        x = x[:-len(SPACER)] + _TINY
    return x or '<w:p/>'


# ------------------------------------------------------------------ tables
def _tbl_pr(width, borders, mar):
    return (f'<w:tblPr><w:tblW w:type="dxa" w:w="{width}"/><w:tblBorders>{borders}</w:tblBorders>'
            f'<w:tblLayout w:type="fixed"/><w:tblCellMar>{mar}</w:tblCellMar><w:tblLook w:firstColumn="1" w:firstRow="1" '
            'w:lastColumn="0" w:lastRow="0" w:noHBand="0" w:noVBand="1" w:val="04A0"/></w:tblPr>')


def _mar(t, l, b, r):
    return (f'<w:top w:w="{t}" w:type="dxa"/><w:left w:w="{l}" w:type="dxa"/>'
            f'<w:bottom w:w="{b}" w:type="dxa"/><w:right w:w="{r}" w:type="dxa"/>')


def _grid(widths):
    return '<w:tblGrid>' + ''.join(f'<w:gridCol w:w="{w}"/>' for w in widths) + '</w:tblGrid>'


def data_table(headers, rows, widths):
    """Ruled table: dark top rule, pale green header row, hairlines. First column is bolded.
    `widths` in dxa must sum to <= the column it sits in (minus ~200 for padding)."""
    borders = ('<w:top w:val="single" w:sz="10" w:color="1B2420" w:space="0"/><w:left w:val="nil"/>'
               '<w:bottom w:val="single" w:sz="4" w:color="DFE6E1" w:space="0"/><w:right w:val="nil"/>'
               '<w:insideH w:val="single" w:sz="4" w:color="DFE6E1" w:space="0"/><w:insideV w:val="nil"/>')
    x = '<w:tbl>' + _tbl_pr(sum(widths), borders, _mar(39, 68, 39, 68)) + _grid(widths)
    x += '<w:tr><w:trPr><w:tblHeader/></w:trPr>' + ''.join(
        f'<w:tc><w:tcPr><w:tcW w:type="dxa" w:w="{w}"/><w:shd w:val="clear" w:color="auto" w:fill="F3F7F4"/></w:tcPr>'
        + para(run(h.upper(), bold=True, color=GREY, sz=15), after=0) + '</w:tc>'
        for h, w in zip(headers, widths)) + '</w:tr>'
    for row in rows:
        x += '<w:tr><w:trPr><w:cantSplit/></w:trPr>'
        for i, (cell, w) in enumerate(zip(row, widths)):
            md = f'**{cell}**' if i == 0 and '**' not in cell else cell
            x += f'<w:tc><w:tcPr><w:tcW w:type="dxa" w:w="{w}"/></w:tcPr>' + para(runs(md, sz=18), after=0) + '</w:tc>'
        x += '</w:tr>'
    return x + '</w:tbl>' + SPACER


def callout(md, width=5840):
    """Pale green box with a green left bar: the one thing the reader must not miss."""
    borders = ('<w:top w:val="nil"/><w:left w:val="single" w:sz="18" w:color="3C8A45" w:space="0"/>'
               '<w:bottom w:val="nil"/><w:right w:val="nil"/><w:insideH w:val="nil"/><w:insideV w:val="nil"/>')
    return ('<w:tbl>' + _tbl_pr(width, borders, _mar(68, 141, 68, 113)) + _grid([width]) +
            f'<w:tr><w:tc><w:tcPr><w:tcW w:type="dxa" w:w="{width}"/><w:shd w:val="clear" w:color="auto" w:fill="EEF5EF"/></w:tcPr>'
            + para(runs(md, sz=19), after=0) + '</w:tc></w:tr></w:tbl>' + SPACER)


def layout(left, right, lw=SPLIT_DEFAULT[0], rw=SPLIT_DEFAULT[1]):
    """Borderless 2-column table. left/right are lists of block XML strings."""
    borders = ('<w:top w:val="nil"/><w:left w:val="nil"/><w:bottom w:val="nil"/><w:right w:val="nil"/>'
               '<w:insideH w:val="nil"/><w:insideV w:val="nil"/>')
    return ('<w:tbl>' + _tbl_pr(lw + rw, borders, _mar(0, 0, 0, 141)).replace('<w:tblBorders>', '<w:jc w:val="left"/><w:tblBorders>', 1)
            + _grid([lw, rw]) + '<w:tr>'
            f'<w:tc><w:tcPr><w:tcW w:type="dxa" w:w="{lw}"/><w:vAlign w:val="top"/></w:tcPr>{_cell(left)}</w:tc>'
            f'<w:tc><w:tcPr><w:tcW w:type="dxa" w:w="{rw}"/>'
            f'<w:tcMar><w:left w:w="340" w:type="dxa"/></w:tcMar><w:vAlign w:val="top"/></w:tcPr>{_cell(right)}</w:tc>'
            '</w:tr></w:tbl>')


# ------------------------------------------------------------------ the document
class Guide:
    """Collects pages, numbers them, packs the .docx.

        g = Guide('Clients Dashboard', img_dir='final')
        g.page('BASICS', 'Getting in', left=[...], right=[g.image('01.png'), cap(1, '...')])
        g.cover(intro_left=[...], right=[...])   # call last or first; cover is always page 1
        g.build('out/Clients-Dashboard-User-Guide.docx')

    Cross-references: g.pg('Getting in') -> page number (int), valid once every page is declared.
    Declare pages first (g.plan([...titles])) if earlier pages need to reference later ones.
    """

    def __init__(self, product, img_dir, *, date_label=None, template=TEMPLATE):
        self.product = product
        self.img_dir = img_dir
        self.date_label = date_label or date.today().strftime('%B %Y')
        self.template = template
        self.pages = []        # (toc label, xml)
        self.titles = []       # planned TOC labels in order (for page numbers / TOC)
        self.cover_xml = None
        self.images = []       # (rid, filename)

    # page numbers: cover is page 1, then one page per section in plan order
    def plan(self, titles):
        self.titles = list(titles)

    def pg(self, title):
        if title not in self.titles:
            raise KeyError(f'{title!r} not in plan(); planned: {self.titles}')
        return self.titles.index(title) + 2

    def toc_rows(self):
        return [[t, str(self.pg(t))] for t in self.titles]

    def image(self, fname, max_cx=5688000, max_cy=3500000):
        """Inline PNG from img_dir, fitted inside max_cx x max_cy EMU (default fits the 60% column)."""
        w, h = Image.open(os.path.join(self.img_dir, fname)).size
        cx = min(max_cx, int(max_cy * w / h))
        cy = int(cx * h / w)
        n = len(self.images) + 1
        rid = f'rId{100 + n}'
        self.images.append((rid, fname))
        return para(
            '<w:r><w:drawing><wp:inline xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
            'xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture">'
            f'<wp:extent cx="{cx}" cy="{cy}"/><wp:docPr id="{n}" name="Picture {n}"/>'
            '<wp:cNvGraphicFramePr><a:graphicFrameLocks noChangeAspect="1"/></wp:cNvGraphicFramePr>'
            '<a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture"><pic:pic>'
            f'<pic:nvPicPr><pic:cNvPr id="0" name="{escape(fname)}"/><pic:cNvPicPr/></pic:nvPicPr>'
            f'<pic:blipFill><a:blip r:embed="{rid}"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>'
            f'<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm><a:prstGeom prst="rect"/></pic:spPr>'
            '</pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing></w:r>', after=80)

    def page(self, eyebrow_text, title, left, right, *, toc=None, lw=SPLIT_DEFAULT[0], rw=SPLIT_DEFAULT[1]):
        """One landscape page: eyebrow, title, 2 columns. `toc` = its label in plan()/TOC when it differs
        from the title (e.g. title 'Overview', toc 'Client profile: overview')."""
        key = toc or title
        if self.titles and key not in self.titles:
            raise KeyError(f'page {key!r} missing from plan()')
        self.pages.append((key, eyebrow(eyebrow_text) + heading(title) + layout(left, right, lw=lw, rw=rw)))

    def cover(self, left, right, *, subtitle='User Guide', lw=SPLIT_HALF[0], rw=SPLIT_HALF[1]):
        """Page 1: eyebrow (product caps), big 2-line title, then a 2-column intro.
        Put `data_table(['Section', 'Page'], g.toc_rows(), [5670, 1134])` in `left` for the TOC."""
        self.cover_xml = (eyebrow(self.product, page_break=False)
                          + para(run(self.product, bold=True, color=INK, sz=60), after=0, extra='<w:pStyle w:val="Title"/>')
                          + para(run(subtitle, bold=True, color=GREEN, sz=60), after=160, extra='<w:pStyle w:val="Subtitle"/>')
                          + layout(left, right, lw=lw, rw=rw))

    def build(self, out):
        assert self.cover_xml, 'call cover() before build()'
        if self.titles:
            got = [t for t, _ in self.pages]
            assert got == self.titles, f'page order {got} != plan {self.titles}'
        body = self.cover_xml + ''.join(x for _, x in self.pages)
        work = tempfile.mkdtemp(prefix='frxguide-')
        try:
            with zipfile.ZipFile(self.template) as z:
                z.extractall(work)
            os.makedirs(f'{work}/word/media', exist_ok=True)

            doc = open(f'{work}/word/document.xml', encoding='utf-8').read()
            head = doc[:doc.index('<w:body>') + len('<w:body>')]
            sect = re.search(r'<w:sectPr\b.*?</w:sectPr>', doc, re.S).group(0)
            open(f'{work}/word/document.xml', 'w', encoding='utf-8').write(head + body + sect + '</w:body></w:document>')

            rels = open(f'{work}/word/_rels/document.xml.rels', encoding='utf-8').read()
            new = ''
            for i, (rid, fname) in enumerate(self.images, 1):
                shutil.copy(os.path.join(self.img_dir, fname), f'{work}/word/media/image{i}.png')
                new += (f'<Relationship Id="{rid}" Type="http://schemas.openxmlformats.org/officeDocument/2006/'
                        f'relationships/image" Target="media/image{i}.png"/>')
            open(f'{work}/word/_rels/document.xml.rels', 'w', encoding='utf-8').write(rels.replace('</Relationships>', new + '</Relationships>'))

            for part, subs in {
                'word/header1.xml': {'__PRODUCT__': escape(self.product), '__DATE__': escape(self.date_label)},
                'docProps/core.xml': {'__TITLE__': escape(f'{self.product} User Guide'),
                                      '__ISODATE__': date.today().isoformat() + 'T00:00:00Z'},
            }.items():
                s = open(f'{work}/{part}', encoding='utf-8').read()
                for k, v in subs.items():
                    s = s.replace(k, v)
                open(f'{work}/{part}', 'w', encoding='utf-8').write(s)

            os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
            tmp_out = out + '.tmp'
            with zipfile.ZipFile(tmp_out, 'w', zipfile.ZIP_DEFLATED) as z:
                ct = '[Content_Types].xml'
                z.write(f'{work}/{ct}', ct)  # must be the first entry
                for root, _, files in os.walk(work):
                    for f in sorted(files):
                        full = os.path.join(root, f)
                        arc = os.path.relpath(full, work)
                        if arc != ct:
                            z.write(full, arc)
            os.replace(tmp_out, out)
        finally:
            shutil.rmtree(work, ignore_errors=True)
        print(f'wrote {out}: cover + {len(self.pages)} pages, {len(self.images)} images')
        return out


# ------------------------------------------------------------------ editing an existing guide
# For adding/changing a few things in a guide that is already shipped (keep the user's manual
# edits in Word/Google Docs). Work on document.xml text; anchor on visible strings that occur once.

def read_part(path, part='word/document.xml'):
    with zipfile.ZipFile(path) as z:
        return z.read(part).decode('utf-8')


def write_docx(src, dst, replacements):
    """Copy src -> dst, replacing parts given as {part_name: bytes|str}. New parts (media) are added."""
    with zipfile.ZipFile(src) as zin, zipfile.ZipFile(dst, 'w', zipfile.ZIP_DEFLATED) as zout:
        seen = set()
        for item in zin.infolist():
            data = replacements.get(item.filename, zin.read(item.filename))
            zout.writestr(item, data.encode('utf-8') if isinstance(data, str) else data)
            seen.add(item.filename)
        for name, data in replacements.items():
            if name not in seen:
                zout.writestr(name, data.encode('utf-8') if isinstance(data, str) else data)


def _find(doc, anchor, occurrence):
    """occurrence=None: anchor must be unique. occurrence=k: the k-th hit (0 = first, -1 = last).
    TOC labels appear twice (TOC row first, page title later), so TOC edits use occurrence=0."""
    hits = [m.start() for m in re.finditer(re.escape(anchor), doc)]
    if occurrence is None:
        assert len(hits) == 1, f'anchor not unique ({len(hits)}x): {anchor!r}; pass occurrence='
        return hits[0]
    assert hits, f'anchor not found: {anchor!r}'
    return hits[occurrence]


def end_of(doc, anchor, closing, occurrence=None):
    """Index just after the `closing` tag (e.g. '</w:p>', '</w:tr>') that follows the anchor."""
    return doc.index(closing, _find(doc, anchor, occurrence)) + len(closing)


def insert_after(doc, anchor, closing, xml, occurrence=None):
    j = end_of(doc, anchor, closing, occurrence)
    return doc[:j] + xml + doc[j:]


def start_of(doc, anchor, opening='<w:p>', occurrence=None):
    """Index of the `opening` tag containing the anchor. Insert a new page before a page's eyebrow:
    i = start_of(doc, '>PAGES<', occurrence=0) ... or anchor on the page title and step back one <w:p>."""
    return doc.rfind(opening, 0, _find(doc, anchor, occurrence))


def add_toc_row(doc, after_label, label, page):
    """Clone the TOC row `after_label` as a new row (label, page) right below it."""
    j = end_of(doc, f'>{after_label}<', '</w:tr>', occurrence=0)
    row = doc[doc.rfind('<w:tr>', 0, j):j]
    new = row.replace(f'>{after_label}<', f'>{escape(label)}<', 1)
    new = re.sub(r'(<w:t(?: [^>]*)?>)\d+(</w:t>)', rf'\g<1>{page}\g<2>', new)
    return doc[:j] + new + doc[j:]


def bump_page_numbers(doc, toc_anchor, by=1):
    """After inserting a page: add `by` to every bare page-number cell in the TOC table after toc_anchor.
    Also update 'page N' cross-references in body text by hand (grep for 'page ')."""
    i = end_of(doc, toc_anchor, '</w:tr>', occurrence=0)
    j = doc.index('</w:tbl>', i)
    seg = re.sub(r'(<w:t(?: [^>]*)?>)(\d+)(</w:t>)', lambda m: f'{m.group(1)}{int(m.group(2)) + by}{m.group(3)}', doc[i:j])
    return doc[:i] + seg + doc[j:]


# ------------------------------------------------------------------ restyle a pre-2026-10-16 guide
# Old guides (VNPM, Clients Dashboard) were Poppins headings + Arial body with direct formatting and no
# heading styles. Restyle keeps every word, image and layout; it only swaps fonts and tags headings.
LEGACY_HEADINGS = [  # (font, half-point size, colour) of a paragraph's first run -> style
    (('Poppins', '60', INK), 'Title'),
    (('Poppins', '60', GREEN), 'Subtitle'),
    (('Poppins', '36', INK), 'Heading1'),
    (('Poppins', '28', INK), 'Heading2'),    # in-column subheading; caps switched off below
    (('Poppins', '17', GREEN), 'Heading2'),  # green caps label
    (('Poppins', '20', INK), 'Heading3'),    # FAQ question
]
STYLE_PARTS = ['word/styles.xml', 'word/stylesWithEffects.xml', 'word/theme/theme1.xml', 'word/fontTable.xml']


def restyle_legacy(src, dst, template=TEMPLATE):
    """Old guide -> Montserrat everywhere + real heading styles. Returns {style: count}.
    Style parts come from the template; only safe when the old file's styles.xml is the stock one
    (check: no custom styles the user added in Word). Body text, tables, images are untouched."""
    with zipfile.ZipFile(template) as t:
        parts = {p: t.read(p) for p in STYLE_PARTS}
    with zipfile.ZipFile(src) as z:
        doc = z.read('word/document.xml').decode('utf-8')
        hf = {n: z.read(n).decode('utf-8') for n in z.namelist() if re.match(r'word/(header|footer)\d*\.xml$', n)}
    counts = {}

    def tag(m):
        p = m.group(0)
        if '<w:pStyle ' in p or '<w:pPr>' not in p:
            return p
        r = re.search(r'<w:r><w:rPr>(.*?)</w:rPr>', p)
        if not r:
            return p
        rpr = r.group(1)
        f = re.search(r'w:ascii="([^"]+)"', rpr)
        sz = re.search(r'<w:sz w:val="(\d+)"', rpr)
        col = re.search(r'<w:color w:val="(\w+)"', rpr)
        key = (f and f.group(1), sz and sz.group(1), col and col.group(1))
        for k, style in LEGACY_HEADINGS:
            if key == k:
                counts[style] = counts.get(style, 0) + 1
                p = p.replace('<w:pPr>', f'<w:pPr><w:pStyle w:val="{style}"/>', 1)
                if k[1] == '28':
                    p = p.replace('<w:b/>', '<w:b/><w:caps w:val="0"/>')
                return p
        return p

    doc = re.sub(r'<w:p\b[^>]*>.*?</w:p>', tag, doc, flags=re.S)
    # Old builds left an empty Normal paragraph after a nested table, ahead of the 2pt spacer: on the
    # cover it pushed the layout row onto a blank page 2, shifting every TOC page number by one.
    doc, n_blank = re.subn(r'</w:tbl><w:p/>(?=<w:p><w:pPr><w:spacing w:after="0" w:before="0" w:line="40"'
                           r' w:lineRule="exact"/></w:pPr></w:p></w:tc>)',
                           '</w:tbl>', doc, count=1)  # first cell-ending table = cover TOC; inner pages keep their spacing
    counts['removed_blank_paras'] = n_blank
    swap =lambda s: re.sub(r'w:(ascii|hAnsi|eastAsia|cs)="(Arial|Poppins)"', r'w:\1="Montserrat"', s)
    out = {'word/document.xml': swap(doc), **{n: swap(s) for n, s in hf.items()}, **parts}
    write_docx(src, dst, out)
    left = len(re.findall(r'"(Arial|Poppins)"', out['word/document.xml']))
    print(f'restyled {dst}: {counts}, Arial/Poppins left: {left}')
    return counts
