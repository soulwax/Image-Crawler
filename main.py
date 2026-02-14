#!/usr/bin/env python3
# File: main.py

"""
Web Crawler - Download all files of a specific format from a website.
Crawls through pages and follows links to find and download matching files.

Usage: python main.py <url> <file_extension> [options]
Example: python main.py https://example.com ".gif" --depth 3 --max-pages 100
"""

import sys
import os
import argparse
import time
import asyncio
import aiohttp
import aiofiles
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, urldefrag
from urllib.robotparser import RobotFileParser
from pathlib import Path
from collections import deque
from typing import Set, List, Tuple, Optional


class WebCrawler:
    """Async web crawler to find and download files across multiple pages."""

    def __init__(self, start_url: str, file_extensions: List[str], max_depth: int = 2,
                 max_pages: int = 100, delay: float = 0.1, stay_on_domain: bool = True,
                 respect_robots: bool = False, max_concurrent: int = 10,
                 content_pattern: Optional[str] = None, download_all_files: bool = False):
        """
        Initialize the web crawler.

        Args:
            start_url: The starting URL to crawl
            file_extensions: List of file extensions to download (e.g., ['.gif', '.jpg'])
            max_depth: Maximum depth to crawl (0 = only start page)
            max_pages: Maximum number of pages to crawl
            delay: Delay between requests in seconds
            stay_on_domain: Only crawl URLs on the same domain
            respect_robots: Respect robots.txt rules
            max_concurrent: Maximum concurrent requests
            content_pattern: Regex pattern to search in page content (saves matching pages)
            download_all_files: Download ALL files regardless of extension
        """
        self.start_url = start_url
        self.file_extensions = [ext.lower() for ext in file_extensions]
        self.max_depth = max_depth
        self.max_pages = max_pages
        self.delay = delay
        self.stay_on_domain = stay_on_domain
        self.respect_robots = respect_robots
        self.max_concurrent = max_concurrent
        self.download_all_files = download_all_files

        # Compile content pattern if provided
        self.content_pattern = None
        if content_pattern:
            try:
                self.content_pattern = re.compile(content_pattern, re.IGNORECASE | re.MULTILINE)
            except re.error as e:
                print(f"[WARN] Invalid regex pattern: {e}")
                self.content_pattern = None

        self.start_domain = urlparse(start_url).netloc
        self.visited_urls: Set[str] = set()
        self.queued_urls: Set[str] = set()  # FAST duplicate checking!
        self.downloaded_files: Set[str] = set()
        self.saved_pages: Set[str] = set()  # For content pattern matches
        self.to_visit: deque = deque([(start_url, 0)])  # (url, depth)
        self.queued_urls.add(start_url)
        self.pages_crawled = 0

        # Setup robots.txt parser
        self.robot_parser = None
        if respect_robots:
            self._setup_robots_parser()

    def _setup_robots_parser(self):
        """Setup robots.txt parser for the domain."""
        try:
            parsed = urlparse(self.start_url)
            robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
            self.robot_parser = RobotFileParser()
            self.robot_parser.set_url(robots_url)
            self.robot_parser.read()
            print(f"[INFO] Loaded robots.txt from {robots_url}")
        except Exception as e:
            print(f"[WARN] Could not load robots.txt: {e}")
            self.robot_parser = None

    def _can_fetch(self, url: str) -> bool:
        """Check if we can fetch the URL according to robots.txt."""
        if not self.robot_parser:
            return True
        try:
            return self.robot_parser.can_fetch("*", url)
        except:
            return True

    def _is_valid_url(self, url: str, current_depth: int) -> bool:
        """Check if URL should be crawled."""
        # Remove fragment
        url, _ = urldefrag(url)

        # Skip if already visited
        if url in self.visited_urls:
            return False

        # Check depth
        if current_depth > self.max_depth:
            return False

        # Check domain restriction
        if self.stay_on_domain:
            if urlparse(url).netloc != self.start_domain:
                return False

        # Check robots.txt
        if not self._can_fetch(url):
            return False

        # Check if it's a valid HTTP(S) URL
        parsed = urlparse(url)
        if parsed.scheme not in ['http', 'https']:
            return False

        return True

    def _is_downloadable_file(self, url: str) -> bool:
        """Check if a URL points to a file we want to download."""
        if self.download_all_files:
            # Download everything that looks like a file
            parsed = urlparse(url)
            path = parsed.path
            # Has an extension (contains a dot in the last segment)
            if path and '.' in path.split('/')[-1]:
                return True
            return False

        # Check against specific extensions
        url_lower = url.lower()
        for ext in self.file_extensions:
            if url_lower.endswith(ext):
                return True
        return False

    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> Tuple[List[str], List[str]]:
        """
        Extract file links and page links from HTML.

        Args:
            soup: BeautifulSoup object
            base_url: Base URL for resolving relative links

        Returns:
            Tuple of (file_urls, page_urls)
        """
        file_urls = []
        page_urls = []

        # Find all links
        for tag in soup.find_all(['a', 'img', 'source', 'video', 'audio']):
            link = tag.get('href') or tag.get('src')
            if not link:
                continue

            # Convert to absolute URL
            absolute_url = urljoin(base_url, link)

            # Check if it's a file we want to download
            if self._is_downloadable_file(absolute_url):
                if absolute_url not in self.downloaded_files:
                    file_urls.append(absolute_url)
            # If it's a page link (from <a> tags), add to crawl queue
            elif tag.name == 'a':
                page_urls.append(absolute_url)

        return file_urls, page_urls

    async def _download_file(self, session: aiohttp.ClientSession, url: str, output_dir: Path) -> bool:
        """Download a file from URL asynchronously."""
        try:
            filename = os.path.basename(urlparse(url).path)
            if not filename:
                # Generate filename with appropriate extension
                ext = self.file_extensions[0] if self.file_extensions else '.bin'
                filename = f'file_{len(self.downloaded_files)}{ext}'

            filepath = output_dir / filename

            # Skip if already exists or already downloaded
            if filepath.exists() or url in self.downloaded_files:
                return False

            async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                response.raise_for_status()

                async with aiofiles.open(filepath, 'wb') as f:
                    await f.write(await response.read())

            file_size = filepath.stat().st_size
            print(f"  [DOWNLOAD] {filename} ({file_size / 1024:.1f} KB)")
            self.downloaded_files.add(url)
            return True

        except Exception as e:
            print(f"  [ERROR] Failed to download {url}: {e}")
            return False

    async def _save_matching_page(self, url: str, content: bytes, output_dir: Path) -> bool:
        """Save a page that matches the content pattern."""
        try:
            # Create 'pages' subdirectory
            pages_dir = output_dir / 'matching_pages'
            pages_dir.mkdir(exist_ok=True)

            # Generate filename from URL
            parsed = urlparse(url)
            filename = parsed.path.replace('/', '_').strip('_')
            if not filename:
                filename = 'index'
            filename = f"{filename}.html"

            filepath = pages_dir / filename

            # Skip if already saved
            if url in self.saved_pages or filepath.exists():
                return False

            async with aiofiles.open(filepath, 'wb') as f:
                await f.write(content)

            print(f"  [SAVED PAGE] {filename} (pattern match!)")
            self.saved_pages.add(url)
            return True

        except Exception as e:
            print(f"  [ERROR] Failed to save page {url}: {e}")
            return False

    async def _fetch_page(self, session: aiohttp.ClientSession, url: str, depth: int, output_dir: Path):
        """Fetch a single page and extract links."""
        # Skip if not valid
        if not self._is_valid_url(url, depth):
            return

        # Mark as visited
        self.visited_urls.add(url)
        self.pages_crawled += 1

        print(f"\n[{self.pages_crawled}/{self.max_pages}] Crawling (depth {depth}): {url}")

        try:
            # Fetch page
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                response.raise_for_status()
                content = await response.read()

            # Check for content pattern matches
            if self.content_pattern:
                try:
                    text_content = content.decode('utf-8', errors='ignore')
                    if self.content_pattern.search(text_content):
                        print(f"  [MATCH] Content pattern found!")
                        await self._save_matching_page(url, content, output_dir)
                except Exception as e:
                    print(f"  [WARN] Content pattern check failed: {e}")

            # Parse HTML
            soup = BeautifulSoup(content, 'html.parser')

            # Extract links
            file_urls, page_urls = self._extract_links(soup, url)

            # Download files concurrently
            if file_urls:
                print(f"  Found {len(file_urls)} file(s) to download:")
                download_tasks = [self._download_file(session, file_url, output_dir) for file_url in file_urls]
                await asyncio.gather(*download_tasks, return_exceptions=True)

            # Add new pages to crawl queue (FAST duplicate checking with set!)
            if depth < self.max_depth:
                new_pages = 0
                for page_url in page_urls:
                    page_url, _ = urldefrag(page_url)
                    if page_url not in self.visited_urls and page_url not in self.queued_urls:
                        self.to_visit.append((page_url, depth + 1))
                        self.queued_urls.add(page_url)  # O(1) instead of O(n)!
                        new_pages += 1
                if new_pages > 0:
                    print(f"  Added {new_pages} new page(s) to queue")

            # Small delay
            if self.delay > 0:
                await asyncio.sleep(self.delay)

        except asyncio.TimeoutError:
            print(f"  [ERROR] Timeout fetching page")
        except aiohttp.ClientError as e:
            print(f"  [ERROR] Failed to fetch page: {e}")
        except Exception as e:
            print(f"  [ERROR] Unexpected error: {e}")

    async def crawl(self, output_dir: Path) -> dict:
        """
        Start crawling and downloading files asynchronously.

        Args:
            output_dir: Directory to save downloaded files

        Returns:
            Statistics dictionary
        """
        print(f"\n{'='*70}")
        print(f"Starting ASYNC crawler...")
        print(f"  Start URL: {self.start_url}")
        if self.download_all_files:
            print(f"  File types: ALL files (*)")
        else:
            print(f"  File types: {', '.join(self.file_extensions)}")
        if self.content_pattern:
            print(f"  Content search: Active (pattern: {self.content_pattern.pattern})")
        print(f"  Max depth: {self.max_depth}")
        print(f"  Max pages: {self.max_pages}")
        print(f"  Max concurrent: {self.max_concurrent}")
        print(f"  Stay on domain: {self.stay_on_domain}")
        print(f"{'='*70}\n")

        start_time = time.time()

        # Create aiohttp session with connection limits
        connector = aiohttp.TCPConnector(limit=self.max_concurrent)
        async with aiohttp.ClientSession(
            connector=connector,
            headers={'User-Agent': 'Mozilla/5.0 (compatible; PyImageDL/1.0)'}
        ) as session:
            # Process pages with controlled concurrency
            semaphore = asyncio.Semaphore(self.max_concurrent)

            async def controlled_fetch(url, depth):
                async with semaphore:
                    await self._fetch_page(session, url, depth, output_dir)

            # Main crawl loop with concurrent processing
            tasks = []
            while (self.to_visit or tasks) and self.pages_crawled < self.max_pages:
                # Start new tasks up to concurrent limit
                while self.to_visit and len(tasks) < self.max_concurrent and self.pages_crawled < self.max_pages:
                    url, depth = self.to_visit.popleft()
                    task = asyncio.create_task(controlled_fetch(url, depth))
                    tasks.append(task)

                # Wait for at least one task to complete
                if tasks:
                    done, tasks = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
                    tasks = list(tasks)  # Convert back to list

        elapsed_time = time.time() - start_time

        # Return statistics
        stats = {
            'pages_crawled': self.pages_crawled,
            'files_downloaded': len(self.downloaded_files),
            'pages_saved': len(self.saved_pages),
            'elapsed_time': elapsed_time
        }

        return stats




def get_shortened_url(url):
    """
    Create a shortened directory name from the URL.

    Args:
        url: The source URL

    Returns:
        A clean directory name
    """
    parsed = urlparse(url)
    # Use domain + path, cleaned of special characters
    short_name = parsed.netloc + parsed.path
    # Remove invalid characters for directory names
    short_name = short_name.replace('/', '_').replace(':', '_').replace('?', '_')
    short_name = short_name.strip('_')
    return short_name if short_name else 'downloads'


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='FAST Async Web Crawler - Download files and search content across websites',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Download GIFs from a page
  python main.py https://example.com ".gif"

  # Download multiple file types (comma-separated)
  python main.py https://example.com ".jpg,.png,.gif"

  # Download ALL files from a site
  python main.py https://example.com "*"

  # Search for pages containing a pattern (saves matching HTML)
  python main.py https://example.com ".jpg" --content "API key|password"

  # Super fast: 50 concurrent connections, no delay
  python main.py https://example.com ".png" --concurrent 50 --delay 0

  # Download all image types
  python main.py https://example.com ".jpg,.jpeg,.png,.gif,.webp,.svg"
        '''
    )

    parser.add_argument('url', help='Starting URL to crawl')
    parser.add_argument('extension', nargs='?', default='*',
                        help='File extension(s) to download: ".gif", ".jpg,.png", or "*" for all files (default: *)')

    parser.add_argument('-d', '--depth', type=int, default=2,
                        help='Maximum crawl depth (default: 2, use 0 for single page)')
    parser.add_argument('-p', '--max-pages', type=int, default=100,
                        help='Maximum number of pages to crawl (default: 100)')
    parser.add_argument('-c', '--concurrent', type=int, default=10,
                        help='Maximum concurrent requests (default: 10)')
    parser.add_argument('--delay', type=float, default=0.1,
                        help='Delay between requests in seconds (default: 0.1)')
    parser.add_argument('--content', type=str, default=None,
                        help='Regex pattern to search in page content (saves matching pages)')
    parser.add_argument('--no-domain-restriction', action='store_true',
                        help='Allow crawling external domains')
    parser.add_argument('--respect-robots', action='store_true',
                        help='Respect robots.txt rules (default: ignore for speed)')

    return parser.parse_args()


async def async_main():
    """Main async function to coordinate the crawling process."""
    args = parse_arguments()

    # Parse file extensions
    download_all_files = False
    file_extensions = []

    if args.extension == '*':
        download_all_files = True
        ext_name = 'all_files'
    else:
        # Split by comma for multiple extensions
        exts = [e.strip() for e in args.extension.split(',')]
        file_extensions = []
        for ext in exts:
            if not ext.startswith('.'):
                ext = '.' + ext
            file_extensions.append(ext)
        ext_name = '_'.join([e.lstrip('.') for e in file_extensions])

    # Create output directory structure: output/<shortened_url>/<extensions>/
    shortened_url = get_shortened_url(args.url)
    output_dir = Path('output') / shortened_url / ext_name
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\nOutput directory: {output_dir.absolute()}")
    if download_all_files:
        print("Mode: Download ALL files")
    else:
        print(f"File types: {', '.join(file_extensions)}")
    if args.content:
        print(f"Content pattern: {args.content}")
        print(f"Matching pages will be saved to: {output_dir / 'matching_pages'}")

    # Create and run crawler
    crawler = WebCrawler(
        start_url=args.url,
        file_extensions=file_extensions,
        max_depth=args.depth,
        max_pages=args.max_pages,
        delay=args.delay,
        stay_on_domain=not args.no_domain_restriction,
        respect_robots=args.respect_robots,  # Default False for speed!
        max_concurrent=args.concurrent,
        content_pattern=args.content,
        download_all_files=download_all_files
    )

    stats = await crawler.crawl(output_dir)

    # Print summary
    print(f"\n{'='*70}")
    print(f"Crawling complete!")
    print(f"  Pages crawled: {stats['pages_crawled']}")
    print(f"  Files downloaded: {stats['files_downloaded']}")
    if stats['pages_saved'] > 0:
        print(f"  Pages saved (pattern match): {stats['pages_saved']}")
    print(f"  Time elapsed: {stats['elapsed_time']:.2f} seconds")
    if stats['files_downloaded'] > 0:
        print(f"  Average speed: {stats['files_downloaded'] / stats['elapsed_time']:.2f} files/sec")
    print(f"  Files saved to: {output_dir.absolute()}")
    print(f"{'='*70}\n")


def main():
    """Entry point that runs the async main function."""
    asyncio.run(async_main())


if __name__ == '__main__':
    main()
