# CASCADE
CASCADE is a research project at MITRE which seeks to automate much of the investigative work a “blue-team” team
would perform to determine the scope and maliciousness of suspicious behavior on a network using host data.

The prototype CASCADE server contained in this repository has the ability to handle user authentication, run analytics, 
and perform investigations. The server runs analytics against data stored in Splunk/ElasticSearch to generate alerts. 
Alerts trigger a recursive investigative process where several ensuing queries gather related events. Supported event 
relationships include parent and child processes (process trees), network connections, and file activity. 
The server automatically generates a graph of these events, showing relationships between them, 
and tags the graph with information from
the [Adversarial Tactics, Techniques & Common Knowledge (ATT&CK)](https://attack.mitre.org) project. The events in  
generated graph can also be displayed as a timeline. 

To reduce the false-positive rate, the CASCADE servers analytics can also be tuned analytics to the environment 
it is deployed in. 

The server also offers the ability to
express simple analytics in a platform agnostic query language. Native CASCADE queries are automatically
translated by the server into Splunk and ElasticSearch queries depending on which platform the server is connected to.
The server allows users to easily create new analytics, and comes bundled with analytics to detect several ATT&CK 
techniques.

For more information on how CASCADE performs these activities refer to the [user guide](docs/user-guide.md).
The functionality is exposed via a RESTful API and a web interface. CASCADE uses Python Flask and Gevent
to create an asynchronous HTTP server.

## Requirements
There are a number of requirements to run CASCADE:
* Python 2.7 and the associated libraries listed in the [requirements.txt](requirements.txt).
* A MongoDB server running locally
* CASCADE can retrieve sensor data stored in either Splunk or ElasticSearch. This data must be normalized 
and stored in the [Cyber Analytic Repository](https://car.mitre.org/wiki/Main_Page) 
(CAR) [Data Model](https://car.mitre.org/wiki/Data_Model). 
[Unfetter Analytic](https://github.com/unfetter-analytic/unfetter) provides an implementation of 
this Data Model using [sysmon](https://technet.microsoft.com/en-us/sysinternals/sysmon) as the host sensor. 

## Installation 
* Clone the repository.
* Install all [requirements](docs/requirements.md).
* Run CASCADE with the `--setup` flag to begin initialization. The setup will prompt for server configuration settings, 
database encryption keys, etc. If no values are provided for the parameters, setup continues with the default values.

    python cascade.py --setup


## Running the CASCADE server

    python cascade.py --help

To start the web server:

    python cascade.py

A second process is responsible for executing queries against Splunk or ElasticSearch and should be started as 
well (e.g. in a second console): 

    python cascade.py --jobs
    
## Getting Started

### Account Creation 
* In a browser navigate to the server ( http://127.0.0.1:5000 , by default). 
* Click 'Login'
* Click 'Create Account'
* Alternatively, accounts can be created from the command line:

    python cascade.py --create_user username
    
### Configure Connection to ElasticSearch/Splunk Data Source
*NOTE: CASCADE expects data to be normalized according to its Data Model.*
* Login to the CASCADE web server. 
* Click your name in the top-right corner of the page. Select 'Manage External Databases.'
* Click Connect to Database and fill out the ensuing form. 
*NOTE: Access to these database may require different credentials for each user specific; these credentials are
configured at a later step, in your CASCADE user's profile.*
* Click Connect

### Configure an account to use a database
* Login to the CASCADE web server.
* Click your name in top-right corner of page and select 'Account Settings'
* Select 'Connect to Database'
* Choose a database connection you configured earlier, fill in credentials as necessary, and submit the form. 

### Create a Session and Run Analytics
*NOTE: To use a data source, you must 1) have previously created a database connection and 2) added it to your 
CASCADE user's profile*
* Login to the CASCADE Server
* Click on the sessions tab and select 'Create a New Session' 
* Enter the time interval you would like to run analytics against and select 'Create'
* From the created session's tab, select 'Run Analytics' 
* Select some analytics from the list and select 'Run Analytics.'  Analytics can be run in different modes. 
The 'first-pass' mode is best for high signal-to-noise ratio analytics that are very indicative of malicious activity. 
The 'second-pass' mode is best for 'noisier' analytics that provide useful contextual information, 
but have a prohibitively high false-positive rate. For more information about analytics modes, 
see the [user guide](docs/user-guide.md). 

## Database Management
### Exporting to a file

    python cascade.py --export path/to/cascade_dump.bson 
        [--collection analytics]
        [--collection users]
        [--collection <collection name>]

### Importing from a file
*WARNING: Importing a CASCADE database from a file will overwrite any existing content.*

    python cascade.py --import path/to/cascade_dump.bson

