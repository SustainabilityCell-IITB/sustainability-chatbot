"""
Document loader module for loading text files, PDFs, and web content
Supports JavaScript-rendered websites using Selenium
"""
import os
import time
from typing import List, Tuple


def load_text_file(file_path: str) -> str:
    """
    Load text content from a text file.

    Args:
        file_path: Path to the text file

    Returns:
        Text content as a string
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()

        if not text.strip():
            raise ValueError(f"File is empty: {file_path}")

        return text
    except Exception as e:
        raise IOError(f"Error reading file {file_path}: {str(e)}")


def load_pdf_file(file_path: str) -> str:
    """
    Load text content from a PDF file.

    Args:
        file_path: Path to the PDF file

    Returns:
        Extracted text content as a string
    """
    try:
        from pypdf import PdfReader
    except ImportError:
        raise ImportError("pypdf is required to load PDF files. Install with: pip install pypdf")

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    try:
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"

        if not text.strip():
            raise ValueError(f"No text extracted from PDF: {file_path}")

        return text
    except Exception as e:
        raise IOError(f"Error reading PDF {file_path}: {str(e)}")


def load_url_with_selenium(url: str, wait_time: int = 5) -> str:
    """
    Load text content from a JavaScript-rendered website using Selenium.

    Args:
        url: The website URL to scrape
        wait_time: Time to wait for JavaScript to render (seconds)

    Returns:
        Extracted text content as a string
    """
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from webdriver_manager.chrome import ChromeDriverManager
    except ImportError:
        raise ImportError(
            "selenium and webdriver-manager are required for JavaScript rendering. "
            "Install with: pip install selenium webdriver-manager"
        )

    driver = None
    try:
        # Configure Chrome options for headless browsing
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-infobars")
        chrome_options.add_argument("--log-level=3")  # Suppress logs
        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])

        # Initialize Chrome driver
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)

        # Load the page
        driver.get(url)

        # Wait for page to load and JavaScript to render
        time.sleep(wait_time)

        # Try to wait for body to be present
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
        except:
            pass

        # Get the page source after JavaScript rendering
        page_source = driver.page_source

        # Parse with BeautifulSoup
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(page_source, 'html.parser')

        # Remove unwanted elements
        for element in soup(['script', 'style', 'noscript', 'iframe']):
            element.decompose()

        # Get text from main content areas
        text_parts = []

        # Try to find main content areas
        main_selectors = ['main', 'article', '.content', '#content', '.main-content', '#main-content']
        main_content = None
        for selector in main_selectors:
            main_content = soup.select_one(selector)
            if main_content:
                break

        if main_content:
            text = main_content.get_text(separator='\n', strip=True)
        else:
            # Fall back to body
            body = soup.find('body')
            if body:
                text = body.get_text(separator='\n', strip=True)
            else:
                text = soup.get_text(separator='\n', strip=True)

        # Clean up whitespace
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        text = '\n'.join(lines)

        if not text.strip():
            raise ValueError(f"No text extracted from URL: {url}")

        return text

    except Exception as e:
        raise IOError(f"Error fetching URL with Selenium {url}: {str(e)}")
    finally:
        if driver:
            driver.quit()


def load_url_basic(url: str) -> str:
    """
    Load text content from a website URL using basic requests (no JavaScript).

    Args:
        url: The website URL to scrape

    Returns:
        Extracted text content as a string
    """
    try:
        import requests
        from bs4 import BeautifulSoup
    except ImportError:
        raise ImportError(
            "requests and beautifulsoup4 are required for web scraping. "
            "Install with: pip install requests beautifulsoup4"
        )

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')

        # Remove script and style elements
        for element in soup(['script', 'style', 'nav', 'footer', 'header']):
            element.decompose()

        # Get text content
        text = soup.get_text(separator='\n', strip=True)

        # Clean up whitespace
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        text = '\n'.join(lines)

        return text
    except Exception as e:
        raise IOError(f"Error fetching URL {url}: {str(e)}")


def load_url(url: str, use_selenium: bool = True) -> str:
    """
    Load text content from a website URL.
    Tries Selenium first for JavaScript rendering, falls back to basic requests.

    Args:
        url: The website URL to scrape
        use_selenium: Whether to use Selenium for JavaScript rendering

    Returns:
        Extracted text content as a string
    """
    text = ""

    if use_selenium:
        try:
            print(f"      Loading with Selenium: {url}")
            text = load_url_with_selenium(url)
            if len(text) > 200:  # If we got substantial content
                return text
        except Exception as e:
            print(f"      Selenium failed, trying basic: {str(e)[:50]}...")

    # Fall back to basic requests
    try:
        basic_text = load_url_basic(url)
        # Use basic if it got more content or if selenium failed
        if len(basic_text) > len(text):
            text = basic_text
    except Exception as e:
        if not text:
            raise IOError(f"Failed to load URL {url}: {str(e)}")

    if not text.strip():
        raise ValueError(f"No text extracted from URL: {url}")

    return text


def load_document(file_path: str) -> str:
    """
    Load document content. Auto-detects file type (txt or pdf).

    Args:
        file_path: Path to the document

    Returns:
        Document text content
    """
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()

    if ext == '.txt':
        return load_text_file(file_path)
    elif ext == '.pdf':
        return load_pdf_file(file_path)
    else:
        raise ValueError(f"Unsupported file type: {ext}. Supported types: .txt, .pdf")


def load_all_documents(data_dir: str) -> Tuple[str, List[str]]:
    """
    Load all supported documents (.txt, .pdf) from a directory.

    Args:
        data_dir: Path to the data directory

    Returns:
        Tuple of (combined text, list of loaded file names)
    """
    if not os.path.exists(data_dir):
        raise FileNotFoundError(f"Data directory not found: {data_dir}")

    supported_extensions = {'.txt', '.pdf'}
    combined_text = ""
    loaded_files = []

    for filename in sorted(os.listdir(data_dir)):
        _, ext = os.path.splitext(filename)
        if ext.lower() in supported_extensions:
            file_path = os.path.join(data_dir, filename)
            try:
                text = load_document(file_path)
                combined_text += f"\n\n--- Content from: {filename} ---\n\n{text}"
                loaded_files.append(filename)
            except Exception as e:
                print(f"   [WARNING] Skipping {filename}: {str(e)}")

    if not loaded_files:
        raise ValueError(f"No supported documents found in {data_dir}")

    return combined_text.strip(), loaded_files


def load_urls(urls: List[str], use_selenium: bool = True) -> Tuple[str, List[str]]:
    """
    Load content from multiple URLs.

    Args:
        urls: List of URLs to scrape
        use_selenium: Whether to use Selenium for JavaScript rendering

    Returns:
        Tuple of (combined text, list of successfully loaded URLs)
    """
    combined_text = ""
    loaded_urls = []

    for url in urls:
        try:
            text = load_url(url, use_selenium=use_selenium)
            combined_text += f"\n\n--- Content from: {url} ---\n\n{text}"
            loaded_urls.append(url)
            print(f"   [OK] Loaded {len(text)} chars from: {url}")
        except Exception as e:
            print(f"   [WARNING] Skipping {url}: {str(e)}")

    return combined_text.strip(), loaded_urls


def load_all_sources(data_dir: str, urls: List[str] = None, use_selenium: bool = True) -> Tuple[str, dict]:
    """
    Load content from all sources: files in data directory and URLs.

    Args:
        data_dir: Path to the data directory
        urls: Optional list of URLs to scrape
        use_selenium: Whether to use Selenium for JavaScript rendering

    Returns:
        Tuple of (combined text, dict with 'files' and 'urls' lists)
    """
    combined_text = ""
    sources = {'files': [], 'urls': []}

    # Load files from data directory
    try:
        file_text, loaded_files = load_all_documents(data_dir)
        combined_text += file_text
        sources['files'] = loaded_files
    except Exception as e:
        print(f"   [WARNING] Error loading files: {str(e)}")

    # Load URLs if provided
    if urls:
        url_text, loaded_urls = load_urls(urls, use_selenium=use_selenium)
        if url_text:
            combined_text += "\n\n" + url_text
        sources['urls'] = loaded_urls

    if not combined_text.strip():
        raise ValueError("No content loaded from any source")

    return combined_text.strip(), sources
