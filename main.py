# -*- coding: utf-8 -*-
import argparse
import sqlite3
import os
from urllib.parse import urlparse, urljoin
import requests
from bs4 import BeautifulSoup # Will be added to requirements.txt
# import json # Not strictly needed if translations are embedded

# --- Internationalization (i18n) ---
translations = {} # Global translations dictionary
_ = lambda s, **kwargs: s.format(**kwargs) if kwargs else s # Placeholder before init

def load_translations(language_code="en"):
    """Loads translation strings. For simplicity, defined here. Could be from JSON files."""
    all_translations = {
        "en": {
            "app_description": "WebHuntDownloader: Crawl a website and download specific file types.",
            "url_help": "The starting URL to crawl. Not required if --gui is used.",
            "extensions_help": "List of file extensions to download (e.g., .jpg .png .pdf). Can also be categories: images, videos, documents, audio.",
            "custom_extensions_help": "Define your own custom extensions, overrides --extensions if categories are used.",
            "output_dir_help": "Directory to save downloaded files.",
            "db_path_help": "Path to the SQLite database for reports.",
            "no_backward_crawl_help": "Prevent crawler from visiting upper-level directories.",
            "strategy_help": "Crawling strategy to use.",
            "gui_help": "Launch the graphical user interface.",
            "language_help": "Set the language for the application (en, tr).",
            "error_gui_module_import": "Could not import the gui module. Make sure gui.py is in the same directory.",
            "error_gui_app_missing": "Could not find App class or mainloop in gui.py.",
            "error_url_required": "the following arguments are required: url (unless --gui is used)",
            "error_no_extensions": "Error: No file extensions specified for download. Use --extensions or --custom-extensions.",
            "status_no_extensions_defaulting": "No specific extensions provided. Downloading all default types: images, videos, documents, audio.",
            "status_starting_crawl": "Starting crawl for URL: {url}",
            "status_targeting_extensions": "Targeting extensions: {extensions}",
            "status_saving_to": "Saving files to: {output_dir}",
            "status_db_at": "Database at: {db_path}",
            "status_backward_crawl": "Backward crawl prevention: {status}",
            "status_enabled": "Enabled",
            "status_disabled": "Disabled",
            "status_crawling_strategy": "Crawling strategy: {strategy}",
            "log_skipped_downloaded": "Skipped (already downloaded): {file_url}",
            "log_downloaded": "Downloaded: {file_url} to {full_file_path}",
            "log_failed_download": "Failed to download {file_url}: {error}",
            "log_failed_unexpected": "An unexpected error occurred while downloading {file_url}: {error}",
            "log_crawling": "Crawling: {current_url}",
            "log_skipped_backward_crawl": "Skipping backward crawl: {next_page_url} (base: {base_url})",
            "log_could_not_crawl": "Could not crawl {current_url}: {error}",
            "log_unexpected_error_crawling": "Unexpected error crawling {current_url}: {error}",
            "log_skipping_already_logged": "Skipping already logged/downloaded file: {file_url}",
            "summary_header": "\\n--- Crawl Summary ---",
            "summary_pages_processed": "Total pages discovered/processed: {count}",
            "summary_files_downloaded": "Total files downloaded successfully: {count}",
            "summary_file_types_header": "\\nFile types downloaded:",
            "summary_unknown_type": "Unknown",
            "summary_failed_downloads_header": "\\nFiles that failed to download:",
            "summary_failed_item": "  URL: {url}, Reason: {reason}",
            "summary_none_failed": "  None.",
            "summary_large_files_header": "\\nFiles larger than 10MB:",
            "summary_large_file_item": "  File: {file_path}, Size: {size:.2f} MB",
            "summary_none_large": "  None.",
            "log_found_potential_file": "Found potential file link: {file_url}",
            "log_found_potential_page_link": "Found potential page link to explore: {page_url}",
            "status_ignore_query_strings": "Ignore query strings: {status}"
        },
        "tr": {
            "app_description": "WebHuntDownloader: Bir web sitesini tarar ve belirli dosya türlerini indirir.",
            "url_help": "Taramak için başlangıç URL\\\'si. --gui kullanılırsa gerekli değildir.",
            "extensions_help": "İndirilecek dosya uzantılarının listesi (örneğin, .jpg .png .pdf). Kategoriler de olabilir: images, videos, documents, audio.",
            "custom_extensions_help": "Kendi özel uzantılarınızı tanımlayın, kategoriler kullanılırsa --extensions öğesini geçersiz kılar.",
            "output_dir_help": "İndirilen dosyaların kaydedileceği dizin.",
            "db_path_help": "Raporlar için SQLite veritabanının yolu.",
            "no_backward_crawl_help": "Tarayıcının üst düzey dizinleri ziyaret etmesini engelleyin.",
            "strategy_help": "Kullanılacak tarama stratejisi.",
            "gui_help": "Grafik kullanıcı arayüzünü başlatın.",
            "language_help": "Uygulama dilini ayarlayın (en, tr).",
            "ignore_query_strings_help": "URL'lerdeki ? karakterini ve sonrasını yoksay.",
            "error_gui_module_import": "gui modülü içe aktarılamadı. gui.py dosyasının aynı dizinde olduğundan emin olun.",
            "error_gui_app_missing": "gui.py içinde App sınıfı veya mainloop bulunamadı.",
            "error_url_required": "şu argümanlar gereklidir: url (--gui kullanılmadığı sürece)",
            "error_no_extensions": "Hata: İndirmek için dosya uzantısı belirtilmedi. --extensions veya --custom-extensions kullanın.",
            "status_no_extensions_defaulting": "Belirli bir uzantı sağlanmadı. Tüm varsayılan türler indiriliyor: images, videos, documents, audio.",
            "status_starting_crawl": "URL için tarama başlatılıyor: {url}",
            "status_targeting_extensions": "Hedeflenen uzantılar: {extensions}",
            "status_saving_to": "Dosyalar şuraya kaydediliyor: {output_dir}",
            "status_db_at": "Veritabanı şurada: {db_path}",
            "status_backward_crawl": "Geriye doğru tarama engelleme: {status}",
            "status_enabled": "Etkin",
            "status_disabled": "Devre Dışı",
            "status_crawling_strategy": "Tarama stratejisi: {strategy}",
            "log_skipped_downloaded": "Atlandı (zaten indirilmiş): {file_url}",
            "log_downloaded": "İndirildi: {file_url} -> {full_file_path}",
            "log_failed_download": "{file_url} indirilemedi: {error}",
            "log_failed_unexpected": "{file_url} indirilirken beklenmeyen bir hata oluştu: {error}",
            "log_crawling": "Taranıyor: {current_url}",
            "log_skipped_backward_crawl": "Geriye doğru tarama atlanıyor: {next_page_url} (temel: {base_url})",
            "log_could_not_crawl": "{current_url} taranamadı: {error}",
            "log_unexpected_error_crawling": "{current_url} taranırken beklenmeyen hata: {error}",
            "log_skipping_already_logged": "Zaten günlüğe kaydedilmiş/indirilmiş dosya atlanıyor: {file_url}",
            "summary_header": "\\n--- Tarama Özeti ---",
            "summary_pages_processed": "Toplam keşfedilen/işlenen sayfa: {count}",
            "summary_files_downloaded": "Başarıyla indirilen toplam dosya: {count}",
            "summary_file_types_header": "\\nİndirilen dosya türleri:",
            "summary_unknown_type": "Bilinmeyen",
            "summary_failed_downloads_header": "\\nİndirilemeyen dosyalar:",
            "summary_failed_item": "  URL: {url}, Neden: {reason}",
            "summary_none_failed": "  Yok.",
            "summary_large_files_header": "\\n10MB\\\'den büyük dosyalar:",
            "summary_large_file_item": "  Dosya: {file_path}, Boyut: {size:.2f} MB",
            "summary_none_large": "  Yok.",
            "log_found_potential_file": "Potansiyel dosya bağlantısı bulundu: {file_url}",
            "log_found_potential_page_link": "Keşfedilecek potansiyel sayfa bağlantısı bulundu: {page_url}",
            "status_ignore_query_strings": "Sorgu dizgeleri yoksayılsın: {status}"
        }
    }
    return all_translations.get(language_code, all_translations["en"])

def get_translation(key, **kwargs):
    """Gets a translated string by key, formatting it with kwargs."""
    return translations.get(key, key).format(**kwargs)
# --- End Internationalization ---

# Default file extensions, can be expanded
DEFAULT_EXTENSIONS = {
    "images": [".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg"],
    "videos": [".mp4", ".webm", ".avi", ".mov"],
    "documents": [".pdf", ".docx", ".pptx", ".xlsx"],
    "audio": [".mp3", ".wav", ".ogg"],
}

def init_db(db_path="download_reports.db"):
    """Initializes the SQLite database to store download reports."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS downloads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT NOT NULL,
            file_path TEXT NOT NULL,
            file_type TEXT,
            status TEXT, -- e.g., "downloaded", "failed", "skipped"
            size_bytes INTEGER,
            download_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS crawled_pages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def log_download(db_path, url, file_path, file_type, status, size_bytes=None):
    """Logs a download attempt in the database."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO downloads (url, file_path, file_type, status, size_bytes)
        VALUES (?, ?, ?, ?, ?)
    ''', (url, file_path, file_type, status, size_bytes))
    conn.commit()
    conn.close()

def log_crawled_page(db_path, url):
    """Logs a crawled page in the database."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO crawled_pages (url) VALUES (?)", (url,))
        conn.commit()
    except sqlite3.IntegrityError: # URL already exists
        pass
    finally:
        conn.close()

def is_already_crawled(db_path, url):
    """Checks if a URL has already been crawled."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM crawled_pages WHERE url = ?", (url,))
    exists = cursor.fetchone() is not None
    conn.close()
    return exists

def is_file_downloaded(db_path, file_url):
    """Checks if a file URL has already been successfully downloaded."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM downloads WHERE url = ? AND status = 'downloaded'", (file_url,))
    exists = cursor.fetchone() is not None
    conn.close()
    return exists


def sanitize_filename(filename):
    """Removes or replaces characters that are invalid in Windows filenames."""
    return "".join(c for c in filename if c.isalnum() or c in ('.', '_', '-')).rstrip()

def download_file(file_url, save_dir, db_path="download_reports.db"):
    """Downloads a single file."""
    if is_file_downloaded(db_path, file_url):
        print(_("log_skipped_downloaded", file_url=file_url))
        log_download(db_path, file_url, "N/A", "N/A", "skipped")
        return

    try:
        response = requests.get(file_url, stream=True, timeout=10)
        response.raise_for_status()

        parsed_url = urlparse(file_url)
        path_parts = [sanitize_filename(part) for part in parsed_url.path.strip('/').split('/')]
        
        filename = path_parts[-1] if '.' in path_parts[-1] else "downloaded_file"
        if not any(filename.endswith(ext) for ext_list in DEFAULT_EXTENSIONS.values() for ext in ext_list):
            content_type = response.headers.get('content-type')
            if content_type and '/' in content_type:
                ext_from_content_type = "." + content_type.split('/')[-1]
                ext_from_content_type = "".join(c for c in ext_from_content_type if c.isalnum() or c == '.')
                if 1 < len(ext_from_content_type) < 6:
                     filename += ext_from_content_type

        current_save_path = os.path.join(save_dir, parsed_url.netloc, *path_parts[:-1]) if len(path_parts) > 1 else os.path.join(save_dir, parsed_url.netloc)
        os.makedirs(current_save_path, exist_ok=True)
        
        final_filename = sanitize_filename(filename)
        if not final_filename:
            final_filename = "untitled"
            original_ext = os.path.splitext(filename)[1]
            if original_ext:
                final_filename += sanitize_filename(original_ext)

        full_file_path = os.path.join(current_save_path, final_filename)
        file_type = os.path.splitext(final_filename)[1].lower()
        file_size = 0

        with open(full_file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                file_size += len(chunk)
        
        print(_("log_downloaded", file_url=file_url, full_file_path=full_file_path))
        log_download(db_path, file_url, full_file_path, file_type, "downloaded", file_size)

    except requests.exceptions.RequestException as e:
        print(_("log_failed_download", file_url=file_url, error=e))
        log_download(db_path, file_url, "N/A", "N/A", f"failed: {e}")
    except Exception as e:
        print(_("log_failed_unexpected", file_url=file_url, error=e))
        log_download(db_path, file_url, "N/A", "N/A", f"failed_unexpected: {e}")


def crawl_website(start_url, allowed_extensions, save_dir, db_path, prevent_backward_crawl=True, strategy="depth-first", ignore_query_strings=False):
    """Crawls a website and downloads files with specified extensions."""
    if not start_url.startswith(("http://", "https://")):
        start_url = "http://" + start_url

    parsed_start_url = urlparse(start_url)
    base_crawl_path = parsed_start_url.path
    if not base_crawl_path or not base_crawl_path.endswith('/'):
        base_crawl_path = os.path.dirname(parsed_start_url.path)
        if not base_crawl_path.endswith('/'):
            base_crawl_path += '/'

    to_visit = [start_url]
    visited_urls = set()

    if strategy == "breadth-first":
        from collections import deque
        to_visit = deque(to_visit)

    processed_urls_count = 0
    # downloaded_files_count = 0 # This counter wasn\'t perfectly accurate, DB query is better

    while to_visit:
        current_url = to_visit.pop() if strategy == "depth-first" else to_visit.popleft()

        if current_url in visited_urls:
            # print(f"DEBUG: Skipping {current_url} because it is in visited_urls memory set.") # DEBUG
            continue

        # The is_file_downloaded check in download_file prevents re-downloading existing files.
        # Pages will be re-scanned for new files by removing the is_already_crawled check.
        
        print(_("log_crawling", current_url=current_url))
        visited_urls.add(current_url)
        log_crawled_page(db_path, current_url)
        processed_urls_count += 1

        try:
            response = requests.get(current_url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            for tag in soup.find_all(["a", "img", "source", "link"], href=True) + soup.find_all(src=True):
                href = tag.get("href") or tag.get("src")
                if not href:
                    continue

                file_url = urljoin(current_url, href)
                
                if ignore_query_strings and '?' in file_url:
                    file_url = file_url.split('?', 1)[0]

                print(_("log_found_potential_file", file_url=file_url))
                parsed_file_url = urlparse(file_url)

                if parsed_file_url.netloc != parsed_start_url.netloc and \
                   not parsed_file_url.netloc.endswith("." + parsed_start_url.netloc):
                    continue

                file_ext = os.path.splitext(parsed_file_url.path)[1].lower()
                if file_ext in allowed_extensions:
                    if not is_file_downloaded(db_path, file_url): # download_file handles its own skip message
                         download_file(file_url, save_dir, db_path)
                         # downloaded_files_count +=1 # Rely on DB for final count
                    else:
                        # Logged as skipped by download_file if called, or if is_file_downloaded is true here
                        print(_("log_skipping_already_logged", file_url=file_url))
                        # Ensure it's logged as skipped if download_file isn't called
                        log_download(db_path, file_url, "N/A", file_ext, "skipped_log_check")


            for link_tag in soup.find_all("a", href=True):
                next_page_url = urljoin(current_url, link_tag["href"])

                if ignore_query_strings and '?' in next_page_url:
                    print(f"DEBUG: Original next_page_url with query: {next_page_url}") # Debug
                    next_page_url = next_page_url.split('?', 1)[0]
                    print(f"DEBUG: Modified next_page_url without query: {next_page_url}") # Debug
                
                print(_("log_found_potential_page_link", page_url=next_page_url))
                parsed_next_url = urlparse(next_page_url)

                if parsed_next_url.scheme not in ["http", "https"] or \
                   (parsed_next_url.netloc != parsed_start_url.netloc and \
                    not parsed_next_url.netloc.endswith("." + parsed_start_url.netloc)):
                    continue
                
                if prevent_backward_crawl:
                    current_page_path = parsed_next_url.path
                    if not current_page_path.startswith(base_crawl_path):
                        base_url_display = f"{parsed_start_url.scheme}://{parsed_start_url.netloc}{base_crawl_path}"
                        print(_("log_skipped_backward_crawl", next_page_url=next_page_url, base_url=base_url_display))
                        continue
                
                if next_page_url not in visited_urls and next_page_url not in to_visit:
                    if strategy == "depth-first":
                        to_visit.append(next_page_url)
                    else: # breadth-first
                        to_visit.append(next_page_url)

        except requests.exceptions.RequestException as e:
            print(_("log_could_not_crawl", current_url=current_url, error=e))
        except Exception as e:
            print(_("log_unexpected_error_crawling", current_url=current_url, error=e))
            
    print(_("summary_header"))
    print(_("summary_pages_processed", count=processed_urls_count))
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM downloads WHERE status = 'downloaded'")
    fetch_result = cursor.fetchone()
    total_downloaded_from_db = fetch_result[0] if fetch_result else 0
    print(_("summary_files_downloaded", count=total_downloaded_from_db))

    print(_("summary_file_types_header"))
    cursor.execute("SELECT file_type, COUNT(*) FROM downloads WHERE status = 'downloaded' GROUP BY file_type")
    for row in cursor.fetchall():
        print(f"  {row[0] if row[0] else _('summary_unknown_type')}: {row[1]}")

    print(_("summary_failed_downloads_header"))
    cursor.execute("SELECT url, status FROM downloads WHERE status LIKE 'failed%'")
    failed_downloads = cursor.fetchall()
    if failed_downloads:
        for row in failed_downloads:
            print(_("summary_failed_item", url=row[0], reason=row[1]))
    else:
        print(_("summary_none_failed"))
        
    print(_("summary_large_files_header"))
    cursor.execute("SELECT file_path, size_bytes FROM downloads WHERE status = 'downloaded' AND size_bytes > 10000000")
    large_files = cursor.fetchall()
    if large_files:
        for row in large_files:
            print(_("summary_large_file_item", file_path=row[0], size=row[1]/1000000))
    else:
        print(_("summary_none_large"))

    conn.close()


import locale # Added for language detection

def get_system_language():
    try:
        lang_code, _ = locale.getdefaultlocale()
        if lang_code:
            if lang_code.startswith("tr"):
                return "tr"
            elif lang_code.startswith("en"):
                return "en"
    except Exception:
        # Fallback or if detection fails
        pass
    return "en" # Default to English

def main():
    # Temporary parser to get language argument FIRST.
    pre_parser = argparse.ArgumentParser(add_help=False)
    # We'll determine default based on system lang if --language is not given
    pre_parser.add_argument("--language", "-lang", choices=["en", "tr"], default=None, help="Set language (en for English, tr for Turkish).")
    pre_args, remaining_argv = pre_parser.parse_known_args()

    # Determine initial language
    initial_lang = pre_args.language
    if initial_lang is None:
        initial_lang = get_system_language()
    
    # Ensure initial_lang is valid if detected, else default to 'en'
    if initial_lang not in ["en", "tr"]:
        initial_lang = "en"
    
    pre_args.language = initial_lang # Set it back for later use by main parser

    global translations
    translations = load_translations(pre_args.language)
    global _ 
    _ = get_translation

    parser = argparse.ArgumentParser(description=_("app_description"))
    parser.add_argument("url", nargs='?', default=None, help=_("url_help"))
    parser.add_argument("--extensions", "-e", nargs="+", 
                        help=_("extensions_help"))
    parser.add_argument("--custom-extensions", nargs="+", help=_("custom_extensions_help"))
    parser.add_argument("--output-dir", "-o", default="downloaded_files", 
                        help=_("output_dir_help"))
    parser.add_argument("--db-path", default="download_reports.db",
                        help=_("db_path_help"))
    parser.add_argument("--no-backward-crawl", action="store_true",
                        help=_("no_backward_crawl_help"))
    parser.add_argument("--strategy", choices=["depth-first", "breadth-first"], default="depth-first",
                        help=_("strategy_help"))
    parser.add_argument("--ignore-query-strings", action="store_true",
                        help=_("ignore_query_strings_help", default="Ignore query strings in URLs."))
    parser.add_argument("--gui", action="store_true", help=_("gui_help"))
    parser.add_argument("--language", "-lang", choices=["en", "tr"], default=pre_args.language, help=_("language_help"))

    args = parser.parse_args(remaining_argv)
    
    if args.language != pre_args.language: # If language changed via main args
        translations = load_translations(args.language)
        _ = get_translation
        # Parser help messages would have used the initial language.
        # For full dynamic language switching of help, a more complex setup or library is needed.

    if args.gui:
        try:
            import gui
            app = gui.App(language=args.language) # Pass only language
            app.mainloop()
        except ImportError:
            print(_("error_gui_module_import"))
        except AttributeError as e:
            print(_("error_gui_app_missing"))
            print(f"Details: {e}") 
        return

    if not args.url:
        parser.error(_("error_url_required"))

    init_db(args.db_path)

    target_extensions = set()
    if args.custom_extensions:
        for ext in args.custom_extensions:
            target_extensions.add(ext.lower() if ext.startswith(".") else "." + ext.lower())
    elif args.extensions:
        for ext_or_category in args.extensions:
            ext_or_category = ext_or_category.lower()
            if ext_or_category in DEFAULT_EXTENSIONS:
                target_extensions.update(DEFAULT_EXTENSIONS[ext_or_category])
            else:
                target_extensions.add(ext_or_category if ext_or_category.startswith(".") else "." + ext_or_category)
    else:
        for category_extensions in DEFAULT_EXTENSIONS.values():
            target_extensions.update(category_extensions)
        print(_("status_no_extensions_defaulting"))

    if not target_extensions:
        print(_("error_no_extensions"))
        return

    print(_("status_starting_crawl", url=args.url))
    print(_("status_targeting_extensions", extensions=', '.join(target_extensions)))
    print(_("status_saving_to", output_dir=args.output_dir))
    print(_("status_db_at", db_path=args.db_path))
    enabled_disabled_str = _("status_enabled") if args.no_backward_crawl else _("status_disabled")
    print(_("status_backward_crawl", status=enabled_disabled_str))
    print(_("status_crawling_strategy", strategy=args.strategy))
    ignore_query_status_str = _("status_enabled") if args.ignore_query_strings else _("status_disabled")
    print(_("status_ignore_query_strings", status=ignore_query_status_str))

    os.makedirs(args.output_dir, exist_ok=True)

    crawl_website(
        start_url=args.url,
        allowed_extensions=target_extensions,
        save_dir=args.output_dir,
        db_path=args.db_path,
        prevent_backward_crawl=args.no_backward_crawl,
        strategy=args.strategy,
        ignore_query_strings=args.ignore_query_strings
    )

if __name__ == "__main__":
    main()
