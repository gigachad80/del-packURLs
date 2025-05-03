
import sys
import os
import re
import signal
import threading
import requests
import fitz  # PyMuPDF
from concurrent.futures import ThreadPoolExecutor


YELLOW = '\033[93m'
GREEN = '\033[92m'
RED = '\033[91m'
RESET = '\033[0m'

# Keywords to search
keywords = [
    "internal use only", "confidential", "strictly private", "personal & confidential private",
    "restricted", "internal", "not for distribution", "do not share", "proprietary",
    "trade secret", "classified", "sensitive", "bank statement", "invoice", "salary",
    "contract", "agreement", "mom disclosure", "passport", "social security", "ssn",
    "date of birth", "credit card", "identity", "id number", "company confidential",
    "staff only", "management only", "internal only"
]

pattern = re.compile("|".join(re.escape(kw) for kw in keywords), re.IGNORECASE)
OUTPUT_FILE = "sorted-keywords.txt"

findings = []
findings_lock = threading.Lock()
stop_requested = False

def signal_handler(signum, frame):
    global stop_requested
    if not stop_requested:
        print(f"\n{YELLOW}Ctrl+C detected. Finishing current tasks and saving results...{RESET}", file=sys.stderr, flush=True)
        stop_requested = True

def check_pdf_url(url):
    if stop_requested:
        return
    try:
        print(f"{YELLOW}Downloading:{RESET} {url}", file=sys.stderr, flush=True)
        response = requests.get(url, stream=True, timeout=10)

        if response.status_code == 404:
            print(f"{RED}Not Found (404):{RESET} {url}", file=sys.stderr, flush=True)
            return

        response.raise_for_status()

        with fitz.open(stream=response.content, filetype="pdf") as doc:
            text = "".join(page.get_text() for page in doc)
            matches = pattern.findall(text)

            if matches:
                found_keywords = set(matches)
                keywords_str = ", ".join(sorted(found_keywords))
                print(f"{GREEN}Found keywords:{RESET} {keywords_str} in {url}", flush=True)
                with findings_lock:
                    findings.append((url, found_keywords))
            else:
                print(f"{YELLOW}No sensitive keywords found in:{RESET} {url}", file=sys.stderr, flush=True)

    except requests.HTTPError as e:
        if e.response.status_code == 404:
            print(f"{RED}Not Found (404):{RESET} {url}", file=sys.stderr, flush=True)
        else:
            print(f"{RED}HTTP Error ({e.response.status_code}):{RESET} {url}", file=sys.stderr, flush=True)
    except requests.RequestException as e:
        print(f"{RED}Error downloading {url}: {e}{RESET}", file=sys.stderr, flush=True)
    except fitz.FileDataError as e:
        print(f"{RED}Error processing PDF {url}: {e}{RESET}", file=sys.stderr, flush=True)
    except Exception as e:
        print(f"{RED}Unexpected error with {url}: {e}{RESET}", file=sys.stderr, flush=True)

def process_urls(urls, use_concurrency):
    if use_concurrency:
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(check_pdf_url, url) for url in urls if not stop_requested]
            for future in futures:
                try:
                    future.result()
                except Exception:
                    pass
    else:
        for i, url in enumerate(urls, 1):
            if stop_requested:
                break
            check_pdf_url(url)

def main():
    signal.signal(signal.SIGINT, signal_handler)

    if len(sys.argv) != 3:
        print(f"Usage: python {sys.argv[0]} <input_file> <concurrency_yes_no>", file=sys.stderr, flush=True)
        print("Example: python sort-keywords.py filtered_output.txt yes", file=sys.stderr, flush=True)
        sys.exit(1)

    input_file = sys.argv[1]
    concurrency_choice = sys.argv[2].strip().lower()
    use_concurrency = concurrency_choice == "yes"

    print(f"Processing '{input_file}' with concurrency: {use_concurrency}", file=sys.stderr, flush=True)

    if not os.path.exists(input_file):
        print(f"{RED}Error:{RESET} Input file '{input_file}' not found.", file=sys.stderr, flush=True)
        sys.exit(1)

    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            urls = [line.strip() for line in f if line.strip() and line.strip().lower().endswith(".pdf")]
    except Exception as e:
        print(f"{RED}Error reading input file '{input_file}':{RESET} {e}", file=sys.stderr, flush=True)
        sys.exit(1)

    if not urls:
        print(f"{YELLOW}No valid PDF URLs found in '{input_file}'.{RESET}", file=sys.stderr, flush=True)
        try:
            with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
                pass
            print(f"Created empty output file: {OUTPUT_FILE}", file=sys.stderr, flush=True)
        except Exception as e:
            print(f"{RED}Error creating empty output file '{OUTPUT_FILE}':{RESET} {e}", file=sys.stderr, flush=True)
        return

    process_urls(urls, use_concurrency)

    findings.sort(key=lambda x: x[0])
    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            for url, keywords_set in findings:
                keywords_str = ", ".join(sorted(keywords_set))
                f.write(f"{url} - Found Keyword(s): {keywords_str}\n")
        print(f"{GREEN}Results saved to '{OUTPUT_FILE}'{RESET}", file=sys.stderr, flush=True)
    except Exception as e:
        print(f"{RED}Error saving results to '{OUTPUT_FILE}':{RESET} {e}", file=sys.stderr, flush=True)

if __name__ == "__main__":
    try:
        import fitz
    except ImportError:
        print(f"{RED}Error:{RESET} PyMuPDF (fitz) not installed. Please install it: pip install PyMuPDF", file=sys.stderr, flush=True)
        sys.exit(1)
    main()
