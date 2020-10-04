#!/bin/bash

TMP_DIR="/tmp"
DEFAULT_FILENAME="lambda_function.py"
LAMBDA_HANDLERS_DIR="../lambda_handlers"

function usage() {
    cat <<EOF
    Usage: $0 [options]
    
    -f|--function               Name of Lambda Function (to be picked from `lambda_handlers` directory)
    -p|--package-dir            Directory package
                                Default - _package
    
    This script helps create a deployment package for different Lambda functions!
EOF
}

for arg in "$@"; do
    shift
    case "$arg" in
        "--help")               set -- "$@" "-h" ;;
        "--function")           set -- "$@" "-f" ;;
        "--package-dir")        set -- "$@" "-p" ;;
        *)                      set -- "$@" "$arg"
  esac
done

while getopts "hf:p:" opt
do
  case "$opt" in
    "h") usage; exit 0 ;;
    "f") FUNCTION_NAME=${OPTARG} ;;
    "p") PACKAGE_DIR=${OPTARG} ;;
    "?") usage >&2; exit 1 ;;
  esac
done

if [[ -n "$FUNCTION_NAME" ]]; then
    FUNCTION_NAME=${FUNCTION_NAME//.py}
    echo "Got Lambda function name: ${FUNCTION_NAME}"
    if [[ ! -f  ${LAMBDA_HANDLERS_DIR}/${FUNCTION_NAME}.py ]]; then
        echo "File  ${LAMBDA_HANDLERS_DIR}/${FUNCTION_NAME}.py doesn't exist! Exiting!"
        exit 1
    fi
else
    echo "No function name passed. Exiting!"
    usage
    exit 1
fi

if [[ -n "$PACKAGE_DIR" ]]; then
    echo "Got package directory: ${PACKAGE_DIR}"
else
    echo "No Package directory passed. Using default"
    PACKAGE_DIR="_package"
fi

function cleanup() {
    if [ -d "${PACKAGE_DIR}" ]; then rm -rf ${PACKAGE_DIR}; fi
    if [ -f ${FUNCTION_NAME}.zip ]; then rm ${FUNCTION_NAME}.zip; fi
    if [ -f /tmp/${DEFAULT_FILENAME} ]; then rm /tmp/${DEFAULT_FILENAME}; fi
}

cleanup

mkdir -p ${PACKAGE_DIR}

# Build package if req_function_name.txt file exists in lambda_handlers directory
if [[ -f ${LAMBDA_HANDLERS_DIR}/req_${FUNCTION_NAME}.txt ]]; then
    pip install --target ./${PACKAGE_DIR} -r ${LAMBDA_HANDLERS_DIR}/req_${FUNCTION_NAME}.txt
    cd ${PACKAGE_DIR} && zip -r9 ${OLDPWD}/${FUNCTION_NAME}.zip . && cd -
fi

cp ${LAMBDA_HANDLERS_DIR}/${FUNCTION_NAME}.py ${TMP_DIR}/${DEFAULT_FILENAME}
cd ${TMP_DIR} && zip -g ${OLDPWD}/${FUNCTION_NAME}.zip ${DEFAULT_FILENAME} && cd -

# cleanup
