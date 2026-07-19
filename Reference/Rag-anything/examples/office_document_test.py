#!/usr/bin/env python3
"""
Office Document Parsing Test Script for RAG-Anything

This script demonstrates how to parse various Office document formats
using MinerU, including DOC, DOCX, PPT, PPTX, XLS, and XLSX files.

Requirements:
- LibreOffice installed on the system
- RAG-Anything package

Usage:
    python office_document_test.py --file path/to/office/document.docx
"""

import argparse
import asyncio
import sys
from pathlib import Path
from raganything import RAGAnything


def check_libreoffice_installation():
    """Check if LibreOffice is installed and available"""
    import subprocess

    for cmd in ["libreoffice", "soffice"]:
        try:
            result = subprocess.run(
                [cmd, "--version"], capture_output=True, check=True, timeout=10
            )
            print(f"✅ LibreOffice found: {result.stdout.decode().strip()}")
            return True
        except (
            subprocess.CalledProcessError,
            FileNotFoundError,
            subprocess.TimeoutExpired,
        ):
            continue

    print("❌ LibreOffice not found. Please install LibreOffice:")
    print("  - Windows: Download from https://www.libreoffice.org/download/download/")
    print("  - macOS: brew install --cask libreoffice")
    print("  - Ubuntu/Debian: sudo apt-get install libreoffice")
    print("  - CentOS/RHEL: sudo yum install libreoffice")
    return False


async def test_office_document_parsing(file_path: str):
    """Test Office document parsing with MinerU"""

    print(f"🧪 Testing Office document parsing: {file_path}")

    # Check if file exists and is a supported Office format
    file_path = Path(file_path)
    if not file_path.exists():
        print(f"❌ File does not exist: {file_path}")
        return False

    supported_extensions = {".doc", ".docx", ".ppt", ".pptx", ".xls", ".xlsx"}
    if file_path.suffix.lower() not in supported_extensions:
        print(f"❌ Unsupported file format: {file_path.suffix}")
        print(f"   Supported formats: {', '.join(supported_extensions)}")
        return False

    print(f"📄 File format: {file_path.suffix.upper()}")
    print(f"📏 File size: {file_path.stat().st_size / 1024:.1f} KB")

    # Initialize RAGAnything (only for parsing functionality)
    rag = RAGAnything()

    try:
        # Test document parsing with MinerU
        print("\n🔄 Testing document parsing with MinerU...")
        content_list, md_content = await rag.parse_document(
            file_path=str(file_path),
            output_dir="./test_output",
            parse_method="auto",
            display_stats=True,
        )

        print("✅ Parsing successful!")
        print(f"   📊 Content blocks: {len(content_list)}")
        print(f"   📝 Markdown length: {len(md_content)} characters")

        # Analyze content types
        content_types = {}
        for item in content_list:
            if isinstance(item, dict):
                content_type = item.get("type", "unknown")
                content_types[content_type] = content_types.get(content_type, 0) + 1

        if content_types:
            print("   📋 Content distribution:")
            for content_type, count in sorted(content_types.items()):
                print(f"      • {content_type}: {count}")

        # Display some parsed content preview
        if md_content.strip():
            print("\n📄 Parsed content preview (first 500 characters):")
            preview = md_content.strip()[:500]
            print(f"   {preview}{'...' if len(md_content) > 500 else ''}")

        # Display some structured content examples
        text_items = [
            item
            for item in content_list
            if isinstance(item, dict) and item.get("type") == "text"
        ]
        if text_items:
            print("\n📝 Sample text blocks:")
            for i, item in enumerate(text_items[:3], 1):
                text_content = item.get("text", "")
                if text_content.strip():
                    preview = text_content.strip()[:200]
                    print(
                        f"   {i}. {preview}{'...' if len(text_content) > 200 else ''}"
                    )

        # Check for images
        image_items = [
            item
            for item in content_list
            if isinstance(item, dict) and item.get("type") == "image"
        ]
        if image_items:
            print(f"\n🖼️  Found {len(image_items)} image(s):")
            for i, item in enumerate(image_items, 1):
                print(f"   {i}. Image path: {item.get('img_path', 'N/A')}")

        # Check for tables
        table_items = [
            item
            for item in content_list
            if isinstance(item, dict) and item.get("type") == "table"
        ]
        if table_items:
            print(f"\n📊 Found {len(table_items)} table(s):")
            for i, item in enumerate(table_items, 1):
                table_body = item.get("table_body", "")
                row_count = len(table_body.split("\n"))
                print(f"   {i}. Table with {row_count} rows")

        print("\n🎉 Office document parsing test completed successfully!")
        print("📁 Output files saved to: ./test_output")
        return True

    except Exception as e:
        print(f"\n❌ Office document parsing failed: {str(e)}")
        import traceback

        print(f"   Full error: {traceback.format_exc()}")
        return False


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="Test Office document parsing with MinerU"
    )
    parser.add_argument("--file", help="Path to the Office document to test")
    parser.add_argument(
        "--check-libreoffice",
        action="store_true",
        help="Only check LibreOffice installation",
    )

    args = parser.parse_args()

    # Check LibreOffice installation
    print("🔧 Checking LibreOffice installation...")
    if not check_libreoffice_installation():
        return 1

    if args.check_libreoffice:
        print("✅ LibreOffice installation check passed!")
        return 0

    # If not just checking dependencies, file argument is required
    if not args.file:
        print(
            "❌ Error: --file argument is required when not using --check-libreoffice"
        )
        parser.print_help()
        return 1

    # Run the parsing test
    try:
        success = asyncio.run(test_office_document_parsing(args.file))
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
