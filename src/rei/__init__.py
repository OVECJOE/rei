"""
Rei: Universal Context Compression Library

A lightweight library that compresses any context into a fixed 128-character
encrypted string + decryption instructions, enabling unlimited context
for any LLM.
"""

from api import compress_context, compress_stream, chat_with_context
from compressor import ReiCompressor
from streaming import ReiStreamer
from integrations import (
    OpenAIIntegration,
    AnthropicIntegration,
    GeminiIntegration
)

__version__ = "0.1.0"
__author__ = "OVECJOE"
__license__ = "MIT"
__url__ = "https://github.com/OVECJOE/rei"
__description__ = "Universal Context Compression Library"

# Expose the API
__all__ = [
    "compress_context",
    "compress_stream",
    "chat_with_context",
    "ReiCompressor",
    "ReiStreamer",
    "OpenAIIntegration",
    "AnthropicIntegration",
    "GeminiIntegration"
]
