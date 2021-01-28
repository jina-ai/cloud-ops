Steps

1. Clone this repo in client machine
1. Configure env vars in `.env` to match aws machines
1. Run `bash env_vars_config.sh`. This replaces all env vars used in the yml files with the env vars you've set. This is required in order to make sure the hosts referred to are the same across machines in the flow
1. Configure `FLOW_HOST_PORT` to point to the gateway machine in AWS.
1. Start flow `python app.py --jinad index`
1. Run the client to index `python3 client.py -t index -n 100 -l 0 -c 1 -h 0.0.0.0 -p 45678`. Replace `-h` and `-p` with machine and port for gateway
