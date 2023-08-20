import numpy as np
import pandas as pd
import datetime as dt

import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func, inspect

from flask import Flask, jsonify

#################################################
# Database Setup
#################################################
engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# reflect an existing database into a new model
Base = automap_base()

# reflect the tables
Base.prepare(engine, reflect=True)

# Save references to each table
Measurement = Base.classes.measurement
Station = Base.classes.station

# Create our session (link) from Python to the DB
session = Session(engine)

#################################################
# Flask Setup
#################################################
app = Flask(__name__)

#################################################
# Flask Routes
#################################################
@app.route("/")
def home():
    """List all available api routes."""
    return (
        f"Welcome,available routes are:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/<start><br/>"
        f"/api/v1.0/<start>/<end><br/>"
    )

@app.route("/api/v1.0/precipitation")
def precipitation():

    #create session link from Python to DB
    sessions=Session(engine)
    # Query to retrieve the last 12 months of precipitation data. 
    last_date = session.query(Measurement.date).order_by(Measurement.date.desc()).first()
    #latest_date= 2017-8-23 (Y-m-d)
    a_year = dt.date(2017,8,23) - dt.timedelta(days= 365)
    
    precip = session.query(Measurement.date, Measurement.prcp).\
    filter(Measurement.date >= a_year, Measurement.prcp != None).\
    order_by(Measurement.date).all()
    session.close()

#Return the JSON representation of your dictionary
    return jsonify(dict(precip))

@app.route("/api/v1.0/stations")
def stations():
    
    # Create session link from Python to DB
    session = Session(engine)
    
    # Query stations from the dataset
    stations = session.query(
        Station.station, Station.name, Station.latitude,
        Station.longitude, Station.elevation
    ).all()
    
    session.close()
    
    # Create a list to hold all station dictionaries
    all_stations = []
    
    # Loop through each station and create a dictionary for each
    for station, name, latitude, longitude, elevation in stations:
        station_dict = {
            "station": station,
            "name": name,
            "latitude": latitude,
            "longitude": longitude,
            "elevation": elevation
        }
        all_stations.append(station_dict)
    
    # Return JSON representation of all stations
    return jsonify(all_stations)

@app.route("/api/v1.0/tobs")
def tobs():
    # Create session link from Python to DB
    session = Session(engine)
    
    # Calculate the date one year from the last date in the dataset.
    last_date = session.query(Measurement.date).order_by(Measurement.date.desc()).first()[0]
    a_year_ago = dt.datetime.strptime(last_date, '%Y-%m-%d') - dt.timedelta(days=365)

    # Most active
    most_active = session.query(Measurement.station, func.count(Measurement.station)).\
        group_by(Measurement.station).\
        order_by(func.count().desc()).first()
    # Get the ID for most active
    most_active_ID = most_active[0]
    
    # Query the last 12 months of temperature observation data of the most active station
    temp_year = session.query(Measurement.date, Measurement.tobs).\
        filter(Measurement.date >= a_year_ago, Measurement.station == most_active_ID).\
        order_by(Measurement.date).all()
    
    session.close()
    
    # Create a list to hold all temperature dictionaries
    temp_all_year = []
    for date, temp in temp_year:
        tempy = {}
        tempy["date"] = date  # Assign the date
        tempy["temperature"] = temp  # Assign the temperature
        temp_all_year.append(tempy)
    
    return jsonify(temp_all_year)  
     
   
@app.route("/api/v1.0/<start>",defaults={'end':None})
@app.route("/api/v1.0/<start>/<end>")
def start_to_end(start, end):  
#Return a JSON list of the minimum temperature, the average temperature, and the maximum temperature 
# for a specified start or start-end range.

#create session link to DB
    session=Session(engine)
   
#Condition for both start and end date are used
    if end:
       start= dt.datetime.strptime(start,"%m%d%Y")
       end= dt.datetime.strptime(end,"%m%d%Y")
       t_temp = session.query(*[func.min(Measurement.tobs),func.max(Measurement.tobs),func.avg(Measurement.tobs)]).\
                filter(Measurement.date >= start).\
                filter(Measurement.date <= end).all()
#condition for only start date
    else:
        start= dt.datetime.strptime(start,"%m%d%Y")
        t_temp = session.query(*[func.min(Measurement.tobs),func.max(Measurement.tobs),func.avg(Measurement.tobs)]).filter(Measurement.date >= start).all()
    session.close()
#To convert query to list
    temp_list= list(np.ravel(t_temp))
    return jsonify(temp_list)
     
if __name__ == '__main__':
    app.run(debug=True)

