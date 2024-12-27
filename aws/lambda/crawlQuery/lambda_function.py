import logging
import os

from pymongo import MongoClient

from spider.query import GachiGaHandler
from spider.structure import Node
from spider.utils.logging import init_logging
from spider.utils.mongo import get_data_with, sync_database

def lambda_handler(event, context):
    kw_map = {'statusCode': 'status', 'message': 'message',
              'nodes': 'nodes', 'db_ip': 'db_ip', 'db_port': 'db_port',
              'del_nat_gateway': 'del_nat_gateway'}
    
    kwargs = dict()
    for event_key, key in kw_map.items():
        kwargs[key] = event.get(event_key)

    init_logging(logging.INFO, "query-to-rdb-using-lambda.log", dir_path='/tmp/')
    handler_kwargs = {
        "host": os.getenv("host"),
        "user": os.getenv("user"),
        "password": os.getenv("password"),
        "database": os.getenv("database"),
    }
    try:
        client = MongoClient(host=kwargs['db_ip'], port=kwargs['db_port'])
        server_info = client.server_info()
        print(server_info)
        collection = client['Pages']
        collection = collection['Nodes']
        kwargs['nodes'] = get_data_with(collection, label='Transformed')
            
        handler = GachiGaHandler(**handler_kwargs)
        for node in kwargs['nodes']:
            processed_node = handler.run(node=node)
            sync_database([processed_node], collection, use_cache=False)
        handler.db_client.close()
        return {'statusCode': 200, 'message': "Succeeded", "del_nat_gateway": kwargs['del_nat_gateway']}
    
    except Exception as e:
        return {'statusCode': -1, 'message': "Unexpected exit", "del_nat_gateway": kwargs['del_nat_gateway']}

def make_dummy_nodes(db_ip, db_port=None):
    from pymongo import MongoClient
    from spider.utils.mongo import get_data_with
    
    client = MongoClient(host=db_ip, port=db_port)
    server_info = client.server_info()
    collection = client['Pages']
    collection = collection['Nodes']
    
    alternatives = get_data_with(collection, label='Transformed')
    return [x.to_dict() for x in alternatives]
