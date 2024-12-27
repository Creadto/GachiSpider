import json
import os.path as osp
import re
from urllib.parse import urljoin, urlparse

def get_json(root, filename):
    with open(osp.join(root, filename)) as f:
        config = json.load(f)
    
    return config

def get_form(node, root="./spider/form", **kwargs):
    logger = None
    if "logger" in kwargs:
        logger = kwargs['logger']
    
    result = {
        'node': node,
        'form': None
    }
    
    parsed_url = urlparse(node.url.replace('www.', ''))
    root = osp.join(root, parsed_url.netloc)
    file_path = osp.join(root, 'index.json') 
    if not osp.exists(file_path):
        message = "Not found %s" % parsed_url.netloc
        logger.info(message) if logger is not None else print(message)
        return result
    
    with open (file_path, "r") as f:
        data = json.load(f)
    
    for key, form in data.items():
        message = "Compare key: %s" % key
        logger.info(message) if logger is not None else print(message)
        searched = re.search(key, urljoin(parsed_url.path, parsed_url.query))
        if searched is not None:
            message = "Found form from: %s" % file_path
            logger.info(message) if logger is not None else print(message)
            result['node'].pattern = key
            result['form'] = form
            break
        
    return result