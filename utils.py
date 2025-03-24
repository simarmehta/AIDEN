# utils.py
import requests
import re
from bs4 import BeautifulSoup
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.190 Safari/537.36"
}
def fetch_html(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch {url}: {e}")
        return None
    

    
def extract_text_from_html(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    for tag in soup(["script", "style", "nav", "header", "footer", "aside"]):
        tag.extract()
    return soup.get_text(separator="\n", strip=True)

def clean_text(text, mode="sentence"):
    text = text.replace('\x00', '')
    if mode == "paragraph":
        text = re.sub(r'\r\n', '\n', text)              
        text = re.sub(r'\n{3,}', '\n\n', text)          
        text = re.sub(r'[ \t]+', ' ', text)             
        return text.strip()
    else:
        text = re.sub(r'\n+', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
