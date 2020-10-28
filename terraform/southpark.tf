provider "aws" {
  version = "~> 2.0"
  region  = "us-east-2"
}

#Create repo
resource "aws_ecr_repository" "southpark" {
  name = "sp-repo" # Naming my repository
  tags = {
    Name = "southpark_repo"
  }
}

resource "aws_default_vpc" "default_vpc" {
}

data "aws_subnet_ids" "default" {
  vpc_id = "${aws_default_vpc.default_vpc.id}"
}


resource "aws_ecs_cluster" "southpark_cluster" {
  name = "southpark_cluster" # Naming the cluster
}

#Create role
resource "aws_iam_role_policy_attachment" "ecsTaskExecutionRole_policy" {
  role       = "${aws_iam_role.ecsExecutionRole.name}"
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_role" "ecsExecutionRole" {
  name               = "ecsExecutionRole"
  assume_role_policy = "${data.aws_iam_policy_document.assume_role_policy.json}"
}

data "aws_iam_policy_document" "assume_role_policy" {
  statement {
    effect = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

#Create task
resource "aws_ecs_task_definition" "southpark_task" {
  family                   = "southpark_task" 
  container_definitions    = <<DEFINITION
  [
    {
      "name": "southpark_task",
      "image": "${aws_ecr_repository.southpark.repository_url}",
      "essential": true,
      "portMappings": [
        {
          "containerPort": 45678,
          "hostPort": 45678
        }
      ],
      "memory": 512,
      "cpu": 256
    }
  ]
  DEFINITION
  requires_compatibilities = ["FARGATE"] # Stating that we are using ECS Fargate
  network_mode             = "awsvpc"    # Using awsvpc as our network mode as this is required for Fargate
  memory                   = 512         # Specifying the memory our container requires
  cpu                      = 256         # Specifying the CPU our container requires
  execution_role_arn       = "${aws_iam_role.ecsExecutionRole.arn}"
}


#create load balancer
resource "aws_alb" "application_load_balancer" {
  name               = "southpark-lb-tf" # Naming our load balancer
  load_balancer_type = "application"
  subnets            = "${data.aws_subnet_ids.default.ids}" 
  # Referencing the security group
  security_groups = ["${aws_security_group.load_balancer_security_group.id}"]
}

resource "aws_lb_listener" "lsr" {
  load_balancer_arn = "${aws_alb.application_load_balancer.arn}" # Referencing our load balancer
  port              = "45678"
  protocol          = "HTTP"
  default_action {
    type             = "forward"
    target_group_arn = "${aws_lb_target_group.target_group.arn}" # Referencing our tagrte group
  }
}

resource "aws_lb_target_group" "target_group" {
  name        = "target-gp"
  port        = 45678
  protocol    = "HTTP"
  target_type = "ip"
  deregistration_delay = 90
  vpc_id      = "${aws_default_vpc.default_vpc.id}" # Referencing the default VPC
  health_check {
    healthy_threshold   = "3"
    interval            = "80"
    protocol            = "HTTP"
    timeout             = "60"
    unhealthy_threshold = "2"
    matcher             = "200-405"
    path                = "/"
  }
}


# Creating a security group for the load balancer:
# This is the one that will receive traffic from internet
resource "aws_security_group" "load_balancer_security_group" {
  description = "control access to the ALB"
  ingress {
    from_port   = 45678
    to_port     = 45678
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # Allowing traffic in from all sources
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

#ECS will receive traffic from the ALB
resource "aws_security_group" "service_security_group" {
  description = "Allow acces only from the ALB"
  ingress {
    from_port = 0
    to_port   = 0
    protocol  = "-1"
    # Only allowing traffic in from the load balancer security group
    security_groups = ["${aws_security_group.load_balancer_security_group.id}"]
  }

  egress { 
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

#create service
resource "aws_ecs_service" "southpark_service" {
  name            = "southpark_service"                             # Naming our first service
  cluster         = "${aws_ecs_cluster.southpark_cluster.id}"             # Referencing our created Cluster
  task_definition = "${aws_ecs_task_definition.southpark_task.arn}" # Referencing the task our service will spin up
  launch_type     = "FARGATE"
  desired_count   = 1

  load_balancer {
    target_group_arn = "${aws_lb_target_group.target_group.arn}" # Referencing our target group
    container_name   = "${aws_ecs_task_definition.southpark_task.family}"
    container_port   = 45678 # Specifying the container port
  }

  network_configuration {
    subnets          = data.aws_subnet_ids.default.ids
    assign_public_ip = true                                                # Providing our containers with public IPs
    security_groups  = ["${aws_security_group.service_security_group.id}"] # Setting the security group
  }
  depends_on = [aws_lb_listener.lsr, aws_iam_role_policy_attachment.ecsTaskExecutionRole_policy]
}

output "alb_url" {
  value = "http://${aws_alb.application_load_balancer.dns_name}"
}




