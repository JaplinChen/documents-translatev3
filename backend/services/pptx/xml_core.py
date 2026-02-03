from __future__ import annotations

import logging
import zipfile

import lxml.etree as ET

logger = logging.getLogger(__name__)


class PPTXThemeAnalyzer:
    """Extract theme colors/fonts from PPTX theme XML."""

    NS = {
        "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
        "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
        "r": (
            "http://schemas.openxmlformats.org/"
            "officeDocument/2006/relationships"
        ),
    }

    def __init__(self, pptx_path: str):
        self.pptx_path = pptx_path
        self.theme_data: dict[str, dict[str, str]] = {}

    def analyze(self) -> dict[str, dict[str, str]]:
        """Parse theme1.xml and return colors/fonts definitions."""
        with zipfile.ZipFile(self.pptx_path, "r") as archive:
            theme_xml_path = "ppt/theme/theme1.xml"
            if theme_xml_path not in archive.namelist():
                return self.theme_data
            theme_content = archive.read(theme_xml_path)
            self.theme_data["colors"] = self._extract_colors(theme_content)
            self.theme_data["fonts"] = self._extract_fonts(theme_content)
        return self.theme_data

    def _extract_colors(self, xml_content: bytes) -> dict[str, str]:
        """Extract colored elements (Accent, Text, Background)."""
        colors: dict[str, str] = {}
        root = ET.fromstring(xml_content)
        clr_scheme = root.find(".//a:clrScheme", self.NS)
        if clr_scheme is None:
            return colors

        for child in clr_scheme:
            name = child.tag.split("}")[-1]
            srgb = child.find(".//a:srgbClr", self.NS)
            if srgb is not None:
                colors[name] = srgb.get("val")
                continue

            sys_clr = child.find(".//a:sysClr", self.NS)
            if sys_clr is not None:
                colors[name] = sys_clr.get("lastClr") or "000000"
        return colors

    def _extract_fonts(self, xml_content: bytes) -> dict[str, str]:
        """Return major/minor font definitions from the theme."""
        fonts: dict[str, str] = {}
        root = ET.fromstring(xml_content)
        major = root.find(".//a:majorFont/a:latin", self.NS)
        if major is not None:
            fonts["major"] = major.get("typeface")

        minor = root.find(".//a:minorFont/a:latin", self.NS)
        if minor is not None:
            fonts["minor"] = minor.get("typeface")
        return fonts


def get_pptx_theme_summary(pptx_path: str) -> dict[str, dict[str, str]]:
    """Return theme summary (colors/fonts) for the provided PPTX."""
    try:
        return PPTXThemeAnalyzer(pptx_path).analyze()
    except Exception as err:
        logger.exception("Failed to analyze PPTX theme: %s", err)
        return {}
