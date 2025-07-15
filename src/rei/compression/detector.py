"""
Content type detection for optimal compression strategy.
"""

import json
import re
from typing import Any, Dict

class ContentDetector:
    """Detects content type for optimal compression strategy."""

    def __init__(self):
        self._text_patterns = {
            "text/json": self._is_json,
            "text/xml": self._is_xml,
            "text/csv": self._is_csv,
            "text/yaml": self._is_yaml,
            "text/code": self._is_code,
            "text/markdown": self._is_markdown,
            "text/plain": self._is_plain_text,
        }
    
    def _is_json(self, text: str) -> bool:
        """Check if text is valid JSON."""
        try:
            json.loads(text)
            return True
        except (json.JSONDecodeError, TypeError):
            return False
    
    def _is_xml(self, text: str) -> bool:
        """Check if text is XML."""
        text = text.strip()
        return (text.startswith('<?xml') or
                (text.startswith('<') and text.endswith('>')))
    
    def _is_csv(self, text: str) -> bool:
        """Check if text is CSV."""
        lines = text.strip().split('\n')
        if len(lines) < 2:
            return False
        
        # Check for consistent delimiter usage
        for delimiter in [',', ';', '\t', '|']:
            first_count = lines[0].count(delimiter)
            if first_count > 0:
                consistent = all(
                    abs(lines.count(delimiter) - first_count) <= 1
                    for line in lines[1:5]
                )
                if consistent:
                    return True
        return False
    
    def _is_yaml(self, text: str) -> bool:
        """Check if text is YAML."""
        lines = text.strip().split('\n')
        yaml_indicators = [
            '---',  # Document separator
            ':',    # Key-value separator
            '- ',   # List item
        ]
        
        for line in lines[:5]:  # Check first 5 lines
            line = line.strip()
            if any(indicator in line for indicator in yaml_indicators):
                return True
        
        return False
    
    def _is_code(self, text: str) -> bool:
        """Check if text is code."""
        code_indicators = [
            'def ', 'class ', 'import ', 'from ',  # Python
            'function ', 'const ', 'let ', 'var ',  # JavaScript
            'public ', 'private ', 'static ',       # Java/C#
            '#include', 'int main',                 # C/C++
            '<?php', '<?=',                        # PHP
        ]
        
        return any(indicator in text for indicator in code_indicators)
    
    def _is_markdown(self, text: str) -> bool:
        """Check if text is Markdown."""
        markdown_patterns = [
            r'^#+\s',       # Headers
            r'^\*\s',       # Bullet points
            r'^\d+\.\s',    # Numbered lists
            r'\[.*\]\(.*\)', # Links
            r'\*\*.*\*\*',  # Bold
            r'```',         # Code blocks
        ]
        
        return any(re.search(pattern, text, re.MULTILINE) 
                  for pattern in markdown_patterns)
    
    def _is_plain_text(self, text: str) -> bool:
        """Check if text is plain text (always true as fallback)."""
        return True
    
    def _detect_text(self, text: str) -> str:
        """Detect text content type."""
        for content_type, detector in self._text_patterns.items():
            if detector(text):
                return content_type
        return "text/plain"
    
    def _detect_binary(self, data: bytes) -> str:
        """Detect binary content type."""
        # Check for common binary signatures
        if data.startswith(b'\x89PNG'):
            return "image/png"
        elif data.startswith(b'\xff\xd8\xff'):
            return "image/jpeg"
        elif data.startswith(b'GIF8'):
            return "image/gif"
        elif data.startswith(b'PK'):
            return "application/zip"
        elif data.startswith(b'%PDF'):
            return "application/pdf"
        else:
            return "application/octet-stream"
    
    def detect(self, data: Any) -> str:
        """
        Detect content type of input data.

        Args:
            data: Input data of any type
        
        Returns:
            MIME-type string indicating content type
        """
        # Handle different input types
        if isinstance(data, bytes):
            return self._detect_binary(data)
        elif isinstance(data, (dict, list)):
            return "text/json"
        elif isinstance(data, str):
            return self._detect_text(data)
        return self._detect_text(str(data))
    
    def get_compression_hints(self, content_type: str) -> Dict[str, Any]:
        """
        Get compression hints based on content type.
        
        Args:
            content_type: Detected content type
            
        Returns:
            Dictionary with compression hints
        """
        hints = {
            "text/json": {
                "priority": "structure",
                "preprocessing": ["minify", "sort_keys"],
                "expected_ratio": 0.3,
                "dictionary_compression": True
            },
            "text/xml": {
                "priority": "structure", 
                "preprocessing": ["remove_whitespace", "compress_tags"],
                "expected_ratio": 0.4,
                "dictionary_compression": True
            },
            "text/csv": {
                "priority": "patterns",
                "preprocessing": ["compress_headers", "numeric_encoding"],
                "expected_ratio": 0.35,
                "dictionary_compression": True
            },
            "text/code": {
                "priority": "tokens",
                "preprocessing": ["tokenize", "compress_keywords"],
                "expected_ratio": 0.45,
                "dictionary_compression": True
            },
            "text/markdown": {
                "priority": "structure",
                "preprocessing": ["compress_headers", "link_shortening"],
                "expected_ratio": 0.5,
                "dictionary_compression": False
            },
            "text/plain": {
                "priority": "frequency",
                "preprocessing": ["word_frequency"],
                "expected_ratio": 0.6,
                "dictionary_compression": False
            }
        }
        
        return hints.get(content_type, {
            "priority": "generic",
            "preprocessing": [],
            "expected_ratio": 0.7,
            "dictionary_compression": False
        })
