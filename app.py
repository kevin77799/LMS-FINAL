import os
import sys

# Add the current directory to sys.path so 'api' can be imported
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from api.app import app

if __name__ == "__main__":
    import uvicorn
    # Hugging Face Spaces expects the app to run on port 7860
    port = int(os.environ.get("PORT", 7860))
    uvicorn.run(app, host="0.0.0.0", port=port)
