# Stress Tests on AWS

Generic AWS framework built on boto3 for Jina's usage. This can be reused for other tests/activities to be triggered on AWS

#### Cloudformation

Creates [Cloudformation](https://aws.amazon.com/cloudformation/) stack on AWS (Following can be customized)
- EC2 instance
  - [Instance Type](https://aws.amazon.com/ec2/instance-types/)
  - [AMI](https://docs.aws.amazon.com/systems-manager/latest/userguide/ssm-agent.html)
  - [Availability Zone](https://howto.lintel.in/list-of-aws-regions-and-availability-zones/)
- Volume
  - Volume Size
  - [Volume Type](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ebs-volume-types.html)
- Elastic IP
  


#### SSM Document

Creates [SSM Document](https://docs.aws.amazon.com/systems-manager/latest/userguide/ssm-agent.html) (Way to run long-running commands on ec2)
- Mounts Volume on ec2
- Compiles [jina](https://github.com/jina-ai/jina) from pip or git (any remote branch)
- Clones [jina-ai/stress-test](https://github.com/jina-ai/stress-test) from any remote branch
- Runs stress-test on ec2
- Gets results pushed to public s3 bucket `aws:s3:::stress-test-jina` bucket


##### Pending
- Push cloudwatch metrics/dashboard to get CPU, Disk utilization metrics
- Push other result objects to S3