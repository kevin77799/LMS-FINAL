import re
from typing import List, Dict

import requests

from .gemini import analyze_report , generate_timetable , generate_roadmap , extract_topic , generate_quiz_json 
from ..core.config import SERP_API_KEY


def youtube_recommendations(search_keyword: str, min_duration_sec: int = 30) -> List[Dict[str, str]]:
    q = search_keyword
    
    # 1. Try SerpAPI (Professional & Stable)
    if SERP_API_KEY:
        try:
            print(f"[DEBUG] Fetching YouTube results via SerpAPI for: {q}")
            params = {
                "engine": "youtube",
                "search_query": q,
                "api_key": SERP_API_KEY
            }
            response = requests.get("https://serpapi.com/search", params=params, timeout=10)
            if response.status_code == 200:
                results = response.json().get("video_results", [])
                videos = []
                for v in results:
                    v_id = v.get("video_id")
                    v_title = v.get("title")
                    if v_id and v_title:
                        videos.append({"id": v_id, "title": v_title})
                if videos:
                    return videos[:10]
        except Exception as e:
            print(f"SerpAPI YouTube error: {e}")

    # 2. Fallback to Scraping (Fails on some cloud tiers like Hugging Face)
    try:
        q_clean = q.replace(" ", "+")
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        url = f"https://www.youtube.com/results?search_query={q_clean}"
        response = requests.get(url, timeout=10, headers=headers)
        html = response.text
        
        import json
        pattern = r"ytInitialData = (\{.*?\});"
        match = re.search(pattern, html)
        
        videos = []
        if match:
            try:
                data = json.loads(match.group(1))
                contents = data.get("contents", {}).get("twoColumnSearchResultsRenderer", {}).get("primaryContents", {}).get("sectionListRenderer", {}).get("contents", [])
                for item in contents:
                    video_list = item.get("itemSectionRenderer", {}).get("contents", [])
                    for entry in video_list:
                        video_data = entry.get("videoRenderer")
                        if video_data:
                            v_id = video_data.get("videoId")
                            title_runs = video_data.get("title", {}).get("runs", [])
                            v_title = title_runs[0].get("text", "") if title_runs else ""
                            if v_id and v_title:
                                videos.append({"id": v_id, "title": v_title})
                if videos: return videos[:10]
            except Exception: pass
        
        if not videos:
            video_ids = re.findall(r"watch\?v=(\S{11})", html)[:20]
            seen = set()
            for vid in video_ids:
                if vid not in seen:
                    seen.add(vid)
                    videos.append({"id": vid, "title": f"Video {vid}"})
        return videos[:10]
    except Exception as e:
        print(f"YouTube scraping fallback error: {e}")
        return []


def website_recommendations(query: str) -> List[str]:
    # 1. Try SerpAPI (Reliable)
    if SERP_API_KEY:
        try:
            print(f"[DEBUG] Fetching Web results via SerpAPI for: {query}")
            params = {
                "engine": "google",
                "q": query,
                "api_key": SERP_API_KEY
            }
            response = requests.get("https://serpapi.com/search", params=params, timeout=10)
            if response.status_code == 200:
                results = response.json().get("organic_results", [])
                urls = [r.get("link") for r in results if r.get("link")]
                if urls:
                    return urls[:8]
        except Exception as e:
            print(f"SerpAPI Web error: {e}")

    # 2. Try Scraping Approach (Fallback)
    urls = []
    
    # Method 1: DuckDuckGo HTML scrape
    try:
        q = query.replace(" ", "+")
        headers = { "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" }
        response = requests.get(f"https://duckduckgo.com/html/?q={q}", timeout=10, headers=headers)
        html = response.text
        matches = re.findall(r'href="([^"]*)" class="result__url"', html)
        for match in matches:
            url = requests.utils.unquote(match)
            if url.startswith(('http://', 'https://')) and 'duckduckgo.com' not in url:
                if url not in urls: urls.append(url)
    except Exception: pass
    
    # Method 2: Fallback to Educational links
    if not urls:
        urls = [
            "https://www.coursera.org/search?query=" + query.replace(" ", "%20"),
            "https://www.edx.org/search?q=" + query.replace(" ", "+"),
            "https://www.khanacademy.org/search?page_search_query=" + query.replace(" ", "+")
        ]
    
    return urls[:8]
