"""
Main ReiCompressor class that orchestrates the compression pipeline.
"""

from typing import Any, Dict, List, Tuple, Optional, Literal
import hashlib
import json

from compression.detector import ContentDetector
from compression.text_compressor import TextCompressor
from compression.binary_compressor import BinaryCompressor
from compression.final_compressor import FinalCompressor
from encryption.encryptor import Encryptor
from encryption.key_manager import KeyManager
from encryption.formatter import Formatter
from tools.generator import ToolGenerator
from models.adapters import ModelAdapter
from utils import ValidationError, CompressionError

SupportsModel = Literal["gpt-4", "claude-3.5"]


class ReiCompressor:
    """
    Main compression engine that converts any context into a fixed
    128-character encrypted string plus model-specific decryption tools.
    """

    def __init__(self, model_name: SupportsModel) -> None:
        pass
