#!/usr/bin/env python3

print("Testing dependencies...")

try:
    import google.generativeai as genai
    print("✓ google.generativeai: OK")
except Exception as e:
    print(f"✗ google.generativeai: FAILED - {e}")

try:
    from phi.agent import Agent
    print("✓ phi.agent: OK")
except Exception as e:
    print(f"✗ phi.agent: FAILED - {e}")

try:
    from phi.model.google import Gemini
    print("✓ phi.model.google.Gemini: OK")
except Exception as e:
    print(f"✗ phi.model.google.Gemini: FAILED - {e}")

try:
    from phi.tools.duckduckgo import DuckDuckGo
    print("✓ phi.tools.duckduckgo: OK")
except Exception as e:
    print(f"✗ phi.tools.duckduckgo: FAILED - {e}")

try:
    from phi.tools.serpapi_tools import SerpApiTools
    print("✓ phi.tools.serpapi_tools: OK")
except Exception as e:
    print(f"✗ phi.tools.serpapi_tools: FAILED - {e}")

print("\nTesting API configuration...")
try:
    from api.core.config import API_KEYS, SERP_API_KEY
    print(f"API_KEYS available: {[bool(k) for k in API_KEYS]}")
    print(f"SERP_API_KEY available: {bool(SERP_API_KEY)}")
except Exception as e:
    print(f"✗ Config loading failed: {e}")
