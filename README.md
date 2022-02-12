![WLDragnet Logo](wldragnet/static/talkliberation-investigates-logo.png) 
# [WLDragnet](https://talkliberation.com/wldragnet) Search
https://wldragnet.com

This project is brought to you by the team building [Panquake](https://panquake.com) and is an example of the strong ethical design and high-quality standard we bring to the software development process. It is released as Free and Open-Source Software (FOSS) in the interest of the public good.

In October 2021, [Talk Liberation](https://talkliberation.com/wldragnet) published WLDragnet - an investigation that included 1500+ reports and a repository of 7,100+ files that prove US military contractors and weapons manufacturers are utilizing open-source intelligence to track and analyze the social media conversations of persons, hashtags, keywords and topics of political consequence, effectively creating target lists.

This profiling spans from 2018 up to the present day and its scope continues to grow. Nearly 200 reports and 500+ files were added to the WLDragnet repository in February 2022.

Featured in the target lists are whistleblowers, journalists, activists, and thousands of regular citizens. The files can be onerous to manually search through and difficult to understand, so Talk Liberation created a more high-level and stripped-down view: the WLDragnet Search.

Talk Liberation encourages readers to independently validate this work and to develop it further. The information here is provided for context as well as journalistic and technical exploration beyond the scope of our initial investigation. To support this important & innovative work, subscribe today: [TalkLiberation.com](https://talkliberation.com)

## App Overview

This repository contains an application that complements investigative reporting into [WLDragnet](https://talkliberation.com/wldragnet) and makes it easy for Twitter users to find out if they have been targeted and in what context. They can then click through to the relevant sources for the full picture.

The WLDragnet Search is a Flask application that displays results generated from the [WLDragnet files](https://talkliberation.com/wldragnet-repo). This repository also includes [utility scripts](filescan/README.md) for scraping the data and a DDL file for the required database structure.

## Installation and Configuration

### Dependencies
* Python 3.9
* Flask
* Postgresql12.6+
* Redis
* pip
* virtualenv
* psycopg2
* wkhtmltopdf
* poppler

### Docker Setup
```shell
docker-compose up
```
This will spawn three containers, `wldragnet_redis`, `wldragnet_postgresql` and `wldragnet_flask`. The application will then be available at http://127.0.0.1:5000/

In order to get data into the database, the folder `documents/` will be mounted as a volume to the `wldragnet_flask` container.
All PDF files in there can be scanned with
```shell
docker exec -it wldragnet_flask python3 /app/filescan/filescan.py
```

### Manual Setup
The application needs a [postgresql](https://www.postgresql.org/) and a [redis](https://redis.io/) instance
For testing and evaluation the`psycopg2-binary` library from pip can be used instead of `psycopg2` itself.

#### Preparation
1. [Download and install dependencies for psycopg2](https://www.psycopg.org/docs/install.html)
1. [Download and install wkhtmltopdf](https://wkhtmltopdf.org/)
1. [Download and install pdftotext requirements](https://github.com/jalan/pdftotext#os-dependencies) 
1. [Download and install Python](https://www.python.org/downloads/release/python-390/)
1. [Install pip](https://pip.pypa.io/en/stable/installation/)
1. ```pip install virtualenv```
### Installation
1. Clone this repo
1. `cd` into the cloned repo
1. ```virtualenv venv```
1. ```source venv/bin/activate```
1. ```pip install -r dependencies.txt```
1. Connect to a postgres database and run the wldragnet-search-ddl.sql script to set up the database
### Configuration
Create a `.env` file in the project root folder and edit accordingly. These weak credentials are for local testing and should be changed in other scenarios.
```
DOCUMENT_PATH=<path-to-graphs>
DOCUMENT_GLOB_PATTERN=**/*.html
SCAN_PROCESS_POOL_SIZE_MAX=4
DB_HOST=128.0.0.1
DB_PORT=5432
DB_NAME=wldragnet_search
DB_USER=wldragnet_search
DB_PW=<password>
DB_POOL_SIZE_MIN=4
DB_POOL_SIZE_MAX=4
JWT_SECRET_KEY=<arbitrary-secret>
JWT_TOKEN_LIFETIME=600
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
```
### Running the Application
Since this is a flask app, you can start the application from its vitualenv environment via 
```shell
flask run
```

## Licensing

This project is ethical Free and Open-Source Software (FOSS). Any and all original work contained in this repository that is authored by Talk Liberation is released under the [GNU AGPL version 3](http://www.gnu.org/licenses/agpl-3.0.html) or any later version. See [`LICENSE`](LICENSE) for more information.

For JavaScript licensing information, see the [LibreJS](https://www.gnu.org/software/librejs/) labels in [`weblabels.html`](static/weblabels.html)

All of the data used to generate WLDragnet Search reports was gathered via technical analysis with freely-available and FOSS tools, and none of the published information was obtained via leaks, hacking, or data breaches.

The articles written on [talkliberation.substack.com](https://talkliberation.substack.com) are © Copyright Talk Liberation CIC Limited and licensed under a [Creative Commons Attribution-ShareAlike 4.0 International](https://creativecommons.org/licenses/by-sa/4.0/) license. Contact Talk Liberation for further information or additional permissions.


## Contact

For media inquiries, please contact [media@talkliberation.com](mailto:media@talkliberation.com)
