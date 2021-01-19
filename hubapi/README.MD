`HubAPI`
The HubAPI supports operations for listing jina hub images
and pushing images to the hub. These are authorised using the
hub authorizer. We use MongoDB for storing and retrieving
information related to hub. This document elaborates on the functioning
of each of these APIs
1. `Hub List` API
List API provides the user the ability to query jina images. Under the hood, the implementation uses a Mongodb Handler to connect to the database & insert documents in the collection.
Documents are generally manifest files that have metadata information of hub images. Currently, the List API is optimised for listing the images with the latest jina version.

* API gateway endpoint: `/GET` `images`        
* Supports cursor based pagination and alphabetical sorting
* Returns only latest images for all executors (only one result per executor)
* Returns docker pull command in addition to all info in manifest file.
* Semver sort implementation with different fields for `major`, `minor` & `patch`
* Optimized filter for searching with params:
`kind` (indexer, encoder, segmenter etc),
`type` (pod, app etc),
`jina version`,
`executor (manifest) version`,
`keywords` (array search),
`executor name` (simple regex search).
  
The `Aggregation` pipeline has the following stages:

    Stage 1:
    - Form `$match` from different query strings
    - This will be executed only if proper query strings are passed
    - Accepted query strings -
      - `name` -> simple regex search
      - `jina_version` -> exact match
      - `version` -> exact match
      - `kind` -> exact match
      - `type` -> exact match
      - `keywords` -> array search

    Stage 2:
    - Sort by `name`, `jina_version` & `version`
    - `name`: 1 - this sorts alphabetically (set to -1 for reverse order)
    - `jina_version`: -1 - Sorted according to semver. This should always be latest first.
    - `version`: -1 - Sorted according to semver. This should also be latest first.

    Stage 3:
    - Groupby `name` of the executor
    - Add `jina_version`, `version` & `manifest_info` to `images` list (this will be ordered)

    Stage 4:
    - Since groupby removes the sort on `name`, sort it again
    
    sort_by_name_again_stage = {
        '$sort': {
            '_id.name': 1
        }
    } 

    Stage 5:
    - Pagination: Fetch images only after a certain image name

    Stage 6:
    - Fetch n results at a time

    Stage 7:
     - 1st element of the `images` list would be the latest executor

    Stage 8:
    - Finalize the set of arguments to be set


2. `Hub Push` API
Push API writes data into Mongodb Atlas (Used to perform `jina hub push`)
   
* `POST` `/push` endpoint of API Gateway writes the executor details into 2 collections:
* `hubpods` - This just has info about name, version, jina version & manifest info
* `hubpods_metadata` - This has info about name, version, jina version, build history, docker inspect details (All info that is rarely used for hublist)
   