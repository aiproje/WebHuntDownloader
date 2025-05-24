# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import threading
import sys
from io import StringIO

# Import from main.py
# main_translations_dict is an alias for main.py's module-level 'translations' dictionary
from main import crawl_website, DEFAULT_EXTENSIONS, load_translations, get_translation, translations as main_translations_dict, init_db

class StdoutRedirector(object):
    """A class to redirect stdout to a Tkinter text widget."""
    def __init__(self, text_widget_log_method):
        self.text_widget_log_method = text_widget_log_method
        self.buffer = StringIO()

    def write(self, str_):
        # Buffer lines until a newline is encountered
        self.buffer.write(str_)
        if '\n' in str_:
            # If there's a newline, flush the buffer to the log method
            self.text_widget_log_method(self.buffer.getvalue().rstrip('\n'))
            self.buffer = StringIO() # Reset buffer

    def flush(self):
        # If there's anything left in the buffer when flush is called, log it.
        if self.buffer.tell() > 0:
            self.text_widget_log_method(self.buffer.getvalue().rstrip('\n'))
            self.buffer = StringIO() # Reset buffer

class App(tk.Tk):
    def __init__(self, language='en'): # Language is the only parameter needed for init
        super().__init__()
        self.language = language
        self.title("WebHuntDownloader GUI") # Placeholder title
        self.geometry("800x700")

        # App takes full responsibility for populating main_translations_dict
        # main_translations_dict is main.py's global 'translations' dictionary.
        
        # 1. Load main translations for self.language into main_translations_dict
        current_lang_main_strings = load_translations(self.language)
        main_translations_dict.clear()
        main_translations_dict.update(current_lang_main_strings)

        # 2. Add/overwrite GUI-specific translations into main_translations_dict.
        self._add_gui_specific_translations(main_translations_dict, self.language)
        
        # 3. self._ should always be main.get_translation, which uses the now populated main_translations_dict.
        self._ = get_translation 
        
        self.title(self._("gui_title", default="WebHuntDownloader GUI")) # Set translated title

        style = ttk.Style(self)
        style.theme_use('clam')

        # Language selection
        self.lang_frame = ttk.Frame(self, padding=(10, 10, 10, 0))
        self.lang_frame.pack(fill=tk.X)

        # Map language codes to display names and vice-versa
        self.language_code_to_display = {"en": "English", "tr": "Türkçe"}
        self.language_display_to_code = {"English": "en", "Türkçe": "tr"}

        # Current language display name
        current_display_language = self.language_code_to_display.get(self.language, "English")
        self.language_var = tk.StringVar(value=current_display_language)
        
        # Supported display languages 
        display_languages = list(self.language_display_to_code.keys())
        self.language_combobox = ttk.Combobox(self.lang_frame, textvariable=self.language_var, values=display_languages, state="readonly", width=10) # Adjusted width for longer names
        self.language_combobox.pack(side=tk.LEFT, padx=(0,5)) # Added some padding to the right
        self.language_combobox.bind("<<ComboboxSelected>>", self.change_language)

        # Main content frame
        self.main_frame = ttk.Frame(self, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        self._create_widgets()

    def _add_gui_specific_translations(self, target_dict, lang_code):
        # This function directly modifies the passed dictionary (which should be main_translations_dict)
        gui_specific_strings = {}
        if lang_code == "tr":
            gui_specific_strings = {
                "gui_title": "WebHunt İndirici Arayüzü",
                "gui_browse_button": "Gözat",
                "gui_extensions_label": "Uzantılar (kategoriler: images, videos, documents, audio veya .uzn1 .uzn2):",
                "gui_start_button": "İndirmeyi Başlat",
                "gui_log_label": "Günlük Kayıtları:",
                "gui_error_title": "Hata",
                "gui_url_empty": "Başlangıç URL'si boş olamaz.",
                "gui_output_dir_empty": "Çıktı Dizini boş olamaz.",
                "gui_invalid_extensions_format": "Uzantı formatı geçersiz. Kategorileri veya boşlukla ayrılmış .ext uzantılarını kullanın.",
                "gui_download_complete": "İndirme tamamlandı.",
                "gui_download_failed": "İndirme başarısız oldu. Ayrıntılar için günlüğe bakın.",
                "gui_ignore_query_strings_label": "URL'lerdeki ? karakterini yoksay"
            }
        else:  # English defaults
            gui_specific_strings = {
                "gui_title": "WebHuntDownloader GUI",
                "gui_browse_button": "Browse",
                "gui_extensions_label": "Extensions (categories: images, videos, documents, audio or .ext1 .ext2):",
                "gui_start_button": "Start Download",
                "gui_log_label": "Log:",
                "gui_error_title": "Error",
                "gui_url_empty": "Start URL cannot be empty.",
                "gui_output_dir_empty": "Output Directory cannot be empty.",
                "gui_invalid_extensions_format": "Invalid extensions format. Use categories or .ext1 .ext2 separated by spaces.",
                "gui_download_complete": "Download complete.",
                "gui_download_failed": "Download failed. Check log for details.",
                "gui_ignore_query_strings_label": "Ignore URLs with ?"
            }
        target_dict.update(gui_specific_strings) # Merge GUI strings into the main dictionary

    def _create_widgets(self):
        # Clear existing widgets in main_frame if any
        for widget in self.main_frame.winfo_children():
            widget.destroy()

        ttk.Label(self.main_frame, text=self._("url_help").split('.')[0] + ":").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.url_entry = ttk.Entry(self.main_frame, width=60)
        self.url_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(self.main_frame, text=self._("output_dir_help").split('.')[0] + ":").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.output_dir_entry = ttk.Entry(self.main_frame, width=50)
        self.output_dir_entry.insert(0, "downloaded_files") # Default value
        self.output_dir_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        self.browse_button = ttk.Button(self.main_frame, text=self._("gui_browse_button", default="Browse"), command=self.browse_output_dir)
        self.browse_button.grid(row=1, column=2, padx=5, pady=5)

        ttk.Label(self.main_frame, text=self._("gui_extensions_label", default="Extensions (categories: images, videos, documents, audio or .ext1 .ext2):")).grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.extensions_entry = ttk.Entry(self.main_frame, width=60)
        self.extensions_entry.insert(0, "images .pdf") # Default value
        self.extensions_entry.grid(row=2, column=1, padx=5, pady=5, sticky="ew")
        
        ttk.Label(self.main_frame, text=self._("strategy_help").split('.')[0] + ":").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.strategy_var = tk.StringVar(value="depth-first")
        self.strategy_combobox = ttk.Combobox(self.main_frame, textvariable=self.strategy_var, values=["depth-first", "breadth-first"], state="readonly")
        self.strategy_combobox.grid(row=3, column=1, padx=5, pady=5, sticky="w")

        self.no_backward_crawl_var = tk.BooleanVar(value=True)
        self.no_backward_crawl_check = ttk.Checkbutton(self.main_frame, text=self._("no_backward_crawl_help").split('.')[0], variable=self.no_backward_crawl_var)
        self.no_backward_crawl_check.grid(row=4, column=0, columnspan=2, padx=5, pady=5, sticky="w")

        self.ignore_query_strings_var = tk.BooleanVar(value=False)
        self.ignore_query_strings_check = ttk.Checkbutton(self.main_frame, text=self._("gui_ignore_query_strings_label", default="Ignore URLs with ?"), variable=self.ignore_query_strings_var)
        self.ignore_query_strings_check.grid(row=5, column=0, columnspan=2, padx=5, pady=5, sticky="w")

        self.start_button = ttk.Button(self.main_frame, text=self._("gui_start_button", default="Start Download"), command=self.start_download_thread)
        self.start_button.grid(row=6, column=0, columnspan=3, padx=5, pady=10)

        ttk.Label(self.main_frame, text=self._("gui_log_label", default="Log:")).grid(row=7, column=0, padx=5, pady=5, sticky="w")
        self.log_text = tk.Text(self.main_frame, height=15, width=80, state=tk.DISABLED)
        self.log_text.grid(row=8, column=0, columnspan=3, padx=5, pady=5, sticky="nsew")
        
        scrollbar = ttk.Scrollbar(self.main_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text['yscrollcommand'] = scrollbar.set
        scrollbar.grid(row=8, column=3, sticky='ns')

        self.main_frame.columnconfigure(1, weight=1)
        self.main_frame.rowconfigure(8, weight=1)
        
        # Store current values to restore them after language change
        self._store_widget_values()


    def _store_widget_values(self):
        self.widget_values = {
            "url": self.url_entry.get() if hasattr(self, 'url_entry') else "",
            "output_dir": self.output_dir_entry.get() if hasattr(self, 'output_dir_entry') else "downloaded_files",
            "extensions": self.extensions_entry.get() if hasattr(self, 'extensions_entry') else "images .pdf",
            "strategy": self.strategy_var.get() if hasattr(self, 'strategy_var') else "depth-first",
            "no_backward": self.no_backward_crawl_var.get() if hasattr(self, 'no_backward_crawl_var') else True,
            "ignore_query": self.ignore_query_strings_var.get() if hasattr(self, 'ignore_query_strings_var') else False,
        }

    def _restore_widget_values(self):
        if hasattr(self, 'widget_values'):
            self.url_entry.insert(0, self.widget_values["url"])
            self.output_dir_entry.delete(0, tk.END)
            self.output_dir_entry.insert(0, self.widget_values["output_dir"])
            self.extensions_entry.insert(0, self.widget_values["extensions"])
            self.strategy_var.set(self.widget_values["strategy"])
            self.no_backward_crawl_var.set(self.widget_values["no_backward"])
            self.ignore_query_strings_var.set(self.widget_values["ignore_query"])


    def change_language(self, event=None):
        selected_display_language = self.language_var.get()
        new_language_code = self.language_display_to_code.get(selected_display_language)

        if new_language_code and new_language_code != self.language:
            self._store_widget_values() # Store input field values before they are destroyed

            self.language = new_language_code

            # 1. Load main translation strings for the new language
            # This returns a new dictionary, it does NOT modify main_translations_dict directly
            new_lang_main_strings = load_translations(self.language)

            # 2. Update main.py's global 'translations' dictionary (aliased as main_translations_dict)
            # Clear it first, then update with the new language's main strings.
            main_translations_dict.clear()
            main_translations_dict.update(new_lang_main_strings)

            # 3. Add GUI-specific translations for the new language into main_translations_dict
            self._add_gui_specific_translations(main_translations_dict, self.language)

            # 4. self._ (which is main.get_translation) will now use the updated main_translations_dict.
            #    No need to reassign self._ as it's already main.get_translation, which uses the 
            #    module-level main_translations_dict that we just updated.

            self.title(self._("gui_title", default="WebHuntDownloader GUI")) # Update window title
            self._create_widgets() # Recreate widgets with new translations
            self._restore_widget_values() # Restore input field values to the newly created widgets


    def browse_output_dir(self):
        directory = filedialog.askdirectory()
        if directory:
            self.output_dir_entry.delete(0, tk.END)
            self.output_dir_entry.insert(0, directory)

    def log_message(self, message):
        if self.log_text:
            self.log_text.config(state=tk.NORMAL)
            self.log_text.insert(tk.END, message + "\n")
            self.log_text.see(tk.END)
            self.log_text.config(state=tk.DISABLED)
            self.update_idletasks()

    def parse_extensions(self, extensions_str):
        target_extensions = set()
        parts = extensions_str.lower().split()
        for part in parts:
            if part in DEFAULT_EXTENSIONS:
                target_extensions.update(DEFAULT_EXTENSIONS[part])
            elif part.startswith('.') and len(part) > 1:
                target_extensions.add(part)
            else:
                # Handle potential malformed entries if necessary, or ignore
                pass 
        if not target_extensions: # If after parsing, it's empty, maybe default to all
            self.log_message(self._("status_no_extensions_defaulting"))
            for category_extensions in DEFAULT_EXTENSIONS.values():
                target_extensions.update(category_extensions)
        return target_extensions

    def actual_download_logic(self, url, output_dir, extensions_str, strategy, no_backward, ignore_query_strings):
        original_stdout = sys.stdout
        sys.stdout = StdoutRedirector(self.log_message)
        try:
            self.log_message(self._("status_starting_crawl", url=url))
            self.log_message(self._("status_saving_to", output_dir=output_dir))
            self.log_message(self._("status_targeting_extensions", extensions=extensions_str))
            self.log_message(self._("status_crawling_strategy", strategy=strategy))
            enabled_disabled_str = self._("status_enabled") if no_backward else self._("status_disabled")
            self.log_message(self._("status_backward_crawl", status=enabled_disabled_str))
            ignore_query_status_str = self._("status_enabled") if ignore_query_strings else self._("status_disabled")
            self.log_message(self._("status_ignore_query_strings", default="Ignore query strings: {status}", status=ignore_query_status_str))

            target_extensions = self.parse_extensions(extensions_str)
            if not target_extensions:
                messagebox.showerror(self._("gui_error_title", default="Error"), self._("gui_invalid_extensions_format", default="Invalid extensions format."))
                self.start_button.config(state=tk.NORMAL) # Re-enable button
                return

            os.makedirs(output_dir, exist_ok=True)
            
            # Initialize the database for the GUI session
            gui_db_path = os.path.join(output_dir, "gui_download_reports.db")
            init_db(gui_db_path)
            
            crawl_website(
                start_url=url,
                allowed_extensions=target_extensions,
                save_dir=output_dir,
                db_path=gui_db_path, # GUI specific DB path
                prevent_backward_crawl=no_backward,
                strategy=strategy,
                ignore_query_strings=ignore_query_strings
            )
            self.log_message(self._("gui_download_complete", default="Download complete."))
            messagebox.showinfo("Info", self._("gui_download_complete", default="Download complete."))
        except Exception as e:
            self.log_message(self._("gui_download_failed", default="Download failed. Check log for details."))
            self.log_message(str(e))
            messagebox.showerror(self._("gui_error_title", default="Error"), str(e))
        finally:
            sys.stdout = original_stdout # Restore stdout
            self.start_button.config(state=tk.NORMAL) # Re-enable button

    def start_download_thread(self):
        url = self.url_entry.get()
        output_dir = self.output_dir_entry.get()
        extensions_str = self.extensions_entry.get()
        strategy = self.strategy_var.get()
        no_backward = self.no_backward_crawl_var.get()
        ignore_query_strings = self.ignore_query_strings_var.get()

        if not url:
            messagebox.showerror(self._("gui_error_title", default="Error"), self._("gui_url_empty", default="Start URL cannot be empty."))
            return
        if not output_dir:
            messagebox.showerror(self._("gui_error_title", default="Error"), self._("gui_output_dir_empty", default="Output directory cannot be empty."))
            return

        self.start_button.config(state=tk.DISABLED) # Disable button during download
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete('1.0', tk.END) # Clear previous logs
        self.log_text.config(state=tk.DISABLED)

        download_thread = threading.Thread(
            target=self.actual_download_logic,
            args=(url, output_dir, extensions_str, strategy, no_backward, ignore_query_strings),
            daemon=True
        )
        download_thread.start()

import locale # Added for language detection

def get_gui_system_language(): # Renamed to avoid conflict if main.py is imported elsewhere in future
    try:
        lang_code, _ = locale.getdefaultlocale()
        if lang_code:
            if lang_code.startswith("tr"):
                return "tr"
            elif lang_code.startswith("en"):
                return "en"
    except Exception:
        pass
    return "en" # Default to English

if __name__ == "__main__":
    # When running gui.py directly:
    # 1. Detect system language or default to English.
    # 2. Explicitly load this language's main strings into main_translations_dict (main.py's 'translations').
    # 3. App's __init__ will then handle adding GUI-specific strings to main_translations_dict
    #    and correctly setting self._ to main.get_translation.
    # 4. Pass translator_from_main=None to App to indicate it's a direct run.

    initial_language = get_gui_system_language()

    # Load initial language's main strings into main.py's 'translations' dictionary (main_translations_dict)
    initial_lang_main_strings = load_translations(initial_language)
    main_translations_dict.clear()
    main_translations_dict.update(initial_lang_main_strings)
    
    # Pass translator_from_main=None because we are not running from main.py's main()
    app = App(language=initial_language) 
    app.mainloop()
