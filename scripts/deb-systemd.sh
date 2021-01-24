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

    # install jinad
    pip3 install --prefix /usr/local "jina[daemon]"
INIT

echo -e "\n\nInstalling jinad as daemon\n"
sudo bash -c 'cat  << EOF > /etc/systemd/system/jinad.service
[Unit]
Description=JinaD (Jina Remote manager)
After=network.target
[Service]
User=ubuntu
ExecStart=/usr/local/bin/jinad
Restart=always
[Install]
WantedBy=multi-user.target
EOF'


echo -e "\n\nStarting jinad service\n"
sudo bash <<JINAD_START
    systemctl daemon-reload
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
