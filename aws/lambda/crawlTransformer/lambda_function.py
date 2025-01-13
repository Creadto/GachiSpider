import logging
from spider.transformer import DocDBTransformer
from spider.utils.logging import init_logging

def lambda_handler(event, context):
    kw_map = {'statusCode': 'status', 'message': 'message',
              'db_ip': 'db_ip', 'db_port': 'db_port', 'root': 'root'}
    
    kwargs = dict()
    for event_key, key in kw_map.items():
        kwargs[key] = event.get(event_key)

    if kwargs['status'] < 300:
        init_logging(logging.INFO, "transform-to-rdb-using-lambda.log", dir_path='/tmp/')
        transformer = DocDBTransformer(**kwargs)
        
        if transformer.alternatives == None:
            kwargs.update({'statusCode': 301, 'message': "Failed DB Connection"})
        else:
            result = transformer.run()
            kwargs.update(result)
            kwargs.update({'statusCode': 200, 'message': "Unclear Succeeded"})
    
    else:
        kwargs['statusCode'] = kwargs['status']
    return kwargs
