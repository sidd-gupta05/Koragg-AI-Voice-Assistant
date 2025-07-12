from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
# ↓↓↓ NEW ↓↓↓
import chromedriver_autoinstaller                         # ADDED
# ↑↑↑ NEW ↑↑↑
from dotenv import dotenv_values
import os
import mtranslate as mt

env_vars = dotenv_values('.env')
InputLanguage = env_vars.get("InputLanguage")

HtmlCode = '''<!DOCTYPE html>
<html lang="en">
<head>
    <title>Speech Recognition</title>
</head>
<body>
    <button id="start" onclick="startRecognition()">Start Recognition</button>
    <button id="end" onclick="stopRecognition()">Stop Recognition</button>
    <p id="output"></p>
    <script>
        const output = document.getElementById('output');
        let recognition;

        function startRecognition() {
            recognition = new webkitSpeechRecognition() || new SpeechRecognition();
            recognition.lang = '';
            recognition.continuous = true;

            recognition.onresult = function(event) {
                const transcript = event.results[event.results.length - 1][0].transcript;
                output.textContent += transcript;
            };

            recognition.onend = function() {
                recognition.start();
            };
            recognition.start();
        }

        function stopRecognition() {
            recognition.stop();
            output.innerHTML = "";
        }
    </script>
</body>
</html>'''

HtmlCode = str(HtmlCode).replace(
    "recognition.lang = '';",
    f"recognition.lang = '{InputLanguage}';"
)

with open(r"Data/Voice.html", "w") as f:
    f.write(HtmlCode)

current_dir = os.getcwd()
Link = f"{current_dir}/Data/Voice.html"

# ---------- Selenium options ----------
chrome_options = Options()
user_agent = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/89.0.4389.90 Safari/537.36"
)
chrome_options.add_argument(f"user-agent={user_agent}")
chrome_options.add_argument("--use-fake-ui-for-media-stream")
chrome_options.add_argument("--use-fake-device-for-media-stream")
chrome_options.add_argument("--headless=new")  # works with latest Selenium
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

# ---------- NEW driver setup ----------
# Automatically downloads a matching ChromeDriver and sets the executable path
chromedriver_autoinstaller.install()
driver = webdriver.Chrome(options=chrome_options)
# --------------------------------------

TempDirPath = rf"{current_dir}/Frontend/Files"

def SetAssistanceStatus(Status: str):
    with open(rf"{TempDirPath}/Status.data", "w", encoding="utf-8") as file:
        file.write(Status)

def QueryModifier(Query: str) -> str:
    new_query = Query.lower().strip()
    query_words = new_query.split()
    question_words = [
        "how", "what", "where", "when", "who", "why", "which", "whose", "whom",
        "can you", "could you", "would you", "will you", "do you", "did you",
        "is it", "are you", "am i", "was it", "were you", "have you", "has it",
        "should i", "shall i", "what's", "what is", "how much", "how many",
        "how long", "how far", "how often", "tell me", "explain", "give me",
        "does", "did", "may i", "might i", "let me know", "could it be",
        "are there", "is there", "do we", "does it"
    ]

    if any(word + " " in new_query for word in question_words):
        if query_words[-1][-1] in ['.', '?', '!']:
            new_query = new_query[:-1] + "?"
        else:
            new_query += "?"
    else:
        if query_words[-1][-1] in ['.', '?', '!']:
            new_query = new_query[:-1] + "."
        else:
            new_query += "."

    return new_query.capitalize()

def UniversalTranslator(Text: str) -> str:
    english_translation = mt.translate(Text, "en", "auto")
    return english_translation.capitalize()

def SpeechRecognization() -> str:
    driver.get("file:///" + Link)
    driver.find_element(By.ID, "start").click()

    while True:
        try:
            Text = driver.find_element(By.ID, "output").text
            if Text:
                driver.find_element(By.ID, "end").click()

                if InputLanguage.lower() == "en" or "en" in InputLanguage.lower():
                    return QueryModifier(Text)
                else:
                    SetAssistanceStatus("Translating...")
                    return QueryModifier(UniversalTranslator(Text))
        except Exception:
            pass

if __name__ == "__main__":
    while True:
        Text = SpeechRecognization()
        print(Text)
