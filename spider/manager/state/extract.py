from urllib.parse import urljoin, urlparse
from spider.structure import Node, State
from spider.utils.io import get_form
from spider.utils.web import get_base_url
from .failed import Failed
from .unwrap import Unwrap


class Extract(State):
    def __init__(self, node: Node, parent):
        super(Extract, self).__init__("extract", node=node, parent=parent)
        
    def run(self):
        try:
            self.logger.info("Extract fan out links from fetched html")
            base_url = get_base_url(self.node.url)
            for i, node in reversed(list(enumerate(self.node.fan_out))):
                parsed_url = urlparse(node.url)              
                if parsed_url.hostname == None:
                    self.node.fan_out[i].url = urljoin(base_url, node.url)
                
                form_dict = get_form(node=node, logger=self.logger)
                self.node.fan_out[i] = form_dict['node']
                if form_dict['form'] is None:
                    self.node.fan_out[i].label = "Not found correct form"          
            self.parent.transit(Unwrap(node=self.node, parent=self.parent))
        except Exception as e:
            self.node.label = "Failed Attach Base URL"
            self.parent.transit(Failed(node=self.node, parent=self.parent))
    
    def pause(self):
        raise NotImplementedError
    
    def stop(self):
        raise NotImplementedError
