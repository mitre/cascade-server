# CASCADE User Guide
CASCADE is a platform that aides analysts in hunting advanced cyber adversaries. By using MITRE's ATT&CK framework, known adversary behaviors can be identified and searched for. Typically, upon finding suspicious activity, an analyst will continue to search the database for related process activity, and identifying how alerts are related to each other. CASCADE automates significant portions of the hunting process, and identifies ATT&CK techniques. Because context is automatically gathered and graphs of activity can be built and labelled with ATT&CK data, analysts can focus efforts on decision making, and response and remediation.



## Table of contents

1. [Sessions](#sessions)
2. [Data Model](#data-model)
3. [Analytics](#analytics)
    1. [Run Mode](#run-mode) (first vs. second pass)
    2. [Query Language](#query-language)
    3. [ATT&CK Mapping](#attack-mapping)
    3. [Configurations](#analytic-configurations)
4. [Investigation Process](#investigation-process)
4. [Tuning Analytics](#tuning-analytics)
5. [Connecting Accounts](#connecting-accounts)
5. [Managing Jobs](#jobs)


## Sessions
Any investigation within CASCADE is done within the context of a session, where cyber analytics are run and event graph building occurs. A session is defined by a name, and the timeframe of activity, defined by the start and end points. These can be described with absolute points in time, such as "01/13/2017 17:00:00 UTC", or with relative offsets, such as "-DD:HH:MM:SS" which indicate sliding windows, where the timeframes are continuously relative to present time. CASCADE allows for either start or end time to be set, allowing for different types of ranges. For instance, setting only the end time to "01/13/2017 17:00:00" but leaving the start undefined is equivalent to "Anything before January 13th, 2017 at 5PM". Internally, all times are stored in UTC, but CASCADE can convert time offsets, such as "-05:00" if appended.

For relative windows, events will automatically roll off as they fall out of the time window. To update a relative window, the session needs to be "refreshed" which causes the server to run all of the analytics again over that time range and investigate any new results that were found.

[Create a new session.](#/create-session)


## Data Model
All events within CASCADE are defined within the extensible data model, which is based off the model in MITRE's [Cyber Analytic Repository](https://car.mitre.org/wiki/Data_Model). The data model defines all of the types of events

- *object* is the name of the changed, accessed or manipulated resource. These can include OS-level entities such as processes, files, network connections, and threads.
- *action* describes what actually happened to or from the resource of interest. For instance, a process can be *created* or *terminated*, a file could be *created*, *written to*, *read* or *deleted*.
- *fields* are the names of the properties that can be used to describe an event. If a process is created, then it is useful to know the *process id* or the *path* of the file executing, or the *command line* arguments.

In CASCADE, a data model event needs to have objects, actions and fields populated, and always needs a time field that specifies when the event occurred. Causal relationships between events are described with links between the two. For example, a link from one process to another could describe the parent-child relationship. The [investigation process](#/investiation-process) section describes how these relationships are defined and chained together.

[View the Data Model.](#/data-model)


## Analytics
Within the browser or via REST API, new analytics can be added to CASCADE. Analytics are essentially queries created to detect specific behaviors. Analytics can be mapped to ATT&CK techniques and tactics, which is useful in understanding specific ATT&CK behaviors. This is key in generating a labelling events with ATT&CK techniques and tactics, and generating an ATT&CK matrix, crucial for identifying detection gaps. Analytics identify suspicious events to [investigate](#investigation). Some behaviors may be significantly more common than others and may yield high volumes of events. In that case, analytics need to be [finely tuned](#tuning-analytics), to filter out predictable and regularly occurring events, which is crucial in avoiding data explosion for number of events found.

[List the existing analytics.](#/analytics)


### Run Mode
Analytics are run as either a first- or second-pass of detection. When running an analytic as a first pass, all results returned (not in the baseline) will be investigated. However, the second-pass mode will only run, but constrain output to results that have *already* been detected by the automated investigation process. When events are identified, they will be fully investigated, via forward- and backward- chaining. Each run mode follows a slightly different order of operations:

#### First Pass
Generate a query for the target database language. For each result returned

1. Ignore the result if it matches the baseline (if present for the analytic).
2. Otherwise, add the event(s) to the session and create a corresponding analytic result.
3. Begin investigating all events via forward and backward chaining. Discovered events will automatically be added to the session.

#### Second Pass
Instead of querying over the database for all instances, a second pass analytic will identify all events in the session that match the analytic query. These include events that were discovered indirectly, by investigating other events identified in other first- or second- pass analytics. Second pass may be useful in cases where an event is not necessarily suspicious without some other incriminating context. For instance, in Windows, finding a `cmd.exe` execution in the parent process tree may be worth investigating, to see any other children it may have caused.

1. Run the analytic over the events *already discovered* in the session. This includes any events found directly by first-pass or indirectly, by investigations or other second-pass analytics.
2. Begin re-investigating these events, in both directions (forward and backward chaining).
3. As new events are added to the session, re-investigate any that trigger the second-pass analytic.

#### Identify Only
There are also two other modes within CASCADE, more for experimental purposes. If desired, analytics can be run as *identify only*, which essentially finds events that match analytics, but does not continue down the investigate process. Hence, it only identifes the events that trigger the analytic, and no further. There is another nearly identical mode that ignores the baseline, temporarily ignoring any tuning that has been done on the analytic. This could be also be useful for gathering metrics and identifying periods of time in which useful tuning could occur.


### Query Language
The CASCADE query language is tightly integrated with the data model. The data model describes the types of events that are collected and the fields that may be present in those events. By integrating with the data model, analytics can be developed in a way that is independent of sensor or database configurations. When analytics are run, the query can be parsed and converted into the target query language of choice, such as Splunk or ElasticSearch.

A data model query is built according to 

    search [object] [action] where ( boolean search expression )

The inner part of the query, the boolean expression, is built off of boolean logic, `and`/`or`/`not`, and field comparisons. The expression `field1 == "value1"` limits the query to events where `field1` is equal to the string "value1". WildCards can also be expressed using `*`. Expressions also can be used to filter down existing analytics by referencing another analytic by name `analytic("Analytic - Remote Thread Creation")`or by id `analytic(579a56ccb16e3c9abd53a15a)`. CASCADE will dereference any analytics upon search time.

For example, to search for all creations of the command shell process that are run with the flag `/c`, a query could be constructed that looks like

    search process create where exe == "cmd.exe" and command_line == "* /c *"

A more complex analytic may look for all events that triggered the analytic "Analytic - Remote Thread Creation", where the thread start function begins with the string "LoadLibrary"


    search thread remote_create where 
        analytic( "Analytic - Remote Thread Creation" ) and start_function == "LoadLibrary*"


Supported Expressions:

- Boolean Operators
    - **and**
    - **or**
    - **not**
- Field Comparisons
    - **==** equality 
    - **!=** inequality
    - **<**  less than
    - **<=** less than or equal to
    - **>=** greater than or equal to
    - **>**  greater than
- Analytic References
    - analytic(`id`)
    - analytic("Name of Analytic")
- Order of Operations
    - field1 == "value1" **and** **not** ( field2 == "value2" **or** field3 != "value4")


### External Analytics
To detect more complex behaviors that require patterns between multiple analytics, it may be best to implement these in another platform. CASCADE's query language may be easy to convert into multiple languages, but at the cost of its simplicity. As a compromise, more sophisticated logic, such as statistical summaries, outliers, joins, and transactions should be implemented in the target database query language directly, and CASCADE requires the name of the saved search.

To make this possible, there needs to be a mapping of the query outputs into the data model events. For instance, if an external query detects events using custom field names and has several events, CASCADE just needs to know how each field maps to the query. This is implemented in the browser or directly via API. One example field mapping for [CAR-2014-02-001: New Service Monitoring](https://car.mitre.org/wiki/CAR-2014-02-001), that identifies a process create and a file create  event of a Windows service. The data model fields are on the left and the analytic output fields are on the right

- file - create
    - file_path == Image
    - fqdn  == ComputerName
    - image_path == CreatorImagePath
    - pid == FileCreatePid
- process - create
    - fqdn  == ComputerName
    - image_path == Image
    - pid == ServiceProcessPid

### Analytic Configurations
There may be multiple use cases for different analytics. Depending on the environment, and the type of behavior an analyst is looking for, a different set of first or second pass analytics may be created. For instance, it may be useful to have a list of every analytic run as second-pass mode. This could be very useful to force ATT&CK labeling of all discovered events that match an analytic, or as part of a forensic process. Or a list of high confidence analytics could be generated and run as a first-pass to quickly identify malicious activity. It may also be useful to create a hybrid list of first and second pass analytics to detect a specific red team or adversary, for testing or evaluation purposes. When operating in the context of a session, multiple configurations may be run and these are easily built on-the-fly.

[View or modify analytic configurations.](#/analytics/configure)


## Investigation Process
As events are identified by analytics, they start of a recursive investigative process in two directions: forward and backward. For example, if one analytic identifies a suspicious process execution, then there are naturally several causally related events that may also be suspect. These events may happen before the suspicious process creation as part of its history, or could be part of its future. The investigation process can looks for cause-and-effect relationships both ways

- **Forward Pivots** - *What events did this cause to happen?*
    - Parent Process -> Child Process
    - File Modification (.exe) -> Process Execution
- **Backward Pivots** - *What events was this caused by?*
    - Child Process <- Parent Process
    - Process Execution <- File Modification (.exe)

By recursively chaining these relationships, CASCADE can identify distant related events. For instance, by chaining forward pivots, children, grandchildren, and distant descendants can all be identified. But chaining backward pivots, an ancestry can be built to identify a lineage for context, or to identify earlier suspicious events. When an analytic identifies a suspicious event (via first-pass or second-pass searches), CASCADE begins investigating both the ancestry and descendant events.

[View the data model relationships.](#/data-model)

## Tuning Analytics
Analytic baselines are generated and adjusted via the tuning process. Tuned analytics must also have a start and end time to specify the time period to collect events for the analytic. Once the results are collected, CASCADE organizes the events into a [hierarchical tree](https://en.wikipedia.org/wiki/Hierarchical_clustering). This tree is partitioned by looking for the most common key-value pairs and repeating this process recursively. Currently, wildcard matching is not supported, so there is no effort to identify "similar" strings when building these structures. These hierarchies can be collapsed by left-clicking on nodes to baseline at a higher level. When an event is returned by the event, it effectively walks the tree, and determines if its fields match the conditions in the baseline. If it continues to make this process to a leaf node and the key-value pair still matches, then that result is considered to be a match. By collapsing nodes, the criteria for matches can be made less strict. These decisions--strictness, time frame, etc.--are decisions that analysts make and are not automated by CASCADE. To remove events from the baseline, right clicking on a node will remove the corresponding events. Additionally, the organizational fields may be dynamically decided, and if one field is redundant or has high entropy, it can be unchecked and the baseline will rebuild upon clicking "Update Fields".

[View or modify analytic baselines.](#/analytics/tuning)

## Connecting Accounts
Currently, CASCADE query can be integrated with Splunk, ElasticSearch and MongoDB, if the events are already normalized according to the data model. To connect CASCADE to a new database instance, it needs to know configuration information. This can be configured from the browser by navigating to the User **>** [Manage External Databases](#/admin/databases) **>** [Connect to Database](#/admin/databases/connect) menu. This information only pertains to connection information about the database, but not login credentials. Any login information to the database is connected to the CASCADE account, described below in account management.


### Authentication to External Databases
If a user exists and the connection information is also present (see [Connecting to Databases](#connecting-to-databases)), it can be connected to the account with login information. Within the web application, click the User **>** Account Settings **>** [Connect to Database](#/account/add-database) link. Select the database instance that was created earlier and specify the user login information, such as user name and password. If login is successful, the external credentials are associated with the CASCADE user account, and all queries will happen on behalf of it.


## Jobs
Many different types of searches can be performed to fetch for events or perform other actions. In CASCADE, pending requests are implemented in a job queue. All jobs happen on behalf of a user. Jobs may create additional jobs, allowing for the graph to self-expand as new events are discovered. To manage jobs from the web app, click the User **>** [Manage Jobs](#/admin/jobs) link.

Types of jobs

* **AnalyticJob**       - Run an analytic (first- or second-pass) and investigate the results returned
* **ExtractEventsJob**  - Extracts events out of external analytics based off the specified field mapping
* **CustomQueryJob**    - Searches for any events that match a query that is specified on-the-fly
* **InvestigateJob**    - Create forward and backward pivots for an identified event. No searches are run
* **PivotJob**          - For an event and a specific pivot, search for matching events
* **TuningJob**         - Tune an analytic over a specified period of time to build an initial baseline
