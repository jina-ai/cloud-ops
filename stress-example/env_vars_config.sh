# load envs from .env
# for each file with *.yml
# substitute envs
echo "env vars found in .env"
export $(egrep -v '^#' .env | xargs)
#
#cat .env | while read line; do
#  echo $line && export $line
#done

find . -name "*.yml" | while read originalfile; do
  echo "handling $originalfile" && \
  tmpfile=$(mktemp) && \
  cp --attributes-only --preserve $originalfile $tmpfile && \
  cat $originalfile | envsubst > $tmpfile &&  \
  mv $tmpfile $originalfile
done
