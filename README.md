# PyImageDL - Python Web Crawler & File Downloader

A powerful web crawler that downloads all files of a specific format from websites. Crawls through multiple pages, follows links, and respects robots.txt.

## Features

- 🕷️ **Full Web Crawler** - Crawls through multiple pages following links
- 📊 **Configurable Depth** - Control how deep the crawler goes (0 = single page, 1+ = follow links)
- 🎯 **File Type Filtering** - Download only the file types you want
- 🔒 **Robots.txt Support** - Respects website crawling rules by default
- 🌐 **Domain Control** - Stay on the same domain or allow external links
- ⚡ **Rate Limiting** - Configurable delay between requests to be respectful
- 📁 **Organized Output** - Files saved in `output/<domain>/<file_type>/` structure
- 📈 **Progress Tracking** - Real-time crawl progress and statistics

## Installation

### 1. Clone or Download this Repository

```bash
cd PyImageDL
```

### 2. Create a Virtual Environment

#### On Windows:
```bash
python -m venv .venv
.venv\Scripts\activate
```

#### On macOS/Linux:
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

**Crawl 3 levels deep, download all JPGs:**
```bash
python main.py https://example.com ".jpg" --depth 3
```

**Download PNGs, crawl max 50 pages:**
```bash
python main.py https://example.com ".png" --depth 2 --max-pages 50
```

**Download videos, allow external domains:**
```bash
python main.py https://example.com ".mp4" --depth 2 --no-domain-restriction
```

**Slower crawling (2 second delay):**
```bash
python main.py https://example.com ".gif" --delay 2.0
```

### Command-Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `url` | Starting URL to crawl (required) | - |
| `extension` | File extension to download, e.g., ".gif", "jpg" (required) | - |
| `-d, --depth` | Maximum crawl depth (0 = single page only) | 2 |
| `-p, --max-pages` | Maximum number of pages to crawl | 100 |
| `--delay` | Delay between requests in seconds | 0.5 |
| `--no-domain-restriction` | Allow crawling to external domains | false |
| `--no-robots` | Ignore robots.txt rules | false |

### Advanced Examples

**Deep crawl for images (depth 5, up to 500 pages):**
```bash
python main.py https://example.com/gallery ".jpg" --depth 5 --max-pages 500
```

**Fast crawl with no delay (use responsibly!):**
```bash
python main.py https://example.com ".gif" --delay 0
```

**Ignore robots.txt and crawl external links:**
```bash
python main.py https://example.com ".png" --no-robots --no-domain-restriction
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

1. **Start Crawling** - Begins at the provided URL
2. **Extract Links** - Finds all links and files on the page
3. **Download Files** - Downloads files matching your extension
4. **Follow Links** - If depth > 0, follows page links and repeats
5. **Respect Limits** - Stops at max depth or max pages
6. **Stay Polite** - Delays between requests, respects robots.txt

## Common File Extensions

- **Images**: `.jpg`, `.jpeg`, `.png`, `.gif`, `.webp`, `.svg`, `.bmp`
- **Videos**: `.mp4`, `.webm`, `.avi`, `.mov`, `.mkv`
- **Audio**: `.mp3`, `.wav`, `.ogg`, `.flac`
- **Documents**: `.pdf`, `.doc`, `.docx`, `.txt`
- **Archives**: `.zip`, `.rar`, `.tar`, `.gz`

## Tips & Best Practices

### 🚦 Be Respectful
- Use appropriate delays (`--delay 1.0` or higher for large crawls)
- Don't crawl the same site repeatedly in short periods
- Respect robots.txt (don't use `--no-robots` unless you have permission)

### ⚡ Performance
- Start with `--depth 0` to test on a single page first
- Use `--max-pages` to limit crawl size
- Lower delays for faster crawling, but be careful not to overload servers

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

Free to use for educational and personal projects. Be respectful of website terms of service and robots.txt.
