#!/bin/bash

HOME_DIR=/mnt/data

function usage() {
    cat <<EOF
    Usage: $0 [options]

    -h|--help                  Entrypoint script for running stress-test on AWS.
    -j|--jina-compilation       Select whether to download jina from pip or compile from git
                                Default - pip
                                Allowed values [pip, git]
    -b|--jina-branch            If jina is compiled via git, select the branch
                                Default - master

EOF
}

for arg in "$@"; do
    shift
    case "$arg" in
        "--help")               set -- "$@" "-h" ;;
        "--jina-compilation")   set -- "$@" "-j" ;;
        "--jina-branch")        set -- "$@" "-b" ;;
        *)                      set -- "$@" "$arg"
  esac
done

while getopts "hj:b:" opt
do
  case "$opt" in
    "h") usage; exit 0 ;;
    "j") COMPILATION=${OPTARG} ;;
    "b") BRANCH=${OPTARG} ;;
    "?") usage >&2; exit 1 ;;
  esac
done


if [[ -n "$COMPILATION" ]]; then
    echo "Jina will be downloaded via ${COMPILATION}"
else
    COMPLIATION=pip
    echo "Selecting Jina download to be ${COMPLIATION} as no params are passed\n"
    pip3 install jina
fi

if [[ $COMPILATION == "git" ]]; then
    if [[ -n "$BRANCH" ]]; then
        echo "Jina will be downloaded via ${BRANCH} branch"
    else
        BRANCH=master
        echo "Selecting Jina download to be from ${BRANCH} branch"
    fi
    git clone -b $BRANCH --single-branch https://github.com/jina-ai/jina.git $HOME_DIR
    cd $HOME_DIR/jina && pip3 install '.[match-py-ver]' --no-cache-dir
fi

cd $HOME_DIR/stress-test/benchmark
echo "Triggering stress-test --"
pip3 install -r requirements.txt
python3.8 app.py

