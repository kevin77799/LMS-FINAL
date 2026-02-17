#!/usr/bin/env python3

import requests
import time
import json

print("Waiting for server to start...")
time.sleep(3)

try:
    print("Testing quiz generation endpoint...")
    response = requests.post('http://localhost:8000/quizzes/groups/2/generate', 
                           json={'subject': 'Math'}, 
                           timeout=30)
    print(f'Status: {response.status_code}')
    print(f'Response: {response.text}')
except Exception as e:
    print(f'Error: {e}')
