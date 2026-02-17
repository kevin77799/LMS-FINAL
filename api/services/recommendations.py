import re
from typing import List, Dict

import requests

from .gemini import analyze_report , generate_timetable , generate_roadmap , extract_topic , generate_quiz_json 


def youtube_recommendations(search_keyword: str, min_duration_sec: int = 30) -> List[Dict[str, str]]:
    q = search_keyword.replace(" ", "+")
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        url = f"https://www.youtube.com/results?search_query={q}"
        response = requests.get(url, timeout=10, headers=headers)
        html = response.text
        
        # Regex to find video IDs and Titles more efficiently from the initial search page
        # YouTube search results usually contain JSON data in 'ytInitialData'
        import json
        pattern = r"ytInitialData = (\{.*?\});"
        match = re.search(pattern, html)
        
        videos = []
        
        if match:
            try:
                data = json.loads(match.group(1))
                # Traverse the YouTube complex JSON structure to find video results
                # This is more reliable than flat regex for titles
                contents = data.get("contents", {}).get("twoColumnSearchResultsRenderer", {}).get("primaryContents", {}).get("sectionListRenderer", {}).get("contents", [])
                
                for item in contents:
                    video_list = item.get("itemSectionRenderer", {}).get("contents", [])
                    for entry in video_list:
                        video_data = entry.get("videoRenderer")
                        if video_data:
                            v_id = video_data.get("videoId")
                            # Extract title text correctly
                            v_title = ""
                            title_runs = video_data.get("title", {}).get("runs", [])
                            if title_runs:
                                v_title = title_runs[0].get("text", "")
                            
                            if v_id and v_title:
                                videos.append({"id": v_id, "title": v_title})
                                if len(videos) >= 10:
                                    return videos
            except Exception as e:
                print(f"JSON parse error in YouTube service: {e}")
        
        # Fallback to Regex if JSON parsing fails
        if not videos:
            video_ids = re.findall(r"watch\?v=(\S{11})", html)[:20]
            seen = set()
            for vid in video_ids:
                if vid not in seen:
                    seen.add(vid)
                    videos.append({"id": vid, "title": f"Video {vid}"})
        
        return videos[:10]
    except Exception as e:
        print(f"YouTube recommendation error: {e}")
        return []


def website_recommendations(query: str) -> List[str]:
    # Try multiple search approaches
    urls = []
    
    # Method 1: DuckDuckGo HTML scrape with updated pattern
    try:
        q = query.replace(" ", "+")
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        response = requests.get(f"https://duckduckgo.com/html/?q={q}", timeout=10, headers=headers)
        html = response.text
        
        # Try multiple regex patterns for DuckDuckGo
        patterns = [
            r'href="([^"]*)" class="result__url"',
            r'href="([^"]*)" class="result-link"',
            r'href="/l/\?kh=-1&amp;uddg=([^"&]+)',
            r'href="([^"]*)" data-testid="result-extras-url-link"',
            r'<a[^>]*href="([^"]*)"[^>]*class="[^"]*result[^"]*"'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, html)
            if matches:
                for match in matches:
                    try:
                        # Clean and decode URL
                        url = requests.utils.unquote(match)
                        # Skip DuckDuckGo internal URLs
                        if not url.startswith(('http://', 'https://')) or 'duckduckgo.com' in url:
                            continue
                        if url not in urls:
                            urls.append(url)
                    except:
                        continue
                if urls:
                    break
                    
    except Exception as e:
        print(f"DuckDuckGo search failed: {e}")
    
    # Method 2: Try Bing search as it's more scraping-friendly
    if not urls:
        try:
            q = query.replace(" ", "+")
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            response = requests.get(f"https://www.bing.com/search?q={q}", timeout=10, headers=headers)
            html = response.text
            
            # Extract URLs from Bing search results
            bing_patterns = [
                r'<a[^>]*href="(https?://[^"]+)"[^>]*>',
                r'href="(https?://[^"]*)"[^>]*class="[^"]*result[^"]*"',
            ]
            
            for pattern in bing_patterns:
                matches = re.findall(pattern, html)
                if matches:
                    for match in matches:
                        try:
                            url = match if isinstance(match, str) else match[0]
                            # Skip search engine URLs and ads
                            skip_domains = ['bing.com', 'microsoft.com', 'msn.com', 'live.com', 'youtube.com', 'facebook.com', 'twitter.com']
                            if any(skip in url.lower() for skip in skip_domains):
                                continue
                            if url.startswith(('http://', 'https://')) and url not in urls:
                                urls.append(url)
                        except:
                            continue
                    if len(urls) >= 3:  # Stop if we have enough results
                        break
        except Exception as e:
            print(f"Bing search failed: {e}")
    
    # Method 2b: If still no results, try Google search fallback
    if not urls:
        try:
            q = query.replace(" ", "+")
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            response = requests.get(f"https://www.google.com/search?q={q}", timeout=10, headers=headers)
            html = response.text
            
            # Extract URLs from Google search results
            google_patterns = [
                r'<a[^>]*href="(/url\?q=([^&"]+))[^"]*"',
                r'href="(https?://[^"]*)" data-ved='
            ]
            
            for pattern in google_patterns:
                matches = re.findall(pattern, html)
                if matches:
                    for match in matches:
                        try:
                            url = match[1] if isinstance(match, tuple) and len(match) > 1 else match[0] if isinstance(match, tuple) else match
                            url = requests.utils.unquote(url)
                            # Skip Google internal URLs and ads
                            if any(skip in url for skip in ['google.com', 'youtube.com', 'googleadservices', 'googlesyndication']):
                                continue
                            if url.startswith(('http://', 'https://')) and url not in urls:
                                urls.append(url)
                        except:
                            continue
                    if urls:
                        break
        except Exception as e:
            print(f"Google search failed: {e}")
    
    # Method 3: Fallback to some relevant educational URLs if search fails
    if not urls:
        fallback_urls = [
            "https://www.coursera.org/search?query=" + query.replace(" ", "%20"),
            "https://www.edx.org/search?q=" + query.replace(" ", "+"),
            "https://www.khanacademy.org/search?search_again=1&page_search_query=" + query.replace(" ", "+"),
            "https://en.wikipedia.org/wiki/Special:Search?search=" + query.replace(" ", "+"),
            "https://scholar.google.com/scholar?q=" + query.replace(" ", "+")
        ]
        urls.extend(fallback_urls)
    
    return urls[:8]  # Return up to 8 URLs


