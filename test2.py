# import the module
import requests
from dotenv import load_dotenv
import table2ascii as t2a
from table2ascii import table2ascii as t2a, PresetStyle
from string import capwords
from vars.eind_vars import *
from pyowm import OWM
from pyowm.utils import config
from pyowm.utils import timestamps


load_dotenv()
OPENWEATHER_API_KEY = "69a61359cca39d186031c5ef6cf3de01"
CITY = "EINDHOVEN, NL"
BASE_URL = "http://api.openweathermap.org/data/2.5/forecast?"
UNIT = "metric"
LATITUDE = 51.4231
LONGITUDE = 5.4623

owm = OWM(OPENWEATHER_API_KEY)
mgr = owm.weather_manager()

observation = mgr.forecast_at_place(CITY, "3h", units="metric")

print(observation.forecast.weathers)