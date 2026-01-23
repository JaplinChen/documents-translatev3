import zipfile
import lxml.etree as ET
from io import BytesIO
from typing import Dict, List, Optional

class PPTXThemeAnalyzer:
    """解析 PPTX 內部的 XML 以提取主題、字體與顏色。"""
    
    # XML Namespaces
    NS = {
        'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
        'p': 'http://schemas.openxmlformats.org/presentationml/2006/main',
        'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
    }

    def __init__(self, pptx_path: str):
        self.pptx_path = pptx_path
        self.theme_data: Dict = {}

    def analyze(self) -> Dict:
        """執行完整分析並回傳主題數據。"""
        with zipfile.ZipFile(self.pptx_path, 'r') as z:
            # 1. 取得主題 XML (通常是 theme1.xml)
            theme_xml_path = 'ppt/theme/theme1.xml'
            if theme_xml_path in z.namelist():
                theme_content = z.read(theme_xml_path)
                self.theme_data['colors'] = self._extract_colors(theme_content)
                self.theme_data['fonts'] = self._extract_fonts(theme_content)
            
        return self.theme_data

    def _extract_colors(self, xml_content: bytes) -> Dict[str, str]:
        """提取 Accent 1-6, Text 1-2, Background 1-2 的顏色。"""
        colors = {}
        root = ET.fromstring(xml_content)
        
        # 定位 clrScheme (Color Scheme)
        clr_scheme = root.find('.//a:clrScheme', self.NS)
        if clr_scheme is not None:
            # 遍歷色彩定義
            for child in clr_scheme:
                name = child.tag.split('}')[-1] # 去除 namespace 取得標籤名
                # 尋找 srgbClr (Hex 色彩)
                srgb = child.find('.//a:srgbClr', self.NS)
                if srgb is not None:
                    colors[name] = srgb.get('val')
                else:
                    # 有些是 sysClr (系統色彩，如黑色/白色)
                    sys_clr = child.find('.//a:sysClr', self.NS)
                    if sys_clr is not None:
                        colors[name] = sys_clr.get('lastClr') or "000000"
        return colors

    def _extract_fonts(self, xml_content: bytes) -> Dict[str, str]:
        """提取主題定義的字體 (Major/Minor)。"""
        fonts = {}
        root = ET.fromstring(xml_content)
        
        # Major Font (標題)
        major = root.find('.//a:majorFont/a:latin', self.NS)
        if major is not None:
            fonts['major'] = major.get('typeface')
            
        # Minor Font (本文)
        minor = root.find('.//a:minorFont/a:latin', self.NS)
        if minor is not None:
            fonts['minor'] = minor.get('typeface')
            
        return fonts

def get_pptx_theme_summary(pptx_path: str) -> Dict:
    """便捷函數，獲取簡報主題摘要。"""
    try:
        analyzer = PPTXThemeAnalyzer(pptx_path)
        return analyzer.analyze()
    except Exception as e:
        print(f"Error analyzing PPTX XML: {e}")
        return {}
