#!/usr/bin/env python3
"""
Social Card Composer — Pillow Engine
智能布局：根据输入图片实际尺寸自动计算最佳画布比例和元素分配
"""
import os
import sys
import argparse
import subprocess
from PIL import Image, ImageDraw, ImageFont, ImageFilter


# ============================================================
#  资产下载
# ============================================================

def download_assets(bg_url):
    assets_dir = "/tmp/openclaw/social_card_assets"
    os.makedirs(assets_dir, exist_ok=True)

    bg_path = os.path.join(assets_dir, "custom_bg.jpg")
    font_path_title = os.path.join(assets_dir, "SmileySans-Oblique_working.ttf")
    font_path_text = os.path.join(assets_dir, "chinese_font.ttf")

    if bg_url:
        subprocess.run(["curl", "-sL", bg_url, "-o", bg_path])
    elif not os.path.exists(bg_path):
        subprocess.run(["curl", "-sL",
            "https://images.unsplash.com/photo-1542831371-29b0f74f9713?auto=format&fit=crop&w=1200&q=80",
            "-o", bg_path])

    if not os.path.exists(font_path_title):
        subprocess.run(["curl", "-sL",
            "https://github.com/atelier-anchor/smiley-sans/raw/main/v2.0.1/SmileySans-Oblique.ttf",
            "-o", font_path_title])

    if not os.path.exists(font_path_text):
        subprocess.run(["curl", "-sL",
            "https://github.com/lxgw/LxgwWenKai/releases/download/v1.330/LXGWWenKai-Bold.ttf",
            "-o", font_path_text])

    return bg_path, font_path_title, font_path_text


# ============================================================
#  字体 & 绘图工具
# ============================================================

def get_font(font_path, size):
    """安全加载字体，自动 fallback"""
    for path in [font_path, "/tmp/openclaw/social_card_assets/chinese_font.ttf",
                 "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"]:
        try:
            return ImageFont.truetype(path, size)
        except:
            continue
    return ImageFont.load_default()


def paste_with_shadow(canvas, img_rgba, x, y, blur=12, offset=10, opacity=0.35):
    """贴图 + 投影"""
    try:
        alpha = img_rgba.split()[3]
    except IndexError:
        canvas.paste(img_rgba, (x, y))
        return
    shadow_mask = alpha.point(lambda i: int(i * opacity))
    shadow = Image.new('RGBA', img_rgba.size, (0, 0, 0, 0))
    shadow.paste((0, 0, 0), [0, 0, img_rgba.width, img_rgba.height], shadow_mask)
    shadow = shadow.filter(ImageFilter.GaussianBlur(blur))
    canvas.paste(shadow, (x + offset, y + offset + 5), shadow)
    canvas.paste(img_rgba, (x, y), img_rgba)


def fit_image(img, max_w, max_h):
    """等比缩放到 max_w × max_h 以内"""
    if img.width == 0 or img.height == 0:
        return img
    ratio = min(max_w / img.width, max_h / img.height)
    nw, nh = max(1, int(img.width * ratio)), max(1, int(img.height * ratio))
    return img.resize((nw, nh), Image.Resampling.LANCZOS)


def draw_compact_info(draw, font_path, x, y, w, num, title, details):
    """紧凑型底部信息条（自适应高度）"""
    f_num = get_font(font_path, 36)
    f_title = get_font(font_path, 24)
    f_desc = get_font(font_path, 18)

    # 半透明背景条
    line_y = y
    if num:
        draw.text((x, line_y), num, fill=(200, 200, 200), font=f_num)
    draw.text((x + 45, line_y + 8), title, fill=(50, 50, 50), font=f_title)
    line_y += 40
    draw.line([(x, line_y), (x + w, line_y)], fill=(200, 200, 200), width=1)
    line_y += 8
    for d in details:
        if d and d.strip():
            draw.text((x, line_y), f"• {d}", fill=(90, 90, 90), font=f_desc)
            line_y += 26
    return line_y - y  # 返回实际用了多少高度


# ============================================================
#  智能布局计算
# ============================================================

def compute_layout(images, has_title=True, has_subtitle=True, has_info=True):
    """
    根据输入图片自动决定画布大小和区域分配。
    返回 dict: { W, H, title_h, subject_zone, info_h, padding }
    """
    W = 1080  # 固定宽度（小红书/Instagram 标准）

    n = len(images)
    padding = 30

    # 标题区
    title_h = 0
    if has_title:
        title_h += 70   # 主标题
    if has_subtitle:
        title_h += 50   # 副标题
    if title_h > 0:
        title_h += 20   # 标题和主体之间间距

    # 信息区（底部）
    info_h = 100 if has_info else 0

    # 计算主体图片区域需要多少空间
    if n == 0:
        subject_h = 600
    elif n == 1:
        img = images[0]
        # 单图：横幅 → 给高度少一点；竖图 → 给高度多一点
        aspect = img.width / max(img.height, 1)
        avail_w = W - padding * 2
        # 按可用宽度缩放后看高度
        scaled_h = int(avail_w / max(aspect, 0.3))
        subject_h = min(scaled_h, 1200)  # 最高不超过 1200
        subject_h = max(subject_h, 400)  # 最矮不低于 400
    else:
        # 多图：取最高那张的等比缩放高度
        per_w = (W - padding * (n + 1)) // n
        max_h = 0
        for img in images:
            aspect = img.width / max(img.height, 1)
            h = int(per_w / max(aspect, 0.3))
            max_h = max(max_h, h)
        subject_h = min(max_h, 1000)
        subject_h = max(subject_h, 400)

    # 总高度
    H = title_h + subject_h + info_h + padding * 2
    # 约束到合理范围
    H = max(H, 800)
    H = min(H, 1620)

    # 让高度是偶数（某些编码器需要）
    H = H + (H % 2)

    return {
        "W": W,
        "H": H,
        "title_h": title_h,
        "subject_top": title_h + padding,
        "subject_h": H - title_h - info_h - padding * 2,
        "info_h": info_h,
        "info_top": H - info_h - padding // 2,
        "padding": padding,
    }


# ============================================================
#  单图布局
# ============================================================

def build_single_layout(args, bg_path, font_title, font_txt):
    img1 = Image.open(args.img1).convert("RGBA")

    has_title = bool(args.maintitle and args.maintitle.strip())
    has_sub = bool(args.subtitle and args.subtitle.strip())
    has_info = bool(args.box1_title and args.box1_title.strip() and args.box1_title != "ITEM 01")

    layout = compute_layout([img1], has_title, has_sub, has_info)
    W, H = layout["W"], layout["H"]
    pad = layout["padding"]

    # 背景
    bg = Image.open(bg_path).convert("RGBA")
    bg_ratio = max(W / bg.width, H / bg.height)
    bg = bg.resize((int(bg.width * bg_ratio) + 1, int(bg.height * bg_ratio) + 1), Image.Resampling.LANCZOS)
    bg = bg.crop((0, 0, W, H))
    bg = bg.filter(ImageFilter.GaussianBlur(12))

    overlay = Image.new('RGBA', (W, H), (250, 248, 243, 200))
    canvas = Image.alpha_composite(bg, overlay)
    draw = ImageDraw.Draw(canvas)

    # 标题
    cur_y = pad
    if has_title:
        f_main = get_font(font_title, 52)
        tw = draw.textlength(args.maintitle, font=f_main)
        draw.text(((W - tw) / 2, cur_y), args.maintitle, fill=(30, 30, 30), font=f_main)
        cur_y += 65

    if has_sub:
        f_sub = get_font(font_title, 26)
        sw = draw.textlength(args.subtitle, font=f_sub)
        draw.rounded_rectangle([(W - sw) / 2 - 18, cur_y, (W + sw) / 2 + 18, cur_y + 38], radius=10, fill=(40, 40, 40))
        draw.text(((W - sw) / 2, cur_y + 6), args.subtitle, fill=(255, 255, 255), font=f_sub)
        cur_y += 50

    # 主体图片
    subj_top = layout["subject_top"]
    subj_h = layout["subject_h"]
    avail_w = W - pad * 2

    m1 = fit_image(img1, avail_w, subj_h)
    x1 = (W - m1.width) // 2
    y1 = subj_top + (subj_h - m1.height) // 2
    paste_with_shadow(canvas, m1, x1, y1)

    # 底部信息
    if has_info:
        details = [d for d in [args.box1_desc1, args.box1_desc2, args.box1_desc3] if d and d.strip()]
        draw_compact_info(draw, font_txt, pad + 10, layout["info_top"], W - pad * 2 - 20,
                          "01", args.box1_title, details)

    canvas.convert("RGB").save(args.output, "JPEG", quality=95)
    print(f"✅ Single layout: {W}×{H} → {args.output}")


# ============================================================
#  双图对比布局
# ============================================================

def build_comparison_layout(args, bg_path, font_title, font_txt):
    img1 = Image.open(args.img1).convert("RGBA")
    img2 = Image.open(args.img2).convert("RGBA")

    has_title = bool(args.maintitle and args.maintitle.strip())
    has_sub = bool(args.subtitle and args.subtitle.strip())

    layout = compute_layout([img1, img2], has_title, has_sub, has_info=True)
    W, H = layout["W"], layout["H"]
    pad = layout["padding"]

    # 背景
    bg = Image.open(bg_path).convert("RGBA")
    bg_ratio = max(W / bg.width, H / bg.height)
    bg = bg.resize((int(bg.width * bg_ratio) + 1, int(bg.height * bg_ratio) + 1), Image.Resampling.LANCZOS)
    bg = bg.crop((0, 0, W, H))
    bg = bg.filter(ImageFilter.GaussianBlur(8))

    overlay = Image.new('RGBA', (W, H), (242, 240, 235, 200))
    canvas = Image.alpha_composite(bg, overlay)
    draw = ImageDraw.Draw(canvas)

    # 标题
    cur_y = pad
    if has_title:
        f_main = get_font(font_title, 52)
        tw = draw.textlength(args.maintitle, font=f_main)
        draw.text(((W - tw) / 2, cur_y), args.maintitle, fill=(30, 30, 30), font=f_main)
        cur_y += 65

    if has_sub:
        f_sub = get_font(font_title, 26)
        sw = draw.textlength(args.subtitle, font=f_sub)
        draw.rounded_rectangle([(W - sw) / 2 - 18, cur_y, (W + sw) / 2 + 18, cur_y + 38], radius=10, fill=(40, 40, 40))
        draw.text(((W - sw) / 2, cur_y + 6), args.subtitle, fill=(255, 255, 255), font=f_sub)
        cur_y += 50

    # 主体区域
    subj_top = layout["subject_top"]
    subj_h = layout["subject_h"]
    gap = 20
    half_w = (W - pad * 2 - gap) // 2

    m1 = fit_image(img1, half_w, subj_h)
    m2 = fit_image(img2, half_w, subj_h)

    # 底部对齐
    y1 = subj_top + (subj_h - m1.height)
    y2 = subj_top + (subj_h - m2.height)
    x1 = pad + (half_w - m1.width) // 2
    x2 = pad + half_w + gap + (half_w - m2.width) // 2

    paste_with_shadow(canvas, m1, x1, y1)
    paste_with_shadow(canvas, m2, x2, y2)

    # VS 分割线（中间淡灰竖线 + VS 标签）
    cx = W // 2
    line_top = subj_top + 40
    line_bot = subj_top + subj_h - 40
    draw.line([(cx, line_top), (cx, line_bot)], fill=(200, 200, 200, 120), width=2)
    f_vs = get_font(font_title, 22)
    draw.rounded_rectangle([cx - 22, (line_top + line_bot) // 2 - 16, cx + 22, (line_top + line_bot) // 2 + 16],
                           radius=8, fill=(60, 60, 60))
    draw.text((cx - 11, (line_top + line_bot) // 2 - 12), "VS", fill=(255, 255, 255), font=f_vs)

    # 底部信息
    info_y = layout["info_top"]
    b1_desc = [d for d in [args.box1_desc1, args.box1_desc2, args.box1_desc3] if d and d.strip()]
    b2_desc = [d for d in [args.box2_desc1, args.box2_desc2, args.box2_desc3] if d and d.strip()]

    draw_compact_info(draw, font_txt, pad + 10, info_y, half_w - 20, "01", args.box1_title, b1_desc)
    draw_compact_info(draw, font_txt, pad + half_w + gap + 10, info_y, half_w - 20, "02", args.box2_title, b2_desc)

    canvas.convert("RGB").save(args.output, "JPEG", quality=95)
    print(f"✅ Comparison layout: {W}×{H} → {args.output}")


# ============================================================
#  CLI 入口
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="Social Card Composer — Smart Layout Engine")
    parser.add_argument("--img1", required=True, help="Transparent image 1")
    parser.add_argument("--img2", help="Transparent image 2 (triggers comparison layout)")
    parser.add_argument("--maintitle", default="", help="Main title")
    parser.add_argument("--subtitle", default="", help="Subtitle")
    parser.add_argument("--bg-url", help="Custom background image URL")
    parser.add_argument("--box1-title", default="ITEM 01")
    parser.add_argument("--box1-desc1", default="")
    parser.add_argument("--box1-desc2", default="")
    parser.add_argument("--box1-desc3", default="")
    parser.add_argument("--box2-title", default="ITEM 02")
    parser.add_argument("--box2-desc1", default="")
    parser.add_argument("--box2-desc2", default="")
    parser.add_argument("--box2-desc3", default="")
    parser.add_argument("--output", default="/tmp/openclaw/final_social_card.jpg")
    args = parser.parse_args()

    bg_path, font_title, font_txt = download_assets(args.bg_url)

    if args.img2:
        build_comparison_layout(args, bg_path, font_title, font_txt)
    else:
        build_single_layout(args, bg_path, font_title, font_txt)


if __name__ == '__main__':
    main()
