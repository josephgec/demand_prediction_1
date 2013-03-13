demand_preduction
=================

Predict website login traffic

---------------------------- READ ME ---------------------------- 

Project Developer
---------------

Joseph Thomas  -	jt635@cornell.edu


Deliverables
------------

flask_api.py - Python code for the demand prediction system
Predictiontimestamps.csv - The timestamp (UTC) at which demand is to be predicted.
weatherdata.csv - dump of the weather data which saves crawled weather information

Usage
-----


python flask_api.py - To start the API

curl -H "Content-type: application/data" -X POST http://127.0.0.1:5000/input --data-binary @<input_file> - to feed login time stamps to the API for updating predictions. Predictions are stored in the file - Prediction_Output.csv


Requirements
------------

Python 2.7.3
sklearn, flask, datetime, re, json, urllib2, time modules for python


Details
-------
Any questions, problems, or concerns can be directed to my email above.
