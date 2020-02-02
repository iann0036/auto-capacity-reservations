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

    platform = "Linux/UNIX"
    if "Platform" in instance and instance['Platform'].lower() == "windows":
        platform = "Windows"
    
    if 'Tags' in instance:
        for tag in instance['Tags']:
            if tag['Key'] == "AutoCapacityReservationInstanceType":
                platform = tag['Value']

    if event['detail']['state'] == "pending":
        if 'CapacityReservationId' not in instance:
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

            if len(capacity_reservations) > 0:
                print("Incrementing capacity reservation: {}".format(capacity_reservations[0]['CapacityReservationId']))
                client.modify_capacity_reservation(
                    CapacityReservationId=capacity_reservations[0]['CapacityReservationId'],
                    InstanceCount=capacity_reservations[0]['TotalInstanceCount'] + 1,
                )
            else:
                print("Creating capacity reservation")
                client.create_capacity_reservation(
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
                )
        elif instance['LaunchTime'] > datetime.now(timezone.utc) - timedelta(minutes=1):
            # if the instance just launched and has claimed a capacity reservation, it's
            # either claimed a stopped instances spot or has a non-managed reservation

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

            if len(capacity_reservations) > 0 and capacity_reservations[0]['CapacityReservationId'] == instance['CapacityReservationId']:
                print("Incrementing capacity reservation: {}".format(capacity_reservations[0]['CapacityReservationId']))
                client.modify_capacity_reservation(
                    CapacityReservationId=capacity_reservations[0]['CapacityReservationId'],
                    InstanceCount=capacity_reservations[0]['TotalInstanceCount'] + 1,
                )
    elif event['detail']['state'] == "terminated":
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

        if len(capacity_reservations) > 0:
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
