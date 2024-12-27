import logging
import requests
from urllib.parse import urljoin
from spider.structure import Node, State
from spider.utils.matcher import Matcher
from .state import Fetch

class Crawler:
    def __init__(self, init_url, valid_robots=False, name="Crawler"):
        self.logger = logging.getLogger(name=name)
        self.init_url, self.matcher = None, None
        if init_url is not None:
            self.init_url = init_url
            
            response = requests.get(urljoin(base=self.init_url, url='robots.txt'))
            self.matcher = Matcher(mass=response.text)
        
        self.name = name
        self.state = None
        self.cache = None
        self.trajectory = set()
    
    def crawl(self, url):
        if url in self.trajectory:
            return
        
        self.trajectory.add(url)
        allow, reason = True, ""
        if self.matcher is not None:
            allow, reason = self.matcher.allow_by(url=url)
        self.logger.info("%s, %s, url:%s" % (allow, reason, url))
        if allow:
            return self.transit(Fetch(Node(url=url), parent=self))
        
    def transit(self, next_state: State, auto_run: bool = True):          
        self.state = next_state
        if auto_run:
            self.state.run()
    
    def eliminate_duplicated_data(self, nodes, collection):
        duplicated_dict = dict()
        for node in nodes:
            if node.url not in duplicated_dict:
                duplicated_dict[node.url] = []
            duplicated_dict[node.url].append(node)
        
        for url, node_list in duplicated_dict.items():
            if len(node_list) == 1:
                continue
            for idx in range(1, len(node_list)):
                query = {'url': node_list[idx].url, "last_visited": node_list[idx].last_visited}
                result = collection.delete_one(query)
        
        return nodes[0]
