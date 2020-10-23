terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
    }
  }
}

# Configure the AWS Provider
provider "aws" {
  region = "us-east-2"
  access_key = AWS_ACCESS_KEY_ID
  secret_key = AWS_SECRET_ACCESS_KEY
}

resource "aws_instance" "my-first-server" {
  ami           = "ami-07efac79022b86107"
  instance_type = "t2.micro"
  tags = {
    Name = "ubuntu"
  }
}

#Create VPC
resource "aws_vpc" "my_first_vpc" {
  cidr_block = "172.16.0.0/16"

  tags = {
    Name = "production"
  }
}

resource "aws_vpc" "my_second_vpc" {
  cidr_block = "172.18.0.0/16"

  tags = {
    Name = "dev"
  }
}

resource "aws_vpc" "prod-vpc" {
  cidr_block = "10.0.0.0/16"

  tags = {
    Name = "production"
  }
}

#Create Gateway
resource "aws_internet_gateway" "gw" {
  vpc_id = aws_vpc.prod-vpc.id

  tags = {
    Name = "main"
  }
}

# Create Route table
resource "aws_route_table" "prod-route-table" {
  vpc_id = aws_vpc.prod-vpc.id

  route {
    cidr_block = "0.0.0.0/0" #all traffic will be sent to the gateway
    gateway_id = aws_internet_gateway.gw.id
  }

  route {
    ipv6_cidr_block        = "::/0"
    gateway_id = aws_internet_gateway.gw.id
  }

  tags = {
    Name = "Prod"
  }
}

#Create Subnet
resource "aws_subnet" "subnet-new-1" {
  vpc_id = aws_vpc.prod-vpc.id
  cidr_block = "10.0.1.0/24"
  tags = {
    Name = "prod-subnet"
  } 
}

#Associate subnet with Route table 
resource "aws_route_table_association" "a" {
  subnet_id      = aws_subnet.subnet-new-1.id
  route_table_id = aws_route_table.prod-route-table.id
}

#Create securty group to allow ports 443, 80 and 22
resource "aws_security_group" "allow_web" {
  name        = "allow_web_traffic"
  description = "Allow Web inbound traffic"
  vpc_id = aws_vpc.prod-vpc.id

  ingress {
    description = "HTTPS"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "allow_web"
  }
}

#Create network interface with an IP from subnet (this creates a private IP address )
resource "aws_network_interface" "web-server-ni   c" {
  subnet_id       = aws_subnet.subnet-new-1.id
  private_ips     = ["10.0.1.50"]
  security_groups = [aws_security_group.allow_web.id]
}

#Set elastic IP addres (public IP adress )
resource "aws_eip"   "one"  {
  vpc       = true
  network_interface = aws_network_interface.web-server-nic.id
  associate_with_private_ip = "10.0.1.50"
  depends_on = [aws_internet_gateway.gw] 
}

#Create Ubunbut server and install apace
resource "aws_instance" "web-server-instance" {
  ami = "ami-07efac79022b86107"
  instance_type = "t2.micro"
  key_name = "jina-aws-key"

  network_interface {
    device_index = 0
    network_interface_id = aws_network_interface.web-server-nic.id
  }
  user_data = <<-EOF
              #!/bin/bash
              sudo apt update -y
              sudo apt install apache2 -y
              sudo systemctl start apache2
              sudo bash -c 'echo first web server   > /var/www/html/index.html'
              EOF
  tags = {
    "Name" = "web-server"
  }
}

# Configure the Docker provider
provider "docker" {
  host = docker_host
  registry_auth {
    address  = "https://registry.docker.io/v2/jina-ai/jina"
    username = docker_username
    password = docker_password
  }
}

# Create a container
resource "docker_container" "jina_southpark" {
  image = "${docker_image.southparkimage}"
  name  = "jina_southpark"
}

# Find the latest southpark precise image.
resource "docker_image" "southparkimage" {
  name = "jinaai/hub.app.distilbert-southpark"
}