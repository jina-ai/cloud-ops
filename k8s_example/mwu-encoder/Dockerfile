FROM jinaai/jina

ADD mwu_encoder.py mwu_encoder.yml ./

ENTRYPOINT ["jina", "pod", "--uses", "mwu_encoder.yml"]