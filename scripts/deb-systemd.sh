#!/bin/bash
echo "#########################################################"
echo " Jina daemon installation script for Ubuntu/Debian"
echo "#########################################################"
echo "You will be prompted for your password by sudo."

export JINAD_PORT=8000
export JINAD_IP='0.0.0.0'

# clear any previous sudo permission
sudo -k

echo -e "\n\nInitial setup for JinaD\n"
sudo bash <<INIT
    # install python, ruby & fluentd
    apt-get update && apt-get -y install python3.8 python3.8-dev python3.8-distutils python3.8-venv python3-pip && \
        apt-get install --no-install-recommends -y ruby-dev build-essential && \
        gem install fluentd --no-doc
    # add /usr/local/jina/bin to $PATH
    export PATH=/usr/local/jina/bin:$PATH
    # install python packages except jinad
    python3.8 -m pip install --prefix /usr/local/jina $*
    # install jinad
    python3.8 -m pip install --prefix /usr/local/jina --pre "jina[daemon]"
INIT

echo -e "\n\nInstalling jinad as daemon\n"
sudo bash -c 'cat  << EOF > /etc/systemd/system/jinad.service
[Unit]
Description=JinaD (Jina Remote manager)
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu
ExecStart=/usr/local/jina/bin/jinad --workspace /usr/local/jina/tmp
Restart=always

[Install]
WantedBy=multi-user.target
EOF'


echo -e "\n\nStarting jinad service\n"
sudo bash <<JINAD_START
    systemctl daemon-reload
    systemctl enable jinad.service
    systemctl restart jinad.service
JINAD_START

echo -e "Sleeping for 2 secs to allow JinaD service to start"
sleep 2

status_code=$(curl -s -o /dev/null -w "%{http_code}" http://${JINAD_IP}:${JINAD_PORT})

if [[ $status_code -eq 200 ]]; then
    echo -e "\nJinaD started successfully as a daemon. please go to ${JINAD_IP}:${JINAD_PORT}/docs for more info"
else
    echo -e "\nJinaD server is not up. something went wrong! Exiting.."
    exit 1
fi
