set -x

export TIME_LOAD_INDEX_DEFAULT=300
export TIME_LOAD_QUERY_DEFAULT=120
export REQ_SIZE_DEFAULT=16
export CONCURRENCY_DEFAULT=3


if [ -z "$DOCS_INDEX" ]
then
  echo "export DOCS_INDEX=..." && exit 1
fi

if [ -z "$DOCS_QUERY" ]
then
  echo "export DOCS_QUERY=..." && exit 1
fi

if [ -z "$PYTHON_EXEC" ]
then
  echo "export PYTHON_EXEC=..." && exit 1
fi

if [ -z "$SLEEP_TIME" ]
then
  echo "export SLEEP_TIME=..." && exit 1
fi

if [ -z "$DATASET" ]
then
  echo "export DATASET=..." && exit 1
fi

if [ -z "$TIME_LOAD_INDEX" ]
then
  echo "TIME_LOAD_INDEX not set. Using default of $TIME_LOAD_INDEX_DEFAULT"
  echo "export TIME_LOAD_INDEX=..."
  export TIME_LOAD_INDEX=$TIME_LOAD_INDEX_DEFAULT
fi

if [ -z "$TIME_LOAD_QUERY" ]
then
  echo "TIME_LOAD_QUERY not set. Using default of $TIME_LOAD_QUERY_DEFAULT"
  echo "export TIME_LOAD_QUERY=..."
  export TIME_LOAD_QUERY=$TIME_LOAD_QUERY_DEFAULT
fi

if [ -z "$REQ_SIZE" ]
then
  echo "REQ_SIZE not set. Using default of $REQ_SIZE_DEFAULT"
  echo "export REQ_SIZE=..."
  export REQ_SIZE=$REQ_SIZE_DEFAULT
fi

if [ -z "$CONCURRENCY" ]
then
  echo "CONCURRENCY not set. Using default of $CONCURRENCY_DEFAULT"
  echo "export CONCURRENCY=..."
  export CONCURRENCY=$CONCURRENCY_DEFAULT
fi

bash env_info.sh && \
bash ./env_vars_config.sh && \
$PYTHON_EXEC app.py --jinad index --dataset $DATASET && \
sleep $SLEEP_TIME && \
$PYTHON_EXEC client.py --dataset $DATASET -t index -n $DOCS_INDEX -l $TIME_LOAD_INDEX -c $CONCURRENCY -r $REQ_SIZE && \
export workspace=`cat ws.txt` && \
export flow=`cat flow.txt` && \
sleep $SLEEP_TIME && \
$PYTHON_EXEC app.py --jinad remove --flow-id $flow && \
sleep $SLEEP_TIME && \
$PYTHON_EXEC app.py --jinad query_annoy --dataset $DATASET --ws $workspace && \
sleep $SLEEP_TIME && \
$PYTHON_EXEC client.py --dataset $DATASET -t query -n $DOCS_QUERY -l $TIME_LOAD_QUERY -c $CONCURRENCY -r $REQ_SIZE && \
sleep $SLEEP_TIME && \
export flow=`cat flow.txt` && \
$PYTHON_EXEC app.py --jinad remove --flow-id $flow && \
sleep $SLEEP_TIME && \
$PYTHON_EXEC app.py --jinad query_faiss --dataset $DATASET --ws $workspace && \
sleep $SLEEP_TIME && \
$PYTHON_EXEC client.py --dataset $DATASET -t query -n $DOCS_QUERY -l $TIME_LOAD_QUERY -c $CONCURRENCY -r $REQ_SIZE
