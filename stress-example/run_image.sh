set -x

if [ -z "$PYTHON_EXEC" ]
then
  echo "export PYTHON_EXEC=..." && exit 1
fi

if [ -z "$SLEEP_TIME" ]
then
  echo "export SLEEP_TIME=..." && exit 1
fi

if [ -z "$1" ]
then
  echo "No time (seconds) for running supplied. Use e.g. 'bash run_image.sh 60 4'" && exit 1
fi

if [ -z "$2" ]
then
  echo "No concurrency (int). Use e.g. 'bash run_image.sh 60 4'" && exit 1
fi

bash ./env_vars_config.sh && \
$PYTHON_EXEC app.py --jinad index --dataset image && \
sleep $SLEEP_TIME && \
$PYTHON_EXEC client.py --dataset image -t index -n 100 -l $1 -c $2 && \
export workspace=`cat ws.txt` && \
export flow=`cat flow.txt` && \
sleep $SLEEP_TIME && \
$PYTHON_EXEC app.py --jinad remove --flow-id $flow && \
sleep $SLEEP_TIME && \
$PYTHON_EXEC app.py --jinad query --dataset image --ws $workspace && \
sleep $SLEEP_TIME && \
$PYTHON_EXEC client.py --dataset image -t query -n 10 -l $1 -c $2 && \
sleep $SLEEP_TIME && \
export flow=`cat flow.txt` && \
$PYTHON_EXEC app.py --jinad remove --flow-id $flow && \
sleep $SLEEP_TIME && \
$PYTHON_EXEC app.py --jinad query --dataset image --ws $workspace && \
sleep $SLEEP_TIME && \
$PYTHON_EXEC client.py --dataset image -t query -n 10 -l $1 -c $2
