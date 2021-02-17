provider "aws" {
  version = "~> 2.0"
  region  = "eu-central-1"
}

resource "aws_cloudformation_stack" "network" {
  name = "networking-stack"

  template_body = <<STACK
{
  "Parameters": {
      "EC2ImageIdParam": {
          "Type": "String",
          "Default": "ami-0502e817a62226e03",
          "Description": "Enter Image ID. Default is for Ubuntu 20.04, non GPU, Frankfurt"
      },
      "GPUEC2ImageIdParam": {
          "Type": "String",
          "Default": "ami-0502e817a62226e03",
          "Description": "Enter Image ID. Default is for Deep Learning Base Ubuntu 18.04, Frankfurt"
      },
      "EC2InstanceTypeParam": {
          "Type": "String",
          "Default": "c5.2xlarge"
      },
      "KeyNameParam": {
          "Type": "String",
          "Default": "instance-login",
          "Description": "Enter Key Name. Default is instance-login."
      },
      "VolumeSizeParam": {
          "Type": "Number",
          "Default": 100,
          "Description": "Enter EBS volume size (type gp2). Default is 100GB."
      },
      "AvailabilityZoneParam": {
          "Type": "String",
          "Default": "eu-central-1c",
          "Description": "Enter Availability Zone for EC2. Default is eu-central-1c (Frankfurt)"
      }
  },
  "Resources": {
      "daemonVPC": {
          "Type": "AWS::EC2::VPC",
          "Properties": {
              "CidrBlock": "10.0.0.0/16",
              "EnableDnsSupport": "false",
              "EnableDnsHostnames": "false",
              "InstanceTenancy": "dedicated",
              "Tags": [
                  {
                      "Key": "num-pods",
                      "Value": 5
                  }
              ]
          }
      },
      "crafterSubnet": {
          "Type": "AWS::EC2::Subnet",
          "Properties": {
              "VpcId": {
                  "Ref": "daemonVPC"
              },
              "CidrBlock": "10.0.1.0/24",
              "AvailabilityZone": {
                  "Ref": "AvailabilityZoneParam"
              }
          }
      },
      "encoderSubnet": {
          "Type": "AWS::EC2::Subnet",
          "Properties": {
              "VpcId": {
                  "Ref": "daemonVPC"
              },
              "CidrBlock": "10.0.0.0/24",
              "AvailabilityZone": {
                  "Ref": "AvailabilityZoneParam"
              }
          }
      },
      "indexerSubnet": {
          "Type": "AWS::EC2::Subnet",
          "Properties": {
              "VpcId": {
                  "Ref": "daemonVPC"
              },
              "CidrBlock": "10.0.2.0/24",
              "AvailabilityZone": {
                  "Ref": "AvailabilityZoneParam"
              }
          }
      },
      "rankerSubnet": {
          "Type": "AWS::EC2::Subnet",
          "Properties": {
              "VpcId": {
                  "Ref": "daemonVPC"
              },
              "CidrBlock": "10.0.3.0/24",
              "AvailabilityZone": {
                  "Ref": "AvailabilityZoneParam"
              }
          }
      },
      "flowSubnet": {
          "Type": "AWS::EC2::Subnet",
          "Properties": {
              "VpcId": {
                  "Ref": "daemonVPC"
              },
              "CidrBlock": "10.0.4.0/24",
              "AvailabilityZone": {
                  "Ref": "AvailabilityZoneParam"
              }
          }
      },
      "InstanceSecurityGroup": {
          "Type": "AWS::EC2::SecurityGroup",
          "Properties": {
              "GroupDescription": "Allow http to client host",
              "VpcId": {
                  "Ref": "daemonVPC"
              },
              "SecurityGroupIngress": [
                  {
                      "IpProtocol": "tcp",
                      "FromPort": 80,
                      "ToPort": 80,
                      "CidrIp": "0.0.0.0/0"
                  }
              ],
              "SecurityGroupEgress": [
                  {
                      "IpProtocol": "tcp",
                      "FromPort": 80,
                      "ToPort": 80,
                      "CidrIp": "0.0.0.0/0"
                  }
              ]
          }
      },
      "SSHSecurityGroup": {
          "Type": "AWS::EC2::SecurityGroup",
          "Properties": {
              "GroupDescription": "Enable SSH access to instance",
              "SecurityGroupIngress": [
                  {
                      "IpProtocol": "tcp",
                      "FromPort": 22,
                      "ToPort": 22,
                      "CidrIp": "0.0.0.0/0"
                  },
                  {
                      "IpProtocol": "tcp",
                      "FromPort": 8000,
                      "ToPort": 8000,
                      "CidrIp": "0.0.0.0/0"
                  },
                  {
                      "IpProtocol": "tcp",
                      "FromPort": 10000,
                      "ToPort": 65535,
                      "CidrIp": "0.0.0.0/0"
                  }
              ]
          }
      },
      "encoderInstance": {
          "Type": "AWS::EC2::Instance",
          "Metadata": {
              "AWS::CloudFormation::Init": {
                  "configSets": {
                      "jina_install": [
                          "configure_jina"
                      ]
                  },
                  "configure_jina": {
                      "commands": {
                          "01_run_jina_installation": {
                              "command": {
                                  "Fn::Sub": "curl -L https://raw.githubusercontent.com/jina-ai/cloud-ops/master/scripts/deb-systemd.sh > /home/ubuntu/cfn-init-script.sh\n"
                              },
                              "test": {
                                  "Fn::Sub": "echo instance command\n"
                              }
                          }
                      }
                  }
              }
          },
          "Properties": {
              "ImageId": {
                  "Ref": "GPUEC2ImageIdParam"
              },
              "InstanceType": {
                  "Ref": "EC2InstanceTypeParam"
              },
              "KeyName": {
                  "Ref": "KeyNameParam"
              },
              "SecurityGroups": [
                  {
                      "Ref": "SSHSecurityGroup"
                  }
              ],
              "BlockDeviceMappings": [
                  {
                      "DeviceName": "/dev/sda1",
                      "Ebs": {
                          "VolumeSize": {
                              "Ref": "VolumeSizeParam"
                          }
                      }
                  }
              ],
              "UserData": {
                  "Fn::Base64": {
                      "Fn::Sub": "#!/bin/bash -xe\ncd /home/ubuntu\ncurl -L https://raw.githubusercontent.com/jina-ai/cloud-ops/master/scripts/deb-systemd.sh > cfn-init-script.sh\ncurl -L https://raw.githubusercontent.com/jina-ai/cloud-ops/master/stress-example/image/requirements.txt  > image_requirements.txt\ncurl -L https://raw.githubusercontent.com/jina-ai/cloud-ops/master/stress-example/text/requirements.txt  > text_requirements.txt\nchmod +x cfn-init-script.sh\n./cfn-init-script.sh\npython3.8 -m pip install -r image_requirements.txt\npython3.8 -m pip install -r text_requirements.txt\napt-get install -y docker docker.io\nusermod -aG docker ubuntu\nreboot\ncurl -L https://raw.githubusercontent.com/jina-ai/cloud-ops/master/scripts/deb-systemd.sh > cfn-init-script.sh\n./cfn-init-script.sh\n/opt/aws/bin/cfn-init -v --stack $${AWS::StackId} --resource encoderInstance --configsets jina_install --region $${AWS::Region}\n/opt/aws/bin/cfn-signal -e $? --stack $${AWS::StackId} --resource encoderInstance --configsets jina_install --region $${AWS::Region}\n"
                  }
              },
              "Tags": [
                  {
                      "Key": "Name",
                      "Value": "Encoder-Instance"
                  }
              ]
          }
      },
      "encoderVolume": {
          "Type": "AWS::EC2::Volume",
          "Properties": {
              "Size": 20,
              "AvailabilityZone": {
                  "Fn::GetAtt": [
                      "encoderInstance",
                      "AvailabilityZone"
                  ]
              },
              "Tags": [
                  {
                      "Key": "encoder-vol",
                      "Value": "custom"
                  }
              ]
          },
          "DeletionPolicy": "Snapshot"
      },
      "encoderMountPoint": {
          "Type": "AWS::EC2::VolumeAttachment",
          "Properties": {
              "InstanceId": {
                  "Ref": "encoderInstance"
              },
              "VolumeId": {
                  "Ref": "encoderVolume"
              },
              "Device": "/dev/sdh"
          }
      },
      "EncoderEIP": {
          "Type": "AWS::EC2::EIP",
          "Properties": {
              "InstanceId": {
                  "Ref": "encoderInstance"
              }
          }
      },
      "crafterInstance": {
          "Type": "AWS::EC2::Instance",
          "Metadata": {
              "AWS::CloudFormation::Init": {
                  "configSets": {
                      "jina_install": [
                          "configure_jina"
                      ]
                  },
                  "configure_jina": {
                      "commands": {
                          "01_run_jina_installation": {
                              "command": {
                                  "Fn::Sub": "curl -L https://raw.githubusercontent.com/jina-ai/cloud-ops/master/scripts/deb-systemd.sh > /home/ubuntu/cfn-init-script.sh\n"
                              },
                              "test": {
                                  "Fn::Sub": "echo instance command\n"
                              }
                          }
                      }
                  }
              }
          },
          "Properties": {
              "ImageId": {
                  "Ref": "EC2ImageIdParam"
              },
              "InstanceType": {
                  "Ref": "EC2InstanceTypeParam"
              },
              "KeyName": {
                  "Ref": "KeyNameParam"
              },
              "SecurityGroups": [
                  {
                      "Ref": "SSHSecurityGroup"
                  }
              ],
              "BlockDeviceMappings": [
                  {
                      "DeviceName": "/dev/sda1",
                      "Ebs": {
                          "VolumeSize": {
                              "Ref": "VolumeSizeParam"
                          }
                      }
                  }
              ],
              "UserData": {
                  "Fn::Base64": {
                      "Fn::Sub": "#!/bin/bash -xe\ncd /home/ubuntu\ncurl -L https://raw.githubusercontent.com/jina-ai/cloud-ops/master/scripts/deb-systemd.sh > cfn-init-script.sh\ncurl -L https://raw.githubusercontent.com/jina-ai/cloud-ops/master/stress-example/image/requirements.txt  > image_requirements.txt\ncurl -L https://raw.githubusercontent.com/jina-ai/cloud-ops/master/stress-example/text/requirements.txt  > text_requirements.txt\nchmod +x cfn-init-script.sh\n./cfn-init-script.sh\npython3.8 -m pip install -r image_requirements.txt\npython3.8 -m pip install -r text_requirements.txt\napt-get install -y docker docker.io\nusermod -aG docker ubuntu\nreboot\n/opt/aws/bin/cfn-init -v --stack $${AWS::StackId} --resource crafterInstance --configsets jina_install --region $${AWS::Region}\n/opt/aws/bin/cfn-signal -e $? --stack $${AWS::StackId} --resource crafterInstance --configsets jina_install --region $${AWS::Region}\n"
                  }
              },
              "Tags": [
                  {
                      "Key": "Name",
                      "Value": "Crafter-Instance"
                  }
              ]
          }
      },
      "crafterVolume": {
          "Type": "AWS::EC2::Volume",
          "Properties": {
              "Size": 20,
              "AvailabilityZone": {
                  "Fn::GetAtt": [
                      "crafterInstance",
                      "AvailabilityZone"
                  ]
              },
              "Tags": [
                  {
                      "Key": "crafter-vol",
                      "Value": "custom"
                  }
              ]
          },
          "DeletionPolicy": "Snapshot"
      },
      "crafterMountPoint": {
          "Type": "AWS::EC2::VolumeAttachment",
          "Properties": {
              "InstanceId": {
                  "Ref": "crafterInstance"
              },
              "VolumeId": {
                  "Ref": "crafterVolume"
              },
              "Device": "/dev/sdh"
          }
      },
      "CrafterEIP": {
          "Type": "AWS::EC2::EIP",
          "Properties": {
              "InstanceId": {
                  "Ref": "crafterInstance"
              }
          }
      },
      "indexerInstance": {
          "Type": "AWS::EC2::Instance",
          "Metadata": {
              "AWS::CloudFormation::Init": {
                  "configSets": {
                      "jina_install": [
                          "configure_jina"
                      ]
                  },
                  "configure_jina": {
                      "commands": {
                          "01_run_jina_installation": {
                              "command": {
                                  "Fn::Sub": "curl -L https://raw.githubusercontent.com/jina-ai/cloud-ops/master/scripts/deb-systemd.sh > /home/ubuntu/cfn-init-script.sh\n"
                              },
                              "test": {
                                  "Fn::Sub": "echo instance command\n"
                              }
                          }
                      }
                  }
              }
          },
          "Properties": {
              "ImageId": {
                  "Ref": "EC2ImageIdParam"
              },
              "InstanceType": {
                  "Ref": "EC2InstanceTypeParam"
              },
              "KeyName": {
                  "Ref": "KeyNameParam"
              },
              "SecurityGroups": [
                  {
                      "Ref": "SSHSecurityGroup"
                  }
              ],
              "BlockDeviceMappings": [
                  {
                      "DeviceName": "/dev/sda1",
                      "Ebs": {
                          "VolumeSize": {
                              "Ref": "VolumeSizeParam"
                          }
                      }
                  }
              ],
              "UserData": {
                  "Fn::Base64": {
                      "Fn::Sub": "#!/bin/bash -xe\ncd /home/ubuntu\ncurl -L https://raw.githubusercontent.com/jina-ai/cloud-ops/master/scripts/deb-systemd.sh > cfn-init-script.sh\ncurl -L https://raw.githubusercontent.com/jina-ai/cloud-ops/master/stress-example/image/requirements.txt  > image_requirements.txt\ncurl -L https://raw.githubusercontent.com/jina-ai/cloud-ops/master/stress-example/text/requirements.txt  > text_requirements.txt\nchmod +x cfn-init-script.sh\n./cfn-init-script.sh\npython3.8 -m pip install -r image_requirements.txt\npython3.8 -m pip install -r text_requirements.txt\napt-get install -y docker docker.io\nusermod -aG docker ubuntu\napt-get install -y redis-server && redis-server --bind 0.0.0.0 --port 6379:6379 --daemonize yes\nreboot\n/opt/aws/bin/cfn-init -v --stack $${AWS::StackId} --resource indexerInstance --configsets jina_install --region $${AWS::Region}\n/opt/aws/bin/cfn-signal -e $? --stack $${AWS::StackId} --resource indexerInstance --configsets jina_install --region $${AWS::Region}\n"
                  }
              },
              "Tags": [
                  {
                      "Key": "Name",
                      "Value": "Indexer-Instance"
                  }
              ]
          }
      },
      "indexerVolume": {
          "Type": "AWS::EC2::Volume",
          "Properties": {
              "Size": 20,
              "AvailabilityZone": {
                  "Fn::GetAtt": [
                      "indexerInstance",
                      "AvailabilityZone"
                  ]
              },
              "Tags": [
                  {
                      "Key": "indexer-vol",
                      "Value": "custom"
                  }
              ]
          },
          "DeletionPolicy": "Snapshot"
      },
      "indexerMountPoint": {
          "Type": "AWS::EC2::VolumeAttachment",
          "Properties": {
              "InstanceId": {
                  "Ref": "indexerInstance"
              },
              "VolumeId": {
                  "Ref": "indexerVolume"
              },
              "Device": "/dev/sdh"
          }
      },
      "IndexerEIP": {
          "Type": "AWS::EC2::EIP",
          "Properties": {
              "InstanceId": {
                  "Ref": "indexerInstance"
              }
          }
      },
      "rankerInstance": {
          "Type": "AWS::EC2::Instance",
          "Metadata": {
              "AWS::CloudFormation::Init": {
                  "configSets": {
                      "jina_install": [
                          "configure_jina"
                      ]
                  },
                  "configure_jina": {
                      "commands": {
                          "01_run_jina_installation": {
                              "command": {
                                  "Fn::Sub": "curl -L https://raw.githubusercontent.com/jina-ai/cloud-ops/master/scripts/deb-systemd.sh > /home/ubuntu/cfn-init-script.sh\n"
                              },
                              "test": {
                                  "Fn::Sub": "echo instance command\n"
                              }
                          }
                      }
                  }
              }
          },
          "Properties": {
              "ImageId": {
                  "Ref": "EC2ImageIdParam"
              },
              "InstanceType": {
                  "Ref": "EC2InstanceTypeParam"
              },
              "KeyName": {
                  "Ref": "KeyNameParam"
              },
              "SecurityGroups": [
                  {
                      "Ref": "SSHSecurityGroup"
                  }
              ],
              "BlockDeviceMappings": [
                  {
                      "DeviceName": "/dev/sda1",
                      "Ebs": {
                          "VolumeSize": {
                              "Ref": "VolumeSizeParam"
                          }
                      }
                  }
              ],
              "UserData": {
                  "Fn::Base64": {
                      "Fn::Sub": "#!/bin/bash -xe\ncd /home/ubuntu\ncurl -L https://raw.githubusercontent.com/jina-ai/cloud-ops/master/scripts/deb-systemd.sh > cfn-init-script.sh\ncurl -L https://raw.githubusercontent.com/jina-ai/cloud-ops/master/stress-example/image/requirements.txt  > image_requirements.txt\ncurl -L https://raw.githubusercontent.com/jina-ai/cloud-ops/master/stress-example/text/requirements.txt  > text_requirements.txt\nchmod +x cfn-init-script.sh\n./cfn-init-script.sh\npython3.8 -m pip install -r image_requirements.txt\npython3.8 -m pip install -r text_requirements.txt\napt-get install -y docker docker.io\nusermod -aG docker ubuntu\napt-get install -y redis-server && redis-server --bind 0.0.0.0 --port 6379:6379 --daemonize yes\nreboot\n/opt/aws/bin/cfn-init -v --stack $${AWS::StackId} --resource rankerInstance --configsets jina_install --region $${AWS::Region}\n/opt/aws/bin/cfn-signal -e $? --stack $${AWS::StackId} --resource rankerInstance --configsets jina_install --region $${AWS::Region}\n"
                  }
              },
              "Tags": [
                  {
                      "Key": "Name",
                      "Value": "Ranker-Instance"
                  }
              ]
          }
      },
      "rankerVolume": {
          "Type": "AWS::EC2::Volume",
          "Properties": {
              "Size": 20,
              "AvailabilityZone": {
                  "Fn::GetAtt": [
                      "rankerInstance",
                      "AvailabilityZone"
                  ]
              },
              "Tags": [
                  {
                      "Key": "ranker-vol",
                      "Value": "custom"
                  }
              ]
          },
          "DeletionPolicy": "Snapshot"
      },
      "rankerMountPoint": {
          "Type": "AWS::EC2::VolumeAttachment",
          "Properties": {
              "InstanceId": {
                  "Ref": "rankerInstance"
              },
              "VolumeId": {
                  "Ref": "rankerVolume"
              },
              "Device": "/dev/sdh"
          }
      },
      "RankerEIP": {
          "Type": "AWS::EC2::EIP",
          "Properties": {
              "InstanceId": {
                  "Ref": "rankerInstance"
              }
          }
      },
      "flowInstance": {
          "Type": "AWS::EC2::Instance",
          "Metadata": {
              "AWS::CloudFormation::Init": {
                  "configSets": {
                      "jina_install": [
                          "configure_jina"
                      ]
                  },
                  "configure_jina": {
                      "commands": {
                          "01_run_jina_installation": {
                              "command": {
                                  "Fn::Sub": "curl -L https://raw.githubusercontent.com/jina-ai/cloud-ops/master/scripts/deb-systemd.sh > /home/ubuntu/cfn-init-script.sh\n"
                              },
                              "test": {
                                  "Fn::Sub": "echo instance command\n"
                              }
                          }
                      }
                  }
              }
          },
          "Properties": {
              "ImageId": {
                  "Ref": "EC2ImageIdParam"
              },
              "InstanceType": {
                  "Ref": "EC2InstanceTypeParam"
              },
              "KeyName": {
                  "Ref": "KeyNameParam"
              },
              "SecurityGroups": [
                  {
                      "Ref": "SSHSecurityGroup"
                  }
              ],
              "BlockDeviceMappings": [
                  {
                      "DeviceName": "/dev/sda1",
                      "Ebs": {
                          "VolumeSize": {
                              "Ref": "VolumeSizeParam"
                          }
                      }
                  }
              ],
              "UserData": {
                  "Fn::Base64": {
                      "Fn::Sub": "#!/bin/bash -xe\ncd /home/ubuntu\ncurl -L https://raw.githubusercontent.com/jina-ai/cloud-ops/master/scripts/deb-systemd.sh > cfn-init-script.sh\ncurl -L https://raw.githubusercontent.com/jina-ai/cloud-ops/master/stress-example/image/requirements.txt  > image_requirements.txt\ncurl -L https://raw.githubusercontent.com/jina-ai/cloud-ops/master/stress-example/text/requirements.txt  > text_requirements.txt\nchmod +x cfn-init-script.sh\n./cfn-init-script.sh\npython3.8 -m pip install -r image_requirements.txt\npython3.8 -m pip install -r text_requirements.txt\napt-get install -y docker docker.io\nusermod -aG docker ubuntu\nreboot\n/opt/aws/bin/cfn-init -v --stack $${AWS::StackId} --resource flowInstance --configsets jina_install --region $${AWS::Region}\n/opt/aws/bin/cfn-signal -e $? --stack $${AWS::StackId} --resource flowInstance --configsets jina_install --region $${AWS::Region}\n"
                  }
              },
              "Tags": [
                  {
                      "Key": "Name",
                      "Value": "Flow-Instance"
                  }
              ]
          }
      },
      "FlowEIP": {
          "Type": "AWS::EC2::EIP",
          "Properties": {
              "InstanceId": {
                  "Ref": "flowInstance"
              }
          }
      },
      "FlowVolume": {
          "Type": "AWS::EC2::Volume",
          "Properties": {
              "Size": 20,
              "AvailabilityZone": {
                  "Fn::GetAtt": [
                      "flowInstance",
                      "AvailabilityZone"
                  ]
              },
              "Tags": [
                  {
                      "Key": "flow-vol",
                      "Value": "custom"
                  }
              ]
          },
          "DeletionPolicy": "Snapshot"
      },
      "FlowMountPoint": {
          "Type": "AWS::EC2::VolumeAttachment",
          "Properties": {
              "InstanceId": {
                  "Ref": "flowInstance"
              },
              "VolumeId": {
                  "Ref": "FlowVolume"
              },
              "Device": "/dev/sdh"
          }
      },
      "clientInstance": {
          "Type": "AWS::EC2::Instance",
          "Metadata": {
              "AWS::CloudFormation::Init": {
                  "configSets": {
                      "jina_install": [
                          "configure_jina"
                      ]
                  },
                  "configure_jina": {
                      "commands": {
                          "01_run_jina_installation": {
                              "command": {
                                  "Fn::Sub": "curl -L https://raw.githubusercontent.com/jina-ai/cloud-ops/master/scripts/deb-systemd.sh > /home/ubuntu/cfn-init-script.sh\n"
                              },
                              "test": {
                                  "Fn::Sub": "echo instance command\n"
                              }
                          }
                      }
                  }
              }
          },
          "Properties": {
              "ImageId": {
                  "Ref": "EC2ImageIdParam"
              },
              "InstanceType": {
                  "Ref": "EC2InstanceTypeParam"
              },
              "KeyName": {
                  "Ref": "KeyNameParam"
              },
              "SecurityGroups": [
                  {
                      "Ref": "SSHSecurityGroup"
                  }
              ],
              "BlockDeviceMappings": [
                  {
                      "DeviceName": "/dev/sda1",
                      "Ebs": {
                          "VolumeSize": {
                              "Ref": "VolumeSizeParam"
                          }
                      }
                  }
              ],
              "UserData": {
                  "Fn::Base64": {
                      "Fn::Sub": "#!/bin/bash -xe\ncd /home/ubuntu\napt-get update && apt-get -y install python3.8 python3.8-dev python3.8-distutils python3.8-venv python3-pip git-all\npython3 -m pip install --pre jina[cv,http]\npython3 -m pip install nltk\ngit clone https://github.com/jina-ai/cloud-ops.git /home/ubuntu/cloud-ops\n/opt/aws/bin/cfn-init -v --stack $${AWS::StackId} --resource clientInstance --configsets jina_install --region $${AWS::Region}\n/opt/aws/bin/cfn-signal -e $? --stack $${AWS::StackId} --resource clientInstance --configsets jina_install --region $${AWS::Region}\n"
                  }
              },
              "Tags": [
                  {
                      "Key": "Name",
                      "Value": "Client-Instance"
                  }
              ]
          }
      },
      "clientVolume": {
          "Type": "AWS::EC2::Volume",
          "Properties": {
              "Size": 20,
              "AvailabilityZone": {
                  "Fn::GetAtt": [
                      "clientInstance",
                      "AvailabilityZone"
                  ]
              },
              "Tags": [
                  {
                      "Key": "client-vol",
                      "Value": "custom"
                  }
              ]
          },
          "DeletionPolicy": "Snapshot"
      },
      "clientMountPoint": {
          "Type": "AWS::EC2::VolumeAttachment",
          "Properties": {
              "InstanceId": {
                  "Ref": "clientInstance"
              },
              "VolumeId": {
                  "Ref": "clientVolume"
              },
              "Device": "/dev/sdh"
          }
      },
      "ClientEIP": {
          "Type": "AWS::EC2::EIP",
          "Properties": {
              "InstanceId": {
                  "Ref": "clientInstance"
              }
          }
      }
  },
  "Outputs": {
      "FlowIP": {
          "Value": {
              "Ref": "FlowEIP"
          },
          "Export": {
              "Name": "FlowEIP::Address"
          }
      },
      "EncoderIP": {
          "Value": {
              "Ref": "EncoderEIP"
          },
          "Export": {
              "Name": "EncoderEIP::Address"
          }
      },
      "IndexerIP": {
          "Value": {
              "Ref": "IndexerEIP"
          },
          "Export": {
              "Name": "IndexerEIP::Address"
          }
      },
      "RankerIP": {
          "Value": {
              "Ref": "RankerEIP"
          },
          "Export": {
              "Name": "RankerEIP::Address"
          }
      },
      "ClientIP": {
          "Value": {
              "Ref": "ClientEIP"
          },
          "Export": {
              "Name": "ClientEIP::Address"
          }
      },
      "CrafterIP": {
          "Value": {
              "Ref": "CrafterEIP"
          },
          "Export": {
              "Name": "CrafterEIP::Address"
          }
      }
  }
}
STACK
}
