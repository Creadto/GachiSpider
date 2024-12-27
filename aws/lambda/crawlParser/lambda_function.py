import logging
from spider.crawler import LambdaCrawler
from spider.utils.logging import init_logging

def lambda_handler(event, context):
    kw_map = {'statusCode': 'status', 'message': 'message',
              'db_ip': 'db_ip', 'db_port': 'db_port',
              'del_nat_gateway': 'del_nat_gateway'}
    
    kwargs = dict()
    for event_key, key in kw_map.items():
        kwargs[key] = event.get(event_key)

    init_logging(logging.DEBUG, "parser-using-lambda.log", dir_path='/tmp/')
    parser = LambdaCrawler(**kwargs)
    
    result_dict = kwargs
    if parser.collection == None:
        result_dict.update({'statusCode': 301, 'message': "Failed DB Connection"})
    else:
        for node in parser.alternatives:
            stub = {node.url: parser.crawl(node=node)}
            result_dict.update(stub)
        result_dict.update({'statusCode': 201, 'message': "Unclear Succeeded"})
    return result_dict