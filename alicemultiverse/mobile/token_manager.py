"""Token management for mobile companion authentication."""

import secrets
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any
import hashlib

class TokenManager:
    """Manages authentication tokens for mobile access."""
    
    def __init__(self, token_file: Optional[Path] = None):
        """
        Initialize token manager.
        
        Args:
            token_file: Path to store tokens (default: ~/.alice/mobile_tokens.json)
        """
        self.token_file = token_file or Path.home() / ".alice" / "mobile_tokens.json"
        self.token_file.parent.mkdir(parents=True, exist_ok=True)
        self.tokens = self._load_tokens()
    
    def _load_tokens(self) -> Dict[str, Any]:
        """Load tokens from file."""
        if self.token_file.exists():
            try:
                with open(self.token_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _save_tokens(self):
        """Save tokens to file."""
        with open(self.token_file, 'w') as f:
            json.dump(self.tokens, f, indent=2, default=str)
    
    def generate_token(self, name: str = "default", expires_hours: int = 24) -> str:
        """
        Generate a new access token.
        
        Args:
            name: Token name/description
            expires_hours: Hours until token expires
            
        Returns:
            Generated token string
        """
        # Generate secure random token
        token = secrets.token_urlsafe(32)
        
        # Hash token for storage
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        
        # Store token info
        self.tokens[token_hash] = {
            "name": name,
            "created": datetime.now().isoformat(),
            "expires": (datetime.now() + timedelta(hours=expires_hours)).isoformat(),
            "last_used": None,
            "usage_count": 0
        }
        
        self._save_tokens()
        return token
    
    def validate_token(self, token: str) -> bool:
        """
        Validate a token and update usage.
        
        Args:
            token: Token to validate
            
        Returns:
            True if valid, False otherwise
        """
        # Hash token to look up
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        
        if token_hash not in self.tokens:
            return False
        
        token_info = self.tokens[token_hash]
        
        # Check expiration
        expires = datetime.fromisoformat(token_info["expires"])
        if datetime.now() > expires:
            # Remove expired token
            del self.tokens[token_hash]
            self._save_tokens()
            return False
        
        # Update usage
        token_info["last_used"] = datetime.now().isoformat()
        token_info["usage_count"] += 1
        self._save_tokens()
        
        return True
    
    def revoke_token(self, token: str) -> bool:
        """
        Revoke a token.
        
        Args:
            token: Token to revoke
            
        Returns:
            True if revoked, False if not found
        """
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        
        if token_hash in self.tokens:
            del self.tokens[token_hash]
            self._save_tokens()
            return True
        
        return False
    
    def list_tokens(self) -> Dict[str, Any]:
        """
        List all tokens (without actual token values).
        
        Returns:
            Token information
        """
        result = {}
        for token_hash, info in self.tokens.items():
            # Clean expired tokens
            expires = datetime.fromisoformat(info["expires"])
            if datetime.now() > expires:
                continue
            
            result[token_hash[:8] + "..."] = {
                "name": info["name"],
                "created": info["created"],
                "expires": info["expires"],
                "last_used": info["last_used"],
                "usage_count": info["usage_count"]
            }
        
        return result
    
    def cleanup_expired(self):
        """Remove all expired tokens."""
        expired = []
        
        for token_hash, info in self.tokens.items():
            expires = datetime.fromisoformat(info["expires"])
            if datetime.now() > expires:
                expired.append(token_hash)
        
        for token_hash in expired:
            del self.tokens[token_hash]
        
        if expired:
            self._save_tokens()
        
        return len(expired)