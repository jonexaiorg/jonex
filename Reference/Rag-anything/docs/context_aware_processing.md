# Context-Aware Multimodal Processing in RAGAnything

This document describes the context-aware multimodal processing feature in RAGAnything, which provides surrounding content information to LLMs when analyzing images, tables, equations, and other multimodal content for enhanced accuracy and relevance.

## Overview

The context-aware feature enables RAGAnything to automatically extract and provide surrounding text content as context when processing multimodal content. This leads to more accurate and contextually relevant analysis by giving AI models additional information about where the content appears in the document structure.

### Key Benefits

- **Enhanced Accuracy**: Context helps AI understand the purpose and meaning of multimodal content
- **Semantic Coherence**: Generated descriptions align with document context and terminology
- **Automated Integration**: Context extraction is automatically enabled during document processing
- **Flexible Configuration**: Multiple extraction modes and filtering options

## Key Features

### 1. Configuration Support
- **Integrated Configuration**: Complete context options in `RAGAnythingConfig`
- **Environment Variables**: Configure all context parameters via environment variables
- **Dynamic Updates**: Runtime configuration updates supported
- **Content Format Control**: Configurable content source format detection

### 2. Automated Integration
- **Auto-Initialization**: Modal processors automatically receive tokenizer and context configuration
- **Content Source Setup**: Document processing automatically sets content sources for context extraction
- **Position Information**: Automatic position info (page_idx, index) passed to processors
- **Batch Processing**: Context-aware batch processing for efficient document handling

### 3. Advanced Token Management
- **Accurate Token Counting**: Uses LightRAG's tokenizer for precise token calculation
- **Smart Boundary Preservation**: Truncates at sentence/paragraph boundaries
- **Backward Compatibility**: Fallback to character truncation when tokenizer unavailable

### 4. Universal Context Extraction
- **Multiple Formats**: Support for MinerU, plain text, custom formats
- **Flexible Modes**: Page-based and chunk-based context extraction
- **Content Filtering**: Configurable content type filtering
- **Header Support**: Optional inclusion of document headers and structure

## Configuration

### RAGAnythingConfig Parameters

```python
# Context Extraction Configuration
context_window: int = 1                    # Context window size (pages/chunks)
context_mode: str = "page"                 # Context mode ("page" or "chunk")
max_context_tokens: int = 2000             # Maximum context tokens
include_headers: bool = True               # Include document headers
include_captions: bool = True              # Include image/table captions
context_filter_content_types: List[str] = ["text"]  # Content types to include
content_format: str = "minerU"             # Default content format for context extraction
```

### Environment Variables

```bash
# Context extraction settings
CONTEXT_WINDOW=2
CONTEXT_MODE=page
MAX_CONTEXT_TOKENS=3000
INCLUDE_HEADERS=true
INCLUDE_CAPTIONS=true
CONTEXT_FILTER_CONTENT_TYPES=text,image
CONTENT_FORMAT=minerU
```

## Usage Guide

### 1. Basic Configuration

```python
from raganything import RAGAnything, RAGAnythingConfig

# Create configuration with context settings
config = RAGAnythingConfig(
    context_window=2,
    context_mode="page",
    max_context_tokens=3000,
    include_headers=True,
    include_captions=True,
    context_filter_content_types=["text", "image"],
    content_format="minerU"
)

# Create RAGAnything instance
rag_anything = RAGAnything(
    config=config,
    llm_model_func=your_llm_function,
    embedding_func=your_embedding_function
)
```

### 2. Automatic Document Processing

```python
# Context is automatically enabled during document processing
await rag_anything.process_document_complete("document.pdf")
```

### 3. Manual Content Source Configuration

```python
# Set content source for specific content lists
rag_anything.set_content_source_for_context(content_list, "minerU")

# Update context configuration at runtime
rag_anything.update_context_config(
    context_window=1,
    max_context_tokens=1500,
    include_captions=False
)
```

### 4. Direct Modal Processor Usage

```python
from raganything.modalprocessors import (
    ContextExtractor,
    ContextConfig,
    ImageModalProcessor
)

# Configure context extraction
config = ContextConfig(
    context_window=1,
    context_mode="page",
    max_context_tokens=2000,
    include_headers=True,
    include_captions=True,
    filter_content_types=["text"]
)

# Initialize context extractor
context_extractor = ContextExtractor(config)

# Initialize modal processor with context support
processor = ImageModalProcessor(lightrag, caption_func, context_extractor)

# Set content source
processor.set_content_source(content_list, "minerU")

# Process with context
item_info = {
    "page_idx": 2,
    "index": 5,
    "type": "image"
}

result = await processor.process_multimodal_content(
    modal_content=image_data,
    content_type="image",
    file_path="document.pdf",
    entity_name="Architecture Diagram",
    item_info=item_info
)
```

## Context Modes

### Page-Based Context (`context_mode="page"`)
- Extracts context based on page boundaries
- Uses `page_idx` field from content items
- Suitable for document-structured content
- Example: Include text from 2 pages before and after current image

### Chunk-Based Context (`context_mode="chunk"`)
- Extracts context based on content item positions
- Uses sequential position in content list
- Suitable for fine-grained control
- Example: Include 5 content items before and after current table

## Processing Workflow

### 1. Document Parsing
```
Document Input → MinerU Parsing → content_list Generation
```

### 2. Context Setup
```
content_list → Set as Context Source → All Modal Processors Gain Context Capability
```

### 3. Multimodal Processing
```
Multimodal Content → Extract Surrounding Context → Enhanced LLM Analysis → More Accurate Results
```

## Content Source Formats

### MinerU Format
```json
[
    {
        "type": "text",
        "text": "Document content here...",
        "text_level": 1,
        "page_idx": 0
    },
    {
        "type": "image",
        "img_path": "images/figure1.jpg",
        "image_caption": ["Figure 1: Architecture"],
        "image_footnote": [],
        "page_idx": 1
    }
]
```

### Custom Text Chunks
```python
text_chunks = [
    "First chunk of text content...",
    "Second chunk of text content...",
    "Third chunk of text content..."
]
```

### Plain Text
```python
full_document = "Complete document text with all content..."
```

## Configuration Examples

### High-Precision Context
For focused analysis with minimal context:
```python
config = RAGAnythingConfig(
    context_window=1,
    context_mode="page",
    max_context_tokens=1000,
    include_headers=True,
    include_captions=False,
    context_filter_content_types=["text"]
)
```

### Comprehensive Context
For broad analysis with rich context:
```python
config = RAGAnythingConfig(
    context_window=2,
    context_mode="page",
    max_context_tokens=3000,
    include_headers=True,
    include_captions=True,
    context_filter_content_types=["text", "image", "table"]
)
```

### Chunk-Based Analysis
For fine-grained sequential context:
```python
config = RAGAnythingConfig(
    context_window=5,
    context_mode="chunk",
    max_context_tokens=2000,
    include_headers=False,
    include_captions=False,
    context_filter_content_types=["text"]
)
```

## Performance Optimization

### 1. Accurate Token Control
- Uses real tokenizer for precise token counting
- Avoids exceeding LLM token limits
- Provides consistent performance

### 2. Smart Truncation
- Truncates at sentence boundaries
- Maintains semantic integrity
- Adds truncation indicators

### 3. Caching Optimization
- Context extraction results can be reused
- Reduces redundant computation overhead

## Advanced Features

### Context Truncation
The system automatically truncates context to fit within token limits:
- Uses actual tokenizer for accurate token counting
- Attempts to end at sentence boundaries (periods)
- Falls back to line boundaries if needed
- Adds "..." indicator for truncated content

### Header Formatting
When `include_headers=True`, headers are formatted with markdown-style prefixes:
```
# Level 1 Header
## Level 2 Header
### Level 3 Header
```

### Caption Integration
When `include_captions=True`, image and table captions are included as:
```
[Image: Figure 1 caption text]
[Table: Table 1 caption text]
```

## Integration with RAGAnything

The context-aware feature is seamlessly integrated into RAGAnything's workflow:

1. **Automatic Setup**: Context extractors are automatically created and configured
2. **Content Source Management**: Document processing automatically sets content sources
3. **Processor Integration**: All modal processors receive context capabilities
4. **Configuration Consistency**: Single configuration system for all context settings

## Error Handling

The system includes robust error handling:
- Gracefully handles missing or invalid content sources
- Returns empty context for unsupported formats
- Logs warnings for configuration issues
- Continues processing even if context extraction fails

## Compatibility

- **Backward Compatible**: Existing code works without modification
- **Optional Feature**: Context can be selectively enabled/disabled
- **Flexible Configuration**: Supports multiple configuration combinations

## Best Practices

1. **Token Limits**: Ensure `max_context_tokens` doesn't exceed LLM context limits
2. **Performance Impact**: Larger context windows increase processing time
3. **Content Quality**: Context quality directly affects analysis accuracy
4. **Window Size**: Match window size to content structure (documents vs articles)
5. **Content Filtering**: Use `context_filter_content_types` to reduce noise

## Troubleshooting

### Common Issues

**Context Not Extracted**
- Check if `set_content_source_for_context()` was called
- Verify `item_info` contains required fields (`page_idx`, `index`)
- Confirm content source format is correct

**Context Too Long/Short**
- Adjust `max_context_tokens` setting
- Modify `context_window` size
- Check `context_filter_content_types` configuration

**Irrelevant Context**
- Refine `context_filter_content_types` to exclude noise
- Reduce `context_window` size
- Set `include_captions=False` if captions are not helpful

**Configuration Issues**
- Verify environment variables are set correctly
- Check RAGAnythingConfig parameter names
- Ensure content_format matches your data source

## Examples

Check out these example files for complete usage demonstrations:

- **Configuration Examples**: See how to set up different context configurations
- **Integration Examples**: Learn how to integrate context-aware processing into your workflow
- **Custom Processors**: Examples of creating custom modal processors with context support

## API Reference

For detailed API documentation, see the docstrings in:
- `raganything/modalprocessors.py` - Context extraction and modal processors
- `raganything/config.py` - Configuration options
- `raganything/raganything.py` - Main RAGAnything class integration
