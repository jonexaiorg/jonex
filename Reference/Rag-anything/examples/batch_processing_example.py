#!/usr/bin/env python
"""
Batch Processing Example for RAG-Anything

This example demonstrates how to use the batch processing capabilities
to process multiple documents in parallel for improved throughput.

Features demonstrated:
- Basic batch processing with BatchParser
- Asynchronous batch processing
- Integration with RAG-Anything
- Error handling and progress tracking
- File filtering and directory processing
"""

import asyncio
import logging
from pathlib import Path
import tempfile
import time

# Add project root directory to Python path
import sys

sys.path.append(str(Path(__file__).parent.parent))

from raganything import RAGAnything, RAGAnythingConfig
from raganything.batch_parser import BatchParser


def create_sample_documents():
    """Create sample documents for batch processing testing"""
    temp_dir = Path(tempfile.mkdtemp())
    sample_files = []

    # Create various document types
    documents = {
        "document1.txt": "This is a simple text document for testing batch processing.",
        "document2.txt": "Another text document with different content.",
        "document3.md": """# Markdown Document

## Introduction
This is a markdown document for testing.

### Features
- Markdown formatting
- Code blocks
- Lists

```python
def example():
    return "Hello from markdown"
```
""",
        "report.txt": """Business Report

Executive Summary:
This report demonstrates batch processing capabilities.

Key Findings:
1. Parallel processing improves throughput
2. Progress tracking enhances user experience
3. Error handling ensures reliability

Conclusion:
Batch processing is essential for large-scale document processing.
""",
        "notes.md": """# Meeting Notes

## Date: 2024-01-15

### Attendees
- Alice Johnson
- Bob Smith
- Carol Williams

### Discussion Topics
1. **Batch Processing Implementation**
   - Parallel document processing
   - Progress tracking
   - Error handling strategies

2. **Performance Metrics**
   - Target: 100 documents/hour
   - Memory usage: < 4GB
   - Success rate: > 95%

### Action Items
- [ ] Implement batch processing
- [ ] Add progress bars
- [ ] Test with large document sets
- [ ] Optimize memory usage

### Next Steps
Continue development and testing of batch processing features.
""",
    }

    # Create files
    for filename, content in documents.items():
        file_path = temp_dir / filename
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        sample_files.append(str(file_path))

    return sample_files, temp_dir


def demonstrate_basic_batch_processing():
    """Demonstrate basic batch processing functionality"""
    print("\n" + "=" * 60)
    print("BASIC BATCH PROCESSING DEMONSTRATION")
    print("=" * 60)

    # Create sample documents
    sample_files, temp_dir = create_sample_documents()

    try:
        print(f"Created {len(sample_files)} sample documents in: {temp_dir}")
        for file_path in sample_files:
            print(f"  - {Path(file_path).name}")

        # Create batch parser
        batch_parser = BatchParser(
            parser_type="mineru",
            max_workers=3,
            show_progress=True,
            timeout_per_file=60,
            skip_installation_check=True,  # Skip installation check for demo
        )

        print("\nBatch parser configured:")
        print("  - Parser type: mineru")
        print("  - Max workers: 3")
        print("  - Progress tracking: enabled")
        print("  - Timeout per file: 60 seconds")

        # Check supported extensions
        supported_extensions = batch_parser.get_supported_extensions()
        print(f"  - Supported extensions: {supported_extensions}")

        # Filter files to supported types
        supported_files = batch_parser.filter_supported_files(sample_files)
        print("\nFile filtering results:")
        print(f"  - Total files: {len(sample_files)}")
        print(f"  - Supported files: {len(supported_files)}")

        # Process batch
        output_dir = temp_dir / "batch_output"
        print("\nStarting batch processing...")
        print(f"Output directory: {output_dir}")

        start_time = time.time()
        result = batch_parser.process_batch(
            file_paths=supported_files,
            output_dir=str(output_dir),
            parse_method="auto",
            recursive=False,
        )
        processing_time = time.time() - start_time

        # Display results
        print("\n" + "-" * 40)
        print("BATCH PROCESSING RESULTS")
        print("-" * 40)
        print(result.summary())
        print(f"Total processing time: {processing_time:.2f} seconds")
        print(f"Success rate: {result.success_rate:.1f}%")

        if result.successful_files:
            print("\nSuccessfully processed files:")
            for file_path in result.successful_files:
                print(f"  ✅ {Path(file_path).name}")

        if result.failed_files:
            print("\nFailed files:")
            for file_path in result.failed_files:
                error = result.errors.get(file_path, "Unknown error")
                print(f"  ❌ {Path(file_path).name}: {error}")

        return result

    except Exception as e:
        print(f"❌ Batch processing demonstration failed: {str(e)}")
        return None


async def demonstrate_async_batch_processing():
    """Demonstrate asynchronous batch processing"""
    print("\n" + "=" * 60)
    print("ASYNCHRONOUS BATCH PROCESSING DEMONSTRATION")
    print("=" * 60)

    # Create sample documents
    sample_files, temp_dir = create_sample_documents()

    try:
        print(f"Processing {len(sample_files)} documents asynchronously...")

        # Create batch parser
        batch_parser = BatchParser(
            parser_type="mineru",
            max_workers=2,
            show_progress=True,
            skip_installation_check=True,
        )

        # Process batch asynchronously
        output_dir = temp_dir / "async_output"

        start_time = time.time()
        result = await batch_parser.process_batch_async(
            file_paths=sample_files,
            output_dir=str(output_dir),
            parse_method="auto",
            recursive=False,
        )
        processing_time = time.time() - start_time

        # Display results
        print("\n" + "-" * 40)
        print("ASYNC BATCH PROCESSING RESULTS")
        print("-" * 40)
        print(result.summary())
        print(f"Async processing time: {processing_time:.2f} seconds")
        print(f"Success rate: {result.success_rate:.1f}%")

        return result

    except Exception as e:
        print(f"❌ Async batch processing demonstration failed: {str(e)}")
        return None


async def demonstrate_rag_integration():
    """Demonstrate batch processing integration with RAG-Anything"""
    print("\n" + "=" * 60)
    print("RAG-ANYTHING BATCH INTEGRATION DEMONSTRATION")
    print("=" * 60)

    # Create sample documents
    sample_files, temp_dir = create_sample_documents()

    try:
        # Initialize RAG-Anything with temporary storage
        config = RAGAnythingConfig(
            working_dir=str(temp_dir / "rag_storage"),
            enable_image_processing=True,
            enable_table_processing=True,
            enable_equation_processing=True,
            max_concurrent_files=2,
        )

        rag = RAGAnything(config=config)

        print("RAG-Anything initialized with batch processing capabilities")

        # Show available batch methods
        batch_methods = [method for method in dir(rag) if "batch" in method.lower()]
        print(f"Available batch methods: {batch_methods}")

        # Demonstrate batch processing with RAG integration
        print(f"\nProcessing {len(sample_files)} documents with RAG integration...")

        # Use the RAG-integrated batch processing
        try:
            # Process documents in batch
            result = rag.process_documents_batch(
                file_paths=sample_files,
                output_dir=str(temp_dir / "rag_batch_output"),
                max_workers=2,
                show_progress=True,
            )

            print("\n" + "-" * 40)
            print("RAG BATCH PROCESSING RESULTS")
            print("-" * 40)
            print(result.summary())
            print(f"Success rate: {result.success_rate:.1f}%")

            # Demonstrate batch processing with full RAG integration
            print("\nProcessing documents with full RAG integration...")

            rag_result = await rag.process_documents_with_rag_batch(
                file_paths=sample_files[:2],  # Process subset for demo
                output_dir=str(temp_dir / "rag_full_output"),
                max_workers=1,
                show_progress=True,
            )

            print("\n" + "-" * 40)
            print("FULL RAG INTEGRATION RESULTS")
            print("-" * 40)
            print(f"Parse result: {rag_result['parse_result'].summary()}")
            print(
                f"RAG processing time: {rag_result['total_processing_time']:.2f} seconds"
            )
            print(
                f"Successfully processed with RAG: {rag_result['successful_rag_files']}"
            )
            print(f"Failed RAG processing: {rag_result['failed_rag_files']}")

            return rag_result

        except Exception as e:
            print(f"⚠️ RAG integration demo completed with limitations: {str(e)}")
            print(
                "Note: This is expected in environments without full API configuration"
            )
            return None

    except Exception as e:
        print(f"❌ RAG integration demonstration failed: {str(e)}")
        return None


def demonstrate_directory_processing():
    """Demonstrate processing entire directories"""
    print("\n" + "=" * 60)
    print("DIRECTORY PROCESSING DEMONSTRATION")
    print("=" * 60)

    # Create a directory structure with nested files
    temp_dir = Path(tempfile.mkdtemp())

    # Create main directory files
    main_files = {
        "overview.txt": "Main directory overview document",
        "readme.md": "# Project README\n\nThis is the main project documentation.",
    }

    # Create subdirectory
    sub_dir = temp_dir / "subdirectory"
    sub_dir.mkdir()

    sub_files = {
        "details.txt": "Detailed information in subdirectory",
        "notes.md": "# Notes\n\nAdditional notes and information.",
    }

    # Write all files
    all_files = []
    for filename, content in main_files.items():
        file_path = temp_dir / filename
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        all_files.append(str(file_path))

    for filename, content in sub_files.items():
        file_path = sub_dir / filename
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        all_files.append(str(file_path))

    try:
        print("Created directory structure:")
        print(f"  Main directory: {temp_dir}")
        print(f"  Files in main: {list(main_files.keys())}")
        print(f"  Subdirectory: {sub_dir}")
        print(f"  Files in sub: {list(sub_files.keys())}")

        # Create batch parser
        batch_parser = BatchParser(
            parser_type="mineru",
            max_workers=2,
            show_progress=True,
            skip_installation_check=True,
        )

        # Process entire directory recursively
        print("\nProcessing entire directory recursively...")

        result = batch_parser.process_batch(
            file_paths=[str(temp_dir)],  # Pass directory path
            output_dir=str(temp_dir / "directory_output"),
            parse_method="auto",
            recursive=True,  # Include subdirectories
        )

        print("\n" + "-" * 40)
        print("DIRECTORY PROCESSING RESULTS")
        print("-" * 40)
        print(result.summary())
        print(f"Total files found and processed: {result.total_files}")
        print(f"Success rate: {result.success_rate:.1f}%")

        if result.successful_files:
            print("\nSuccessfully processed:")
            for file_path in result.successful_files:
                relative_path = Path(file_path).relative_to(temp_dir)
                print(f"  ✅ {relative_path}")

        return result

    except Exception as e:
        print(f"❌ Directory processing demonstration failed: {str(e)}")
        return None


def demonstrate_error_handling():
    """Demonstrate error handling and recovery"""
    print("\n" + "=" * 60)
    print("ERROR HANDLING DEMONSTRATION")
    print("=" * 60)

    temp_dir = Path(tempfile.mkdtemp())

    # Create files with various issues
    files_with_issues = {
        "valid_file.txt": "This is a valid file that should process successfully.",
        "empty_file.txt": "",  # Empty file
        "large_file.txt": "x" * 1000000,  # Large file (1MB of 'x')
    }

    created_files = []
    for filename, content in files_with_issues.items():
        file_path = temp_dir / filename
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        created_files.append(str(file_path))

    # Add a non-existent file to the list
    created_files.append(str(temp_dir / "non_existent_file.txt"))

    try:
        print(f"Testing error handling with {len(created_files)} files:")
        for file_path in created_files:
            name = Path(file_path).name
            exists = Path(file_path).exists()
            size = Path(file_path).stat().st_size if exists else 0
            print(f"  - {name}: {'exists' if exists else 'missing'}, {size} bytes")

        # Create batch parser with short timeout for demonstration
        batch_parser = BatchParser(
            parser_type="mineru",
            max_workers=2,
            show_progress=True,
            timeout_per_file=30,  # Short timeout for demo
            skip_installation_check=True,
        )

        # Process files and handle errors
        result = batch_parser.process_batch(
            file_paths=created_files,
            output_dir=str(temp_dir / "error_test_output"),
            parse_method="auto",
        )

        print("\n" + "-" * 40)
        print("ERROR HANDLING RESULTS")
        print("-" * 40)
        print(result.summary())

        if result.successful_files:
            print("\nSuccessful files:")
            for file_path in result.successful_files:
                print(f"  ✅ {Path(file_path).name}")

        if result.failed_files:
            print("\nFailed files with error details:")
            for file_path in result.failed_files:
                error = result.errors.get(file_path, "Unknown error")
                print(f"  ❌ {Path(file_path).name}: {error}")

        # Demonstrate retry logic
        if result.failed_files:
            print(
                f"\nDemonstrating retry logic for {len(result.failed_files)} failed files..."
            )

            # Retry only the failed files
            retry_result = batch_parser.process_batch(
                file_paths=result.failed_files,
                output_dir=str(temp_dir / "retry_output"),
                parse_method="auto",
            )

            print(f"Retry results: {retry_result.summary()}")

        return result

    except Exception as e:
        print(f"❌ Error handling demonstration failed: {str(e)}")
        return None


async def main():
    """Main demonstration function"""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    print("RAG-Anything Batch Processing Demonstration")
    print("=" * 70)
    print("This example demonstrates various batch processing capabilities:")
    print("  - Basic batch processing with progress tracking")
    print("  - Asynchronous processing for improved performance")
    print("  - Integration with RAG-Anything pipeline")
    print("  - Directory processing with recursive file discovery")
    print("  - Comprehensive error handling and recovery")

    results = {}

    # Run demonstrations
    print("\n🚀 Starting demonstrations...")

    # Basic batch processing
    results["basic"] = demonstrate_basic_batch_processing()

    # Asynchronous processing
    results["async"] = await demonstrate_async_batch_processing()

    # RAG integration
    results["rag"] = await demonstrate_rag_integration()

    # Directory processing
    results["directory"] = demonstrate_directory_processing()

    # Error handling
    results["error_handling"] = demonstrate_error_handling()

    # Summary
    print("\n" + "=" * 70)
    print("DEMONSTRATION SUMMARY")
    print("=" * 70)

    for demo_name, result in results.items():
        if result:
            if hasattr(result, "success_rate"):
                print(
                    f"✅ {demo_name.upper()}: {result.success_rate:.1f}% success rate"
                )
            else:
                print(f"✅ {demo_name.upper()}: Completed successfully")
        else:
            print(f"❌ {demo_name.upper()}: Failed or had limitations")

    print("\n📊 Key Features Demonstrated:")
    print("  - Parallel document processing with configurable worker counts")
    print("  - Real-time progress tracking with tqdm progress bars")
    print("  - Comprehensive error handling and reporting")
    print("  - File filtering based on supported document types")
    print("  - Directory processing with recursive file discovery")
    print("  - Asynchronous processing for improved performance")
    print("  - Integration with RAG-Anything document pipeline")
    print("  - Retry logic for failed documents")
    print("  - Detailed processing statistics and timing")

    print("\n💡 Best Practices Highlighted:")
    print("  - Use appropriate worker counts for your system")
    print("  - Enable progress tracking for long-running operations")
    print("  - Handle errors gracefully with retry mechanisms")
    print("  - Filter files to supported types before processing")
    print("  - Set reasonable timeouts for document processing")
    print("  - Use skip_installation_check for environments with conflicts")


if __name__ == "__main__":
    asyncio.run(main())
