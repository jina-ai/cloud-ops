Steps for cloud stress example

1. Have AWS machines up and running. Get IPs and make sure your pem key has access.
    
    Connect with e.g. `ssh -i ~/.ssh/flow-login.pem user@machine.com`

1. Clone this repo in client machine
1. Configure env vars in `.env` to match aws machines. 
   
   **NOTE** Make sure you use the IPs of the machines.

1. Run `bash env_vars_config.sh`. This replaces all env vars used in the yml files with the env vars you've set. This is required in order to make sure the hosts referred to are the same across machines in the flow
1. Configure `FLOW_HOST_PORT` to point to the gateway machine in AWS.
1. Start flow `python app.py --jinad index --dataset $DATASET`
   
    **NOTE** Keep track of flow id and workspace ids.

1. Run the client to index `python3 client.py --dataset $DATASET -t index -n 100 -l 0 -c 1 -h 0.0.0.0 -p 45678`. Replace `-h` and `-p` with machine and port for gateway (`FLOW_HOST_PORT`)
1. Remove flow `python app.py --jina remove --flow-id $FLOW_ID`
1. Start new flow and reuse workspace

    `python3 app.py --jinad query --ws $WORKSPACE_ID --dataset $DATASET`

1. Query some docs: `python3 client.py -t query -n 10 -l 0 -c 1 -h 0.0.0.0 -p 45678 --dataset $DATASET`

Testing locally with docker compose

1. Build docker image `docker build -f debianx.Dockerfile -t stress_example_image_search ~/code/jina`
1. Create docker compose containers `docker-compose -f docker-compose.yml --project-directory . up --build -d`
1. Proceed as normal with creating a Flow, as above.
1. Tear down containers: `docker-compose -f docker-compose.yml --project-directory . down`

