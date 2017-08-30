# CASCADE Technical Guide

This guide describes the design choices behind CASCADE, the interplay between components and details into the structure of the source code. The guide is intended for any audience that desires to know inner workings, and has plans to continue to develop, maintain or fix server-side or client-side code. CASCADE consists of a web server, which provides a RESTful API interface and acts as middleware between the front-end web UI and external database solutions, such as ElasticSearch and Splunk. Analytics are saved queries that are designed to detect known behaviors, and these run on behalf of the user. When an event is found, CASCADE will automate the drilldown process, and continue to return to the external database to fetch more events and gather context. By gathering related events, a graph of activity can be built and analyzed, which provides a much richer view and understanding that can empower an analyst's decision-making process.


#### Table of contents
1. [File Organization](#file-organization)
2. [Server Details](#server)


## File Organization
Several components work together for CASCADE to function properly. The directory structure is described in sections, based off the highest level directories. 


The `app/` directory Contains Python modules and all of the necessary code for the server-side framework. This is where the data model and analytics are defined, connections to external databases (e.g. Splunk, ElasticSearch) are managed, and the web/API server is located.

      .
      |-- app/
      |    `-- cascade/
      |         |-- data_model/
      |         |    |-- language/
      |         |    |-- events.py
      |         |    |-- pivots.py
      |         |    `-- query.py
      |         |-- query_layers/
      |         |    |-- base.py
      |         |    |-- elastic.py
      |         |    `-- splunk.py
      |         |-- analytics.py
      |         |-- attack.py
      |         |-- session.py
      |         |-- jobs.py
      |         |-- runner.py


Configuration files are stored in the `/conf` directory. The configuration file(s) contain settings for CASCADE, such as database keys, links to the ATT&CK and CAR wikis, and server settings. This folder contains files that store the default settings (`default.yml`), as well as the active configuration (`cascade.yml`)

      |-- conf/
      |    |-- cascade.yml
      |    `-- default.yml

Documents, such as these guides are stored in the documents folder, as both Markdown (source) and PDF.

      |-- docs/
      |    |-- user-guide(.md | .pdf)
      |    `-- technical-guide(.md | .pdf)

The `misc/` directory contains useful but miscellaneous files. This directory is prepopulated with a few `.bson` files, which are used to initialize MongoDB, which CASCADE uses as its database.

      |-- misc/

The web application is in the `www/` folder. The application is built with Bootstrap, Angular and d3 frameworks. The shared libraries are all consolidated into `lib/`. The app-specific developments are split off from commonly used directives, templates, and components, from page specific views.

      |-- www/
      |   |-- app/
      |   |   |-- common/
      |   |   |-- components/
      |   |   `-- app.js
      |   `-- lib/
      |        |-- css/
      |        `-- js/

The single python file at the root level, `cascade.py` loads up the other code and starts the server. The command line arguments are printed out by running `python cascade.py --help`.  

      `-- cascade.py

## Server
The CASCADE server is developed in python and the source code is in the `app` folder. The file `cascade.py` loads the server code, parses the command line, or other one-off commands, such as importing the database, creating a user or running setup. Persistent objects are stored in MongoDB, and schemas are defined using the [MongoEngine](http://docs.mongoengine.org/) library
 for Python.


### Command Line Usage
CASCADE can be configured to allow account creation via the web interface. If enabled, any user can access the site to create accounts, manipulate sessions and view data. There are currently no account control mechanisms to define roles and permissions; every user has the same level of access. The account creation can be enabled by setting `config: account_creation` to `True` in the config file `conf/cascade.yml`

Otherwise there are several command line arguments to create users and reset passwords:

    Usage: python cascade.py [-h | --help] [-v | -vv | -vvv]

#### Setup

                --setup

#### Start Job Runner Service

                --jobs | -j | --job_runner

#### Manage Accounts

              --create_user username
              --change_password username
              --reset_password username [--send_email]


#### Manage Mongo Collections

              --export path/to/file.bson [--collection analytic --collection attack_tactic ...  | -a ]
              --import path/to/file.bson
              --purge [--collection analytic --collection attack_tactic ...  | -a ]
