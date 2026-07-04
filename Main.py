# Main.py
import torch
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
from Backend.ScreenAgent import (
    ScreenRead,
    ScreenCode,
    ScreenCodeExecute,
    DetectLanguageFromScreen,
)
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
image_generator = None
Functions = ['open', "close", "play", "system", "content","google search", "youtube search", "screenshoot", "screenshot", "report", "message", "near me" ,"navigate to" ,"directions to","write", "draft", "compose", "make", "create", "type", "letter", "aplication","screen read", "read screen", "what's on", "whats on","solve this", "code this", "fix this", "fix the bug", "debug this", "read the problem", "solve the problem", "what's wrong", "whats wrong", "screen code", "help me code","volume", "increase", "decrease", "reduce", "mute", "unmute"]

def HandleVolumeIntent(Query: str) -> bool:
    """
    Intercepts volume commands instantly, bypassing the DMM router to 
    prevent web searches, and perfectly executes the percentage adjustments.
    """
    query_lower = Query.lower().strip()
    
    # Check if the user is talking about volume or muting
    if "volume" in query_lower or "mute" in query_lower:
        from Backend.Automation import AdjustVolumeByPercentage, System
        
        if "unmute" in query_lower:
            System("unmute")
            answer = "Audio unmuted."
        elif "mute" in query_lower:
            System("mute")
            answer = "Audio muted."
        else:
            answer = AdjustVolumeByPercentage(query_lower)
            
        SetAssistantStatus("Answering...")
        ShowTextToScreen(f"{Assistantname} : {answer}")
        TextToSpeech(answer)
        SetAssistantStatus("Available...")
        return True
        
    return False

def HandleScreenIntent(Query: str) -> bool:
    """
    Intercepts screen-reading and coding assistant commands before they
    reach the DMM router. Returns True if handled, False to fall through.
    """
    query_lower = Query.lower().strip()
 
    # ── Trigger lists ────────────────────────────────────────────────────────
 
    read_triggers = [
        "what's on my screen", "whats on my screen",
        "read my screen", "read the screen",
        "what does this say", "what is on screen",
        "describe my screen", "what do you see",
        "read this for me",
    ]
 
    solve_triggers = [
        "solve this", "solve this problem", "solve the problem",
        "code this", "code this for me", "write code for this",
        "write the code", "type the code", "help me code",
        "read the problem and solve", "read and solve", "screen code",
        "read the whole files and solve", "read the whole file and solve"  # FIXED: Added your voice variant
    ]
 
    fix_triggers = [
        "solve the bug", "solve this bug", "solve bugs",  # FIXED: Added your specific trigger variations
        "fix this", "fix this bug", "fix the bug",
        "debug this", "find the bug",
        "what's wrong with my code", "whats wrong with my code",
        "help fix", "fix my code", "there's a bug", "there is a bug",
        "error in my code",
    ]
 
    is_read  = any(t in query_lower for t in read_triggers)
    is_solve = any(t in query_lower for t in solve_triggers)
    is_fix   = any(t in query_lower for t in fix_triggers)
 
    if not (is_read or is_solve or is_fix):
        return False   # not our command — let DMM handle it normally
 
    # ── Extract user hint (anything said after the trigger phrase) ────────────
    hint = ""
    for trigger in solve_triggers + fix_triggers + read_triggers:
        if trigger in query_lower:
            remainder = query_lower.replace(trigger, "").strip(" ,.")
            if len(remainder) > 3:
                hint = remainder
            break
 
    # ── READ MODE ─────────────────────────────────────────────────────────────
    if is_read and not is_solve and not is_fix:
        SetAssistantStatus("Reading screen...")
        answer = ScreenRead(user_question=hint if hint else "")
        ShowTextToScreen(f"{Assistantname} : {answer}")
        SetAssistantStatus("Answering...")
        TextToSpeech(answer)
        SetAssistantStatus("Available...")
        return True
 
    # ── CODING MODE ───────────────────────────────────────────────────────────
    SetAssistantStatus("Reading screen...")
 
    result = ScreenCode(
        user_hint=hint,
        language="",             # empty = auto-detect from screen
        speak_fn=TextToSpeech    # so ScreenCode can speak the permission prompt
    )
 
    # ── PERMISSION GATE ───────────────────────────────────────────────────────
    if not result.startswith("__PERMISSION_REQUIRED__"):
        # ScreenCode returned a direct message (e.g. "not a coding screen")
        ShowTextToScreen(f"{Assistantname} : {result}")
        TextToSpeech(result)
        SetAssistantStatus("Available...")
        return True
 
    # Parse the token:
    # __PERMISSION_REQUIRED__|context_type|screen_data_json|user_hint|language
    parts = result.split("|", 4)
    context_type      = parts[1] if len(parts) > 1 else "browser_judge"
    screen_data_json  = parts[2] if len(parts) > 2 else "{}"
    user_hint_out     = parts[3] if len(parts) > 3 else hint
    language_out      = parts[4] if len(parts) > 4 else "python"
 
    # ── Listen for yes / no ───────────────────────────────────────────────────
    SetAssistantStatus("Waiting for your confirmation...")
    try:
        permission_response = SpeechRecognization()
    except Exception:
        permission_response = ""
 
    permission_response = (permission_response or "").lower().strip()
 
    yes_words = [
        "yes", "yeah", "sure", "go ahead", "proceed",
        "do it", "ok", "okay", "yep", "yup", "please",
        "affirmative", "go", "do that", "yes please",
    ]
    no_words = [
        "no", "nope", "cancel", "stop", "don't",
        "never mind", "nevermind", "negative", "abort", "exit",
    ]
 
    user_said_yes = any(w in permission_response for w in yes_words)
    user_said_no  = any(w in permission_response for w in no_words)
 
    if user_said_no or (not user_said_yes):
        msg = "Understood sir, cancelling."
        ShowTextToScreen(f"{Assistantname} : {msg}")
        TextToSpeech(msg)
        SetAssistantStatus("Available...")
        return True
 
    # ── User confirmed — execute ───────────────────────────────────────────────
    SetAssistantStatus("Generating solution...")
    TextToSpeech("Got it sir, working on it now.")
 
    final_result = ScreenCodeExecute(
        context_type  = context_type,
        screen_desc   = screen_data_json,   # JSON string
        user_hint     = user_hint_out,
        language      = language_out,
        clipboard_code= "",                  
    )
 
    # Show full code on Koragg screen, speak only the summary sentence
    ShowTextToScreen(f"{Assistantname} : {final_result}")
    SetAssistantStatus("Answering...")
 
    # Speak only the first non-code sentence (the human-readable status line)
    spoken = final_result.split("\n")[0] if final_result else "Done."
    TextToSpeech(spoken)
    SetAssistantStatus("Available...")
    return True

def HandleCreatorIntent(Query: str) -> bool:
    """
    Intercepts questions about Koragg's creator and returns a hardcoded response.
    """
    query_lower = Query.lower().strip()
    
    creator_triggers = [
        "who created you", "who made you", "who is your boss", 
        "who developed you", "who is your creator", "who programmed you"
    ]
    
    if any(t in query_lower for t in creator_triggers):
        answer = "I was created by my Boss, Siddharth."
        
        SetAssistantStatus("Answering...")
        ShowTextToScreen(f"{Assistantname} : {answer}")
        TextToSpeech(answer)
        SetAssistantStatus("Available...")
        return True
        
    return False

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

    if image_generator is None:
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

    if HandleScreenIntent(Query):
        SetAssistantStatus("Available...")
        return True

    if HandleCreatorIntent(Query):
        return True

    if HandleVolumeIntent(Query):
        return True
    
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
