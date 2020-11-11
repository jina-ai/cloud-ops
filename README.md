# cloud-ops

## 🚀 Terraform 

### Getting started with setting up AWS resources with Terraform

To use terraform scripts, users could firstly initialise via `aws configure`:
- Run terraform init this will download the aws plugin
- Run sudo apt install awscli to install awscli
- Run aws configure to configure with access keys, secret key:
`aws configure`
```
AWS Access Key ID [None]:
AWS Secret Access Key [None]:
Default region name [None]: us-east-2
Default output format [None]:
```
- Run `terraform plan` for dry-run of the script
Advantages of this approach is it avoids exposing of any secret keys in the script
This spots any errors before actually applying changes
- Run `terraform apply` to actually apply these changes
- Run `terraform apply --target=<resource-name>` to spin up a particular resource only
- Run `terraform destroy` to release all the spinned up resources. Likewise use `--target` flag for destroying a particular resource

Following terraform script spins up:
1. Configure the AWS Provider
2. Creates VPC (3 VPC)
3. Creates a Gateway
4. Creates Route table
5. Creates Subnet
6. Associate subnet with Route table 
7. Create security group to allow ports 443, 80 and 22<br/>
8. Create network interface with an IP from subnet <br/>
9. Create elastic IP addres<br/>
10. Create Ubunbut server and install apace<br/>

### Run it
To run this, initialize with `terraform init`
This will create the .terraform and you can run it now wih the command `terraform apply`.
Also you can run `terraform plan` first to see what the changes will be as well as to update the state.

## 🚀 Hub api deployment

## 🚀 Lambda handlres

## 🚀 Stress test trigger

Generic AWS framework built on boto3 for Jina's usage. This can be reused for other tests/activities to be triggered on AWS

#### Cloudformation

Creates [Cloudformation](https://aws.amazon.com/cloudformation/) stack on AWS (Following can be customized)
- EC2 instance
- Volume
- Elastic IP
  
#### SSM Document

Creates [SSM Document](https://docs.aws.amazon.com/systems-manager/latest/userguide/ssm-agent.html) (Way to run long-running commands on ec2)
- Mounts Volume on ec2
- Compiles [jina](https://github.com/jina-ai/jina) from pip or git (any remote branch)
- Clones [jina-ai/stress-test](https://github.com/jina-ai/stress-test) from any remote branch
- Runs stress-test on ec2
- Gets results pushed to public s3 bucket `aws:s3:::stress-test-jina` bucket