#!/usr/bin/env python3
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
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, urldefrag
from urllib.robotparser import RobotFileParser
from pathlib import Path
from collections import deque
from typing import Set, List, Tuple


class WebCrawler:
    """Web crawler to find and download files across multiple pages."""

    def __init__(self, start_url: str, file_extension: str, max_depth: int = 2,
                 max_pages: int = 100, delay: float = 0.5, stay_on_domain: bool = True,
                 respect_robots: bool = True):
        """
        Initialize the web crawler.

        Args:
            start_url: The starting URL to crawl
            file_extension: File extension to download (e.g., '.gif')
            max_depth: Maximum depth to crawl (0 = only start page)
            max_pages: Maximum number of pages to crawl
            delay: Delay between requests in seconds
            stay_on_domain: Only crawl URLs on the same domain
            respect_robots: Respect robots.txt rules
        """
        self.start_url = start_url
        self.file_extension = file_extension
        self.max_depth = max_depth
        self.max_pages = max_pages
        self.delay = delay
        self.stay_on_domain = stay_on_domain
        self.respect_robots = respect_robots

        self.start_domain = urlparse(start_url).netloc
        self.visited_urls: Set[str] = set()
        self.downloaded_files: Set[str] = set()
        self.to_visit: deque = deque([(start_url, 0)])  # (url, depth)
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
            if absolute_url.lower().endswith(self.file_extension.lower()):
                if absolute_url not in self.downloaded_files:
                    file_urls.append(absolute_url)
            # If it's a page link (from <a> tags), add to crawl queue
            elif tag.name == 'a':
                page_urls.append(absolute_url)

        return file_urls, page_urls

    def _download_file(self, url: str, output_dir: Path) -> bool:
        """Download a file from URL."""
        try:
            filename = os.path.basename(urlparse(url).path)
            if not filename:
                filename = f'file_{len(self.downloaded_files)}{self.file_extension}'

            filepath = output_dir / filename

            # Skip if already exists
            if filepath.exists():
                print(f"  [SKIP] {filename} (already exists)")
                return False

            response = requests.get(url, timeout=30, stream=True)
            response.raise_for_status()

            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            file_size = filepath.stat().st_size
            print(f"  [DOWNLOAD] {filename} ({file_size / 1024:.1f} KB)")
            self.downloaded_files.add(url)
            return True

        except Exception as e:
            print(f"  [ERROR] Failed to download {url}: {e}")
            return False

    def crawl(self, output_dir: Path) -> dict:
        """
        Start crawling and downloading files.

        Args:
            output_dir: Directory to save downloaded files

        Returns:
            Statistics dictionary
        """
        print(f"\n{'='*70}")
        print(f"Starting crawler...")
        print(f"  Start URL: {self.start_url}")
        print(f"  File type: {self.file_extension}")
        print(f"  Max depth: {self.max_depth}")
        print(f"  Max pages: {self.max_pages}")
        print(f"  Stay on domain: {self.stay_on_domain}")
        print(f"{'='*70}\n")

        start_time = time.time()

        while self.to_visit and self.pages_crawled < self.max_pages:
            url, depth = self.to_visit.popleft()

            # Skip if not valid
            if not self._is_valid_url(url, depth):
                continue

            # Mark as visited
            self.visited_urls.add(url)
            self.pages_crawled += 1

            print(f"\n[{self.pages_crawled}/{self.max_pages}] Crawling (depth {depth}): {url}")

            try:
                # Fetch page
                response = requests.get(url, timeout=10, headers={
                    'User-Agent': 'Mozilla/5.0 (compatible; PyImageDL/1.0)'
                })
                response.raise_for_status()

                # Parse HTML
                soup = BeautifulSoup(response.content, 'html.parser')

                # Extract links
                file_urls, page_urls = self._extract_links(soup, url)

                # Download files
                if file_urls:
                    print(f"  Found {len(file_urls)} file(s) to download:")
                    for file_url in file_urls:
                        self._download_file(file_url, output_dir)
                        time.sleep(self.delay / 2)  # Small delay between downloads

                # Add new pages to crawl queue
                if depth < self.max_depth:
                    new_pages = 0
                    for page_url in page_urls:
                        page_url, _ = urldefrag(page_url)
                        if page_url not in self.visited_urls and \
                           not any(page_url == u for u, d in self.to_visit):
                            self.to_visit.append((page_url, depth + 1))
                            new_pages += 1
                    if new_pages > 0:
                        print(f"  Added {new_pages} new page(s) to queue")

                # Delay between requests
                time.sleep(self.delay)

            except requests.exceptions.RequestException as e:
                print(f"  [ERROR] Failed to fetch page: {e}")
            except Exception as e:
                print(f"  [ERROR] Unexpected error: {e}")

        elapsed_time = time.time() - start_time

        # Return statistics
        stats = {
            'pages_crawled': self.pages_crawled,
            'files_downloaded': len(self.downloaded_files),
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
        description='Web Crawler - Download files of a specific format from websites',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Download GIFs from a page (depth 0, single page only)
  python main.py https://example.com ".gif"

  # Crawl up to 3 levels deep, max 50 pages
  python main.py https://example.com ".jpg" --depth 3 --max-pages 50

  # Allow external domains, no robots.txt checking
  python main.py https://example.com ".png" --no-domain-restriction --no-robots

  # Custom delay between requests (2 seconds)
  python main.py https://example.com ".mp4" --delay 2.0
        '''
    )

    parser.add_argument('url', help='Starting URL to crawl')
    parser.add_argument('extension', help='File extension to download (e.g., ".gif", "jpg")')

    parser.add_argument('-d', '--depth', type=int, default=2,
                        help='Maximum crawl depth (default: 2, use 0 for single page)')
    parser.add_argument('-p', '--max-pages', type=int, default=100,
                        help='Maximum number of pages to crawl (default: 100)')
    parser.add_argument('--delay', type=float, default=0.5,
                        help='Delay between requests in seconds (default: 0.5)')
    parser.add_argument('--no-domain-restriction', action='store_true',
                        help='Allow crawling external domains')
    parser.add_argument('--no-robots', action='store_true',
                        help='Ignore robots.txt rules')

    return parser.parse_args()


def main():
    """Main function to coordinate the crawling process."""
    args = parse_arguments()

    # Ensure extension starts with a dot
    file_extension = args.extension
    if not file_extension.startswith('.'):
        file_extension = '.' + file_extension

    # Create output directory structure: output/<shortened_url>/<file_extension>/
    shortened_url = get_shortened_url(args.url)
    file_ext_clean = file_extension.lstrip('.')
    output_dir = Path('output') / shortened_url / file_ext_clean
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\nOutput directory: {output_dir.absolute()}")

    # Create and run crawler
    crawler = WebCrawler(
        start_url=args.url,
        file_extension=file_extension,
        max_depth=args.depth,
        max_pages=args.max_pages,
        delay=args.delay,
        stay_on_domain=not args.no_domain_restriction,
        respect_robots=not args.no_robots
    )

    stats = crawler.crawl(output_dir)

    # Print summary
    print(f"\n{'='*70}")
    print(f"Crawling complete!")
    print(f"  Pages crawled: {stats['pages_crawled']}")
    print(f"  Files downloaded: {stats['files_downloaded']}")
    print(f"  Time elapsed: {stats['elapsed_time']:.2f} seconds")
    print(f"  Files saved to: {output_dir.absolute()}")
    print(f"{'='*70}\n")


if __name__ == '__main__':
    main()
