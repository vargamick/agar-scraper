"""
3DN Scraper Template - Configuration Loader
Version: 1.0.0

This module handles loading client-specific configurations.
It provides a centralized way to select and load client deployments.
"""

import importlib
import sys
from pathlib import Path
from typing import Type, Optional

from config.base_config import BaseConfig


class ConfigLoader:
    """Loads and manages client-specific configurations"""
    
    _active_config: Optional[Type[BaseConfig]] = None
    _active_client: Optional[str] = None
    
    @classmethod
    def load_client_config(cls, client_name: str) -> Type[BaseConfig]:
        """Load configuration for a specific client deployment
        
        Args:
            client_name: The client identifier (e.g., 'agar', 'exampleclient')
            
        Returns:
            ClientConfig class for the specified client
            
        Raises:
            ImportError: If client configuration cannot be loaded
            ValueError: If client name is invalid
        """
        if not client_name:
            raise ValueError("Client name cannot be empty")
        
        # Normalize client name
        client_name = client_name.lower().strip()
        
        try:
            # Import the client configuration module
            module_path = f"config.clients.{client_name}.client_config"
            module = importlib.import_module(module_path)
            
            # Get the ClientConfig class
            if not hasattr(module, 'ClientConfig'):
                raise ImportError(
                    f"ClientConfig class not found in {module_path}. "
                    f"Ensure the client configuration file exists and has a ClientConfig class."
                )
            
            config_class = module.ClientConfig
            
            # Validate it inherits from BaseConfig
            if not issubclass(config_class, BaseConfig):
                raise TypeError(
                    f"ClientConfig for '{client_name}' must inherit from BaseConfig"
                )
            
            # Set as active configuration
            cls._active_config = config_class
            cls._active_client = client_name
            
            print(f"✓ Loaded configuration for client: {config_class.CLIENT_FULL_NAME}")
            
            return config_class
            
        except ModuleNotFoundError as e:
            raise ImportError(
                f"Client configuration not found for '{client_name}'. "
                f"Expected file: config/clients/{client_name}/client_config.py\n"
                f"Error: {e}"
            )
        except Exception as e:
            raise ImportError(
                f"Error loading client configuration for '{client_name}': {e}"
            )
    
    @classmethod
    def load_client_strategies(cls, client_name: str):
        """Load extraction strategies for a specific client
        
        Args:
            client_name: The client identifier
            
        Returns:
            ExtractionStrategy class for the specified client
            
        Raises:
            ImportError: If client strategies cannot be loaded
        """
        if not client_name:
            raise ValueError("Client name cannot be empty")
        
        # Normalize client name
        client_name = client_name.lower().strip()
        
        try:
            # Import the client strategies module
            module_path = f"config.clients.{client_name}.extraction_strategies"
            module = importlib.import_module(module_path)
            
            # Look for strategy class (pattern: {Client}ExtractionStrategy)
            strategy_class_name = f"{client_name.capitalize()}ExtractionStrategy"
            
            if hasattr(module, strategy_class_name):
                return getattr(module, strategy_class_name)
            
            # Fallback to generic name
            if hasattr(module, 'ExtractionStrategy'):
                return module.ExtractionStrategy
            
            # If no class found, return the module itself (contains class methods)
            return module
            
        except ModuleNotFoundError:
            print(f"⚠ Warning: No extraction strategies found for '{client_name}'")
            print(f"  Expected file: config/clients/{client_name}/extraction_strategies.py")
            return None
        except Exception as e:
            print(f"⚠ Warning: Error loading strategies for '{client_name}': {e}")
            return None
    
    @classmethod
    def get_active_config(cls) -> Type[BaseConfig]:
        """Get the currently active client configuration
        
        Returns:
            Active ClientConfig class
            
        Raises:
            RuntimeError: If no configuration has been loaded
        """
        if cls._active_config is None:
            raise RuntimeError(
                "No client configuration loaded. "
                "Call ConfigLoader.load_client_config(client_name) first."
            )
        return cls._active_config
    
    @classmethod
    def get_active_client_name(cls) -> str:
        """Get the name of the currently active client
        
        Returns:
            Active client name
            
        Raises:
            RuntimeError: If no configuration has been loaded
        """
        if cls._active_client is None:
            raise RuntimeError(
                "No client configuration loaded. "
                "Call ConfigLoader.load_client_config(client_name) first."
            )
        return cls._active_client
    
    @classmethod
    def list_available_clients(cls) -> list:
        """List all available client deployments
        
        Returns:
            List of available client names
        """
        clients_dir = Path(__file__).parent / "clients"
        
        if not clients_dir.exists():
            return []
        
        available_clients = []
        
        for client_dir in clients_dir.iterdir():
            if client_dir.is_dir() and not client_dir.name.startswith('_'):
                # Check if client_config.py exists
                config_file = client_dir / "client_config.py"
                if config_file.exists():
                    available_clients.append(client_dir.name)
        
        return sorted(available_clients)
    
    @classmethod
    def print_available_clients(cls):
        """Print formatted list of available clients"""
        clients = cls.list_available_clients()
        
        if not clients:
            print("No client deployments found.")
            print("\nTo create a new client deployment:")
            print("  python scripts/deploy_new_client.py")
            return
        
        print("\nAvailable Client Deployments:")
        print("=" * 50)
        
        for client_name in clients:
            try:
                config = cls.load_client_config(client_name)
                print(f"  • {client_name:20s} - {config.CLIENT_FULL_NAME}")
            except Exception as e:
                print(f"  • {client_name:20s} - [Error loading config]")
        
        print("=" * 50)
    
    @classmethod
    def validate_client_config(cls, client_name: str) -> tuple[bool, list]:
        """Validate a client configuration
        
        Args:
            client_name: The client identifier
            
        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []
        
        try:
            config = cls.load_client_config(client_name)
            
            # Check required fields
            required_fields = [
                'CLIENT_NAME',
                'CLIENT_FULL_NAME',
                'BASE_URL',
                'CATEGORY_URL_PATTERN',
                'PRODUCT_URL_PATTERN',
                'OUTPUT_PREFIX',
                'BASE_OUTPUT_DIR'
            ]
            
            for field in required_fields:
                if not hasattr(config, field):
                    issues.append(f"Missing required field: {field}")
                elif not getattr(config, field):
                    issues.append(f"Empty required field: {field}")
            
            # Check URL patterns contain {slug}
            if hasattr(config, 'CATEGORY_URL_PATTERN'):
                if '{slug}' not in config.CATEGORY_URL_PATTERN:
                    issues.append("CATEGORY_URL_PATTERN must contain {slug} placeholder")
            
            if hasattr(config, 'PRODUCT_URL_PATTERN'):
                if '{slug}' not in config.PRODUCT_URL_PATTERN:
                    issues.append("PRODUCT_URL_PATTERN must contain {slug} placeholder")
            
            # Check BASE_URL format
            if hasattr(config, 'BASE_URL'):
                if not config.BASE_URL.startswith('http'):
                    issues.append("BASE_URL must start with http:// or https://")
            
            # Check for extraction strategies
            strategies = cls.load_client_strategies(client_name)
            if strategies is None:
                issues.append("No extraction strategies file found (extraction_strategies.py)")
            
            return (len(issues) == 0, issues)
            
        except Exception as e:
            issues.append(f"Configuration load error: {e}")
            return (False, issues)


# Convenience function for simple usage
def load_config(client_name: str) -> Type[BaseConfig]:
    """Convenience function to load a client configuration
    
    Args:
        client_name: The client identifier
        
    Returns:
        ClientConfig class
    """
    return ConfigLoader.load_client_config(client_name)
