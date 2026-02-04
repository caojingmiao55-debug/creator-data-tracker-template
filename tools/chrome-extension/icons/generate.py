#!/usr/bin/env python3
import cairosvg
import os

svg_template = '''<svg width="{size}" height="{size}" viewBox="0 0 128 128" fill="none" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="grad1" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#6366f1;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#8b5cf6;stop-opacity:1" />
    </linearGradient>
  </defs>
  <rect x="4" y="4" width="120" height="120" rx="28" fill="url(#grad1)"/>
  <rect x="28" y="70" width="16" height="34" rx="4" fill="white" opacity="0.9"/>
  <rect x="56" y="50" width="16" height="54" rx="4" fill="white" opacity="0.9"/>
  <rect x="84" y="30" width="16" height="74" rx="4" fill="white" opacity="0.9"/>
  <circle cx="100" cy="28" r="18" fill="white"/>
  <path d="M94 28 L100 22 L106 28 M100 22 L100 34" stroke="#6366f1" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
</svg>'''

sizes = [16, 48, 128]
script_dir = os.path.dirname(os.path.abspath(__file__))

for size in sizes:
    svg = svg_template.format(size=size)
    output_path = os.path.join(script_dir, f'icon{size}.png')
    cairosvg.svg2png(bytestring=svg.encode(), write_to=output_path, output_width=size, output_height=size)
    print(f'Generated: icon{size}.png')

print('Done!')
