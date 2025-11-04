# Main.py
from Frontend.GUI import(
    GraphicalUserInterface,
    SetAssistantStatus,
    ShowTextToScreen,
    TempDirectoryPath,
    SetMicrophoneStatus,
    AnswerModifier,
    QueryModifier,
    GetMicrophoneStatus,
    GetAssistantStatus,
)
from Backend.Model import FirstLayerDMM
from Backend.RealtimeSearchEngine import RealtimeSearchEngine
from Backend.SpeechToText import SpeechRecognization
from Backend.Chatbot import ChatBot
from Backend.TextToSpeech import TextToSpeech
from Backend.Automation import Automation
from Backend.ImageGeneration import ImageGenerator
from dotenv import dotenv_values
from asyncio import run
from time import sleep
from random import randint
import threading
import json
import os

env_vars = dotenv_values(".env")
Username = env_vars.get("Username")
Assistantname = env_vars.get("Assistantname")
DefaultMessage = f'''{Username} : Hello {Assistantname}, How are you?
{Assistantname} : Welcome {Username}. I am doing well thanks for asking. How may I help you?'''
subprocesses = []
image_generation_process = None
Functions = ['open', "close", "play", "system", "content","google search", "youtube search", "screenshoot", "screenshot", "report", "message", "near me" ,"navigate to" ,"directions to","write", "draft", "compose", "make", "create", "type", "letter", "aplication",]

def cleanup():
    """Cleanup function to terminate subprocesses on exit"""
    for proc in subprocesses:
        try:
            proc.terminate()
        except:
            pass

def enhance_image_prompt(prompt):
    """Enhance the image generation prompt with quality parameters"""
    enhancements = [
        "high quality", "4k resolution", "detailed", "sharp focus",
        "professional photography", "studio lighting"
    ]
    return f"{prompt}, {', '.join(enhancements)}, seed={randint(0, 1000000)}"

def ShowDefaultChatIfNoChats():
    File = open(r"Data\ChatLog.json" , "r", encoding="utf-8") 
    if len(File.read())<5:
        with open(TempDirectoryPath('Database.data'), "w", encoding = 'utf-8') as file:
            file.write("")

        with open(TempDirectoryPath('Responses.data'), "w", encoding = 'utf-8') as file:
            file.write(DefaultMessage)

def ReadChatLogJson():
    with open(r"Data\ChatLog.json", "r", encoding="utf-8")as file:
        chatlog_data = json.load(file)
    return chatlog_data

def ChatLogIntegration():
    json_data = ReadChatLogJson()
    formatted_chatlog = ""
    for entry in json_data:
        if entry["role"] == "user":
            formatted_chatlog += f"User : {entry['content']}\n"
        elif entry["role"] == "assistant":
            formatted_chatlog += f"Assistant : {entry['content']}\n"
        formatted_chatlog = formatted_chatlog.replace("User",Username + " ")
        formatted_chatlog = formatted_chatlog.replace("Assistant",Assistantname + " ")

        with open(TempDirectoryPath('Database.data'), 'w', encoding='utf-8') as file:
            file.write(AnswerModifier(formatted_chatlog))

def ShowChatsOnGUI():
    File = open(TempDirectoryPath("Database.data") , "r", encoding="utf-8") 
    Data = File.read()
    if len(str(Data))>0:
        lines = Data.split('\n')
        result = '\n'.join(lines)
        File.close()
        File = open(TempDirectoryPath("Responses.data") , "w", encoding="utf-8")
        File.write(result)
        File.close()

def InitialExecution():
    SetMicrophoneStatus("False")
    ShowTextToScreen("")
    ShowDefaultChatIfNoChats()
    ChatLogIntegration()
    ShowChatsOnGUI()

InitialExecution()

def MainExecution():
    global image_generator
    
    TaskExecution = False
    ImageExecution = False
    ImageGenrationQuery = ""

    if 'image_generator' not in globals():
        image_generator = ImageGenerator()
    
    SetAssistantStatus("Listening...")
    try:
        Query = SpeechRecognization()
        if not Query:
            SetAssistantStatus("Available...")
            return False
    except Exception as e:
        print(f"Speech recognition error: {e}")
        SetAssistantStatus("Available...")
        return False
    
    ShowTextToScreen(f"{Username}: {Query}")
    SetAssistantStatus("Thinking...")
    Decision = FirstLayerDMM(Query)

    print("")
    print(f"Decision : {Decision}")
    print("")

    G = any([i for i in Decision if i.startswith("general")])
    R = any([i for i in Decision if i.startswith("realtime")])

    Merged_query = " and ".join(
        [" ".join(i.split()[1:])for i in Decision if i.startswith("general") or i.startswith("realtime")]
    ) 

    for query in Decision:
        if any(keyword in query.lower() for keyword in ["generate", "image", "picture"]):
            ImageGenrationQuery = ' '.join([word for word in query.split() 
                                          if word.lower() not in ["generate", "image", "picture", "of"]])
            if ImageGenrationQuery:
                ImageExecution = True

    for queries in Decision:
        if TaskExecution == False:
            if any(queries.startswith(func) for func in Functions):
                run(Automation(list(Decision)))
                TaskExecution = True

    if ImageExecution and ImageGenrationQuery:
        TaskExecution = True
        SetAssistantStatus("Generating image...")
        TextToSpeech(f"Generating an image of {ImageGenrationQuery}")
        
        try:
            image_generator.GenerateImages(ImageGenrationQuery)
            print(f"[INFO] Generated image: {ImageGenrationQuery}")
        except Exception as e:
            print(f"Error generating image: {e}")
            SetAssistantStatus("Image generation failed")
            TextToSpeech("Sorry, I couldn't generate the image.")

    if G and R or R:
        SetAssistantStatus("Searching...")
        Answer = RealtimeSearchEngine(QueryModifier(Merged_query))
        ShowTextToScreen(f"{Assistantname} : {Answer}")   
        SetAssistantStatus("Answering...")
        TextToSpeech(Answer)
        return True
    else:
        for Queries in Decision:
            if "general" in Queries:
                SetAssistantStatus("Thinking...")
                QueryFinal = Queries.replace("general","")
                Answer = ChatBot(QueryModifier(QueryFinal))
                ShowTextToScreen(f"{Assistantname} : {Answer}")
                SetAssistantStatus("Answering...")
                TextToSpeech(Answer)
                return True
            elif "realtime" in Queries:
                SetAssistantStatus("Searching...")
                QueryFinal = Queries.replace("realtime","")
                Answer = RealtimeSearchEngine(QueryModifier(QueryFinal))
                ShowTextToScreen(f"{Assistantname} : {Answer}")
                SetAssistantStatus("Answering...")
                TextToSpeech(Answer)
                return True
            elif "exit" in Queries:
                QueryFinal = "Okay, Bye!"
                Answer = ChatBot(QueryModifier(QueryFinal))
                ShowTextToScreen(f"{Assistantname} : {Answer}")
                SetAssistantStatus("Answering...")
                TextToSpeech(Answer)
                cleanup()
                os._exit(1)

    if any(keyword in Query.lower() for keyword in ["near me", "navigate to", "directions to"]):
        SetAssistantStatus("Searching...")
        run(Automation([Query]))  
        return True

def FirstThread():
    while True:
        CurrentStatus = GetMicrophoneStatus()

        if CurrentStatus == "True":
            try:
                MainExecution()
            except Exception as e:
                print(f"Thread error: {e}")
                SetAssistantStatus("Available...")
        else: 
            AIStatus = GetAssistantStatus()
            if "Available..." in AIStatus:
                sleep(0.1)
            else: 
                SetAssistantStatus("Available...")

def SecondThread():
    GraphicalUserInterface()

if __name__ == "__main__":
    import atexit
    atexit.register(cleanup)
    
    thread2 = threading.Thread(target=FirstThread, daemon=True)
    thread2.start()
    SecondThread()
