from datetime import datetime 
from typing import List
from bs4 import BeautifulSoup as bs
from spider.structure import Node, State
from spider.utils.web import get_unwrapped_url
from .failed import Failed
from .extract import Extract



class Fetch(State):
    def __init__(self, node: Node, parent):
        super(Fetch, self).__init__("fetch", node=node, parent=parent)
        
    def run(self):
        try:
            self.logger.info("New connection, Unwrap URL")
            contents, url = get_unwrapped_url(self.node.url)
                
            if url is not None:
                self.node.url = url
                self.node.last_visited = datetime.timestamp(datetime.now())
                self.node.cache = contents
                self.node.fan_out = self._get_links()
                self.parent.transit(Extract(node=self.node, parent=self.parent))
            else:
                self.logger.warning("Invalid connection, from %s" % (self.node.url))
                self.node.label = "Web Connection Failed"
                self.parent.transit(Failed(node=self.node, parent=self.parent))
        except Exception as e:
            import traceback
            self.logger.error(traceback.print_exc())
            self.parent.transit(Failed(node=self.node, parent=self.parent))
    
    def pause(self):
        raise NotImplementedError
    
    def stop(self):
        raise NotImplementedError
    
    def _get_links(self) -> List[Node]:
        soup = bs(self.node.cache, 'html.parser')
        links = soup.find_all('a')
        fan_out = set()
        for link in links:
            href = link.get('href')
            if href:
                fan_out.add(href)
        
        nodes = []
        for href in fan_out:
            node = Node(url=href, fan_in=self.node.url, last_visited=datetime.timestamp(datetime.now()))
            nodes.append(node)
        return nodes