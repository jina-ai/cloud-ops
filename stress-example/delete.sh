# DELETE
# FOR EACH MACHINE IN LIST
# FOR THAT ELEMENT TYPE
# ISSUE curl -X DELETE MACHINE:PORT/element/all
#!/bin/bash
# declare an array called array and define 3 vales
set -x
array=( $JINA_ENCODER_HOST $JINA_REDIS_INDEXER_HOST $JINA_VEC_INDEXER_HOST $JINA_RANKER_HOST $FLOW_HOST )
for i in "${array[@]}"
do
	echo $i
	curl -X GET i:$FLOW_PORT/$ELEMENT | jq
	curl -X DELETE i:$FLOW_PORT/$ELEMENT/all | jq
done
