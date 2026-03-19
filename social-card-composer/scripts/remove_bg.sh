#!/bin/bash
# Removes backgrounds smoothly with U2Net and Alpha Matting

if [ "$#" -lt 1 ]; then
    echo "Usage: $0 <input_image_1> [input_image_2] ..."
    exit 1
fi

mkdir -p /tmp/openclaw/social_card_assets

for img in "$@"; do
    filename=$(basename -- "$img")
    name="${filename%.*}"
    out_path="/tmp/openclaw/social_card_assets/${name}_transparent.png"
    echo "Processing $img -> $out_path"
    
    # We use basic U2Net with erosion and alpha matting
    rembg i -a -ae 10 "$img" "$out_path" >/dev/null 2>&1
    echo "Saved: $out_path"
done
