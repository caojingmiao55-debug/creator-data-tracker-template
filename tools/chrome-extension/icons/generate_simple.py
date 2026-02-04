#!/usr/bin/env python3
"""生成简单的渐变图标"""
from PIL import Image, ImageDraw
import os

def create_icon(size):
    # 创建图像
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 计算比例
    scale = size / 128
    padding = int(4 * scale)
    radius = int(28 * scale)

    # 绘制圆角矩形背景（紫色渐变效果用纯色近似）
    bg_color = (99, 102, 241)  # #6366f1

    # 简单的圆角矩形
    draw.rounded_rectangle(
        [padding, padding, size - padding, size - padding],
        radius=radius,
        fill=bg_color
    )

    # 绘制三个柱状图
    bar_color = (255, 255, 255, 230)
    bar_width = int(16 * scale)
    bar_radius = int(4 * scale)
    bottom = int(104 * scale)

    # 第一个柱子
    x1 = int(28 * scale)
    h1 = int(34 * scale)
    draw.rounded_rectangle([x1, bottom - h1, x1 + bar_width, bottom], radius=bar_radius, fill=bar_color)

    # 第二个柱子
    x2 = int(56 * scale)
    h2 = int(54 * scale)
    draw.rounded_rectangle([x2, bottom - h2, x2 + bar_width, bottom], radius=bar_radius, fill=bar_color)

    # 第三个柱子
    x3 = int(84 * scale)
    h3 = int(74 * scale)
    draw.rounded_rectangle([x3, bottom - h3, x3 + bar_width, bottom], radius=bar_radius, fill=bar_color)

    # 绘制同步圆圈（仅在较大尺寸时）
    if size >= 48:
        circle_x = int(100 * scale)
        circle_y = int(28 * scale)
        circle_r = int(18 * scale)
        draw.ellipse(
            [circle_x - circle_r, circle_y - circle_r,
             circle_x + circle_r, circle_y + circle_r],
            fill=(255, 255, 255)
        )
        # 绘制箭头（简化版）
        arrow_color = bg_color
        arrow_size = int(6 * scale)
        # 上箭头
        draw.polygon([
            (circle_x, circle_y - arrow_size),
            (circle_x - arrow_size, circle_y),
            (circle_x + arrow_size, circle_y)
        ], fill=arrow_color)
        # 箭头线
        line_width = max(2, int(3 * scale))
        draw.line([(circle_x, circle_y - arrow_size + 2), (circle_x, circle_y + arrow_size)],
                  fill=arrow_color, width=line_width)

    return img

# 生成不同尺寸的图标
script_dir = os.path.dirname(os.path.abspath(__file__))
sizes = [16, 48, 128]

for size in sizes:
    icon = create_icon(size)
    output_path = os.path.join(script_dir, f'icon{size}.png')
    icon.save(output_path, 'PNG')
    print(f'Generated: icon{size}.png ({size}x{size})')

print('Done!')
