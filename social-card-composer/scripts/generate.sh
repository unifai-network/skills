#!/bin/bash
# Wrapper script to run either Satori (default) or Pillow engine for social card layout.

ENGINE="satori"
ARGS_ONLY=()

while [[ $# -gt 0 ]]; do
  case $1 in
    --engine)
      ENGINE="$2"
      shift 2
      ;;
    *)
      ARGS_ONLY+=("$1")
      shift
      ;;
  esac
done

if [ "$ENGINE" == "satori" ]; then
    echo "====================================="
    echo "🚀 Using Satori (HTML/CSS) Render Engine"
    echo "====================================="
    
    TITLE="SOCIAL SHOWCASE"
    SUBTITLE="Generated natively with AI"
    IMG1=""
    CONTENT=""
    OUTPUT="/tmp/final_social_card_satori.png"
    
    # Re-parse array manually to build command string
    set -- "${ARGS_ONLY[@]}"
    while [[ $# -gt 0 ]]; do
      case $1 in
        --img1) IMG1="$2"; shift 2 ;;
        --maintitle) TITLE="$2"; shift 2 ;;
        --subtitle) SUBTITLE="$2"; shift 2 ;;
        --output) OUTPUT="$2"; shift 2 ;;
        --box1-title) CONTENT+="- **$2**\n"; shift 2 ;;
        --box1-desc1) CONTENT+="  - $2\n"; shift 2 ;;
        --box1-desc2) if [ -n "$2" ]; then CONTENT+="  - $2\n"; fi; shift 2 ;;
        --box1-desc3) if [ -n "$2" ]; then CONTENT+="  - $2\n"; fi; shift 2 ;;
        --box2-title) CONTENT+="\n- **$2**\n"; shift 2 ;;
        --box2-desc1) CONTENT+="  - $2\n"; shift 2 ;;
        --box2-desc2) if [ -n "$2" ]; then CONTENT+="  - $2\n"; fi; shift 2 ;;
        --box2-desc3) if [ -n "$2" ]; then CONTENT+="  - $2\n"; fi; shift 2 ;;
        *) shift 2 ;;
      esac
    done
    
    # Delegate rendering
    cd ~/.openclaw/workspace/skills/satori-poster-creator
    node scripts/generate.js \
        --theme polaroid-photo \
        --title "$TITLE" \
        --subtitle "$SUBTITLE" \
        --content "$CONTENT" \
        --image "$IMG1" \
        --output "$OUTPUT"
        
    echo "✅ Success! Created Satori layout at: $OUTPUT"
    
elif [ "$ENGINE" == "pillow" ]; then
    echo "====================================="
    echo "🐍 Using Pillow (Python Canvas) Render Engine"
    echo "====================================="
    ~/.openclaw/workspace/skills/social-card-composer/scripts/generate_card.py "${ARGS_ONLY[@]}"
else
    echo "Unknown engine: $ENGINE. Use 'satori' or 'pillow'."
    exit 1
fi
