"""Docling document parser."""

import base64
import json
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from raganything.parsers.base import Parser

try:
    from docling.document_converter import DocumentConverter, PdfFormatOption
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import PdfPipelineOptions, TableFormerMode
except ImportError:
    DocumentConverter = None  # type: ignore[assignment]


class DoclingParser(Parser):
    """Docling document parsing utility class.

    Specialized in parsing Office documents and HTML files, converting the content
    into structured data and generating markdown and JSON output.

    Backed by the Docling Python API (`docling.document_converter.DocumentConverter`)
    to avoid subprocess overhead and re-initialization of Docling's deep-learning
    models on every call. A `DocumentConverter` instance is built lazily on first
    use and cached per pipeline-option combination so that subsequent parses
    against the same configuration reuse already-loaded models.
    """

    HTML_FORMATS = {".html", ".htm", ".xhtml"}

    def __init__(self) -> None:
        super().__init__()
        self._converter_cache: Dict[Tuple, Any] = {}
        self._converter_cache_lock = threading.Lock()

    def parse_pdf(
        self,
        pdf_path: Union[str, Path],
        output_dir: Optional[str] = None,
        method: str = "auto",
        lang: Optional[str] = None,
        **kwargs,
    ) -> List[Dict[str, Any]]:
        try:
            pdf_path = Path(pdf_path)
            if not pdf_path.exists():
                raise FileNotFoundError(f"PDF file does not exist: {pdf_path}")

            name_without_suff = pdf_path.stem
            if output_dir:
                base_output_dir = self._unique_output_dir(output_dir, pdf_path)
            else:
                base_output_dir = pdf_path.parent / "docling_output"
            base_output_dir.mkdir(parents=True, exist_ok=True)

            doc_dict = self._run_docling_python(
                input_path=pdf_path,
                output_dir=base_output_dir,
                file_stem=name_without_suff,
                **kwargs,
            )
            file_subdir = base_output_dir / name_without_suff / "docling"
            content_list = self.read_from_block_recursive(
                doc_dict["body"], "body", file_subdir, 0, "0", doc_dict
            )
            return content_list

        except Exception as e:
            self.logger.error(f"Error in parse_pdf: {str(e)}")
            raise

    def parse_document(
        self,
        file_path: Union[str, Path],
        method: str = "auto",
        output_dir: Optional[str] = None,
        lang: Optional[str] = None,
        **kwargs,
    ) -> List[Dict[str, Any]]:
        downloaded_temp_file = None

        try:
            if self._is_url(file_path):
                file_path = self._download_file(file_path)
                downloaded_temp_file = file_path

            file_path = Path(file_path)
            if not file_path.exists():
                raise FileNotFoundError(f"File does not exist: {file_path}")

            ext = file_path.suffix.lower()
            if ext == ".pdf":
                return self.parse_pdf(file_path, output_dir, method, lang, **kwargs)
            elif ext in self.OFFICE_FORMATS:
                return self.parse_office_doc(file_path, output_dir, lang, **kwargs)
            elif ext in self.HTML_FORMATS:
                return self.parse_html(file_path, output_dir, lang, **kwargs)
            else:
                raise ValueError(
                    f"Unsupported file format: {ext}. "
                    f"Docling only supports PDF files, Office formats ({', '.join(self.OFFICE_FORMATS)}) "
                    f"and HTML formats ({', '.join(self.HTML_FORMATS)})"
                )
        finally:
            if downloaded_temp_file and downloaded_temp_file.exists():
                try:
                    downloaded_temp_file.unlink()
                    self.logger.debug(f"Removed temporary file: {downloaded_temp_file}")
                except Exception as e:
                    self.logger.warning(
                        f"Failed to remove temporary file {downloaded_temp_file}: {e}"
                    )

    def _get_converter(self, **kwargs) -> Any:
        if DocumentConverter is None:
            raise RuntimeError(
                "Docling Python API is not available. Install it with: pip install docling"
            )

        table_mode = str(kwargs.get("table_mode", "fast")).lower()
        do_tables = bool(kwargs.get("tables", True))
        do_ocr = bool(kwargs.get("allow_ocr", True))
        artifacts_path = kwargs.get("artifacts_path")

        cache_key = (table_mode, do_tables, do_ocr, artifacts_path)
        cached = self._converter_cache.get(cache_key)
        if cached is not None:
            return cached

        pipeline_options = PdfPipelineOptions()
        if hasattr(pipeline_options, "do_ocr"):
            pipeline_options.do_ocr = do_ocr
        if hasattr(pipeline_options, "do_table_structure"):
            pipeline_options.do_table_structure = do_tables
        if hasattr(pipeline_options, "table_structure_options"):
            try:
                pipeline_options.table_structure_options.mode = (
                    TableFormerMode.ACCURATE
                    if table_mode == "accurate"
                    else TableFormerMode.FAST
                )
            except Exception as e:
                self.logger.debug(f"Could not set TableFormer mode '{table_mode}': {e}")
        if artifacts_path and hasattr(pipeline_options, "artifacts_path"):
            pipeline_options.artifacts_path = artifacts_path

        if hasattr(pipeline_options, "generate_picture_images"):
            pipeline_options.generate_picture_images = True
        if hasattr(pipeline_options, "images_scale"):
            pipeline_options.images_scale = 2.0

        with self._converter_cache_lock:
            cached = self._converter_cache.get(cache_key)
            if cached is not None:
                return cached
            converter = DocumentConverter(
                format_options={
                    InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options),
                }
            )
            self._converter_cache[cache_key] = converter
            return converter

    def _run_docling_python(
        self,
        input_path: Union[str, Path],
        output_dir: Union[str, Path],
        file_stem: str,
        **kwargs,
    ) -> Dict[str, Any]:
        file_output_dir = Path(output_dir) / file_stem / "docling"
        file_output_dir.mkdir(parents=True, exist_ok=True)

        custom_env = kwargs.pop("env", None)
        if custom_env is not None:
            if not isinstance(custom_env, dict):
                raise TypeError(
                    f"env must be a dictionary, got {type(custom_env).__name__}"
                )
            for k, v in custom_env.items():
                if not isinstance(k, str) or not isinstance(v, str):
                    raise TypeError("env keys and values must be strings")
            self.logger.debug(
                "DoclingParser: 'env' kwarg accepted for backward compatibility "
                "but ignored by the Python API path."
            )

        try:
            converter = self._get_converter(**kwargs)
        except RuntimeError:
            raise
        except ImportError as e:
            raise RuntimeError(
                "Docling Python API is not available. Install it with: "
                "pip install docling"
            ) from e

        try:
            result = converter.convert(str(input_path))
        except Exception as e:
            self.logger.error(f"Error running Docling Python API on {input_path}: {e}")
            raise

        doc = result.document
        try:
            doc_dict = doc.export_to_dict()
        except Exception as e:
            self.logger.error(f"Failed to export Docling document to dict: {e}")
            raise

        json_path = file_output_dir / f"{file_stem}.json"
        try:
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(doc_dict, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.warning(f"Could not write Docling JSON to {json_path}: {e}")

        md_path = file_output_dir / f"{file_stem}.md"
        try:
            with open(md_path, "w", encoding="utf-8") as f:
                f.write(doc.export_to_markdown())
        except Exception as e:
            self.logger.warning(f"Could not write Docling Markdown to {md_path}: {e}")

        self.logger.info(
            f"Docling Python API parse completed for {Path(input_path).name}"
        )
        return doc_dict

    def read_from_block_recursive(
        self,
        block,
        type: str,
        output_dir: Path,
        cnt: int,
        num: str,
        docling_content: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        content_list = []
        if not block.get("children"):
            cnt += 1
            content_list.append(self.read_from_block(block, type, output_dir, cnt, num))
        else:
            if type not in ["groups", "body"]:
                cnt += 1
                content_list.append(
                    self.read_from_block(block, type, output_dir, cnt, num)
                )
            members = block["children"]
            for member in members:
                cnt += 1
                member_tag = member["$ref"]
                ref_parts = member_tag.split("/")
                if len(ref_parts) < 3:
                    self.logger.warning(
                        f"Unexpected $ref format (expected #/<type>/<index>): {member_tag!r}"
                    )
                    continue
                member_type = ref_parts[1]
                member_num = ref_parts[2]
                try:
                    member_block = docling_content[member_type][int(member_num)]
                except (KeyError, ValueError, IndexError) as e:
                    self.logger.warning(f"Could not resolve $ref {member_tag!r}: {e}")
                    continue
                content_list.extend(
                    self.read_from_block_recursive(
                        member_block,
                        member_type,
                        output_dir,
                        cnt,
                        member_num,
                        docling_content,
                    )
                )
        return content_list

    def read_from_block(
        self, block, type: str, output_dir: Path, cnt: int, num: str
    ) -> Dict[str, Any]:
        if type == "texts":
            if block["label"] == "formula":
                return {
                    "type": "equation",
                    "img_path": "",
                    "text": block["orig"],
                    "text_format": "unknown",
                    "page_idx": cnt // 10,
                }
            else:
                return {
                    "type": "text",
                    "text": block["orig"],
                    "page_idx": cnt // 10,
                }
        elif type == "pictures":
            try:
                base64_uri = block["image"]["uri"]
                parts = base64_uri.split(",", 1)
                base64_str = parts[1] if len(parts) == 2 else parts[0]
                image_dir = output_dir / "images"
                image_dir.mkdir(parents=True, exist_ok=True)
                image_path = image_dir / f"image_{num}.png"
                with open(image_path, "wb") as f:
                    f.write(base64.b64decode(base64_str))
                return {
                    "type": "image",
                    "img_path": str(image_path.resolve()),
                    "image_caption": block.get("caption", ""),
                    "image_footnote": block.get("footnote", ""),
                    "page_idx": cnt // 10,
                }
            except Exception as e:
                self.logger.warning(f"Failed to process image {num}: {e}")
                return {
                    "type": "text",
                    "text": f"[Image processing failed: {block.get('caption', '')}]",
                    "page_idx": cnt // 10,
                }
        else:
            try:
                return {
                    "type": "table",
                    "img_path": "",
                    "table_caption": block.get("caption", ""),
                    "table_footnote": block.get("footnote", ""),
                    "table_body": block.get("data", []),
                    "page_idx": cnt // 10,
                }
            except Exception as e:
                self.logger.warning(f"Failed to process table {num}: {e}")
                return {
                    "type": "text",
                    "text": f"[Table processing failed: {block.get('caption', '')}]",
                    "page_idx": cnt // 10,
                }

    def parse_office_doc(
        self,
        doc_path: Union[str, Path],
        output_dir: Optional[str] = None,
        lang: Optional[str] = None,
        **kwargs,
    ) -> List[Dict[str, Any]]:
        try:
            doc_path = Path(doc_path)
            if not doc_path.exists():
                raise FileNotFoundError(f"Document file does not exist: {doc_path}")

            if doc_path.suffix.lower() not in self.OFFICE_FORMATS:
                raise ValueError(f"Unsupported office format: {doc_path.suffix}")

            name_without_suff = doc_path.stem
            if output_dir:
                base_output_dir = self._unique_output_dir(output_dir, doc_path)
            else:
                base_output_dir = doc_path.parent / "docling_output"
            base_output_dir.mkdir(parents=True, exist_ok=True)

            doc_dict = self._run_docling_python(
                input_path=doc_path,
                output_dir=base_output_dir,
                file_stem=name_without_suff,
                **kwargs,
            )
            file_subdir = base_output_dir / name_without_suff / "docling"
            content_list = self.read_from_block_recursive(
                doc_dict["body"], "body", file_subdir, 0, "0", doc_dict
            )
            return content_list

        except Exception as e:
            self.logger.error(f"Error in parse_office_doc: {str(e)}")
            raise

    def parse_html(
        self,
        html_path: Union[str, Path],
        output_dir: Optional[str] = None,
        lang: Optional[str] = None,
        **kwargs,
    ) -> List[Dict[str, Any]]:
        try:
            html_path = Path(html_path)
            if not html_path.exists():
                raise FileNotFoundError(f"HTML file does not exist: {html_path}")

            if html_path.suffix.lower() not in self.HTML_FORMATS:
                raise ValueError(f"Unsupported HTML format: {html_path.suffix}")

            name_without_suff = html_path.stem
            if output_dir:
                base_output_dir = self._unique_output_dir(output_dir, html_path)
            else:
                base_output_dir = html_path.parent / "docling_output"
            base_output_dir.mkdir(parents=True, exist_ok=True)

            doc_dict = self._run_docling_python(
                input_path=html_path,
                output_dir=base_output_dir,
                file_stem=name_without_suff,
                **kwargs,
            )
            file_subdir = base_output_dir / name_without_suff / "docling"
            content_list = self.read_from_block_recursive(
                doc_dict["body"], "body", file_subdir, 0, "0", doc_dict
            )
            return content_list

        except Exception as e:
            self.logger.error(f"Error in parse_html: {str(e)}")
            raise

    def check_installation(self) -> bool:
        try:
            if DocumentConverter is None:
                return False
            return True
        except ImportError:
            self.logger.debug(
                "Docling Python package is not installed. "
                "Install it with: pip install docling"
            )
            return False
