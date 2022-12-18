import re
from typing import List

import bs4
from bs4 import BeautifulSoup

from .finder import Finder

# Pre-defined elements and classes
HETI_NON_CONTIGUOUS_ELEMENTS = [
    "address", "article", "aside", "blockquote", "dd", "div", 
    "dl", "fieldset", "figcaption", "figure", "footer", "form", "h1", "h2", "h3", 
    "h4", "h5", "h6", "header", "hgroup", "hr", "main", "nav", "noscript", "ol", 
    "output", "p", "pre", "section", "ul", 
    "br", "li", "summary", "dt", "details", "rp", "rt", "rtc", 
    "script", "style", "img", "video", "audio", "canvas", "svg", "map", "object", 
    "input", "textarea", "select", "option", "optgroup", "button", 
    "table", "tbody", "thead", "th", "tr", "td", "caption", "col", "tfoot", "colgroup",
    "ins", "del", "s"
]
HETI_SKIPPED_ELEMENTS = [
    "br", "hr",
    "script", "style", "img", "video", "audio", "canvas", "svg", "map", "object",
    "input", "textarea", "select", "option", "optgroup", "button",
    "pre", "code", "heti-spacing", "heti-close"
]
HETI_SKIPPED_CLASS = [
    "heti-skip"
]

# RegEx
CJK = "\u2e80-\u2eff\u2f00-\u2fdf\u3040-\u309f\u30a0-\u30fa\u30fc-\u30ff\u3100-\u312f\u3200-\u32ff\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff"
A = "A-Za-z\u0080-\u00ff\u0370-\u03ff"
N = "0-9"
S = "`~!@#\\$%\\^&\\*\\(\\)-_=\\+\\[\\]{}\\\\\\|;:'\",<.>\\/\\?"
ANS = f"{A}{N}{S}"
REG_CJK_FULL = rf".*?(?<=[{CJK}])( *[{ANS}]+(?: +[{ANS}]+)* *)(?=[{CJK}])"
REG_CJK_START = rf".*?([{ANS}]+(?: +[{ANS}]+)* *)(?=[{CJK}])"
REG_CJK_END = rf".*?(?<=[{CJK}])( *[{ANS}]+(?: +[{ANS}]+)*)"
REG_BD_STOP = r"。．，、：；！‼？⁇"
REG_BD_SEP = r"·・‧"
REG_BD_OPEN = r"「『（《〈【〖〔［｛"
REG_BD_CLOSE = r"」』）》〉】〗〕］｝"
REG_BD_START = rf"{REG_BD_OPEN}{REG_BD_CLOSE}"
REG_BD_END = rf"{REG_BD_STOP}{REG_BD_OPEN}{REG_BD_CLOSE}"
REG_BD_HALF_OPEN = r"“‘"
REG_BD_HALF_CLOSE = r"”’"
REG_BD_HALF_START = rf"{REG_BD_HALF_OPEN}{REG_BD_HALF_CLOSE}"
REG_BD_HALF = rf".*?([{REG_BD_STOP}])(?=[{REG_BD_START}])|([{REG_BD_OPEN}])(?=[{REG_BD_OPEN}])|([{REG_BD_CLOSE}])(?=[{REG_BD_END}])"
REG_BD_QUARTER = rf".*?([{REG_BD_SEP}])(?=[{REG_BD_OPEN}])|([{REG_BD_CLOSE}])(?=[{REG_BD_SEP}])"
REG_BD_QUARTER_EXTRA = rf".*?([{REG_BD_STOP}])(?=[{REG_BD_HALF_START}])|([{REG_BD_HALF_OPEN}])(?=[{REG_BD_OPEN}])"

# compiled RegEx pattern
COMPILED_REG_CJK_FULL = re.compile(REG_CJK_FULL, re.U)
COMPILED_REG_CJK_START = re.compile(REG_CJK_START, re.U)
COMPILED_REG_CJK_END = re.compile(REG_CJK_END, re.U)
COMPILED_REG_BD_HALF = re.compile(REG_BD_HALF, re.U)
COMPILED_REG_BD_QUARTER = re.compile(REG_BD_QUARTER, re.U)
COMPILED_REG_BD_QUARTER_EXTRA = re.compile(REG_BD_QUARTER_EXTRA, re.U)

class Heti:
    def __init__(self, html: str, rootSelector: str, builder: str = "lxml"):
        self.soup = BeautifulSoup(html, builder)
        self.rootSelector = rootSelector
        
    def funcForceContext(self, node: bs4.element.Tag) -> bool:
        return node.name.lower() in HETI_NON_CONTIGUOUS_ELEMENTS
    
    def funcFilterElement(self, node: bs4.element.Tag) -> bool:
        if node.get("class"):
            for c in node["class"]:
                if c in HETI_SKIPPED_CLASS:
                    return False
        if node.name.lower() in HETI_SKIPPED_ELEMENTS:
            return False
        return True
    
    def spacingElements(self, elmList: List[bs4.element.Tag]) -> None:
        for root in elmList:
            self.spacingElement(root)
    
    def spacingElement(self, node: bs4.element.Tag, step: int) -> None:
        commonConfig = {
            "forceContext": self.funcForceContext,
            "filterElements": self.funcFilterElement,
        }
        
        def getWrapper(elementName, classList, text):
            r = self.soup.new_tag(elementName)
            r["class"] = classList
            r.string = text.strip()
            return r
        
        def spacingStart(text):
            s = self.soup.new_tag("span")
            s["class"] = "heti-spacing"
            s.string = " "
            r = self.soup.new_tag("span")
            r.string = text.strip()
            r.append(s)
            return r
        
        def spacingEnd(text):
            s = self.soup.new_tag("span")
            s["class"] = "heti-spacing"
            s.string = " "
            r = self.soup.new_tag("span")
            r.string = text.strip()
            r.insert(0, s)
            return r
        
        def spacingStartEnd(text):
            s1 = self.soup.new_tag("span")
            s1["class"] = "heti-spacing"
            s1.string = " "
            s2 = self.soup.new_tag("span")
            s2["class"] = "heti-spacing"
            s2.string = " "
            r = self.soup.new_tag("span")
            r["class"] = "heti-skip"
            r.string = text.strip()
            r.insert(0, s1)
            r.append(s2)
            return r
        
        # 西文左右包裹四分宽空格
        if step == 0:
            Finder(self.soup, node, {
                **commonConfig,
                "find": COMPILED_REG_CJK_FULL,
                "replace": lambda portion, _: spacingStartEnd(portion.text),
            })

        # 西文后附带四分宽空格
        if step == 1:
            Finder(self.soup, node, {
                **commonConfig,
                "find": COMPILED_REG_CJK_START,
                "replace": lambda portion, _: spacingStart(portion.text)
            })

        # 西文前附带四分宽空格
        if step == 2:
            Finder(self.soup, node, {
                **commonConfig,
                "find": COMPILED_REG_CJK_END,
                "replace": lambda portion, _: spacingEnd(portion.text)
            })

        # 挤压连续标点至半宽
        if step == 3:
            Finder(self.soup, node, {
                **commonConfig,
                "find": COMPILED_REG_BD_HALF,
                "replace": lambda portion, _: getWrapper("heti-adjacent", "heti-adjacent-half", portion.text),
            })

        # 从分隔符中挤压掉四分宽
        if step == 4:
            Finder(self.soup, node, {
                **commonConfig,
                "find": COMPILED_REG_BD_QUARTER,
                "replace": lambda portion, _: getWrapper("heti-adjacent", "heti-adjacent-quarter", portion.text),
            })

        # original comment: 使用弯引号的情况下，在停顿符号接弯引号（如「。“」）或弯引号接全角开引号（如“《」）时，间距缩进调整到四分之一
        if step == 5:
            Finder(self.soup, node, {
                **commonConfig,
                "find": COMPILED_REG_BD_QUARTER_EXTRA,
                "replace": lambda portion, _: getWrapper("heti-adjacent", "heti-adjacent-quarter", portion.text),
            })
    
    def spacing(self, n) -> str:
        rootList = self.soup.find_all(self.rootSelector)
        for root in rootList:
            self.spacingElement(root, n)
        return str(self.soup)

def heti(html: str, rootSelector: str) -> str:
    for i in range(6):
        _heti = Heti(html, rootSelector)
        html = _heti.spacing(i)
    return html
    

if __name__ == "__main__":
    with open("test.html", "r") as f:
        html = f.read()
    with open("out.html", "w") as f:
        f.write(heti(html, "article"))