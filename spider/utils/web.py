import re
import time
import random
from urllib.request import Request, urlopen
from urllib.parse import urlparse, urljoin

def get_default_header(**kwargs):
    default_dict =  {'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                     'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
                     'Priority': 'u=0, i',
                     'Sec-Ch-Ua': '"Google Chrome";v="129", "Not=A?Brand";v="8", "Chromium";v="129"',
                     'Sec-Ch-Ua-Mobile': '?0',
                     'Sec-Ch-Ua-Platform': '"Windows"',
                     'Sec-Fetch-Dest': 'document',
                     'Sec-Fetch-Mode': 'navigate',
                     'Sec-Fetch-Site': 'none',
                     'Sec-Fetch-User': '?1',
                     'Upgrade-Insecure-Requests': '1',
                     "Connection": "keep-alive",
                     'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36'}
    
    for key, value in kwargs.items():
        default_dict[key] = value
    
    return default_dict

def get_base_url(url):
    parsed = urlparse(url)
    base_url = f'{parsed.scheme}://{parsed.netloc}'
    if parsed.path:
        base_url += f'/{parsed.path}'
    return base_url

def get_unwrapped_url(url, agent_name="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36"):
    factor = 2.0 + (random.random() * 2 - 1.0)
    time.sleep(factor) # for webmaster
    req = Request(url, headers=get_default_header(**{"User-Agent": agent_name}))
    unwrapped_url = None
    try:
        time.sleep(factor) # for webmaster
        context = urlopen(req)
        if context.status == 200:
            unwrapped_url = context.url
            contents = context.read()
        return contents, unwrapped_url
    
    except Exception as e:
        return None, None

def download_media(url, save_path):
    factor = 0.4 + (random.random() * 0.4 - 0.2)
    time.sleep(factor) # for webmaster
    request = Request(urljoin("https://", url), headers=get_default_header())
    try:
        with urlopen(request) as response:
            if response.status != 200:
                raise ConnectionError

            with open(save_path, 'wb') as file:
                file.write(response.read())
        return save_path
    except Exception as e:
        return None
    
def clean_text(element, with_tag: bool=True, lt: str=''):
    # \u200b: zero-width space, \ufeff: BOM, \u2028-\u202f: line separators
    if with_tag:          
        text = element.get_text(strip=True)
        return_text = re.sub(r'[\u200b\ufeff\u2028-\u202f]', '', text)
        
        text = re.sub(r'\s+', ' ', return_text).strip()
        text = re.sub(r'([.!?])\s+', r'\1\n', return_text)
        paragraphs = [p.strip() for p in text.split('\n') if p.strip()]
        if len(paragraphs) > 4:
            return_text = "\n".join(paragraphs)
    
        return return_text
    else:
        return lt.join(t for t in element.contents if isinstance(t, str))