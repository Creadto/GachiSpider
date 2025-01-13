import logging
from spider.manager.linker import CloudLinker
from spider.utils.logging import init_logging

def lambda_handler(event, context):
    kw_map = {'statusCode': 'status', 'message': 'message',
              'url': 'root', 'db_ip': 'db_ip', 'db_port': 'db_port'}
    
    kwargs = dict()
    for event_key, key in kw_map.items():
        kwargs[key] = event.get(event_key)
    
    init_logging(logging.INFO, "link-manager-using-lambda.log", dir_path='/tmp/')
    link_manager = CloudLinker(init_url=None, db_ip=kwargs['db_ip'], db_port=kwargs['db_port'])
    
    if link_manager.collection == None:
        kwargs.update({'statusCode': 301, 'message': "Failed DB Connection"})
    else:
        kwargs.update(link_manager.crawl(url=kwargs['root']))
    
    return kwargs