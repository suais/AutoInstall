# -*- coding: utf-8 -*-
"""生成应用图标 ICO 文件 - Vercel 极简黑白风格（数学符号 Σ 求和）"""
import os
from PIL import Image, ImageDraw


def create_icon(size=256):
    """生成图标图像（黑底圆角方块 + 白色粗体 Σ 求和符号）"""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    def S(v):
        """按基准 256 缩放坐标"""
        return int(round(v * size / 256.0))

    # 背景圆角方块（小圆角）
    margin = S(20)
    radius = max(2, S(26))
    draw.rounded_rectangle(
        [margin, margin, size - margin, size - margin],
        radius=radius,
        fill=(26, 26, 26, 255),
    )

    # 白色粗线（Σ 的三条边）
    lw = max(2, S(14))

    # 顶边
    draw.line(
        [(S(86), S(64)), (S(168), S(64))],
        fill=(255, 255, 255, 255),
        width=lw,
    )
    # 对角线（左上 → 右下）
    draw.line(
        [(S(86), S(64)), (S(168), S(192))],
        fill=(255, 255, 255, 255),
        width=lw,
    )
    # 底边
    draw.line(
        [(S(168), S(192)), (S(86), S(192))],
        fill=(255, 255, 255, 255),
        width=lw,
    )

    return img


def main():
    assets_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
    os.makedirs(assets_dir, exist_ok=True)

    # 生成多种尺寸
    sizes = [16, 24, 32, 48, 64, 128, 256]
    images = [create_icon(s) for s in sizes]

    ico_path = os.path.join(assets_dir, "icon.ico")
    # 以最大尺寸为基础，Pillow 会自动 resize 出所有子图像
    create_icon(256).save(ico_path, format="ICO", sizes=[(s, s) for s in sizes])
    print(f"图标已生成: {ico_path}")

    # 同时保存 256x256 PNG 预览
    png_path = os.path.join(assets_dir, "icon_preview.png")
    create_icon(256).save(png_path)
    print(f"预览图已生成: {png_path}")


if __name__ == "__main__":
    main()
