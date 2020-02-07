import boto3
import pprint
import random
from datetime import datetime, timedelta, timezone

client = boto3.client('ec2')

def handler(event, context):
    instanceid = event['detail']['instance-id']

    instance = client.describe_instances(
        InstanceIds=[instanceid]
    )['Reservations'][0]['Instances'][0]

    image = client.describe_images(
        ImageIds=[instance['ImageId']]
    )['Images'][0]

    platform = image['PlatformDetails']
    instance_capacity_reservation_id = None
    
    if 'Tags' in instance:
        for tag in instance['Tags']:
            if tag['Key'] == "AutoCapacityReservationId":
                instance_capacity_reservation_id = tag['Value']

    if event['detail']['state'] == "pending":
        if not instance_capacity_reservation_id:
            capacity_reservations = client.describe_capacity_reservations(
                Filters=[
                    {
                        'Name': 'state',
                        'Values': [
                            'active',
                        ]
                    },
                    {
                        'Name': 'availability-zone',
                        'Values': [
                            instance['Placement']['AvailabilityZone'],
                        ]
                    },
                    {
                        'Name': 'tag:Platform',
                        'Values': [
                            platform,
                        ]
                    },
                    {
                        'Name': 'instance-type',
                        'Values': [
                            instance['InstanceType'],
                        ]
                    },
                    {
                        'Name': 'tenancy',
                        'Values': [
                            instance['Placement']['Tenancy'],
                        ]
                    },
                    {
                        'Name': 'tag-key',
                        'Values': [
                            'AutoCapacityReservation',
                        ]
                    },
                ]
            )['CapacityReservations']

            capacity_reservation_id = None
            if len(capacity_reservations) > 0:
                print("Incrementing capacity reservation: {}".format(capacity_reservations[0]['CapacityReservationId']))
                client.modify_capacity_reservation(
                    CapacityReservationId=capacity_reservations[0]['CapacityReservationId'],
                    InstanceCount=capacity_reservations[0]['TotalInstanceCount'] + 1,
                )
                capacity_reservation_id = capacity_reservations[0]['CapacityReservationId']
            else:
                print("Creating capacity reservation")
                capacity_reservation = client.create_capacity_reservation(
                    ClientToken=str(random.random())[2:],
                    InstanceType=instance['InstanceType'],
                    InstancePlatform=platform,
                    AvailabilityZone=instance['Placement']['AvailabilityZone'],
                    Tenancy=instance['Placement']['Tenancy'],
                    InstanceCount=1,
                    EndDateType='unlimited',
                    InstanceMatchCriteria='open',
                    TagSpecifications=[
                        {
                            'ResourceType': 'capacity-reservation',
                            'Tags': [
                                {
                                    'Key': 'AutoCapacityReservation',
                                    'Value': 'true'
                                },
                                {
                                    'Key': 'Platform',
                                    'Value': platform
                                },
                            ]
                        },
                    ]
                )['CapacityReservation']
                capacity_reservation_id = capacity_reservation['CapacityReservationId']
            client.create_tags(
                Resources=[
                    instanceid,
                ],
                Tags=[
                    {
                        'Key': 'AutoCapacityReservationId',
                        'Value': capacity_reservation_id
                    },
                ]
            )

    elif event['detail']['state'] == "terminated":
        if instance_capacity_reservation_id:
            capacity_reservations = client.describe_capacity_reservations(
                Filters=[
                    {
                        'Name': 'state',
                        'Values': [
                            'active',
                        ]
                    },
                    {
                        'Name': 'availability-zone',
                        'Values': [
                            instance['Placement']['AvailabilityZone'],
                        ]
                    },
                    {
                        'Name': 'tag:Platform',
                        'Values': [
                            platform,
                        ]
                    },
                    {
                        'Name': 'instance-type',
                        'Values': [
                            instance['InstanceType'],
                        ]
                    },
                    {
                        'Name': 'tenancy',
                        'Values': [
                            instance['Placement']['Tenancy'],
                        ]
                    },
                    {
                        'Name': 'tag-key',
                        'Values': [
                            'AutoCapacityReservation',
                        ]
                    },
                ]
            )['CapacityReservations']

            if len(capacity_reservations) > 0 and capacity_reservations[0]['CapacityReservationId'] == instance_capacity_reservation_id:
                if capacity_reservations[0]['TotalInstanceCount'] <= 1:
                    print("Cancelling capacity reservation: {}".format(capacity_reservations[0]['CapacityReservationId']))
                    client.cancel_capacity_reservation(
                        CapacityReservationId=capacity_reservations[0]['CapacityReservationId']
                    )
                else:
                    print("Decrementing capacity reservation: {}".format(capacity_reservations[0]['CapacityReservationId']))
                    client.modify_capacity_reservation(
                        CapacityReservationId=capacity_reservations[0]['CapacityReservationId'],
                        InstanceCount=capacity_reservations[0]['TotalInstanceCount'] - 1,
                    )
    else:
        print("Unhandled state: {}".format(event['detail']['state']))
