# ReconFIU - Server 

> Python server running on docker container, by running our server in a docker container we can easily change, upgrade and scale our server. In order to use docker, we install `docker-engine` and `docker-compose`. In case of Mac and Windows `docker-machine` with `virtualbox` must also be installed.   

## Requirements

* **Python 3.4* (https://www.python.org/)
    ```
    For Linux run command:
        $ sudo apt-get install python
    Windows/Mac OS:
        Download from https://www.python.org/downloads/release/python-2711/
    ```
    
* **Docker 1.12.6** (https://docs.docker.com/)
    ```
    1. Linux: https://docs.docker.com/engine/installation/linux/
    2. Windows: https://docs.docker.com/docker-for-windows/
        * For older versions of Windows download Docker-Toolbox version 1.12.6 from https://github.com/docker/toolbox/releases
    3. Mac OS: https://docs.docker.com/docker-for-mac/
        * For older versions of Mac download Docker-Toolbox version 1.12.6 from https://github.com/docker/toolbox/releases
    ```
    
* **Docker-compose 1.10.0** 
    ```
    Follow these steps: https://docs.docker.com/compose/install/
    ```
    
* **Docker-machine (Windows/Mac users only)** For docker-machine to run we also need virtualbox. 
    ```
    docker-machine: https://docs.docker.com/machine/install-machine/
    virtualbox: https://www.virtualbox.org/wiki/Downloads
    ```
    After installing docker-machine create a docker virtual machine
    ```
    $ docker-machine create --driver virtualbox default
    $ eval "$(docker-machine env default)"
    ```
    
    Full guide: https://docs.docker.com/machine/get-started/
* **Important Note**
    To check if docker, docker-compose and python are installed run these commands
    ```
    $ docker-compose -v
    $ docker -v
    $ python --version
    ```
    
    If no errors occured then we can build our server.
    
## Setup
To set up our server with docker after all dependencies have been installed follow these steps:
 
* **All platforms** 
    ```
    $ git clone https://github.com/reckonfiu/server.git
    $ cd server
    $ docker-compose up
    ```
    
* **Note:** For Linux you might have to do
    ```
    $ sudo docker-compose up
    ```
    
 In the browser go to `localhost:5000`   
    
## Server Technology Stack
* **Flask** http://flask.pocoo.org/ 
    **flask_cors** https://flask-cors.readthedocs.io/en/latest/
* **Pymongo**  https://api.mongodb.com/python/current/ 
* **PyJWT** https://github.com/jpadilla/pyjwt

## API
* **Search by**
    Returns courses that matched the specific course, term or professor passed in the body of the request. The return data is returned sorted by the fields that are passed. First is course then term and professor. 
    
    Api request route: the object passed to the query parameter must be a JSON string
    ```
    POST /api/searchBy
    headers: 
        content-type: application/json
    body: { query: { course: course_name, term: term_number, prof: firstname<space>lastname  } }
        where course_name and term_number don't contain any white space
    ```    
    If neither course, term or prof fields are passed then the first 100 found records are returned  
    Response:
    ```
    "status": 200,
    "data" : [{ professor : example }],
    "records": 1,
    "message": "Success",
    ```
    TODO:
    Create comparable function for terms (Fall, Spring, Summer)

* **Store comments** - Pending

* **authenticate user**
    ```
    POST /api/login
    headers:  content-type: application/json
    body: { user: {username: "", password: "" } }
    ```
    
* **add user**
    ```
    POST /api/adduser
    headers:  content-type: application/json
    body: { user: {username: "", password: "" } }
    ```
    
* **find user**
    ```
    POST /api/finduser
    headers:  content-type: application/json
    body: { user: {username: "", password: "" } }
    ```
    
* **delete user**  - Pending


## TODO:
     Users should not be allowed to use the API without being logged in.
* **Implement ORM framework library**

     In order to keep the data embedded model consistentin mongo let's implement ORM posibly using
     **Humongolus** https://github.com/entone/Humongolus
    
