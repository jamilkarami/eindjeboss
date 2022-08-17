# import the module
import requests
from dotenv import load_dotenv
import table2ascii as t2a
from table2ascii import table2ascii as t2a, PresetStyle
from string import capwords
from vars.eind_vars import *


load_dotenv()
OPENWEATHER_API_KEY = "69a61359cca39d186031c5ef6cf3de01"
CITY = "EINDHOVEN, NL"
BASE_URL = "http://api.openweathermap.org/data/2.5/forecast?"
UNIT = "metric"
LATITUDE = 51.4231
LONGITUDE = 5.4623

weather_url = f"{BASE_URL}q={CITY}&appid={OPENWEATHER_API_KEY}&cnt=6&units={UNIT}&exclude=current,minutely,daily"
response = requests.get(weather_url)
data = response.json()

lst = data['list']

print(lst)

body = []

CONDITION_EMOJIS = {
    'Rain': WEATHER_EMOJI_CLOUDS_RAIN,
    'Clouds': WEATHER_EMOJI_CLOUDS,
    'Clear': WEATHER_EMOJI_SUN,
    'Drizzle': WEATHER_EMOJI_CLOUDS_RAIN,
    'Thunderstorm': WEATHER_EMOJI_STORM,
    'Snow': WEATHER_EMOJI_SNOW,
}

for itm in lst:

  dt = itm['dt_txt'][-8:-3]
  temperature = round(int(itm['main']['temp']))
  condition = itm['weather'][0]['description'].capitalize()
  icon = CONDITION_EMOJIS[itm['weather'][0]['main']]

  body.append([dt, temperature, condition, icon])

output = t2a(
    header=["Time", "Temperature", "Condition", " "],
    body=body,
    style=PresetStyle.thin_thick_rounded
)

print(output)

# if data['cod'] != "404":
#     main_data = data['main']
#     print(main_data)