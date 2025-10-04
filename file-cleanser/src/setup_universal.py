import os
import subprocess
import sys

def setup_universal_cleanser():
    print("🧹 Universal File Cleanser - Setup")
    print("=" * 50)
    
    # Create directory structure
    directories = [
        "data/input",
        "data/output",
        "data/temp",
        "data/logs",
        "src"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✅ Created: {directory}")
    
    # Create .gitignore
    gitignore_content = """
# Python cache
__pycache__/
*.pyc
*.pyo
*.pyd

# Virtual environments
venv/
.env/

# Data folders
data/temp/
data/output/
data/logs/

# OS files
.DS_Store
Thumbs.db
"""
    with open(".gitignore", "w") as f:
        f.write(gitignore_content.strip() + "\n")
    print("✅ Created: .gitignore")

if __name__ == "__main__":
    setup_universal_cleanser()
