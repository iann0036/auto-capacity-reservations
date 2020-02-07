# Automatic Capacity Reservations

When deployed, EC2 instances will automatically be assigned to a [capacity reservation](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-capacity-reservations.html) which will be maintained at the number of running instances that are matched.

The solution uses EventBridge Rules that react to EC2 instance state changes by invoking a Lambda that creates/increments/decrements or cancels capacity reservations based on the number of instances that match. Instances will be tagged with a `AutoCapacityReservationId` tag which indicates the assigned capacity reservation.

The solution is intended to provide guaranteed capacity for instances that are in a stopped or degraded state. Capacity reservations will be maintained for the entire lifecycle of an EC2 instance until termination. The capacity reservations are deliberately left in an `open` state so degraded instances can be easily replaced.

## Installation

[![Launch Stack](https://cdn.rawgit.com/buildkite/cloudformation-launch-stack-button-svg/master/launch-stack.svg)](https://console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/new?stackName=auto-capacity-reservations&templateURL=https://s3.amazonaws.com/ianmckay-us-east-1/auto-capacity-reservations/template.yml)

Click the above link to deploy the stack to your environment. The capacity reservation provider will be effective for all instances launched within the region after the stack is created.

If you prefer, you can also manually upsert the [template.yml](https://github.com/iann0036/auto-capacity-reservations/blob/master/template.yml) stack from source and compile your own copy of the Lambda source. Please note that if you do this, the Python requirements must be included in the deployment package.

## Instance Platform Support

With the [recent introduction](https://aws.amazon.com/about-aws/whats-new/2020/02/amazon-ec2-adds-ability-to-easily-query-billing-information-of-amazon-machine-images/) of full platform information in the DescribeImages API method, capacity reservations can now support all platform types out of the box, which are:

* Linux/UNIX
* Red Hat Enterprise Linux
* SUSE Linux
* Windows
* Windows with SQL Server
* Windows with SQL Server Enterprise
* Windows with SQL Server Standard
* Windows with SQL Server Web
* Linux with SQL Server Standard
* Linux with SQL Server Web
* Linux with SQL Server Enterprise

## Feedback

All feedback, issues or pull requests are welcomed to be raised in the project. This project is MIT licensed.
