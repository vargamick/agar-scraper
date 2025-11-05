"""
Shared utilities for Agar scraper
"""
import json
import re
import base64
import random
from pathlib import Path
from typing import Dict, Any, Type
from datetime import datetime

from config.base_config import BaseConfig

def sanitize_filename(filename: str) -> str:
    """Sanitize filename for saving"""
    if not filename:
        return "unknown"
    return "".join(c for c in filename if c.isalnum() or c in (' ', '-', '_')).rstrip()[:100]

def save_json(data: Any, filepath: Path) -> None:
    """Save data as JSON"""
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def load_json(filepath: Path) -> Any:
    """Load JSON data from file"""
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)

def clean_product_name(name: str) -> str:
    """Clean up product name by removing common suffixes"""
    if not name:
        return ""
    
    # Remove common suffixes
    clean_endings = [" Data Sheets", " Downloads", " - Agar", " | Agar"]
    for ending in clean_endings:
        if ending in name:
            name = name.split(ending)[0].strip()
    
    # Remove "SDS" or "PDS" if they appear at the end
    name = re.sub(r'\s*(SDS|PDS)\s*$', '', name, flags=re.IGNORECASE).strip()
    
    return name

def save_screenshot(screenshot_data: Any, filepath: Path) -> bool:
    """Save screenshot data to file"""
    try:
        # Handle different types of screenshot data
        if isinstance(screenshot_data, str):
            if screenshot_data.startswith('data:image'):
                # Remove data URL prefix
                base64_data = screenshot_data.split(',')[1]
                screenshot_bytes = base64.b64decode(base64_data)
            else:
                try:
                    screenshot_bytes = base64.b64decode(screenshot_data)
                except:
                    screenshot_bytes = screenshot_data.encode('utf-8')
        elif isinstance(screenshot_data, bytes):
            screenshot_bytes = screenshot_data
        else:
            screenshot_bytes = str(screenshot_data).encode('utf-8')
        
        with open(filepath, "wb") as f:
            f.write(screenshot_bytes)
        
        return True
    except Exception as e:
        print(f"    ⚠️ Could not save screenshot: {e}")
        return False

def create_run_metadata(run_dir: Path, config: Type[BaseConfig], mode: str = "FULL") -> Dict:
    """Create initial run metadata
    
    Args:
        run_dir: Run directory path
        config: Client configuration class
        mode: Run mode (FULL or TEST)
        
    Returns:
        Metadata dictionary
    """
    metadata = {
        "run_id": run_dir.name,
        "start_time": datetime.now().isoformat(),
        "mode": mode,
        "base_url": config.BASE_URL,
        "status": "RUNNING",
        "run_directory": str(run_dir.absolute())
    }
    
    save_json(metadata, run_dir / "run_metadata.json")
    return metadata

def update_run_metadata(run_dir: Path, updates: Dict) -> None:
    """Update run metadata with new information"""
    metadata_path = run_dir / "run_metadata.json"
    if metadata_path.exists():
        metadata = load_json(metadata_path)
        metadata.update(updates)
        save_json(metadata, metadata_path)

def get_rate_limit_delay(config: Type[BaseConfig]) -> float:
    """
    Get a random rate limit delay based on config settings
    
    Args:
        config: Client configuration object
        
    Returns:
        Random delay in seconds between RATE_LIMIT_MIN and RATE_LIMIT_MAX
    """
    return random.uniform(config.RATE_LIMIT_MIN, config.RATE_LIMIT_MAX)
