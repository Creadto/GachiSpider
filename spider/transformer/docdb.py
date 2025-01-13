from pymongo import MongoClient
from spider.structure import State
from spider.transformer.base import Transformer
from spider.utils.mongo import get_data_with, sync_database
from .state import Collect

class DocDBTransformer(Transformer):
    def __init__(self, db_ip, db_port, **kwargs):
        super(DocDBTransformer, self).__init__(**kwargs)
        self.logger.name = "DocDBTransformer"
        
        try:
            client = MongoClient(host=db_ip, port=db_port)
            self.logger.info("Mongo Client: {0}".format(client))
            server_info = client.server_info()
            self.logger.info("Server Information: {0}".format(server_info))
            self.collection = client['Pages']
            self.collection = self.collection['Nodes']
            self.alternatives = get_data_with(self.collection, label='store', root=kwargs['root'])
        except Exception as e:
            self.logger.error("Failed DB connection")
            self.collection = None
            self.alternatives = None    

    def run(self):
        for node in self.alternatives:
            self.state = Collect(node=node, parent=self)
            self.state.run()
            
            sync_database([self.state.node], self.collection, use_cache=True)
        return dict()
    
    def transit(self, next_state: State, auto_run: bool = True):          
        self.state = next_state
        
        if auto_run:
            self.state.run()