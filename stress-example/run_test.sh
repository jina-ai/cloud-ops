set -x

export $(egrep -v '^#' .env | xargs) && \
echo "Running with the following set of parameters:" && \
cat .env && \
bash ./env_vars_config.sh && \
echo "Indexing:" && \
$PYTHON_EXEC app.py --jinad index --dataset $DATASET && \
sleep $SLEEP_TIME && \
$PYTHON_EXEC client.py --dataset $DATASET -t index -n $DOCS_INDEX -l $TIME_LOAD_INDEX -c $CONCURRENCY_INDEX -r $REQ_SIZE && \
export workspace=`cat ws.txt` && \
export flow=`cat flow.txt` && \
sleep $SLEEP_TIME && \
$PYTHON_EXEC app.py --jinad remove --flow-id $flow && \
sleep $SLEEP_TIME && \
echo "Query with NumpyIndexer:" && \
$PYTHON_EXEC app.py --jinad query --dataset $DATASET --ws $workspace && \
sleep $SLEEP_TIME && \
$PYTHON_EXEC client.py --dataset $DATASET -t query -n $DOCS_QUERY -l $TIME_LOAD_QUERY -c $CONCURRENCY_QUERY -r $REQ_SIZE && \
sleep $SLEEP_TIME && \
export flow=`cat flow.txt` && \
$PYTHON_EXEC app.py --jinad remove --flow-id $flow && \
echo "Query with Annoy:" && \
$PYTHON_EXEC app.py --jinad query_annoy --dataset $DATASET --ws $workspace && \
sleep $SLEEP_TIME && \
$PYTHON_EXEC client.py --dataset $DATASET -t query -n $DOCS_QUERY -l $TIME_LOAD_QUERY -c $CONCURRENCY_QUERY -r $REQ_SIZE && \
sleep $SLEEP_TIME && \
export flow=`cat flow.txt` && \
$PYTHON_EXEC app.py --jinad remove --flow-id $flow && \
sleep $SLEEP_TIME && \
echo "Query with Faiss:" && \
$PYTHON_EXEC app.py --jinad query_faiss --dataset $DATASET --ws $workspace && \
sleep $SLEEP_TIME && \
$PYTHON_EXEC client.py --dataset $DATASET -t query -n $DOCS_QUERY -l $TIME_LOAD_QUERY -c $CONCURRENCY_QUERY -r $REQ_SIZE && \
sleep $SLEEP_TIME && \
export flow=`cat flow.txt` && \
$PYTHON_EXEC app.py --jinad remove --flow-id $flow