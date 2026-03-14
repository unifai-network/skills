import { PlaywrightCrawler, Dataset } from 'crawlee';
import fs from 'fs';
import path from 'path';

// Parse basic CLI args
const args = process.argv.slice(2);
let url = null;
let outputPath = '/tmp/crawlee_output.json';

for (let i = 0; i < args.length; i++) {
    if (args[i] === '--url' && args[i + 1]) url = args[i + 1];
    if (args[i] === '--output' && args[i + 1]) outputPath = args[i + 1];
}

if (!url) {
    console.error("Usage: node scrape.js --url <URL> [--output <path.json>]");
    process.exit(1);
}

// In-memory store for quick CLI dumping
let scrapedData = [];

console.log(`[Crawlee] Initializing stealth browser for: ${url}`);

const crawler = new PlaywrightCrawler({
    // Enable stealth to bypass anti-bot protections
    headless: true,
    browserPoolOptions: {
        useFingerprints: true, 
    },
    // Limiting to single request for CLI simplicity, but configurable
    maxRequestsPerCrawl: 1,

    async requestHandler({ page, request, log }) {
        log.info(`Processing ${request.url}...`);
        
        // Wait for network to be mostly idle to ensure JS rendering is done
        await page.waitForLoadState('networkidle');

        // Extract basic data (Title, all generic paragraph text, and main links)
        const title = await page.title();
        
        // Very generic extraction logic that applies to almost any site.
        // For specific sites, this function should be customized.
        const content = await page.evaluate(() => {
            const texts = Array.from(document.querySelectorAll('p, h1, h2, h3, article, section'))
                              .map(el => el.innerText.trim())
                              .filter(text => text.length > 20); // filter out noise
                              
            // Get unique texts
            return [...new Set(texts)].join('\n\n');
        });

        scrapedData.push({
            url: request.url,
            title: title,
            contentPreview: content.substring(0, 3000) + (content.length > 3000 ? '...' : ''), // Limit to 3k chars to prevent massive files
            scrapedAt: new Date().toISOString()
        });
        
        log.info(`Successfully extracted ${content.length} characters of text content.`);
    },
    
    // Let's not fail on the first error
    maxRequestRetries: 2,
});

await crawler.run([url]);

// Ensure output directory exists
const dir = path.dirname(outputPath);
if (!fs.existsSync(dir)){
    fs.mkdirSync(dir, { recursive: true });
}

fs.writeFileSync(outputPath, JSON.stringify(scrapedData, null, 2), 'utf-8');
console.log(`[Crawlee] ✅ Scraping complete. Data saved to ${outputPath}`);
