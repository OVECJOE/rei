"""
Main ReiCompressor class that orchestrates the compression pipeline.
"""

import hashlib
import json
from typing import Any, Dict, List, Tuple, Optional, Literal
from llmrelic.registry import SupportedModels

from rei.compression import (
    ContentDetector,
    TextCompressor,
    BinaryCompressor,
    FinalCompressor
)
from rei.encryption import (
    Encryptor,
    KeyManager,
    Formatter
)
from rei.tools import (
    ToolGenerator
)
from rei.models.adapters import ModelAdapter
from rei.utils import ValidationError, CompressionError


class ReiCompressor:
    """
    Main compression engine that converts any context into a fixed
    128-character encrypted string plus model-specific decryption tools.
    """

    def __init__(self, model_name: str, security_level: Literal["basic", "standard", "enterprise"] = "standard"):
        """
        Initialize the ReiCompressor.

        Args:
            model_name: Target LLM model (e.g. "gpt-4o-mini", "mistral-large-latest")
            security_level: Encryption level (basic, standard, enterprise)
        """
        self.__supported_models = (SupportedModels.create()
                                    .openai(["gpt-4o-mini", "gpt-4o"])
                                    .mistral(["mistral-large-latest", "mistral-small-latest"])
                                    .build())
        
        if not self.__supported_models.is_supported(model_name):
            available = ", ".join(self.__supported_models.get_supported_models())
            raise ValueError(f"Model {model_name} is not supported. Available models: {available}")
        
        self.__model = model_name
        self.__security_level = security_level

        # Initialize components
        self.__content_detector = ContentDetector()
        self.__text_compressor = TextCompressor()
        self.__binary_compressor = BinaryCompressor()
        self.__final_compressor = FinalCompressor()
        self.__encryptor = Encryptor(security_level)
        self.__key_manager = KeyManager()
        self.__formatter = Formatter()
        self.__tool_generator = ToolGenerator()
        self.__model_adapter = ModelAdapter(model_name)

        # Build compression pipeline
        self.compression_pipeline = self._build_pipeline()
    
    def _build_pipeline(self) -> Dict[str, Any]:
        """Build the compression pipeline based on model capabilities."""
        capabilities = self.__model_adapter.get_capabilities()
        return {
            "max_complexity": capabilities.get("max_complexity", 1.0),
            "supports_binary": capabilities.get("supports_binary", True),
            "token_efficiency": capabilities.get("token_efficiency", 1.0),
            "encryption_level": self._get_encryption_level(capabilities)
        }
    
    def _get_encryption_level(self, capabilities: Dict[str, Any]) -> str:
        """Determine optimal encryption level based on model capabilities."""
        if capabilities.get("advanced_reasoning", False):
            return "complex"
        elif capabilities.get("function_calling", False):
            return "standard"
        return "basic"
    
    def compress(self, data: Any) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Compress any data into a fixed 128-character encrypted string.

        Args:
            data: Input data of any type (str, dict, list, bytes, etc.)

        Returns:
            Tuple of (encrypted_128_char_string, decryption_tools)
        
        Raises:
            ValidationError: If input data is invalid
            CompressionError: If compression fails
        """
        try:
            # Step 1: Detect content type and validate
            content_type = self.__content_detector.detect(data)
            validated_data = self._validate_input(data, content_type)

            # Step 2: Apply content-specific compression
            if content_type.startswith("text/"):
                compressed_data = self.__text_compressor.compress(
                    validated_data, content_type
                )
            else:
                compressed_data = self.__binary_compressor.compress(
                    validated_data, content_type
                )
            
            # Step 3: Apply final compression
            compressed_data = self.__final_compressor.compress(
                compressed_data,
                target_size=self._get_target_size()
            )

            # Step 4: Generate deterministic encryption key
            content_hash = hashlib.sha256(
                json.dumps(data, sort_keys=True, default=str).encode()
            ).hexdigest()
            encryption_key = self.__key_manager.derive_key(
                content_hash,
                self.__security_level
            )

            # Step 5: Encrypt to fixed length string
            encrypted_data = self.__encryptor.encrypt(
                compressed_data,
                encryption_key
            )

            # Step 6: Format to exactly 128 characters
            formatted_output = self.__formatter.format_to_128_chars(
                encrypted_data,
                content_type,
                self.__security_level
            )

            # Step 7: Generate model-specific decryption tools
            tools = self.__tool_generator.generate_tools(
                self.__model,
                encryption_key,
                content_type,
                self.__security_level,
                self.compression_pipeline
            )

            return formatted_output, tools
        except Exception as e:
            raise CompressionError(f"Compression failed: {str(e)}")
        
    def _validate_input(self, data: Any, content_type: str) -> Any:
        """Validate input data based on content type."""
        if data is None:
            raise ValidationError("Input data cannot be None")
        
        # Check size limits (prevent abuse)
        if hasattr(data, '__len__') and len(data) > 500_000_000: # 500MB limit
            raise ValidationError("Input data too large (>500MB)")
        
        # Content-specific validation
        if content_type == "text/json":
            try:
                json.loads(data)
            except json.JSONDecodeError:
                raise ValidationError("Invalid JSON input")
        
        return data
    
    def _get_target_size(self) -> int:
        """Get target compression size based on model capabilities."""
        base_size = 512 # Base compression target
        efficiency = self.compression_pipeline['token_efficiency']
        return int(base_size * efficiency)
    
    def decompress(self, encrypted_data: str, tools: List[Dict[str, Any]]) -> Any:
        """
        Decompress encrypted data using provided decryption tools.

        Args:
            encrypted_data: 128-character encrypted string
            tools: List of decryption tools generated during compression
        
        Returns:
            Original data
        """
        try:
            # Extract metadata from encrypted string
            metadata = self.__formatter.extract_metadata(encrypted_data)

            # Get decryption key from tools
            decryption_key = None
            for tool in tools:
                if "decrypt_context" in tool.get("function", {}).get("name", ""):
                    decryption_key = self._extract_key_from_tool(tool)
                    break
            
            if not decryption_key:
                raise CompressionError("Decryption key not found in tools")
            
            # Decrypt data
            decrypted_data = self.__encryptor.decrypt(
                encrypted_data,
                decryption_key
            )

            # Decompress
            if metadata["content_type"].startswith("text/"):
                return self.__text_compressor.decompress(
                    decrypted_data,
                    metadata["content_type"]
                )
            return self.__binary_compressor.decompress(
                decrypted_data,
                metadata["content_type"]
            )
        except Exception as e:
            raise CompressionError(f"Decompression failed: {str(e)}") from e
    
    def _extract_key_from_tool(self, tool: Dict[str, Any]) -> Optional[str]:
        """Extract decryption key from tool definition."""
        description = tool.get("function", {}).get("description", "")
        if "key:" in description:
            return description.split("key:")[-1].split()[0]
        return None
    
    def get_compression_stats(self, data: Any) -> Dict[str, Any]:
        """
        Get compression statistics for given data.
        
        Args:
            data: Input data to analyze
            
        Returns:
            Statistics about compression ratio, type, etc.
        """
        original_size = len(str(data))
        content_type = self.__content_detector.detect(data)
        
        # Estimate compression ratio
        if content_type == "text/json":
            estimated_ratio = 0.3  # JSON compresses well
        elif content_type.startswith("text/"):
            estimated_ratio = 0.4  # Text compresses moderately
        else:
            estimated_ratio = 0.6  # Binary data varies
        
        return {
            "original_size": original_size,
            "content_type": content_type,
            "estimated_compressed_size": 128,  # Always 128 chars
            "compression_ratio": 128 / original_size,
            "estimated_ratio": estimated_ratio,
            "model": self.__model,
            "security_level": self.__security_level
        }
    
    @property
    def model(self) -> str:
        """
        Get the model name.
        """
        return self.__model
    
    @property
    def security_level(self):
        return self.__security_level
