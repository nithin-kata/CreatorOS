import os
import shutil
from app import create_app

# Programmatic copy of generated image asset
source_img = r"C:\Users\NITHIN KATA\.gemini\antigravity-ide\brain\9b43c06a-7832-4553-b264-1e03d1bfd80c\hero_dashboard_1781965847231.png"
dest_dir = r"c:\Users\NITHIN KATA\Downloads\Creator_Os\app\static\images"
if os.path.exists(source_img):
    os.makedirs(dest_dir, exist_ok=True)
    shutil.copy(source_img, os.path.join(dest_dir, "hero_dashboard.png"))

# Copy Gen Z creator images (original 3)
dev_img = r"C:\Users\NITHIN KATA\.gemini\antigravity-ide\brain\d267fd8e-83da-483a-9975-7a2db3e9229e\creator_dev_cinematic_1782027111293.png"
design_img = r"C:\Users\NITHIN KATA\.gemini\antigravity-ide\brain\d267fd8e-83da-483a-9975-7a2db3e9229e\creator_design_cinematic_1782027128096.png"
writer_img = r"C:\Users\NITHIN KATA\.gemini\antigravity-ide\brain\d267fd8e-83da-483a-9975-7a2db3e9229e\creator_writer_cinematic_1782027143962.png"

# Copy new niche creator images (travel, fitness, fashion, food, photography, finance)
travel_img = r"C:\Users\NITHIN KATA\.gemini\antigravity-ide\brain\d267fd8e-83da-483a-9975-7a2db3e9229e\creator_travel_cinematic_1782027906298.png"
fitness_img = r"C:\Users\NITHIN KATA\.gemini\antigravity-ide\brain\d267fd8e-83da-483a-9975-7a2db3e9229e\creator_fitness_cinematic_1782027920048.png"
fashion_img = r"C:\Users\NITHIN KATA\.gemini\antigravity-ide\brain\d267fd8e-83da-483a-9975-7a2db3e9229e\creator_fashion_cinematic_1782027933436.png"
food_img = r"C:\Users\NITHIN KATA\.gemini\antigravity-ide\brain\d267fd8e-83da-483a-9975-7a2db3e9229e\creator_food_cinematic_1782027952221.png"
photography_img = r"C:\Users\NITHIN KATA\.gemini\antigravity-ide\brain\d267fd8e-83da-483a-9975-7a2db3e9229e\creator_photography_cinematic_1782027965219.png"
finance_img = r"C:\Users\NITHIN KATA\.gemini\antigravity-ide\brain\d267fd8e-83da-483a-9975-7a2db3e9229e\creator_finance_cinematic_1782027978216.png"

all_creator_imgs = [
    (dev_img, "creator_dev_cinematic.png"),
    (design_img, "creator_design_cinematic.png"),
    (writer_img, "creator_writer_cinematic.png"),
    (travel_img, "creator_travel_cinematic.png"),
    (fitness_img, "creator_fitness_cinematic.png"),
    (fashion_img, "creator_fashion_cinematic.png"),
    (food_img, "creator_food_cinematic.png"),
    (photography_img, "creator_photography_cinematic.png"),
    (finance_img, "creator_finance_cinematic.png"),
]

for src, name in all_creator_imgs:
    if os.path.exists(src):
        os.makedirs(dest_dir, exist_ok=True)
        shutil.copy(src, os.path.join(dest_dir, name))

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
