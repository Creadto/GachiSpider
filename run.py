import json
import logging
import os.path as osp
import time

import boto3
from botocore.exceptions import ClientError
from spider.scheduler import GachigaScheduler
from spider.utils.logging import init_logging

def get_json(root, filename):
    with open(osp.join(root, filename)) as f:
        config = json.load(f)
    
    return config

def get_secret(name, region, pem, key, **kwargs):
    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region,
        **key
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=name
        )
    except ClientError as e:
        raise e

    secret = json.loads(get_secret_value_response['SecretString'])
    username = secret["username"]
    password = secret["password"]
    host = secret["host"]
    port = secret.get("port", 27017)
    
    # MongoDB URI 설정
    uri = f"mongodb://{username}:{password}@{host}:{port}/?ssl=true&retryWrites=false&tlsAllowInvalidCertificates=true"
    
    args = {
        'username': username,
        'password': password,
        'host': host,
        'port': port,
        'uri': uri
    }
    return args
           
def main():
    config_root = "./spider/configs"
    credential_root = "./credential/aws_authorization_key"
    credential_config = get_json(credential_root, "iam.json")
    scheduler_config = get_json(config_root, "scheduler.json")
    root_nodes = get_json(config_root, "root nodes.json")
    db_config = get_secret(**credential_config['document-db'])
    
    
    scheduler_config['DocDB']['args']['host'] = db_config['uri']
    scheduler_config['Queue']['args'] = credential_config['sqs']['key']
    scheduler_config['Queue']['endpoint'] = credential_config['sqs']['url']
    scheduler_config['Nat']['args'] = credential_config['stepfunctions']['key']
    scheduler_config['Nat']['endpoint'] = credential_config['stepfunctions']['arn']
    scheduler_config['Roots'] = root_nodes
    
    init_logging(logging.INFO, "scheduler.log")
    scheduler = GachigaScheduler(scheduler_config, **scheduler_config['Engine'])
    while True:
        events_result = scheduler.step()
        time.sleep(3)

if __name__ == "__main__":
    main()