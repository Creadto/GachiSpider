from datetime import datetime 
from typing import List
from bs4 import BeautifulSoup as bs
from spider.structure import Node, State
from spider.utils.web import get_unwrapped_url
from .failed import Failed
from .parse import Parse


class Fetch(State):
    def __init__(self, node: Node, parent):
        super(Fetch, self).__init__("fetch", node=node, parent=parent)
        
    def run(self):
        try:
            if self.node.cache:
                self.logger.info("Existed cache,  URL")
                contents, url = self.node.cache, self.node.url
            else:
                self.logger.warning("Empty cache, from %s" % (self.node.url))
                self.node.label = "Invalid matched data"
                self.parent.transit(Failed(node=self.node, parent=self.parent))
                
            if url is not None:
                self.node.url = url
                self.node.last_visited = datetime.timestamp(datetime.now())
                self.node.cache = contents
                self.parent.transit(Parse(node=self.node, parent=self.parent))
            else:
                self.logger.warning("Invalid connection, from %s" % (self.node.url))
                self.node.label = "Connection Failed"
                self.parent.transit(Failed(node=self.node, parent=self.parent))
        except Exception as e:
            import traceback
            self.logger.error(traceback.print_exc())
            self.parent.transit(Failed(node=self.node, parent=self.parent))
    
    def pause(self):
        raise NotImplementedError
    
    def stop(self):
        raise NotImplementedError