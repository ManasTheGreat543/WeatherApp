import json
import requests
import geopandas as gpd
from shapely.geometry import Point
from pymongo import MongoClient
from datetime import datetime

class WeatherApp:

    def __init__(self, request):
        self.data = request.json()
        self.client = MongoClient(f"mongodb+srv://manas_kumar:m_kumar@cluster0.qjbtcsg.mongodb.net/")
        self.db = self.client["TechDatabase"]
        self.collection = self.db["WeatherData"]

    def get_weather_data(self, data):
        weather_url = "https://api.openweathermap.org/data/2.5/weather"
        parameters = {"q": data[0]["name"], "appid": API_KEY, "units": "metric"}
        request = requests.get(weather_url, params=parameters)
        return request.json()

    def get_geo_dataframe(self, data, city, state, country):
        lon = data["coord"]["lon"]
        lat = data["coord"]["lat"]
        temp = data["main"]["temp"]
        description = data["weather"][0]["description"]
        geometry = Point(lon, lat)

        gdf = gpd.GeoDataFrame(
            [
                {
                    "city": city,
                    "state": state,
                    "country": country,
                    "temp": temp,
                    "description": description,
                    "geometry": geometry,
                }
            ],
            crs="EPSG:4326",
        )

        return gdf

    @staticmethod
    def determine_weather(weather_id, temp, description):

        if 200 <= weather_id <= 232:
            return f"🌩 {description, temp}"
        elif 300 <= weather_id <= 321:
            return f"🌦 {description, temp}"
        elif 500 <= weather_id <= 531:
            return f"🌧 {description, temp}"
        elif 600 <= weather_id <= 622:
            return f"❄ {description, temp}"
        elif 701 <= weather_id <= 781:
            if weather_id == 701:
                return f"🌫️ {description, temp}"
            elif weather_id == 711:
                return f"💨 {description, temp}"
            elif weather_id == 721:
                return f"〰 {description, temp}"
            elif weather_id == 731:
                return f"🌬 {description, temp}"
            elif weather_id == 741:
                return f"🌫 {description, temp}"
            elif weather_id == 751:
                return f"🏜️ {description, temp}"
            elif weather_id == 761:
                return f"💨 {description, temp}"
            elif weather_id == 762:
                return f"🌋💨 {description, temp}"
            elif weather_id == 771:
                return f"🌬💨🌪⚡ {description, temp}"
            elif weather_id == 781:
                return f"🌪 {description, temp}"
        elif weather_id == 800:
            return f"☀️ {description, temp}"
        elif 801 <= weather_id <= 804:
            return f"☁️ {description, temp}"
        
    def save_weather_record(self, city, state, country, weather_data):
        record = {
            "city": city,
            "state": state,
            "country": country,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "temperature": weather_data["main"]["temp"],
            "description": weather_data["weather"][0]["description"],
            "weather_id": weather_data["weather"][0]["id"],
            "coord": weather_data["coord"]
        }
        self.collection.insert_one(record)

    def read_all_weather_records(self):
        records = self.collection.find()
        for record in records:
            print(json.dumps(record, default=str, indent=4))

    def delete_weather_record(self, city):
        result = self.collection.delete_many({"city": city})
        print(f"{result.deleted_count} record(s) deleted.")

    def predict_weather(self, city, state, country):

        if not self.data:
            raise requests.exceptions.HTTPError("Your state or city is invalid")

        weather_data = self.get_weather_data(self.data)
        gdf = self.get_geo_dataframe(weather_data, city, state, country)

        world_df = gpd.read_file(gpd.datasets.get_path("naturalearth_lowres"))
        joined_df = gpd.sjoin(gdf, world_df, how="left", predicate="within")
        actual_country = joined_df["name"].values[0]

        if actual_country != country:
            raise ValueError("Provided city is not within the provided country")

        temp_k = weather_data["main"]["temp"]
        weather_description = weather_data["weather"][0]["description"]
        weather_id = weather_data["weather"][0]["id"]
        degrees_type = input("Would you like in Fahrenheit or Celsius(Enter F or C): ")

        match degrees_type:
            case "F" | "f":
                temp_f = (temp_k * 9 / 5) - 459.67
                print(self.determine_weather(weather_id, str(temp_f) + '°F', weather_description))
                self.save_weather_record(city, state, country, weather_data)
            case "C" | "c":
                temp_c = temp_k - 237.15
                print(self.determine_weather(weather_id, str(temp_c) + '°C', weather_description))
                self.save_weather_record(city, state, country, weather_data)
            case _:
                raise ValueError("You need to enter f or c")
            

if __name__ == "__main__":

    API_KEY = "e5670c0d6c7c16bce41c6d09b8f1d342"
    country = input("Give a country(Enter full name): ")
    state = input("Now give me a state within that country: ")
    city = input("Now give me a city within that state: ")
    parameters = {"q": f"{city},{state},{country}", "limit": 1, "appid": API_KEY}
    request = requests.get(
        f"http://api.openweathermap.org/geo/1.0/direct?q={city},{state},{country}&limit=1&appid={API_KEY}",
        params=parameters,
    )

    wa = WeatherApp(request)
    wa.predict_weather(city, state, country)
    
    delete_data = input("Any data would you like to delete?(Type Y for yes): ")

    if delete_data == 'Y' or delete_data == 'y':
        city_to_delete = input("Enter the city ")
        wa.delete_weather_record(city_to_delete)
    
