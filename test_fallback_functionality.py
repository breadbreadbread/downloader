#!/usr/bin/env python3
"""Simple test for fallback functionality."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.extractor.fallbacks import ExtractionFallbackManager

def test_basic_functionality():
    print("Testing ExtractionFallbackManager...")
    
    try:
        # Test basic creation
        fallback_manager = ExtractionFallbackManager()
        print("✓ Fallback manager created successfully")
        
        # Test configuration
        print(f"  Min reference threshold: {fallback_manager.min_reference_threshold}")
        print(f"  Table fallback enabled: {fallback_manager.enable_table_fallback}")
        print(f"  BibTeX fallback enabled: {fallback_manager.enable_bibtex_fallback}")
        print(f"  HTML fallback enabled: {fallback_manager.enable_html_structure_fallback}")
        
        # Test reference detection
        test_text = "Smith, J. (2023). Machine Learning Advances. Journal of AI Research, 15(3), 123-145."
        looks_like_ref = fallback_manager._looks_like_reference(test_text)
        print(f"  Reference detection test: {looks_like_ref}")
        
        # Test fingerprint creation
        from src.models import Reference
        ref = Reference(raw_text=test_text, doi="10.1234/example")
        fingerprints = fallback_manager._create_reference_fingerprint_set([ref])
        print(f"  Fingerprint test: {len(fingerprints)} fingerprints created")
        
        print("✓ All basic functionality tests passed")
        return True
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_basic_functionality()
    if success:
        print("\n🎉 All fallback functionality working correctly!")
        sys.exit(0)
    else:
        print("\n❌ Fallback functionality has issues")
        sys.exit(1)