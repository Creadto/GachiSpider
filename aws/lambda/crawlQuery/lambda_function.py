import logging
import os

from pymongo import MongoClient

from spider.query import GachiGaHandler
from spider.structure import Node
from spider.utils.logging import init_logging
from spider.utils.mongo import get_data_with, sync_database

def lambda_handler(event, context):
    kw_map = {'statusCode': 'status', 'message': 'message',
              'root': 'root', 'db_ip': 'db_ip', 'db_port': 'db_port'}
    
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
    database = None
    try:
        client = MongoClient(host=kwargs['db_ip'], port=kwargs['db_port'])
        server_info = client.server_info()
        print(server_info)
        database = client['Pages']
        collection = database['Nodes']
        kwargs['nodes'] = get_data_with(collection, label='Transformed', root=kwargs['root'])
            
        handler = GachiGaHandler(**handler_kwargs)
        for node in kwargs['nodes']:
            processed_node = handler.run(node=node)
            sync_database([processed_node], collection, use_cache=False)
        kwargs.update({'statusCode': 200, 'message': "Succeeded"})
    
    except Exception as e:
        kwargs.update({'statusCode': -1, 'message': "Unexpected Error"})
               
    if database:
        if kwargs['statusCode'] < 300:
            job_state = 'inactive'
        else:
            job_state = 'pending'

        filter_condition = {"url": kwargs['root']}
        update_operation = {"$set": {"status": job_state}}
        
        result = database['JobTable'].update_many(filter_condition, update_operation)
        print(result)
        
    return kwargs

def make_dummy_nodes(db_ip, db_port=None):
    from pymongo import MongoClient
    from spider.utils.mongo import get_data_with
    
    client = MongoClient(host=db_ip, port=db_port)
    server_info = client.server_info()
    collection = client['Pages']
    collection = collection['Nodes']
    
    alternatives = get_data_with(collection, label='Transformed')
    return [x.to_dict() for x in alternatives]
