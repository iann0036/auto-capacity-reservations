import boto3
import pprint
import random

client = boto3.client('ec2')

def handler(event, context):
    instanceid = event['detail']['instance-id']

    instance = client.describe_instances(
        InstanceIds=[instanceid]
    )['Reservations'][0]['Instances'][0]

    if event['detail']['state'] == "pending":
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
                {
                    'Name': 'tag:ImageId',
                    'Values': [
                        instance['ImageId'],
                    ]
                },
            ]
        )['CapacityReservations']

        if len(capacity_reservations) > 0:
            pass # TODO
        else:
            client.create_capacity_reservation(
                ClientToken=str(random.random())[2:],
                InstanceType=instance['InstanceType'],
                InstancePlatform='Linux/UNIX',
                AvailabilityZone=instance['Placement']['AvailabilityZone'],
                Tenancy=instance['Placement']['Tenancy'],
                InstanceCount=1,
                #EbsOptimized=True|False,
                #EphemeralStorage=True|False,
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
                                'Key': 'ImageId',
                                'Value': instance['ImageId']
                            },
                        ]
                    },
                ]
            )
    elif event['detail']['state'] == "terminated":
        pass # TODO
    else:
        print("Unhandled state: {}".format(event['detail']['state']))
