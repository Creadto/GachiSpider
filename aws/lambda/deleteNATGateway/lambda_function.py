import os
import boto3


# 새로운 NAT Gateway를 생성하고 라우팅 테이블을 업데이트하는 함수
def lambda_handler(event, context):
    
    if event.get("del_nat_gateway") == False:
        return {
            'statusCode': 200,
            'message': "No NAT Gateway to delete."
        }
    
    vpc_id = os.getenv("vpc_id")
    route_table_id = os.getenv("route_table_id")
    subnet_id = os.getenv("subnet_id")
    # AWS 클라이언트 초기화
    aws_client = boto3.client('ec2', region_name='ap-northeast-2')

    # 1. 기존 라우팅 테이블에서 NAT Gateway 대상 삭제
    routes = aws_client.describe_route_tables(RouteTableIds=[route_table_id])['RouteTables'][0]['Routes']
    for route in routes:
        if route.get('NatGatewayId'):  # NAT Gateway가 대상인 라우트
            aws_client.delete_route(RouteTableId=route_table_id, DestinationCidrBlock=route['DestinationCidrBlock'])
            print(f"Deleted route for NAT Gateway {route['NatGatewayId']}")

            aws_client.delete_nat_gateway(NatGatewayId=route['NatGatewayId'])

            # NAT Gateway가 삭제될 때까지 대기
            waiter = aws_client.get_waiter('nat_gateway_deleted')
            waiter.wait(NatGatewayIds=[route['NatGatewayId']])
            print(f"NAT Gateway {route['NatGatewayId']} deleted.")
            
    # 2. 연결 ID없는 탄력적 IP 제거
    addresses = aws_client.describe_addresses()['Addresses']
    for address in addresses:
        allocation_id = address['AllocationId']
        association_id = address.get('AssociationId')
        if not association_id:
            print(f"Releasing unassociated Elastic IP: {address['PublicIp']} (Allocation ID: {allocation_id})")
            aws_client.release_address(AllocationId=allocation_id)
            
    return {
        'statusCode': 200,
        'message': ""
    }