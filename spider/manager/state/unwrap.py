import copy
from typing import List
from spider.structure import Node, State
from spider.utils.web import get_unwrapped_url
from .failed import Failed
from .succeeded import Succeeded


class Unwrap(State):
    def __init__(self, node: Node, parent):
        super(Unwrap, self).__init__("unwrap", node=node, parent=parent)
        
    def run(self):
        try:
            self.logger.info("Unwrap redirected URLs with Check available site")
            self.node.fan_out = self._check_sanity(copy.deepcopy(self.node.fan_out))
            self.node.label = "Succeeded"
            self.parent.transit(Succeeded(node=self.node, parent=self.parent))
        except Exception as e:
            self.node.label = "Failed Attach Base URL"
            self.parent.transit(Failed(node=self.node, parent=self.parent))
    
    def pause(self):
        raise NotImplementedError
    
    def stop(self):
        raise NotImplementedError
    
    def _check_sanity(self, nodes: List[Node]) -> List[Node]:
        for i, node in enumerate(nodes):
            # 여기까진 pure한 상태라 label이 있을 수가 없음
            if node.label is not None:
                continue
            
            contents, url = get_unwrapped_url(node.url)
            if url is not None:
                nodes[i].url = url
                nodes[i].cache = contents
                nodes[i].label = "Unwrapped"
            else:
                self.logger.info("Unwrap failed url: %s" % (node.url))
                nodes[i].label = "Unwrap Failed"
        return nodes
