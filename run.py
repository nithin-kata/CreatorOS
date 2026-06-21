import os
import shutil
from app import create_app

# Programmatic copy of generated image asset
source_img = r"C:\Users\NITHIN KATA\.gemini\antigravity-ide\brain\9b43c06a-7832-4553-b264-1e03d1bfd80c\hero_dashboard_1781965847231.png"
dest_dir = r"c:\Users\NITHIN KATA\Downloads\Creator_Os\app\static\images"
if os.path.exists(source_img):
    os.makedirs(dest_dir, exist_ok=True)
    shutil.copy(source_img, os.path.join(dest_dir, "hero_dashboard.png"))

app = create_app()

if __name__ == '__main__':
    # Retrieve port from environment or default to 5000
    port = int(os.getenv('PORT', 5000))
    debug_mode = os.getenv('FLASK_ENV') == 'development'
    
    print("--------------------------------------------------")
    print(f"CreatorOS MVP Server Starting on http://127.0.0.1:{port}")
    print("Design Palette: Orange & Cream grid template")
    print("Features ready: Memory, Opportunity Alerts, AI Generator")
    print("--------------------------------------------------")
    
    app.run(host='127.0.0.1', port=port, debug=debug_mode)
