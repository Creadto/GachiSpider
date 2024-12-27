import os
import re
import pickle
from urllib.parse import urlparse, urljoin
from spider.structure import Node, State
from spider.utils.mongo import sync_database
from .failed import Failed
from .succeeded import Succeeded

class UpdateMongo(State):
    def __init__(self, node: Node, parent, collection, label_pass=False, leaf=False):
        super(UpdateMongo, self).__init__("store", node=node, parent=parent, label_pass=label_pass)
        self.leaf = leaf
        self.collection = collection
        
    def run(self):
        try:
            result = sync_database(nodes=[self.node], collection=self.collection, use_cache=False)
            if not self.leaf:
                self.parent.transit(Succeeded(node=self.node, parent=self.parent))
        except:
            self.node.label = "DB update failed"
            if not self.leaf:
                self.parent.transit(Failed(node=self.node, parent=self.parent))
            
    def pause(self):
        raise NotImplementedError
    
    def stop(self):
        raise NotImplementedError
    
      
class StoreLocal(State):
    def __init__(self, node: Node, parent, root='./datalake/red_zone'):
        super(StoreLocal, self).__init__("store", node=node, parent=parent)
        self.root = root
        
    def run(self):
        try:
            if not os.path.exists(self.root):
                self.logger.warning("Not found root directory, Made temp directory to : %s" % self.root)
                os.makedirs(self.root)
            self._store_node()
            self.parent.transit(Succeeded(node=self.node, parent=self.parent))
        except:
            self.parent.transit(Failed(node=self.node, parent=self.parent))
            
    def pause(self):
        raise NotImplementedError
    
    def stop(self):
        raise NotImplementedError
    
    def _store_node(self):
        parsed_url = urlparse(self.node.url.replace('www.', ''))
        folder_path = os.path.join(self.root, parsed_url.netloc)
        if not os.path.exists(folder_path):
            os.mkdir(folder_path)
        numbers = re.findall(self.node.pattern, urljoin(parsed_url.path, parsed_url.query))
        numbers = re.findall(r"\d+", numbers[0])
        full_path = os.path.join(folder_path, numbers[0] + '.pkl')
        self.node.cache = None
        with open(full_path, 'wb') as f:
            pickle.dump(self.node, f, pickle.HIGHEST_PROTOCOL)