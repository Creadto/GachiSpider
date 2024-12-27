import logging
from pymongo import MongoClient
from typing import List

from spider.structure import Node, State
from spider.utils.errors import get_error_code
from spider.utils.mongo import sync_database
from .state import Fetch
from .base import Linker

class CloudLinker(Linker):
    def __init__(self, init_url, db_ip: str, db_port: int=27017):
        super(CloudLinker, self).__init__(init_url=init_url)
        self.logger = logging.getLogger(name="LinkManager")
        self.logger.info("Initialize LinkManager as Cloud Linker")
        self.state = Node(url=init_url)
        self.logger.info("Try to connect runtime db")
        try:
            client = MongoClient(host=db_ip, port=db_port)
            self.logger.info("Mongo Client: {0}".format(client))
            server_info = client.server_info()
            self.logger.info("Server Information: {0}".format(server_info))
            runtime_db = client['Pages']
            self.collection = runtime_db['Nodes']
        except Exception as e:
            self.logger.error("Failed DB connection")
            self.collection = None
        self.alternatives = []
        
    def crawl(self, url):
        result_dict = dict()
        self.state.url = url
        self.logger.info("Fetch url: %s" % (self.state.url))
        state = Fetch(node=self.state, parent=self)
        state.run()
        
        if self.state.name.lower() == "succeeded":
            self.logger.info("Eliminate URLs on Freshness after matched runtime DB")
            try:
                self.alternatives = sync_database(self.state.node.fan_out, self.collection)
                self.logger.info("Prioritize URLs")
                self.alternatives.sort(key=lambda node: node.freshness, reverse=True)
                
                self.logger.info("Validate robots")
                if self.matcher is not None:
                    allow, reason = self.matcher.allow_by(url=self.alternatives[0].url)
                
            except Exception as e:
                self.logger.error("Failed DB Access during CRUD")
                self.state.node.label = "CRUD Failed"
                self.alternatives = []
        
        code = get_error_code(self.state.node.label)
        return {
            'statusCode': code,
            'message': self.state.node.label,
            'urls': [x.url for x in self.alternatives]
            }
    
    def transit(self, next_state: State, auto_run: bool = True):          
        self.state = next_state
        
        if auto_run:
            self.state.run()