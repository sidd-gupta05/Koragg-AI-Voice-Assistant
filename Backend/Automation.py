from AppOpener import close, open as appopen 
from webbrowser import open as webopen
# from pywhatkit import search, image_to_base64, take_screenshot_as_base64, playonyt, playony
from pywhatkit import search, playonyt
from dotenv import dotenv_values
from bs4 import BeautifulSoup
from rich import print
from groq import Groq
import webbrowser
import subprocess
import requests
import os
import asyncio 
import keyboard
import pyautogui
import time
import psutil
import requests
from datetime import datetime


env_vars = dotenv_values(".env")
GroqAPIKey = env_vars.get("GroqAPIKey")
WEATHER_API_KEY = env_vars.get("OpenWeatherAPIKey")
# Define CSS classes for prsing specific elements in  HTML content
classes = [
    "zCubwf",  # Common result container
    "hgKElc",  # Featured snippet or info card
    "LTKOO sY7ric",  # Lyrics container or special formatting
    "Z0LcW",  # Direct answer box
    "gsrt vk_bk FzvWSb YwPhnf",  # Paragraph-style answer
    "pclqee",  # Translation block
    "tw-Data_text tw-text-small tw-ta",  # Translated text or dictionary
    "IZ6rdc",  # Info panel in search
    "O5uR6d LTKOO",  # Alternate styling for info box
    "vlzY6d",  # Temperature or numerical values
    "webanswers-webanswers_table__webanswers-tables",  # Table-style answers
    "dDoNo ikb48b gsrt",  # Definitions or highlighted answers
    "sXlaOe",  # Calculator/displayed number results
    "SPZz6b"  # Summary section or title area
]

useragent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
client = Groq(api_key=GroqAPIKey)

professional_responses = [
    "Your satisfaction is our top priority; feel free to reach out if there's anything else I can assist you with.",
    "I'm at your service for addtional question or support you may need-don't hesitate to ask.",
]

messages = []

SystemChatBot = [{"role": "system", "content": f"Hello, I am {os.environ.get('Username', 'User')}, You're a content Writer. You have to write like letters,code,applications,essays, notes, songss,poem etc. "}]

def GoogleSearch(Topic):
    search(Topic)
    return True

def GetWeatherReport(location: str):
    """
    Get current weather report for a location
    """
    try:
        # First try to get coordinates if location is a city name
        geo_url = f"http://api.openweathermap.org/geo/1.0/direct?q={location}&limit=1&appid={WEATHER_API_KEY}"
        geo_response = requests.get(geo_url).json()
        
        if not geo_response:
            return "Location not found"
            
        lat = geo_response[0]['lat']
        lon = geo_response[0]['lon']
        
        # Get weather data
        weather_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={WEATHER_API_KEY}&units=metric"
        weather_data = requests.get(weather_url).json()
        
        # Parse the response
        temp = weather_data['main']['temp']
        feels_like = weather_data['main']['feels_like']
        humidity = weather_data['main']['humidity']
        wind_speed = weather_data['wind']['speed']
        description = weather_data['weather'][0]['description']
        city = weather_data['name']
        
        report = f"""
        Weather Report for {city}:
        - Temperature: {temp}°C (Feels like {feels_like}°C)
        - Conditions: {description.capitalize()}
        - Humidity: {humidity}%
        - Wind Speed: {wind_speed} m/s
        """
        
        return report
        
    except Exception as e:
        return f"Error getting weather data: {str(e)}"

# Alternative using Open-Meteo (no API key needed)
def GetWeatherReportOpenMeteo(location: str):
    """
    Get current weather using Open-Meteo API
    """
    try:
        # First get coordinates (simplified version)
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={location}&count=1"
        geo_response = requests.get(geo_url).json()
        
        if not geo_response.get('results'):
            return "Location not found"
            
        result = geo_response['results'][0]
        lat = result['latitude']
        lon = result['longitude']
        city = result['name']
        
        # Get weather data
        weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,apparent_temperature,wind_speed_10m,weather_code"
        weather_data = requests.get(weather_url).json()
        
        current = weather_data['current']
        
        # Weather code to text mapping (simplified)
        weather_codes = {
            0: "Clear sky",
            1: "Mainly clear",
            2: "Partly cloudy",
            3: "Overcast",
            45: "Fog",
            61: "Slight rain",
            80: "Rain showers"
            # Add more codes as needed
        }
        
        description = weather_codes.get(current['weather_code'], "Unknown weather conditions")
        
        report = f"""
        Weather Report for {city}:
        - Temperature: {current['temperature_2m']}°C (Feels like {current['apparent_temperature']}°C)
        - Conditions: {description}
        - Humidity: {current['relative_humidity_2m']}%
        - Wind Speed: {current['wind_speed_10m']} km/h
        """
        
        return report
        
    except Exception as e:
        return f"Error getting weather data: {str(e)}"

def TakeScreenshot():
    folder = "Data"
    if not os.path.exists(folder):
        os.makedirs(folder)

    i = 1  
    while True:
        filename = f"{folder}/screenshot_{i}.png"
        if not os.path.exists(filename):
            break
        i += 1

    screenshot = pyautogui.screenshot()
    screenshot.save(filename)

    # Open the screenshot automatically
    webbrowser.open(f"file://{os.path.abspath(filename)}")

    return filename

def Content(Topic):

    def OpenNotepad(File):
        default_text_editor = 'notepad.exe'
        subprocess.Popen([default_text_editor, File])

    def ContentWriterAI(prompt):
        messages.append ({"role": "user", "content": f'{prompt}'})

        completion = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=SystemChatBot + messages,
            max_tokens=2048,
            temperature=0.7,
            top_p=1,
            stream=True,
            stop=None
        )

        Answer = ""

        for chunk in completion:
            if chunk.choices[0].delta.content:
                Answer += chunk.choices[0].delta.content

        Answer = Answer.replace("</s>","")
        messages.append({"role": "assistant", "content": Answer})
        return Answer
    
    Topic: str = Topic.replace("Content ", "")
    ContentByAI = ContentWriterAI(Topic)

    with open(rf"Data\{Topic.lower().replace(' ', '')}.txt", "w", encoding="utf8") as file:
        file.write(ContentByAI)
        file.close()

    OpenNotepad (rf"Data\{Topic.lower().replace(' ', '')}.txt")
    return True


def YoutubeSearch(Topic): 
    Url4Search = f"https://www.youtube.com/results?search_query={Topic}"
    webbrowser.open(Url4Search)
    return True

def PlayYoutube(query):
    playonyt(query)
    return True


def OpenApp(app, sess=requests.session()):
    try:
        appopen(app, match_closest=True, output=True, throw_error=True)
        return True
    except Exception:
        app_name = app.lower()

        web_links = {
            app_name: f"https://www.{app_name}.com"
        }

        if app_name in web_links:
            webopen(web_links[app_name])
        else:
            query = app.replace(" ", "+")
            webopen(f"https://www.google.com/search?q={query}")

        return True

def CloseApp(app):

    if "chrome" in app:
        pass
    else:
        try:
            close(app, match_closest=True, output=True, throw_error=True)
            return True
        except:
            return False
        
contacts = {
    "siddharth": "8779032500",
    "laksh": "9321471908",
    "manas amare": "9769819875",
    "yash bro": "8451042568",
    "krrish": "8454066177",
    "mummy": "9867353765",
    "papa": "8689903314",
    "vedanth": "9987602631",
    "sandeep vishwakarma": "9920232578",
    "puja kukade": "9890291263",
    "harshada": "7039526506",
}

import pygetwindow as gw

def CallOnWhatsappByName(name: str, message: str = ""):
    name = name.lower().strip()
    message = message.strip()

    if name not in contacts:
        print(f"No number found for contact '{name}'")
        return False

    number = contacts[name]
    encoded_msg = requests.utils.quote(message)
    url = f"https://wa.me/{number}?text={encoded_msg}"
    webbrowser.open(url)

    time.sleep(5)  

    try:
        window = gw.getWindowsWithTitle("WhatsApp")[0]  
        window.activate()
    except Exception as e:
        print(f"[Warning] Could not focus browser window: {e}")

    time.sleep(2) 

    pyautogui.press("enter")
    return True

def GetSystemReport():
    cpu = psutil.cpu_percent(interval=1)
    ram = psutil.virtual_memory().percent
    disk = psutil.disk_usage('/').percent

    report = f"""
    CPU Usage: {cpu}%
    RAM Usage: {ram}%
    Disk Usage: {disk}%
    """
    print(report)
    return report

def SearchOnGoogleMaps(place: str):
    query = (
        place.replace("near me", "")
        .replace("find", "")
        .replace("search for", "")
        .strip()
    )
    query = query.replace(" ", "+")
    url = f"https://www.google.com/maps/search/{query}"
    webbrowser.open(url)
    return True

def System(command):

    def mute():
        keyboard.press_and_release("volume mute")

    def unmute():
        keyboard.press_and_release("volume unmute")

    def volume_up():
        keyboard.press_and_release("volume up")

    def volume_down():
        keyboard.press_and_release("volume down")

    if command == "mute":
        mute()
    elif command == "unmute":
        unmute()
    elif command == "volume_up":
        volume_up()
    elif command == "volume_down":
        volume_down()

    return True

async def TranslateAndExecute(commands: list[str]):
    funcs = []

    for command in commands:
        command = command.lower().strip()

        if "volume" in command:
            if "mute" in command:
                funcs.append(asyncio.to_thread(System, "mute"))
            elif "unmute" in command:
                funcs.append(asyncio.to_thread(System, "unmute"))
            elif "increase" in command or "up" in command:
                funcs.append(asyncio.to_thread(System, "volume_up"))
            elif "decrease" in command or "down" in command:
                funcs.append(asyncio.to_thread(System, "volume_down"))

        elif command.startswith("open"):
            if "open it" == command or "open file" == command:
                pass
            else:
                fun = asyncio.to_thread(OpenApp, command.removeprefix('open '))
                funcs.append(fun)

        elif command.startswith("general "):
            pass

        elif command.startswith("realtime "):
            pass

        elif command.startswith("close "):
            fun = asyncio.to_thread(CloseApp, command.removeprefix('close '))
            funcs.append(fun)

        elif command.startswith("play "):
            fun = asyncio.to_thread(PlayYoutube, command.removeprefix('play '))
            funcs.append(fun)

        elif command.startswith(("write", "draft", "compose", "make", "create", "type", "content", "letter", "aplication")):
            fun = asyncio.to_thread(Content, command)
            funcs.append(fun)

        elif command.startswith("google search "):
            fun = asyncio.to_thread(GoogleSearch, command.removeprefix('google search '))
            funcs.append(fun)

        elif command.startswith("youtube search "):
            fun = asyncio.to_thread(YoutubeSearch, command.removeprefix('youtube search '))
            funcs.append(fun)

        elif "screenshot" in command or "take screenshot" in command or "capture screen" in command:
            fun = asyncio.to_thread(TakeScreenshot)
            funcs.append(fun)

        elif command.startswith("message "):
            try:
                content = command.removeprefix("message ").strip()
                parts = content.split(" ", 1)
                name = parts[0]
                message = parts[1] if len(parts) > 1 else ""
                fun = asyncio.to_thread(CallOnWhatsappByName, name, message)
                funcs.append(fun)
            except Exception as e:
                print(f"Error processing call command: {e}")

        elif any(keyword in command for keyword in ["weather", "forecast", "temperature"]):
            temp_command = command
            for word in ["what is", "show me", "tell me", "current", "weather", "forecast", "temperature", "report"]:
                temp_command = temp_command.replace(word, "")
            location = temp_command.strip()
            if not location:
                location = "mumbai"

            fun = asyncio.to_thread(GetWeatherReport, location)
            funcs.append(fun)

        elif "report" in command:
            fun = asyncio.to_thread(GetSystemReport)
            funcs.append(fun)
            

        elif any(keyword in command for keyword in ["near me", "navigate to", "directions to"]):
            search_query = command.replace("near me", "").strip()
            fun = asyncio.to_thread(SearchOnGoogleMaps, search_query)
            funcs.append(fun)

        else:
            if not command.startswith("generate image"):
                print(f"No function found. For {command}")

    results = await asyncio.gather(*funcs)

    for result in results:
        if isinstance(result, str):
            yield result
        else:
            yield result


async def Automation(commands: list[str]):
    async for result in TranslateAndExecute(commands):
        pass

    return True

if __name__ == "__main__":
    asyncio.run(Automation([""]))

