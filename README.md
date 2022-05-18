# SDWAN_IP_Route
App for Cisco SDWAN which displays all matching routes for a network from longest to shortest on an edge.

## Installation

~~~
git clone https://github.com/dbrown92700/SDWAN_IP_Route
cd SDWAN_IP_Route
~~~

Recommend using Python virtual environment:
~~~
python3 -m venv venv
source venv/bin/activate
~~~

### For testing purposes
Install requirements and run locally
~~~
pip install -r requirements
python3 main.py
~~~
Browse to http://127.0.0.1:8080

### For production uses

Recommend running on a production webserver using CGI or WSGI.

Option to deploy to GCP AppEngine:
- app.yaml and .gcloudignore files are included
- https://cloud.google.com/appengine/docs/standard/python3/create-app

## Screenshots

### Log In
![image](https://user-images.githubusercontent.com/46031546/169123753-9f1ecb8c-76ee-463f-9835-91286d63840a.png)

### Choose device, VPN and network
![image](https://user-images.githubusercontent.com/46031546/169122982-f10e9b31-f9e0-4a08-b668-ae6d32773635.png)

### Results
![image](https://user-images.githubusercontent.com/46031546/169122716-f69c7425-6ce4-4d77-8128-9062de64b11d.png)
