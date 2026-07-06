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
import ctypes  
import sys

env_vars = dotenv_values(".env")
Username = env_vars.get("Username")
Assistantname = env_vars.get("Assistantname")
DefaultMessage = f'''{Username} : Hello {Assistantname}, How are you?
{Assistantname} : Welcome {Username}. I am doing well thanks for asking. How may I help you?'''
subprocesses = []
image_generation_process = None
image_generator = None
image_generation_lock = threading.Lock()
Functions = ['open', "close", "play", "system", "content","google search", "youtube search", "screenshoot", "screenshot", "report", "message", "near me" ,"navigate to" ,"directions to","write", "draft", "compose", "make", "create", "type", "letter", "aplication","screen read", "read screen", "what's on", "whats on","solve this", "code this", "fix this", "fix the bug", "debug this", "read the problem", "solve the problem", "what's wrong", "whats wrong", "screen code", "help me code","volume", "increase", "decrease", "reduce", "mute", "unmute"]

# ── BACKGROUND MANAGER FOR ALL TASKS ─────────────────────────────────────────
active_background_tasks = {}

def force_stop_thread(thread):
    """Forcefully terminates a python thread so tasks can be aborted mid-execution."""
    if not thread or not thread.is_alive():
        return
    thread_id = thread.ident
    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(thread_id), ctypes.py_object(SystemExit))
    if res > 1:
        ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id, 0)
        print('[Error] Failed to forcefully stop thread.')

def HandleStopIntent(Query: str) -> bool:
    """Intercepts stop commands to cancel ongoing background tasks instantly."""
    query_lower = Query.lower().strip()
    stop_triggers = ["stop", "cancel", "terminate", "abort", "halt"]
    
    if any(trigger in query_lower for trigger in stop_triggers):
        stopped_something = False
        
        if "image" in query_lower and "image_generation" in active_background_tasks:
            force_stop_thread(active_background_tasks["image_generation"])
            del active_background_tasks["image_generation"]
            answer = "Stopped image generation."
            stopped_something = True
        elif "search" in query_lower and "search_task" in active_background_tasks:
            force_stop_thread(active_background_tasks["search_task"])
            del active_background_tasks["search_task"]
            answer = "Stopped the search query."
            stopped_something = True
        elif "thinking" in query_lower and "chat_task" in active_background_tasks:
            force_stop_thread(active_background_tasks["chat_task"])
            del active_background_tasks["chat_task"]
            answer = "Stopped thinking processing."
            stopped_something = True
        elif query_lower in stop_triggers or "everything" in query_lower or "all" in query_lower:
            # Kill every single running background thread
            for task_name, task_thread in list(active_background_tasks.items()):
                force_stop_thread(task_thread)
                del active_background_tasks[task_name]
            answer = "All background tasks terminated."
            stopped_something = True
            
        if stopped_something:
            SetAssistantStatus("Answering...")
            ShowTextToScreen(f"{Assistantname} : {answer}")
            TextToSpeech(answer)
            SetAssistantStatus("Available...")
            return True
            
    return False
# ─────────────────────────────────────────────────────────────────────────────

def HandleScreenIntent(Query: str) -> bool:
    query_lower = Query.lower().strip()
    read_triggers = ["what's on my screen", "whats on my screen", "read my screen", "read the screen", "what does this say", "what is on screen", "describe my screen", "what do you see", "read this for me"]
    solve_triggers = ["solve this", "solve this problem", "solve the problem", "code this", "code this for me", "write code for this", "write the code", "type the code", "help me code", "read the problem and solve", "read and solve", "screen code", "read the whole files and solve", "read the whole file and solve"]
    fix_triggers = ["solve the bug", "solve this bug", "solve bugs", "fix this", "fix this bug", "fix the bug", "debug this", "find the bug", "what's wrong with my code", "whats wrong with my code", "help fix", "fix my code", "there's a bug", "there is a bug", "error in my code"]
    
    is_read  = any(t in query_lower for t in read_triggers)
    is_solve = any(t in query_lower for t in solve_triggers)
    is_fix   = any(t in query_lower for t in fix_triggers)
    if not (is_read or is_solve or is_fix):
        return False
        
    hint = ""
    for trigger in solve_triggers + fix_triggers + read_triggers:
        if trigger in query_lower:
            remainder = query_lower.replace(trigger, "").strip(" ,.")
            if len(remainder) > 3: hint = remainder
            break

    # Run the screen workflow inside its own isolated background thread
    def bg_screen_task():
        try:
            if is_read and not is_solve and not is_fix:
                SetAssistantStatus("Reading screen...")
                answer = ScreenRead(user_question=hint if hint else "")
                ShowTextToScreen(f"{Assistantname} : {answer}")
                SetAssistantStatus("Answering...")
                TextToSpeech(answer)
            else:
                SetAssistantStatus("Reading screen...")
                result = ScreenCode(user_hint=hint, language="", speak_fn=TextToSpeech)
                if not result.startswith("__PERMISSION_REQUIRED__"):
                    ShowTextToScreen(f"{Assistantname} : {result}")
                    TextToSpeech(result)
                else:
                    parts = result.split("|", 4)
                    context_type = parts[1]
                    screen_data_json = parts[2]
                    user_hint_out = parts[3]
                    language_out = parts[4]
                    SetAssistantStatus("Waiting for confirmation...")
                    try:
                        permission_response = SpeechRecognization()
                    except Exception:
                        permission_response = ""
                    permission_response = (permission_response or "").lower().strip()
                    
                    yes_words = ["yes", "yeah", "sure", "go ahead", "proceed", "do it", "ok", "okay", "yep", "yup"]
                    if any(w in permission_response for w in yes_words):
                        SetAssistantStatus("Generating solution...")
                        final_result = ScreenCodeExecute(context_type=context_type, screen_desc=screen_data_json, user_hint=user_hint_out, language=language_out)
                        ShowTextToScreen(f"{Assistantname} : {final_result}")
                        SetAssistantStatus("Answering...")
                        TextToSpeech(final_result.split("\n")[0] if final_result else "Done.")
                    else:
                        ShowTextToScreen(f"{Assistantname} : Cancelled.")
                        TextToSpeech("Cancelled.")
        finally:
            SetAssistantStatus("Available...")
            if "screen_task" in active_background_tasks: del active_background_tasks["screen_task"]

    t = threading.Thread(target=bg_screen_task, daemon=True)
    active_background_tasks["screen_task"] = t
    t.start()
    return True

def HandleCreatorIntent(Query: str) -> bool:
    query_lower = Query.lower().strip()
    creator_triggers = ["who created you", "who made you", "who is your boss", "who developed you", "who is your creator", "who programmed you"]
    if any(t in query_lower for t in creator_triggers):
        def bg_creator():
            answer = "I was created by my Boss, Siddharth."
            ShowTextToScreen(f"{Assistantname} : {answer}")
            TextToSpeech(answer)
            SetAssistantStatus("Available...")
        threading.Thread(target=bg_creator, daemon=True).start()
        return True
    return False

def HandleVolumeIntent(Query: str) -> bool:
    query_lower = Query.lower().strip()
    if "volume" in query_lower or "mute" in query_lower:
        def bg_volume():
            from Backend.Automation import AdjustVolumeByPercentage, System
            if "unmute" in query_lower:
                System("unmute")
                answer = "Audio unmuted."
            elif "mute" in query_lower:
                System("mute")
                answer = "Audio muted."
            else:
                answer = AdjustVolumeByPercentage(query_lower)
            ShowTextToScreen(f"{Assistantname} : {answer}")
            TextToSpeech(answer)
            SetAssistantStatus("Available...")
        threading.Thread(target=bg_volume, daemon=True).start()
        return True
    return False

def cleanup():
    for proc in subprocesses:
        try: proc.terminate()
        except: pass

def enhance_image_prompt(prompt):
    return f"{prompt}, high quality, detailed, sharp focus, seed={randint(0, 1000000)}"

def ShowDefaultChatIfNoChats():
    File = open(r"Data\ChatLog.json" , "r", encoding="utf-8") 
    if len(File.read())<5:
        with open(TempDirectoryPath('Database.data'), "w", encoding = 'utf-8') as file: file.write("")
        with open(TempDirectoryPath('Responses.data'), "w", encoding = 'utf-8') as file: file.write(DefaultMessage)

def ReadChatLogJson():
    with open(r"Data\ChatLog.json", "r", encoding="utf-8")as file: chatlog_data = json.load(file)
    return chatlog_data

def ChatLogIntegration():
    json_data = ReadChatLogJson()
    formatted_chatlog = ""
    for entry in json_data:
        if entry["role"] == "user": formatted_chatlog += f"User : {entry['content']}\n"
        elif entry["role"] == "assistant": formatted_chatlog += f"Assistant : {entry['content']}\n"
        formatted_chatlog = formatted_chatlog.replace("User",Username + " ").replace("Assistant",Assistantname + " ")
        with open(TempDirectoryPath('Database.data'), 'w', encoding='utf-8') as file: file.write(AnswerModifier(formatted_chatlog))

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

    # Intercept commands instantly
    if HandleScreenIntent(Query): return True
    if HandleCreatorIntent(Query): return True
    if HandleVolumeIntent(Query): return True
    if HandleStopIntent(Query): return True
    
    SetAssistantStatus("Thinking...")
    Decision = FirstLayerDMM(Query)
    print(f"\nDecision : {Decision}\n")

    G = any([i for i in Decision if i.startswith("general")])
    R = any([i for i in Decision if i.startswith("realtime")])
    Merged_query = " and ".join([" ".join(i.split()[1:]) for i in Decision if i.startswith("general") or i.startswith("realtime")]) 

    for query in Decision:
        if any(keyword in query.lower() for keyword in ["generate", "image", "picture"]):
            # FIXED: Removed 'realtime', 'general', 'the', 'a', 'an' to make the prompt completely clean
            ImageGenrationQuery = ' '.join([word for word in query.split() 
                                          if word.lower() not in ["generate", "image", "picture", "of", "realtime", "general", "the", "a", "an"]])
            if ImageGenrationQuery: 
                ImageExecution = True

    # 1. Background Automation Task
    for queries in Decision:
        if TaskExecution == False:
            if any(queries.startswith(func) for func in Functions):
                def bg_automation_task():
                    try: run(Automation(list(Decision)))
                    finally:
                        if "automation" in active_background_tasks: del active_background_tasks["automation"]
                auto_thread = threading.Thread(target=bg_automation_task, daemon=True)
                active_background_tasks["automation"] = auto_thread
                auto_thread.start()
                TaskExecution = True

    # 2. Background Image Task (NOW WITH THREAD LOCKING)
    if ImageExecution and ImageGenrationQuery:
        # Check if an image is already generating to prevent the "Already borrowed" crash
        if image_generation_lock.locked():
            TextToSpeech("I am already generating an image, please wait a moment.")
            return True
            
        TextToSpeech(f"Starting image generation for {ImageGenrationQuery}.")
        
        def bg_image_task():
            # This 'with' block locks the generator so no other thread can touch it
            with image_generation_lock:
                try:
                    image_generator.GenerateImages(ImageGenrationQuery)
                    TextToSpeech("Your image is ready.")
                except Exception as e:
                    print(f"Error generating image: {e}")
                finally:
                    if "image_generation" in active_background_tasks: del active_background_tasks["image_generation"]
                    
        img_thread = threading.Thread(target=bg_image_task, daemon=True)
        active_background_tasks["image_generation"] = img_thread
        img_thread.start()
        return True

    # 3. Background Search & Answer Task (Handles text generation without blocking)
    def bg_processing_execution():
        try:
            if G and R or R:
                SetAssistantStatus("Searching...")
                Answer = RealtimeSearchEngine(QueryModifier(Merged_query))
            else:
                for Queries in Decision:
                    if "general" in Queries:
                        SetAssistantStatus("Thinking...")
                        Answer = ChatBot(QueryModifier(Queries.replace("general","")))
                        break
                    elif "realtime" in Queries:
                        SetAssistantStatus("Searching...")
                        Answer = RealtimeSearchEngine(QueryModifier(Queries.replace("realtime","")))
                        break
                    elif "exit" in Queries:
                        cleanup()
                        sys.exit(0)

            
            ShowTextToScreen(f"{Assistantname} : {Answer}")   
            SetAssistantStatus("Answering...")
            TextToSpeech(Answer)
        except Exception as err:
            print(f"Background logic error: {err}")
        finally:
            SetAssistantStatus("Available...")
            if "chat_task" in active_background_tasks: del active_background_tasks["chat_task"]

    chat_thread = threading.Thread(target=bg_processing_execution, daemon=True)
    active_background_tasks["chat_task"] = chat_thread
    chat_thread.start()

    # Crucial step: Return True instantly so the microphone turns right back on!
    return True

def FirstThread():
    while True:
        CurrentStatus = GetMicrophoneStatus()
        if CurrentStatus == "True":
            try: MainExecution()
            except Exception as e: print(f"Thread error: {e}")
        else: 
            sleep(0.1)

def SecondThread():
    GraphicalUserInterface()

if __name__ == "__main__":
    import atexit
    atexit.register(cleanup)
    thread2 = threading.Thread(target=FirstThread, daemon=True)
    thread2.start()
    SecondThread()