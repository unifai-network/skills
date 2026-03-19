#!/usr/bin/env node
const fs = require('fs');
const { execSync } = require('child_process');

function parseArgs() {
    const args = {};
    const cmdArgs = process.argv.slice(2);
    for (let i = 0; i < cmdArgs.length; i += 2) {
        if (cmdArgs[i].startsWith('--')) {
            args[cmdArgs[i].slice(2)] = cmdArgs[i + 1];
        }
    }
    return args;
}

function main() {
    const args = parseArgs();
    if (!args.img1) {
        console.error("Usage: node generate_card_satori.js --img1 <path> [--img2 <path>] --maintitle <title> ...");
        process.exit(1);
    }
    
    // We will build a command that delegates to satori-poster-creator.
    // For a comparison, we map the fields to the polaroid or geometric template of Satori.
    
    let title = args.maintitle || "SOCIAL SHOWCASE";
    let subtitle = args.subtitle || "Generated natively with AI";
    
    // Format the content
    let content = `**${args['box1-title'] || 'ITEM 01'}**\n`;
    content += `- ${args['box1-desc1'] || ''}\n`;
    if (args['box1-desc2']) content += `- ${args['box1-desc2']}\n`;
    if (args['box1-desc3']) content += `- ${args['box1-desc3']}\n\n`;
    
    if (args.img2) {
        content += `**${args['box2-title'] || 'ITEM 02'}**\n`;
        content += `- ${args['box2-desc1'] || ''}\n`;
        if (args['box2-desc2']) content += `- ${args['box2-desc2']}\n`;
        if (args['box2-desc3']) content += `- ${args['box2-desc3']}\n`;
    }
    
    const outPath = args.output || "/tmp/openclaw/final_social_card_satori.png";
    
    // We use the 'polaroid-photo' theme from the satori-poster-creator skill which takes an image and formats text nicely below it.
    // Note: Since we have 2 images optionally, Satori's default polaroid template might only take one main image.
    // Let's pass img1 as the main image.
    
    const cmd = `cd ~/.openclaw/workspace/skills/satori-poster-creator && node scripts/generate_satori_card.js \\
        --theme polaroid-photo \\
        --title "${title}" \\
        --subtitle "${subtitle}" \\
        --content "${content.replace(/\n/g, '\\n')}" \\
        --image "${args.img1}" \\
        --output "${outPath}"`;
        
    console.log("Delegating layout to Satori Poster Creator engine...");
    try {
        execSync(cmd, { stdio: 'inherit' });
        console.log(`✅ Success! Created Satori layout at: ${outPath}`);
    } catch (e) {
        console.error("Satori rendering failed:", e.message);
        process.exit(1);
    }
}

main();
