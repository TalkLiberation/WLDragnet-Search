# WLDragnet filescan

Utility to scan archived copies of public reports in the [NodeXL Graph Gallery](https://nodexlgraphgallery.org). Searches a path for a glob pattern.

## Configuration
Expects the following environment variables to be set. These weak credentials are for local testing and should be changed in other scenarios.
```
DOCUMENT_PATH=<path-to-graphs>
DOCUMENT_GLOB_PATTERN=**/*.html
SCAN_PROCESS_POOL_SIZE_MAX=4
DB_HOST=128.0.0.1
DB_PORT=5432
DB_NAME=wldragnet_search
DB_USER=wldragnet_search
DB_PW=<password>
```
## Run
```shell
python pdfscan.py
```