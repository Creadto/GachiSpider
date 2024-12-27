from abc import ABCMeta, abstractmethod
import logging
from typing import List
import requests

from urllib.parse import urljoin
from spider.structure import Node, State
from spider.utils.matcher import Matcher

class Linker(metaclass=ABCMeta):
    def __init__(self, init_url, **kwargs):
        self.logger = logging.getLogger(name="LinkManager")
        self.node = Node(url=init_url)
        self.init_url, self.matcher = None, None
        if init_url is not None:
            self.init_url = init_url
            
            response = requests.get(urljoin(base=self.init_url, url='robots.txt'))
            self.matcher = Matcher(mass=response.text)
              
    @abstractmethod        
    def crawl(self, url: str):
        raise NotImplementedError
    
    @abstractmethod  
    def transit(self, next_state: State, auto_run: bool = True):          
        raise NotImplementedError

