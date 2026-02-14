# Universal-Crawler - Blazing Fast Async Web Crawler

⚡ **SUPER FAST** async web crawler optimised for concurrency and speed.

## Features

- 🚀 **Blazing Fast** - Async/await with concurrent downloads (10-50x faster than sync!)
- 🕷️ **Full Web Crawler** - Crawls through multiple pages following links
- 📊 **Configurable Depth** - Control how deep the crawler goes (0 = single page, 1+ = follow links)
- 🎯 **Multiple File Types** - Download specific extensions, multiple types, or ALL files (`*`)
- 🔍 **Content Search** - Find pages containing regex patterns and save matching HTML
- ⚡ **Concurrent Requests** - Download multiple files and pages simultaneously (default: 10 concurrent)
- 🌐 **Domain Control** - Stay on the same domain or allow external links
- 📁 **Organized Output** - Files saved in `output/<domain>/<file_type>/` structure
- 📈 **Progress Tracking** - Real-time crawl progress and statistics
- 🔓 **Fast by Default** - Ignores robots.txt for speed (use `--respect-robots` to enable)

## Installation

### 1. Clone or Download this Repository

```bash
cd PyImageDL
```

### 2. Create a Virtual Environment

#### On Windows

```bash
python -m venv .venv
.venv\Scripts\activate
```

#### On macOS/Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

## Usage

### Basic Syntax

```bash
python main.py <url> <file_extension> [options]
```

### Quick Examples

**Download GIFs from a single page:**

```bash
python main.py https://example.com/gallery ".gif"
```

**Download multiple file types (comma-separated):**

```bash
python main.py https://example.com ".jpg,.png,.gif,.webp"
```

**Download ALL files from a site:**

```bash
python main.py https://example.com "*"
```

**Search for pages containing specific content:**

```bash
python main.py https://example.com ".jpg" --content "API key|password|secret"
```

**Crawl 3 levels deep, download all JPGs:**

```bash
python main.py https://example.com ".jpg" --depth 3
```

**Download PNGs, crawl max 50 pages:**

```bash
python main.py https://example.com ".png" --depth 2 --max-pages 50
```

### Command-Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `url` | Starting URL to crawl (required) | - |
| `extension` | File extension(s): ".gif", ".jpg,.png", or "*" for all | `*` |
| `-d, --depth` | Maximum crawl depth (0 = single page only) | 2 |
| `-p, --max-pages` | Maximum number of pages to crawl | 100 |
| `-c, --concurrent` | Maximum concurrent requests (higher = faster!) | 10 |
| `--delay` | Delay between requests in seconds | 0.1 |
| `--content` | Regex pattern to search in pages (saves matching HTML) | none |
| `--no-domain-restriction` | Allow crawling to external domains | false |
| `--respect-robots` | Respect robots.txt rules (slower) | false |

### Advanced Examples

**BLAZING FAST: 50 concurrent connections, no delay:**

```bash
python main.py https://example.com ".jpg" --concurrent 50 --delay 0
```

**Download ALL image types:**

```bash
python main.py https://example.com ".jpg,.jpeg,.png,.gif,.webp,.svg,.bmp"
```

**Search for sensitive data (saves pages with matches):**

```bash
python main.py https://example.com "*" --content "password|api[_-]?key|secret|token" --depth 3
```

**Deep crawl for everything (depth 5, up to 500 pages):**

```bash
python main.py https://example.com "*" --depth 5 --max-pages 500
```

**Respectful crawling (slower but polite):**

```bash
python main.py https://example.com ".gif" --respect-robots --delay 1.0 --concurrent 3
```

**Maximum speed mode (use on your own sites!):**

```bash
python main.py https://example.com "*" --concurrent 100 --delay 0 --no-domain-restriction
```

## Output Structure

Downloaded files are organized as:

```
output/
└── <shortened_url>/
    └── <file_extension>/
        ├── file1.gif
        ├── file2.gif
        └── file3.gif
```

**Example:**
Crawling `https://example.com/gallery` for `.gif` files saves to:

```
output/example.com_gallery/gif/
```

## How It Works

1. **Async Initialization** - Creates aiohttp session with connection pool
2. **Concurrent Crawling** - Fetches multiple pages simultaneously (controlled by `--concurrent`)
3. **Extract Links** - Finds all links and files on each page
4. **Parallel Downloads** - Downloads all files from a page at once
5. **Smart Queue** - O(1) duplicate checking with sets (no slow loops!)
6. **Follow Links** - If depth > 0, adds new pages to queue
7. **Speed Control** - Respects max depth, max pages, and concurrent limits

## Common File Extensions

- **Images**: `.jpg`, `.jpeg`, `.png`, `.gif`, `.webp`, `.svg`, `.bmp`
- **Videos**: `.mp4`, `.webm`, `.avi`, `.mov`, `.mkv`
- **Audio**: `.mp3`, `.wav`, `.ogg`, `.flac`
- **Documents**: `.pdf`, `.doc`, `.docx`, `.txt`
- **Archives**: `.zip`, `.rar`, `.tar`, `.gz`

## Tips & Best Practices

### 🚀 Maximum Speed

- Increase `--concurrent` to 50-100 for blazing fast downloads (on your own sites!)
- Use `--delay 0` to remove delays between requests
- Default settings ignore robots.txt for speed
- The async implementation is 10-50x faster than the old sync version!

### 🚦 Be Respectful (When Crawling Others' Sites)

- Use `--respect-robots` to check robots.txt
- Lower `--concurrent` to 3-5 for polite crawling
- Add `--delay 1.0` or higher for large crawls
- Don't crawl the same site repeatedly in short periods

### ⚡ Performance Tips

- Start with `--depth 0` to test on a single page first
- Use `--max-pages` to limit crawl size
- Higher `--concurrent` = faster, but more load on the server
- Use `--concurrent 10 --delay 0.1` as a good balance

### 🎯 Targeting

- Use `--depth 0` for single-page downloads
- Use `--depth 1-2` for small sites or specific sections
- Use `--depth 3+` only if you need comprehensive coverage
- Use `--no-domain-restriction` carefully (can crawl the entire web!)

## Deactivating Virtual Environment

When you're done:

```bash
deactivate
```

## Troubleshooting

**"No module named 'requests'"**

- Make sure you activated the virtual environment
- Run `pip install -r requirements.txt`

**"Permission denied" or 403 errors**

- Some sites block automated access
- Try increasing `--delay` to 1-2 seconds
- Check if robots.txt allows crawling

**Too many files/pages**

- Use `--max-pages` to limit the crawl
- Use `--depth 0` or `--depth 1` for smaller crawls
- Use `Ctrl+C` to stop the crawler at any time

## License

[AGPL-3.0 License](LICENSE)
