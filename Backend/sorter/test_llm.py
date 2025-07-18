#!/usr/bin/env python3
"""
Test script for LLM filtering with specific examples
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from llm_filter import bloomz_filter, build_prompt

def test_example():
    # Test the specific example
    test_text = "REFONTE, CONCEPTION ET MAINTENANCE ÉVOLUTIVE DU SITE WEB DE L'ANME"
    
    print("=" * 60)
    print("TESTING LLM FILTER")
    print("=" * 60)
    print(f"Input text: {test_text}")
    print("-" * 60)
    
    # Show the prompt being used
    prompt = build_prompt(test_text)
    print("PROMPT BEING USED:")
    print("-" * 30)
    print(prompt)
    print("-" * 30)
    
    # Test the LLM
    result = bloomz_filter(test_text)
    
    print("-" * 60)
    print(f"Final result: {result}")
    print("=" * 60)
    
    return result

if __name__ == "__main__":
    test_example() 