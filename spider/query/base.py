
from datetime import datetime
import logging

import pymysql

from spider.structure import State


class Handler:
    def __init__(self, **kwargs):
        self.logger = logging.getLogger(name="QueryHandler")
      
        try:
            self.db_client = pymysql.connect(**kwargs)
            self.created_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        except Exception as e:
            raise ConnectionError

    def __del__(self):
        self.db_client.close()    
        
    def run(self):
        pass
    
    def transit(self, next_state: State, auto_run: bool = True):          
        self.state = next_state
        
        if auto_run:
            self.state.run()