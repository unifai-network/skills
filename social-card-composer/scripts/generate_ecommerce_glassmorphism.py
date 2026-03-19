#!/usr/bin/env python3
import os
import math
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

def get_font_bold(size):
    try:
        return ImageFont.truetype("/tmp/openclaw/social_card_assets/SmileySans-Oblique_working.ttf", size)
    except:
        return ImageFont.load_default()

def get_font(size):
    try:
        return ImageFont.truetype("/tmp/openclaw/social_card_assets/chinese_font.ttf", size)
    except:
        return ImageFont.load_default()

def draw_round_rect(draw, bbox, radius, fill, outline=None, width=0):
    draw.rounded_rectangle(bbox, radius=radius, fill=fill, outline=outline, width=width)

def paste_with_shadow(base_img, img_rgba, x, y, scale=1.0, deg=0, glow_color=None, float_height=50):
    if scale != 1.0:
        new_w, new_h = int(img_rgba.width * scale), int(img_rgba.height * scale)
        img_rgba = img_rgba.resize((new_w, new_h), Image.Resampling.LANCZOS)
    if deg != 0:
        img_rgba = img_rgba.rotate(deg, expand=True, resample=Image.Resampling.BICUBIC)
    
    # Optional colored backlight glow
    if glow_color:
        glow = Image.new('RGBA', img_rgba.size, (0,0,0,0))
        try:
            mask = img_rgba.split()[3].point(lambda i: i * 0.8)
            glow.paste(glow_color, [0,0,glow.width,glow.height], mask)
            glow = glow.filter(ImageFilter.GaussianBlur(60))
            # Paste glow behind
            base_img.paste(glow, (int(x)-20, int(y)-20), glow)
        except: pass

    # Dark drop shadow (detached to create distance/floating effect)
    shadow = Image.new('RGBA', img_rgba.size, (0, 0, 0, 0))
    try:
        # Flatten the shadow to make it look like it's casting on a floor
        shadow_mask = img_rgba.split()[3].point(lambda i: i * 0.6)
        shadow.paste((0, 0, 0), [0, 0, img_rgba.width, img_rgba.height], shadow_mask)
        # Squash it vertically
        shadow = shadow.resize((img_rgba.width, int(img_rgba.height*0.3)), Image.Resampling.LANCZOS)
        shadow = shadow.filter(ImageFilter.GaussianBlur(30))
        # Place it far below the object
        base_img.paste(shadow, (int(x), int(y) + img_rgba.height - int(img_rgba.height*0.2) + float_height), shadow)
    except: pass
    
    # Finally paste the actual image
    base_img.paste(img_rgba, (int(x), int(y)), img_rgba)

def draw_glass_panel(base_img, draw, bbox, radius):
    x0, y0, x1, y1 = bbox
    panel_w, panel_h = x1 - x0, y1 - y0
    
    mask = Image.new('L', (panel_w, panel_h), 0)
    d_mask = ImageDraw.Draw(mask)
    d_mask.rounded_rectangle([0, 0, panel_w, panel_h], radius=radius, fill=255)
    
    bg_crop = base_img.crop((x0, y0, x1, y1))
    bg_crop = bg_crop.filter(ImageFilter.GaussianBlur(25))
    
    frost = Image.new('RGBA', (panel_w, panel_h), (255, 255, 255, 20))
    gradient = Image.new('RGBA', (panel_w, panel_h), (0,0,0,0))
    gd = ImageDraw.Draw(gradient)
    for i in range(panel_h):
        alpha = int(40 * (1 - i/panel_h))
        gd.line([(0, i), (panel_w, i)], fill=(255, 255, 255, alpha))
    
    glass = Image.alpha_composite(bg_crop.convert('RGBA'), frost)
    glass = Image.alpha_composite(glass, gradient)
    
    glass_final = Image.new('RGBA', (panel_w, panel_h))
    glass_final.paste(glass, (0,0), mask)
    base_img.paste(glass_final, (x0, y0), glass_final)
    
    draw.rounded_rectangle(bbox, radius=radius, outline=(255, 255, 255, 100), width=1)

def main():
    W, H = 1080, 1440
    img = Image.new('RGBA', (W, H), (12, 12, 15, 255))
    draw = ImageDraw.Draw(img)

    # 1. Background Stage Design (Creating Depth & Distance)
    # Deep ambient spotlight in the center
    spotlight = Image.new('RGBA', (W, H), (0,0,0,0))
    d_spot = ImageDraw.Draw(spotlight)
    # A huge central glowing orb far in the background
    d_spot.ellipse([W/2 - 400, H/2 - 400, W/2 + 400, H/2 + 400], fill=(216, 27, 96, 70)) 
    d_spot.ellipse([W/2 - 200, H/2 - 200, W/2 + 200, H/2 + 200], fill=(255, 150, 50, 90))
    spotlight = spotlight.filter(ImageFilter.GaussianBlur(150))
    img.paste(spotlight, (0,0), spotlight)
    
    # Adding an abstract floor horizon
    draw.line([(0, 1000), (W, 1000)], fill=(255,255,255,30), width=1)
    for i in range(1, 15):
        y_line = 1000 + (i * i * 2)
        if y_line < H:
            draw.line([(0, y_line), (W, y_line)], fill=(255,255,255, 20 - i), width=1)

    # Giant typography pushed to the very back
    font_bg = get_font_bold(280)
    bg_txt = Image.new('RGBA', (W, H), (0,0,0,0))
    d_bg_txt = ImageDraw.Draw(bg_txt)
    d_bg_txt.text((W/2, 450), "HONOR", fill=(255, 255, 255, 10), font=font_bg, anchor="mm")
    d_bg_txt.text((W/2, 700), "POWER", fill=(255, 255, 255, 10), font=font_bg, anchor="mm")
    img.paste(bg_txt, (0,0), bg_txt)

    # 2. Top Header Typography (Cleaned up, moved up)
    font_super = get_font_bold(100)
    font_sub_en = get_font_bold(35)
    font_zh = get_font(42)
    
    draw.text((W/2, 120), "电商超级补贴日", fill=(255, 255, 255, 255), font=font_zh, anchor="mm")
    draw_round_rect(draw, [W/2 - 180, 160, W/2 + 180, 210], 25, (216, 27, 96, 255))
    draw.text((W/2, 185), "UP TO 50% OFF", fill=(255, 255, 255, 255), font=font_sub_en, anchor="mm")

    # 3. Floating Products (Dead Center, Strong Visual Break)
    try:
        phone = Image.open("/tmp/openclaw/social_card_assets/real_phone_src_transparent.png").convert("RGBA")
        watch = Image.open("/tmp/openclaw/social_card_assets/real_watch_src_transparent.png").convert("RGBA")
        
        # Calculate scaling to fit the center stage
        ph_scale = 450.0 / phone.height
        wt_scale = 300.0 / watch.height
        
        # Center coordinates
        center_x, center_y = W/2, 600
        
        # Watch positioned slightly behind and to the left
        w_new_w, w_new_h = int(watch.width * wt_scale), int(watch.height * wt_scale)
        wx = center_x - w_new_w - 20
        wy = center_y - w_new_h/2 + 50
        paste_with_shadow(img, watch, wx, wy, scale=wt_scale, deg=-15, float_height=180, glow_color=(50, 150, 255, 80))
        
        # Phone positioned dead center, floating high
        p_new_w, p_new_h = int(phone.width * ph_scale), int(phone.height * ph_scale)
        px = center_x - p_new_w/2 + 60
        py = center_y - p_new_h/2 - 50
        paste_with_shadow(img, phone, px, py, scale=ph_scale, deg=10, float_height=250, glow_color=(255, 50, 100, 60))
        
    except Exception as e:
        print("Images missing:", e)

    # 4. Glassmorphism Info Panels (Moved perfectly below the stage, out of the way)
    font_b_title = get_font_bold(65)
    font_b_txt = get_font(24)
    
    def render_glass_card(x, y, num, lines):
        bw, bh = 460, 230
        draw_glass_panel(img, draw, [x, y, x+bw, y+bh], radius=25)
        
        # Big Number overlay right side
        draw.text((x + bw - 110, y + 20), num, fill=(255, 255, 255, 20), font=get_font_bold(160))
        
        draw.line([(x+30, y+35), (x+80, y+35)], fill=(216, 27, 96, 255), width=5)
        
        ty = y + 60
        for l in lines:
            draw.text((x+30, ty), l, fill=(230, 230, 240, 255), font=font_b_txt)
            ty += 38

    # Card 1 and 2 aligned neatly near the bottom
    render_glass_card(50, 1100, "01", ["通过专属链接注册APP", "首次登录即得2000点超级积分", "全场配件通用无门槛抵扣"])
    render_glass_card(570, 1100, "02", ["积分可叠加活动双重福利", "享受数码家电超低折扣价", "仅限官方电商小程序使用及核销"])

    # 5. Final Noise / Texture Overlay
    noise = Image.effect_noise((W, H), 30).convert('L')
    noise_rgba = Image.new('RGBA', (W, H))
    noise_rgba.putalpha(noise)
    img.paste(noise_rgba, (0,0), noise_rgba.point(lambda p: p * 0.04))

    img.convert('RGB').save('/tmp/openclaw/ecommerce_center_card.jpg', quality=95)
    print("Centered Pro Poster generated at: /tmp/openclaw/ecommerce_center_card.jpg")

if __name__ == '__main__':
    main()
