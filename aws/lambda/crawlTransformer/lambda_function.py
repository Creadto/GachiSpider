import logging
from spider.transformer import DocDBTransformer
from spider.utils.logging import init_logging

def lambda_handler(event, context):
    kw_map = {'statusCode': 'status', 'message': 'message',
              'db_ip': 'db_ip', 'db_port': 'db_port',
              'del_nat_gateway': 'del_nat_gateway'}
    
    kwargs = dict()
    for event_key, key in kw_map.items():
        kwargs[key] = event.get(event_key)

    init_logging(logging.INFO, "transform-to-rdb-using-lambda.log", dir_path='/tmp/')
    transformer = DocDBTransformer(**kwargs)
    
    result_dict = kwargs
    if transformer.alternatives == None:
        result_dict.update({'statusCode': 301, 'message': "Failed DB Connection"})
    else:
        result = transformer.run()
        result_dict.update(result)
        result_dict.update({'statusCode': 200, 'message': "Unclear Succeeded"})
    return result_dict
