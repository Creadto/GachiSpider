import json

def lambda_handler(event, context):
    result = dict()
    print(event)
    if len(event) > 1:
        raise RuntimeError
    
    try:
        record = event[0]['body']
        # SQS 메시지 본문 추출
        body = json.loads(record)
        
        # 메시지 처리 로직
        print(f"Received message: {body}")
        
        # 필요한 작업 수행
        url = body.get("url")
        db_ip = body.get("db_ip")
        db_port = body.get("db_port")
        del_nat_gateway = body.get("del_nat_gateway"),
        replace_nat_gateway = body.get("replace_nat_gateway")
        
        result.update({"statusCode": 200, "url": url, "db_ip": db_ip, "db_port": db_port,
                       "del_nat_gateway": del_nat_gateway, "replace_nat_gateway": replace_nat_gateway})  
        return result

    except Exception as e:
        # 예외 처리
        print(f"Error processing message: {e}")
        raise e  # 예외를 다시 던지면 Lambda가 실패 상태로 처리함