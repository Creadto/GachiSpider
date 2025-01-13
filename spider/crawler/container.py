import logging

from pymongo import MongoClient
from spider.crawler.base import Crawler
from spider.structure import Node, State
from spider.utils.errors import get_error_code
from spider.utils.mongo import get_data_with
from .state import Fetch, UpdateMongo


class LambdaCrawler(Crawler):
    def __init__(self, db_ip, db_port, **kwargs):
        super(LambdaCrawler, self).__init__(init_url=None)
        self.logger = logging.getLogger(name="Lambda script")
        
        try:
            client = MongoClient(host=db_ip, port=db_port)
            self.logger.info("Mongo Client: {0}".format(client))
            server_info = client.server_info()
            self.logger.info("Server Information: {0}".format(server_info))
            self.collection = client['Pages']
            self.collection = self.collection['Nodes']
            
            self.alternatives = get_data_with(self.collection, label='Unwrapped', root=kwargs['root'])
        except Exception as e:
            self.logger.error("Failed DB connection")
            self.collection = None
        
    def crawl(self, node):
        if node.label.lower() == "unwrapped":
            self.state = Fetch(node=node, parent=self)
            self.state.run()
            message = self.state.node.label
        else:
            message = "Unrecognized error"
            
        code = get_error_code(message)
        return {
            'statusCode': code,
            'message': message,
            }
    
    def transit(self, next_state: State, auto_run: bool = True):
        self.state = next_state
        if next_state.name == "store":
            self.state = UpdateMongo(node=next_state.node, parent=self,
                                     collection=self.collection)         
        elif next_state.name == "failed":
            self.state = UpdateMongo(node=next_state.node, parent=self,
                                     collection=self.collection,
                                     leaf=True, label_pass=True)
        if auto_run:
            self.state.run()