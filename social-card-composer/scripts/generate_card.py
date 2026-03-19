#!/usr/bin/env python3
import os
import sys
import argparse
import subprocess
from PIL import Image, ImageDraw, ImageFont, ImageFilter

def download_assets(bg_url):
    assets_dir = "/tmp/openclaw/social_card_assets"
    os.makedirs(assets_dir, exist_ok=True)
    
    bg_path = os.path.join(assets_dir, "custom_bg.jpg")
    font_path_title = os.path.join(assets_dir, "SmileySans-Oblique_working.ttf")
    font_path_text = os.path.join(assets_dir, "chinese_font.ttf")
    
    if bg_url:
        subprocess.run(["curl", "-sL", bg_url, "-o", bg_path])
    elif not os.path.exists(bg_path):
        subprocess.run(["curl", "-sL", "https://images.unsplash.com/photo-1542831371-29b0f74f9713?ixlib=rb-4.0.3&auto=format&fit=crop&w=1200&q=80", "-o", bg_path])
        
    if not os.path.exists(font_path_title):
        subprocess.run(["curl", "-sL", "https://github.com/atelier-anchor/smiley-sans/raw/main/v2.0.1/SmileySans-Oblique.ttf", "-o", font_path_title])
        
    if not os.path.exists(font_path_text):
        subprocess.run(["curl", "-sL", "https://github.com/lxgw/LxgwWenKai/releases/download/v1.330/LXGWWenKai-Bold.ttf", "-o", font_path_text])
        
    return bg_path, font_path_title, font_path_text

def get_font_fallback(font_path, size):
    try:
        return ImageFont.truetype(font_path, size)
    except Exception as e:
        print(f"Font warning: could not load {font_path}. Using fallback.")
        # Fallback to system fonts to prevent squares/missing characters
        try:
            return ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", size)
        except:
            return ImageFont.load_default()

def draw_info_box(canvas, draw, font_title_path, font_txt_path, x, y, num, title, details):
    box_w, box_h = 510, 240 # Adjusted height to fit content accurately without overlapping
    box = Image.new('RGBA', (box_w, box_h), (255, 255, 255, 230))
    
    # Custom rounded rectangle mask
    mask = Image.new('L', (box_w, box_h), 0)
    draw_mask = ImageDraw.Draw(mask)
    draw_mask.rounded_rectangle([0, 0, box_w, box_h], radius=25, fill=255)
    
    temp_box = Image.new('RGBA', (box_w, box_h))
    temp_box.paste(box, (0,0), mask=mask)
    canvas.paste(temp_box, (x, y), mask=mask)
    
    # Load fonts with safe fallback
    f_num = get_font_fallback(font_title_path, 80)
    f_title_obj = get_font_fallback(font_title_path, 38)
    f_txt_obj = get_font_fallback(font_txt_path, 26)
        
    if num:
        # Number Watermark
        draw.text((x + 30, y + 15), num, fill=(235, 235, 235), font=f_num) 
        
    draw.text((x + 40, y + 40), title, fill=(40, 40, 40), font=f_title_obj)
    draw.line([(x+40, y+95), (x+470, y+95)], fill=(200, 200, 200), width=3)
    
    y_offset = y + 115
    for line in details:
        if line and line.strip():
            # Using clean bullet point symbols instead of square blocks to avoid font render issues
            draw.text((x + 40, y_offset), f"•  {line}", fill=(70, 70, 70), font=f_txt_obj)
            y_offset += 38

def paste_with_shadow(base_img, img_rgba, x, y):
    shadow = Image.new('RGBA', img_rgba.size, (0, 0, 0, 0))
    # Extract alpha and dampen for shadow
    try:
        shadow_mask = img_rgba.split()[3].point(lambda i: i * 0.4)
    except:
        return
    shadow.paste((0, 0, 0), [0, 0, img_rgba.width, img_rgba.height], shadow_mask)
    shadow = shadow.filter(ImageFilter.GaussianBlur(15))
    base_img.paste(shadow, (x+15, y+20), shadow)
    base_img.paste(img_rgba, (x, y), img_rgba)

def build_comparison_layout(args, bg_path, font_title, font_txt):
    bg = Image.open(bg_path).convert("RGBA")
    img1 = Image.open(args.img1).convert("RGBA")
    img2 = Image.open(args.img2).convert("RGBA")
    
    W, H = 1200, 1600
    bg = bg.resize((max(W, int(H * bg.width / bg.height)), H), Image.Resampling.LANCZOS)
    bg = bg.crop((0, 0, W, H))
    bg = bg.filter(ImageFilter.GaussianBlur(8))
    
    overlay = Image.new('RGBA', (W, H), (242, 240, 235, 220))
    canvas = Image.alpha_composite(bg, overlay)
    draw = ImageDraw.Draw(canvas)

    f_main = get_font_fallback(font_title, 75)
    f_sub = get_font_fallback(font_title, 36)

    # Dynamic Center Alignment for Title
    title_w = draw.textlength(args.maintitle, font=f_main)
    draw.text(((W - title_w)/2, 60), args.maintitle, fill=(30, 30, 30), font=f_main)
    
    if args.subtitle:
        sub_w = draw.textlength(args.subtitle, font=f_sub)
        draw.rounded_rectangle([(W - sub_w)/2 - 30, 160, (W + sub_w)/2 + 30, 220], radius=15, fill=(40, 40, 40))
        draw.text(((W - sub_w)/2, 172), args.subtitle, fill=(255, 255, 255), font=f_sub)

    # Calculate precise object heights to prevent covering text
    # Top text limits at y=230. Bot text starts at y=1250
    # Available area: 230 to 1250 (1020px height)
    target_h = 980
    
    ratio1 = target_h / img1.height
    new_w1 = int(img1.width * ratio1)
    m1 = img1.resize((new_w1, target_h), Image.Resampling.LANCZOS)
    
    ratio2 = target_h / img2.height
    new_w2 = int(img2.width * ratio2)
    m2 = img2.resize((new_w2, target_h), Image.Resampling.LANCZOS)

    y_models = 250
    # Center each model in their respective half
    x1 = int(300 - new_w1/2) # left half center
    x2 = int(900 - new_w2/2) # right half center
    
    paste_with_shadow(canvas, m1, x1, y_models)
    paste_with_shadow(canvas, m2, x2, y_models)

    # Place info boxes strictly at the bottom
    box_y = 1280
    
    b1_desc = [args.box1_desc1, args.box1_desc2, args.box1_desc3]
    b2_desc = [args.box2_desc1, args.box2_desc2, args.box2_desc3]
    
    draw_info_box(canvas, draw, font_title, font_txt, 70, box_y, "01", args.box1_title, b1_desc)
    draw_info_box(canvas, draw, font_title, font_txt, 620, box_y, "02", args.box2_title, b2_desc)

    canvas.convert("RGB").save(args.output, "JPEG", quality=95)
    print(f"✅ Success! Created comparison layout at: {args.output}")

def main():
    parser = argparse.ArgumentParser(description="Universal Social Media Poster Generator")
    parser.add_argument("--img1", required=True, help="Transparent image 1")
    parser.add_argument("--img2", help="Transparent image 2 (triggers 2-item layout)")
    parser.add_argument("--maintitle", default="SOCIAL SHOWCASE", help="Main Title")
    parser.add_argument("--subtitle", default="Generated natively with AI", help="Sub Title")
    parser.add_argument("--bg-url", help="URL of background image")
    parser.add_argument("--box1-title", default="ITEM 01", help="Box 1 Title")
    parser.add_argument("--box1-desc1", default="Overview description here")
    parser.add_argument("--box1-desc2", default="")
    parser.add_argument("--box1-desc3", default="")
    parser.add_argument("--box2-title", default="ITEM 02", help="Box 2 Title")
    parser.add_argument("--box2-desc1", default="Overview description here")
    parser.add_argument("--box2-desc2", default="")
    parser.add_argument("--box2-desc3", default="")
    parser.add_argument("--output", default="/tmp/openclaw/final_social_card.jpg")
    
    args = parser.parse_args()
    
    bg_path, font_title, font_txt = download_assets(args.bg_url)
    
    if args.img2:
        build_comparison_layout(args, bg_path, font_title, font_txt)
    else:
        # Fallback single image - mostly skip for now
        print("Running single layout feature (stub)")
        pass

if __name__ == '__main__':
    main()
