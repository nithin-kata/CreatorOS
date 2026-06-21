import os
import shutil

brain = r"C:\Users\NITHIN KATA\.gemini\antigravity-ide\brain\d267fd8e-83da-483a-9975-7a2db3e9229e"
dest = r"c:\Users\NITHIN KATA\Downloads\Creator_Os\app\static\images"
os.makedirs(dest, exist_ok=True)

imgs = [
    ("creator_travel_cinematic_1782027906298.png", "creator_travel_cinematic.png"),
    ("creator_fitness_cinematic_1782027920048.png", "creator_fitness_cinematic.png"),
    ("creator_fashion_cinematic_1782027933436.png", "creator_fashion_cinematic.png"),
    ("creator_food_cinematic_1782027952221.png", "creator_food_cinematic.png"),
    ("creator_photography_cinematic_1782027965219.png", "creator_photography_cinematic.png"),
    ("creator_finance_cinematic_1782027978216.png", "creator_finance_cinematic.png"),
]

for src_name, dst_name in imgs:
    src = os.path.join(brain, src_name)
    dst = os.path.join(dest, dst_name)
    if os.path.exists(src):
        shutil.copy(src, dst)
        print(f"✅ Copied: {dst_name}")
    else:
        print(f"❌ MISSING: {src_name}")

print("\nAll done! Restart your Flask server.")
