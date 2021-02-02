declare -a instances=("$@")

counter=1

while true; do
    echo -e "\n\nIteration $counter"
    for instance in "${instances[@]}"; do
        if [[ $instance == *:* ]]; then
            ip=$(echo "$instance" | cut -d\: -f1)
            port=$(echo "$instance" | cut -d\: -f2)
        else
            ip=$instance
            port=8000
        fi
        status_code=$(curl -s -o /dev/null -w "%{http_code}" http://${ip}:${port})
        echo -e "JinaD status code for ip: ${ip} port: ${port} -- ${status_code}"
    done
    counter=$[$counter +1]
    sleep 0.5
done
