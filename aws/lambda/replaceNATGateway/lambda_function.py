import os
import boto3


# 새로운 NAT Gateway를 생성하고 라우팅 테이블을 업데이트하는 함수
def lambda_handler(event, context):
    kw_map = {'del_nat_gateway': 'del_nat_gateway',
              'replace_nat_gateway': 'replace_nat_gateway'}
    
    
    kwargs = dict()
    for event_key, key in kw_map.items():
        kwargs[key] = event.get(event_key)
    
    kwargs.update({'statusCode': 200, 'message': ""})
    
    if kwargs['replace_nat_gateway'] == False:
        return kwargs
    
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
            
    # 2. Elastic IP 생성
    eip = aws_client.allocate_address(Domain='vpc')
    allocation_id = eip['AllocationId']
    print(f"Allocated Elastic IP: {eip['PublicIp']} (Allocation ID: {allocation_id})")

    # 3. NAT Gateway 생성
    nat_gateway = aws_client.create_nat_gateway(SubnetId=subnet_id, AllocationId=allocation_id,
                                                TagSpecifications=[{
                                                    'ResourceType': 'natgateway',
                                                    'Tags': [{'Key': 'Name', 'Value': 'crawler-nat-replicable'}]
                                                    }]
                                                )
    nat_gateway_id = nat_gateway['NatGateway']['NatGatewayId']
    print(f"Created NAT Gateway: {nat_gateway_id}")

    # NAT Gateway가 활성화될 때까지 대기
    waiter = aws_client.get_waiter('nat_gateway_available')
    waiter.wait(NatGatewayIds=[nat_gateway_id])
    print(f"NAT Gateway {nat_gateway_id} is now available.")
            
    # 5. 모든 대상(0.0.0.0/0)을 새 NAT Gateway로 라우팅
    aws_client.create_route(
        RouteTableId=route_table_id,
        DestinationCidrBlock='0.0.0.0/0',
        NatGatewayId=nat_gateway_id
    )
    
    print("Checking for unassociated Elastic IPs...")
    # 6. 연결 ID없는 탄력적 IP 제거
    addresses = aws_client.describe_addresses()['Addresses']
    for address in addresses:
        allocation_id = address['AllocationId']
        association_id = address.get('AssociationId')
        if not association_id:
            print(f"Releasing unassociated Elastic IP: {address['PublicIp']} (Allocation ID: {allocation_id})")
            aws_client.release_address(AllocationId=allocation_id)
    
    return kwargs