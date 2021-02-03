set -x

if [ -z "$PYTHON_EXEC" ]
then
  echo "export PYTHON_EXEC=..." && exit 1
fi

if [ -z "$SLEEP_TIME" ]
then
  echo "export SLEEP_TIME=..." && exit 1
fi

if [ -z "$TIME_LOAD" ]
then
  echo "No time (seconds) for running supplied. 'export TIME_LOAD=...'" && exit 1
fi

if [ -z "$CONCURRENCY" ]
then
  echo "No concurrency (int). Use e.g. 'export CONCURRENCY=...'" && exit 1
fi

bash ./env_vars_config.sh && \
$PYTHON_EXEC app.py --jinad index --dataset $DATASET && \
sleep $SLEEP_TIME && \
$PYTHON_EXEC client.py --dataset $DATASET -t index -n 100 -l $TIME_LOAD -c $CONCURRENCY && \
export workspace=`cat ws.txt` && \
export flow=`cat flow.txt` && \
sleep $SLEEP_TIME && \
$PYTHON_EXEC app.py --jinad remove --flow-id $flow && \
sleep $SLEEP_TIME && \
$PYTHON_EXEC app.py --jinad query --dataset $DATASET --ws $workspace && \
sleep $SLEEP_TIME && \
$PYTHON_EXEC client.py --dataset $DATASET -t query -n 10 -l $TIME_LOAD -c $CONCURRENCY && \
sleep $SLEEP_TIME && \
export flow=`cat flow.txt` && \
$PYTHON_EXEC app.py --jinad remove --flow-id $flow && \
sleep $SLEEP_TIME && \
$PYTHON_EXEC app.py --jinad query --dataset $DATASET --ws $workspace && \
sleep $SLEEP_TIME && \
$PYTHON_EXEC client.py --dataset $DATASET -t query -n 10 -l $TIME_LOAD -c $CONCURRENCY
