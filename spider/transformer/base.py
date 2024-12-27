import logging
from typing import List


class Transformer:
    def __init__(self, **kwargs):
        self.logger = logging.getLogger(name="Transformer")
        
    def run(self, urls: List[str]):
        pass