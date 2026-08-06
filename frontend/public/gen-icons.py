"""
Gera todos os tamanhos de icone PWA a partir de icon-source.png
- 72, 96, 128, 144, 152, 192, 384, 512 (Android)
- 180 (iOS apple-touch-icon)
- maskable 512 (Android adaptive - safe zone)
"""
from PIL import Image
import os

SRC = os.path.join(os.path.dirname(__file__), "icon-source.png")
OUT_DIR = os.path.dirname(__file__)

sizes = [
    (72, "icon-72.png"),
    (96, "icon-96.png"),
    (128, "icon-128.png"),
    (144, "icon-144.png"),
    (152, "icon-152.png"),
    (192, "icon-192.png"),
    (384, "icon-384.png"),
    (512, "icon-512.png"),
    (180, "apple-touch-icon.png"),
    (167, "apple-touch-icon-ipad.png"),
]

img = Image.open(SRC).convert("RGBA")
print(f"Source: {img.size} {img.mode}")

for size, name in sizes:
    out = os.path.join(OUT_DIR, name)
    # LANCZOS para resize de alta qualidade
    resized = img.resize((size, size), Image.Resampling.LANCZOS)
    resized.save(out, "PNG", optimize=True)
    print(f"  {name}: {size}x{size} ({os.path.getsize(out)} bytes)")

# Mascara para Android adaptive icon (safe zone = 80% do centro)
maskable = Image.new("RGBA", (512, 512), (26, 54, 93, 255))  # kairos-900 background
inner = img.resize((int(512 * 0.65), int(512 * 0.65)), Image.Resampling.LANCZOS)
offset = ((512 - inner.width) // 2, (512 - inner.height) // 2)
maskable.paste(inner, offset, inner)
maskable_path = os.path.join(OUT_DIR, "icon-maskable-512.png")
maskable.save(maskable_path, "PNG", optimize=True)
print(f"  icon-maskable-512.png: 512x512 (com safe zone)")

# Favicon .ico multi-tamanho
ico_sizes = [(16, 16), (32, 32), (48, 48)]
favicon = img.resize((48, 48), Image.Resampling.LANCZOS)
favicon_path = os.path.join(OUT_DIR, "favicon.ico")
favicon.save(favicon_path, format="ICO", sizes=ico_sizes)
print(f"  favicon.ico: multi-size")

print("\nPronto!")
