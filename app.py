"""
app.py
------
Entry point for the Resume Architect.
"""

import os
os.environ["NO_PROXY"] = "*"
os.environ["no_proxy"] = "*"

from dotenv import load_dotenv

def main():
    load_dotenv()
    print("=" * 55)
    print("  Resume Architect Agent")
    print("=" * 55)

    from src.ui import launch_ui
    print("\n🚀 Starting Gradio app...\n")
    launch_ui(share=False)

if __name__ == "__main__":
    main()