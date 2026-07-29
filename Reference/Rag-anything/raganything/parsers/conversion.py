"""Office document and text to PDF conversion utilities."""

import logging
import os
import re as _re
import shutil as _shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Union

_IS_WINDOWS = os.name == "nt"
logger = logging.getLogger(__name__)


def convert_office_to_pdf(doc_path: Union[str, Path], output_dir: Optional[str] = None) -> Path:
    """Convert Office document (.doc, .docx, .ppt, .pptx, .xls, .xlsx) to PDF.
    Requires LibreOffice to be installed.
    """
    try:
        doc_path_resolved = Path(doc_path)
        if not doc_path_resolved.exists():
            raise FileNotFoundError(f"Office document does not exist: {doc_path}")

        name_without_suff = doc_path_resolved.stem
        if output_dir:
            base_output_dir = Path(output_dir)
        else:
            base_output_dir = doc_path_resolved.parent / "libreoffice_output"
        base_output_dir.mkdir(parents=True, exist_ok=True)

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            logger.info(f"Converting {doc_path_resolved.name} to PDF using LibreOffice...")
            commands_to_try = ["libreoffice", "soffice"]
            conversion_successful = False
            last_cmd = commands_to_try[-1]

            for cmd in commands_to_try:
                is_last = cmd == last_cmd
                try:
                    convert_cmd = [
                        cmd, "--headless", "--convert-to", "pdf",
                        "--outdir", str(temp_path), str(doc_path_resolved),
                    ]
                    kwargs = {
                        "capture_output": True, "text": True,
                        "timeout": 60, "encoding": "utf-8", "errors": "ignore",
                    }
                    if _IS_WINDOWS:
                        kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
                    result = subprocess.run(convert_cmd, **kwargs)
                    if result.returncode == 0:
                        conversion_successful = True
                        logger.info(f"Successfully converted {doc_path_resolved.name} to PDF using {cmd}")
                        break
                    logger.warning(f"LibreOffice command '{cmd}' failed: {result.stderr}")
                except FileNotFoundError:
                    if is_last:
                        logger.warning(f"LibreOffice command '{cmd}' not found")
                    else:
                        logger.debug(f"LibreOffice command '{cmd}' not found, trying next candidate")
                except subprocess.TimeoutExpired:
                    logger.warning(f"LibreOffice command '{cmd}' timed out")
                except Exception as e:
                    logger.error(f"LibreOffice command '{cmd}' failed with exception: {e}")

            if not conversion_successful:
                raise RuntimeError(
                    f"LibreOffice conversion failed for {doc_path_resolved.name}. "
                    f"Please ensure LibreOffice is installed."
                )

            pdf_files = list(temp_path.glob("*.pdf"))
            if not pdf_files:
                raise RuntimeError(
                    f"PDF conversion failed for {doc_path_resolved.name} - no PDF file generated."
                )
            pdf_path = pdf_files[0]
            logger.info(f"Generated PDF: {pdf_path.name} ({pdf_path.stat().st_size} bytes)")

            if pdf_path.stat().st_size < 100:
                raise RuntimeError("Generated PDF appears to be empty or corrupted.")

            final_pdf_path = base_output_dir / f"{name_without_suff}.pdf"
            _shutil.copy2(pdf_path, final_pdf_path)
            return final_pdf_path

    except Exception as e:
        logger.error(f"Error in convert_office_to_pdf: {str(e)}")
        raise


def convert_text_to_pdf(text_path: Union[str, Path], output_dir: Optional[str] = None) -> Path:
    """Convert text file (.txt, .md) to PDF using ReportLab with full markdown support."""
    try:
        text_path_resolved = Path(text_path)
        if not text_path_resolved.exists():
            raise FileNotFoundError(f"Text file does not exist: {text_path}")

        supported_text_formats = {".txt", ".md"}
        if text_path_resolved.suffix.lower() not in supported_text_formats:
            raise ValueError(f"Unsupported text format: {text_path_resolved.suffix}")

        try:
            with open(text_path_resolved, "r", encoding="utf-8") as f:
                text_content = f.read()
        except UnicodeDecodeError:
            for encoding in ["gbk", "latin-1", "cp1252"]:
                try:
                    with open(text_path_resolved, "r", encoding=encoding) as f:
                        text_content = f.read()
                    logger.info(f"Successfully read file with {encoding} encoding")
                    break
                except UnicodeDecodeError:
                    continue
            else:
                raise RuntimeError(f"Could not decode text file {text_path_resolved.name}")

        if output_dir:
            base_output_dir = Path(output_dir)
        else:
            base_output_dir = text_path_resolved.parent / "reportlab_output"
        base_output_dir.mkdir(parents=True, exist_ok=True)
        pdf_path_resolved = base_output_dir / f"{text_path_resolved.stem}.pdf"
        logger.info(f"Converting {text_path_resolved.name} to PDF...")

        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont

            support_chinese = True
            try:
                if "WenQuanYi" not in pdfmetrics.getRegisteredFontNames():
                    if not Path("/usr/share/fonts/wqy-microhei/wqy-microhei.ttc").exists():
                        support_chinese = False
                        logger.warning(
                            "WenQuanYi font not found. Chinese characters may not render correctly."
                        )
                    else:
                        pdfmetrics.registerFont(
                            TTFont("WenQuanYi", "/usr/share/fonts/wqy-microhei/wqy-microhei.ttc")
                        )
            except Exception as e:
                support_chinese = False
                logger.warning(f"Failed to register WenQuanYi font: {e}")

            doc = SimpleDocTemplate(
                str(pdf_path_resolved), pagesize=A4,
                leftMargin=inch, rightMargin=inch, topMargin=inch, bottomMargin=inch,
            )
            styles = getSampleStyleSheet()
            normal_style = styles["Normal"]
            heading_style = styles["Heading1"]
            if support_chinese:
                normal_style.fontName = "WenQuanYi"
                heading_style.fontName = "WenQuanYi"

            try:
                from reportlab.pdfbase.cidfonts import UnicodeCIDFont
                pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
                if not support_chinese:
                    normal_style.fontName = "STSong-Light"
                    heading_style.fontName = "STSong-Light"
            except Exception:
                pass

            story = []
            if text_path_resolved.suffix.lower() == ".md":
                lines = text_content.split("\n")
                for line in lines:
                    line = line.strip()
                    if not line:
                        story.append(Spacer(1, 12))
                        continue
                    if line.startswith("#"):
                        level = len(line) - len(line.lstrip("#"))
                        header_text = line.lstrip("#").strip()
                        if header_text:
                            hs = ParagraphStyle(
                                name=f"Heading{level}",
                                parent=heading_style,
                                fontSize=max(16 - level, 10),
                                spaceAfter=8,
                            )
                            story.append(Paragraph(_process_inline_markdown(header_text), hs))
                    elif line.startswith("- ") or line.startswith("* "):
                        story.append(Paragraph(f"&bull; {_process_inline_markdown(line[2:])}", normal_style))
                    elif line.startswith("> "):
                        quote_style = ParagraphStyle("Quote", parent=normal_style, leftIndent=20, textColor="gray")
                        story.append(Paragraph(_process_inline_markdown(line[2:]), quote_style))
                    else:
                        safe_line = _process_inline_markdown(line)
                        story.append(Paragraph(safe_line, normal_style))
                        story.append(Spacer(1, 3))
            else:
                for line in text_content.split("\n"):
                    line = line.rstrip()
                    if not line.strip():
                        story.append(Spacer(1, 6))
                        continue
                    safe_line = (
                        line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                    )
                    story.append(Paragraph(safe_line, normal_style))
                    story.append(Spacer(1, 3))

            if not story:
                story.append(Paragraph("(Empty text file)", normal_style))
            doc.build(story)

            logger.info(
                f"Successfully converted {text_path_resolved.name} to PDF "
                f"({pdf_path_resolved.stat().st_size / 1024:.1f} KB)"
            )
        except ImportError:
            raise RuntimeError("reportlab is required for text-to-PDF conversion.")
        except Exception as e:
            raise RuntimeError(f"Failed to convert text file {text_path_resolved.name} to PDF: {e}")

        if not pdf_path_resolved.exists() or pdf_path_resolved.stat().st_size < 100:
            raise RuntimeError("PDF conversion failed - generated PDF is empty or corrupted.")
        return pdf_path_resolved

    except Exception as e:
        logger.error(f"Error in convert_text_to_pdf: {str(e)}")
        raise


def _process_inline_markdown(text: str) -> str:
    """Process inline markdown formatting (bold, italic, code, links)."""
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = _re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", text)
    text = _re.sub(r"__(.*?)__", r"<b>\1</b>", text)
    text = _re.sub(r"(?<!\w)\*([^*\n]+?)\*(?!\w)", r"<i>\1</i>", text)
    text = _re.sub(r"(?<!\w)_([^_\n]+?)_(?!\w)", r"<i>\1</i>", text)
    text = _re.sub(
        r"`([^`]+?)`",
        r'<font name="Courier" size="9" color="darkred">\1</font>',
        text,
    )

    def link_replacer(match):
        link_text = match.group(1)
        url = match.group(2)
        return f'<link href="{url}" color="blue"><u>{link_text}</u></link>'

    text = _re.sub(r"\[([^\]]+?)\]\(([^)]+?)\)", link_replacer, text)
    text = _re.sub(r"~~(.*?)~~", r"<strike>\1</strike>", text)
    return text
