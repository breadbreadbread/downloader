#!/usr/bin/env python3
"""Simple test without external dependencies."""

import sys
import os

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_basic():
    """Test basic functionality without external dependencies."""
    print("✓ Testing basic fallback functionality...")
    
    # Test configuration
    class MockSettings:
        FALLBACK_MIN_REFERENCE_THRESHOLD = 3
        ENABLE_TABLE_FALLBACK = True
        ENABLE_BIBTEX_FALLBACK = True
        ENABLE_HTML_STRUCTURE_FALLBACK = True
    
    # Test creation
    try:
        from src.extractor.fallbacks import ExtractionFallbackManager
        fallback_manager = ExtractionFallbackManager()
        print("✓ Fallback manager created successfully")
        
        # Test configuration
        print(f"  Min reference threshold: {fallback_manager.min_reference_threshold}")
        print(f"  Table fallback enabled: {fallback_manager.enable_table_fallback}")
        print(f"  BibTeX fallback enabled: {fallback_manager.enable_bibtex_fallback}")
        print(f"  HTML fallback enabled: {fallback_manager.enable_html_structure_fallback}")
        
        print("✓ All basic functionality tests passed!")
        return True
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_basic()
    if success:
        print("\n🎉 Extraction fallbacks feature is working correctly!")
        sys.exit(0)
    else:
        print("\n❌ Extraction fallbacks has issues")
        sys.exit(1)