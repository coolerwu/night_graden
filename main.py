"""Night Garden (夜花园) — COLA Architecture

Minimal implementation with only domain.agent for LLM calls.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from domain.agent.llm_agent import LLMAgent


def run_llm_call(user_input: str, output_file: str = None):
    """Execute LLM call with user input"""
    print("=" * 60)
    print("  Night Garden (夜花园) - COLA Architecture")
    print("  Domain.Agent Only - LLM Calls")
    print("=" * 60)
    
    agent = LLMAgent()
    
    print(f"\nInput: {user_input}")
    print("\nCalling LLM...")
    
    try:
        result = agent.invoke(user_input)
        print("\nLLM Response:")
        print("-" * 40)
        print(result)
        print("-" * 40)
        
        if output_file:
            Path(output_file).write_text(result, encoding='utf-8')
            print(f"\nResult saved to: {output_file}")
            
    except Exception as e:
        print(f"\nError: {e}")
    
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="Night Garden - COLA Architecture (Domain.Agent Only)")
    parser.add_argument("--input", "-i", type=str, help="Input prompt for LLM")
    parser.add_argument("--output", "-o", type=str, help="Output file path")
    args = parser.parse_args()

    if args.input:
        run_llm_call(args.input, args.output)
    else:
        print("Usage: python main.py --input 'your prompt' [--output result.txt]")
        print("Example: python main.py --input 'Explain quantum computing' --output response.txt")


if __name__ == "__main__":
    main()