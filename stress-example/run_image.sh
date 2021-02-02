set -x

if [ -z "$1" ]
then
  echo "No time (seconds) for running supplied. Use e.g. 'bash run_image.sh 60'" && exit 1
fi

bash ./env_vars_config.sh && \
python app.py --jinad index --dataset image && \
python client.py --dataset image -t index -n 100 -l $1 -c 1 && \
export workspace=`cat ws.txt` && \
export flow=`cat flow.txt` && \
python app.py --jinad remove --flow-id $flow && \
python app.py --jinad query --dataset image --ws $workspace && \
python client.py --dataset image -t query -n 10 -l $1 -c 1
