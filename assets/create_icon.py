import os
from PIL import Image, ImageDraw


def create_daddy_icon():
    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([2, 2, size - 2, size - 2], fill=(0, 180, 255, 255))

    draw.line([20, 16, 20, 48], fill="white", width=5)

    draw.arc([20, 16, 46, 48], start=270, end=90, fill="white", width=5)

    os.makedirs("assets", exist_ok=True)
    img.save("assets/daddy_icon.png")
    print("Icon created at assets/daddy_icon.png")


if __name__ == "__main__":
    create_daddy_icon()