# jina-terraform
Terraform for provisioning cloud resources on providers like AWS for Jina.

The main.tf will follow the next steps:


1. Configure the AWS Provider: <br/> Hardcode the region there, otherwise Amazon will set it randomly and sometimes the subnet and the interface `availabitiy_zones` won't match
2. Create VPC 
3. Create Gateway
4. Create Route table<br/>
    ```
    route {
        cidr_block = "0.0.0.0/0" #all traffic will be sent to the gateway
        gateway_id = aws_internet_gateway.gw.id
    }
    ```
    Here we define the routes for the Route table, and from the subnet specified we'll send it to the Gateway. Becuase in this case the subnet is 0.0.0.0/0, all traffic will be send to the Gateway
5. Associate subnet with Route table 
6. Create security group to allow all ports<br/>
    This will expose the ports for different rquests, `HTTPS`, `HTTP` and `SSH` in that order
    We could also specify a range of ports here but we're using only those ones 
    For the `egress` we are allowing all ports and any protocol, that is set with -1
7. Create network interface with an IP from subnet <br/>
    We need to pick here an IP address from the subnet. 
    This is actually a list `private_ips     = ["10.0.1.50"]` so we could  give more than one if necessary 
8. Create elastic IP addres<br/>
    `depends_on = [aws_internet_gateway.gw]` this is needed because it depends on the gateway, so the gateway needs to be deployed first
9. Create Ubunbut server and install apace<br/>

# Run it
To run this, initialize with `terraform init`
This will create the .terraform and you can run it now wih the command `terraform apply`.
Also you can run `terraform plan` first to see what the changes will be as well as to update the state.