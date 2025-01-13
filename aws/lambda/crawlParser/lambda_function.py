import logging
from spider.crawler import LambdaCrawler
from spider.utils.logging import init_logging

def lambda_handler(event, context):
    kw_map = {'statusCode': 'status', 'message': 'message',
              'db_ip': 'db_ip', 'db_port': 'db_port', 'root': 'root'}
    
    kwargs = dict()
    for event_key, key in kw_map.items():
        kwargs[key] = event.get(event_key)
            
    if kwargs['status'] < 300:
        init_logging(logging.DEBUG, "parser-using-lambda.log", dir_path='/tmp/')
        parser = LambdaCrawler(**kwargs)
        
        if parser.collection == None:
            kwargs.update({'statusCode': 301, 'message': "Failed DB Connection"})
        else:
            for node in parser.alternatives:
                stub = {node.url: parser.crawl(node=node)}
                kwargs.update(stub)
            kwargs.update({'statusCode': 201, 'message': "Unclear Succeeded"})
    else:
        kwargs['statusCode'] = kwargs['status']
    return kwargs