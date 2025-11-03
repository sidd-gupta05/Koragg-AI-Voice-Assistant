# import cohere
# from rich import print
# from dotenv import dotenv_values

# env_vars = dotenv_values(".env")

# CohereAPIKey = env_vars.get("CohereAPIKey")

# co = cohere.Client(api_key=CohereAPIKey)

# funcs = [
#     "exit", "general", "realtime", "open", "close", "play",
#     "generate image", "system", "connect", "google search",
#     "youtube search", "reminder","content", 
#     "system report", "map search","message","screenshoot","screenshot","weather"
# ]

# messages = []

# preamble = """
# You are a very accurate Decision-Making Model, which decides what kind of a query is given to you.
# You will decide whether a query is a 'general' query, a 'realtime' query, or is asking to perform any task or automation like 'open facebook, instagram', 'can you write a application and open it in notepad'
# *** Do not answer any query, just decide what kind of query is given to you. ***
# -> Respond with 'general ( query )' if a query can be answered by a llm model (conversational ai chatbot) and doesn't require any up to date information like if the query is 'who was akbar?' respond with 'general who was akbar?', if the query is 'how can i study more effectively?' respond with 'general how can i study more effectively?', if the query is 'can you help me with this math problem?' respond with 'general can you help me with this math problem?', if the query is 'Thanks, i really liked it.' respond with 'general thanks, i really liked it.' , if the query is 'what is python programming language?' respond with 'general what is python programming language?', etc. Respond with 'general (query)' if a query doesn't have a proper noun or is incomplete like if the query is 'who is he?' respond with 'general who is he?', if the query is 'what's his networth?' respond with 'general what's his networth?', if the query is 'tell me more about him.' respond with 'general tell me more about him.', and so on even if it require up-to-date information to answer. Respond with 'general (query)' if the query is asking about time, day, date, month, year, etc like if the query is 'what's the time?' respond with 'general what's the time?'.
# -> Respond with 'realtime ( query )' if a query can not be answered by a llm model (because they don't have realtime data) and requires up to date information like if the query is 'who is indian prime minister' respond with 'realtime who is indian prime minister', if the query is 'tell me about facebook's recent update.' respond with 'realtime tell me about facebook's recent update.', if the query is 'tell me news about coronavirus.' respond with 'realtime tell me news about coronavirus.', etc and if the query is asking about any individual or thing like if the query is 'who is akshay kumar' respond with 'realtime who is akshay kumar', if the query is 'what is today's news?' respond with 'realtime what is today's news?', if the query is 'what is today's headline?' respond with 'realtime what is today's headline?', etc.
# -> Respond with 'open (application name or website name)' if a query is asking to open any application like 'open facebook', 'open telegram', etc. but if the query is asking to open multiple applications, respond with 'open 1st application name, open 2nd application name' and so on.
# -> Respond with 'close (application name)' if a query is asking to close any application like 'close notepad', 'close facebook', etc. but if the query is asking to close multiple applications or websites, respond with 'close 1st application name, close 2nd application name' and so on.
# -> Respond with 'play (song name)' if a query is asking to play any song like 'play afsanay by ys', 'play let her go', etc. but if the query is asking to play multiple songs, respond with 'play 1st song name, play 2nd song name' and so on.
# -> STRICTLY respond with 'generate image (prompt)' if the user asks to create, draw, or generate any image. Examples:
#    - "Generate an image of a cat" → "generate image cat"
#    - "Draw me a sunset" → "generate image sunset"
#    - "Make a picture of a forest" → "generate image forest"
#    - "Create an image of a robot" → "generate image robot"
#    DO NOT respond with ASCII art or text. ONLY use 'generate image (prompt)'.
# -> Respond with 'reminder (datetime with message)' if a query is requesting to set a reminder like 'set a reminder at 9:00pm on 25th june for my business meeting.' respond with 'reminder 9:00pm 25th june business meeting'.
# -> Respond with 'weather (location)' if the query is asking about current weather or temperature in any specific location like 'what is the weather in Mumbai?', 'show me today's forecast in Delhi', 'what's the temperature in Pune', etc.
# -> Respond with 'system (task name)' if a query is asking to mute, unmute, volume up, volume down , etc. but if the query is asking to do multiple tasks, respond with 'system 1st task, system 2nd task', etc.
# -> Respond with 'content (topic)' if a query is asking to write any type of content like application, codes, emails or anything else about a specific topic but if the query is asking to write multiple types of content, respond with 'content 1st topic, content 2nd topic' and so on.
# -> Respond with 'google search (topic)' if a query is asking to search a specific topic on google but if the query is asking to search multiple topics on google, respond with 'google search 1st topic, google search 2nd topic' and so on.
# -> Respond with 'youtube search (topic)' if a query is asking to search a specific topic on youtube but if the query is asking to search multiple topics on youtube, respond with 'youtube search 1st topic, youtube search 2nd topic' and so on.
# -> Respond with 'screenshot' if a query is asking to take a screenshot like 'take a screenshot', 'capture screen', etc.
# -> Respond with 'screenshoot' if a query is asking to take a screenshoot like 'take a screenshoot', 'capture screen', 'click screen'etc.
# -> Respond with 'system report' if a query is asking about CPU, RAM, or disk usage like 'how much RAM is used?', 'show me system report', etc.
# -> Respond with 'map search (place)' if a query is asking to search a place on Google Maps like 'search Taj Mahal on map', 'search domino's near me', 'show nearby restaurants', 'find hospitals around me', etc. Any query including keywords like 'near me', 'on map', 'location of', or 'directions to' should be treated as a map search.
# -> Respond with 'message (recipient message)' if a query is asking to send a WhatsApp message like 'send message to dad on WhatsApp saying I will be late', or 'send a message to 9876543210 saying meeting postponed', or 'send message to laksh that I will come soon at home', or 'text boss I need a day off'. You should extract the recipient and the message clearly. If the query uses phrasing like "send message to [recipient] that [message]" or "send message to [recipient] saying [message]" or "message [recipient] [message]", handle all of them. If the query involves sending multiple messages, respond with 'message 1st recipient 1st message, message 2nd recipient 2nd message' and so on.
# *** If the query is asking to perform multiple tasks like 'open facebook, telegram and close whatsapp' respond with 'open facebook, open telegram, close whatsapp' ***
# *** If the user is saying goodbye or wants to end the conversation like 'bye jarvis.' respond with 'exit'.***
# *** Respond with 'general (query)' if you can't decide the kind of query or if a query is asking to perform a task which is not mentioned above. ***
# """

# ChatHistory = [
#     {"role": "User", "message": "how are you?"},
#     {"role": "Chatbot", "message": "general how are you?" },
#     {"role": "User", "message": "do you like pizza?"},
#     {"role": "Chatbot", "message": "general do you like pizza?"},
#     {"role": "User", "message": "open chrome and tell me about mahatma gandhi?"},
#     {"role": "Chatbot", "message": "open chrome, general tell me about mahatma gandhi?"},
#     {"role": "User", "message": "open chrome and firefox"},
#     {"role": "Chatbot", "message": "open chrome , firefox"},
#     {"role": "User", "message": "What is today's date and by the way remind me that i have a dancing performance on 5th aug at 11pm"},
#     {"role": "Chatbot", "message": "general What is today's date , reminder 11:00pm 5th aug dancing performance"},
#     {"role": "User", "message": "chat with me"},
#     {"role": "Chatbot", "message": "general chat with me"},
#     {"role": "User", "message": "message laksh on whatsapp ",},
#     {"role": "Chatbot", "message": "message laksh",},
#     {"role": "User", "message": "show me system report"},
#     {"role": "Chatbot", "message": "system report"},
#     {"role": "User", "message": "search Taj Mahal on map"},
#     {"role": "Chatbot", "message": "map search Taj Mahal"},
#     {"role": "User", "message": "search domino's near me"},
#     {"role": "Chatbot", "message": "map search domino's near me"},
#     {"role": "User", "message": "send message to laksh that I will come soon at home"},
#     {"role": "Chatbot", "message": "message laksh I will come soon at home"},
#     {"role": "User", "message": "take a screenshot"},
#     {"role": "Chatbot", "message": "screenshot"},
#     {"role": "User", "message": "capture screen"},
#     {"role": "Chatbot", "message": "screenshot"},
#     {"role": "User", "message": "can you take a screenshot please"},
#     {"role": "Chatbot", "message": "screenshot"},
#     {"role": "User", "message": "screenshot the current window"},
#     {"role": "Chatbot", "message": "screenshoot"},
#     {"role": "User", "message": "take a screenshoot"},
#     {"role": "Chatbot", "message": "screenshoot"},
#     {"role": "User", "message": "capture screen"},
#     {"role": "Chatbot", "message": "screenshoot"},
#     {"role": "User", "message": "can you take a screenshoot please"},
#     {"role": "Chatbot", "message": "screenshoot"},
#     {"role": "User", "message": "screenshoot the current window"},
#     {"role": "Chatbot", "message": "screenshoot"},
#     {"role": "User", "message": "generate image of a mountain"},
#     {"role": "Chatbot", "message": "generate image mountain"},
#     {"role": "User", "message": "draw me a cat"},
#     {"role": "Chatbot", "message": "generate image cat"},
#     {"role": "User", "message": "create a picture of a sunset"},
#     {"role": "Chatbot", "message": "generate image sunset"},
#     {"role": "User", "message": "what is the weather in mumbai"},
#     {"role": "Chatbot", "message": "weather mumbai"},
# ]

# def FirstLayerDMM(prompt: str = "test"):
    
#     messages.append({"role": "user","content": f"{prompt}"})

#     stream = co.chat_stream(
#         model = 'command-r-plus',
#         message = prompt,
#         temperature = 0.7,
#         chat_history = ChatHistory,
#         prompt_truncation = 'OFF',
#         connectors = [],
#         preamble = preamble
#     )

#     response = ""

#     for event in stream:
#         if event.event_type == "text-generation":
#             response += event.text

#     response = response.replace("\n","")
#     response = response.split(",")

#     response = [i.strip() for i in response]

#     temp = []

#     for task in response:
#         for func in funcs:
#             if task.startswith(func):
#                 temp.append(task)

#     response = temp

#     if "(query)" in response:
#         newresponse = FirstLayerDMM(prompt=prompt)
#         return newresponse
#     else:
#         return response


# if __name__ == "__main__":
#     while True:
#         print(FirstLayerDMM(input(">>> ")))
        

from rich import print
import re

funcs = [
    "exit", "general", "realtime", "open", "close", "play",
    "generate image", "system", "connect", "google search",
    "youtube search", "reminder","content", 
    "system report", "map search","message","screenshoot","screenshot","weather"
]

messages = []

def FirstLayerDMM(prompt: str = "test"):
    prompt_lower = prompt.lower().strip()
    
    # Direct command detection - these should NEVER go to general
    if any(prompt_lower.startswith(cmd) for cmd in ['open ', 'close ', 'play ', 'generate image', 'screenshot', 'screenshoot']):
        if prompt_lower.startswith('open '):
            return [f"open {prompt[5:]}"]
        elif prompt_lower.startswith('close '):
            return [f"close {prompt[6:]}"]
        elif prompt_lower.startswith('play '):
            return [f"play {prompt[5:]}"]
        elif 'generate image' in prompt_lower or 'draw' in prompt_lower or 'create image' in prompt_lower:
            image_prompt = prompt_lower.replace('generate image', '').replace('draw', '').replace('create image', '').replace('of', '').strip()
            return [f"generate image {image_prompt}"]
        elif 'screenshot' in prompt_lower:
            return ['screenshot']
        elif 'screenshoot' in prompt_lower:
            return ['screenshoot']
    
    # Message detection
    if any(word in prompt_lower for word in ['message', 'send message', 'whatsapp']):
        if 'to' in prompt_lower and ('saying' in prompt_lower or 'that' in prompt_lower):
            parts = re.split(r'\bto\b|\bsaying\b|\bthat\b', prompt_lower)
            if len(parts) >= 2:
                recipient = parts[1].strip()
                message = parts[2].strip() if len(parts) > 2 else ""
                return [f"message {recipient} {message}"]
        elif prompt_lower.startswith('message '):
            return [f"message {prompt[8:]}"]
    
    # Weather detection
    if any(word in prompt_lower for word in ['weather', 'temperature', 'forecast']):
        location = re.sub(r'weather|temperature|forecast|in|at', '', prompt_lower).strip()
        if location:
            return [f"weather {location}"]
        else:
            return ['weather']
    
    # System report
    if any(word in prompt_lower for word in ['system report', 'cpu', 'ram', 'memory', 'disk']):
        return ['system report']
    
    # Map search
    if any(word in prompt_lower for word in ['near me', 'on map', 'location of', 'directions to']):
        place = re.sub(r'near me|on map|location of|directions to|find|search', '', prompt_lower).strip()
        return [f"map search {place}"]
    
    # Google search
    if any(word in prompt_lower for word in ['google search', 'search on google']):
        query = re.sub(r'google search|search on google', '', prompt_lower).strip()
        return [f"google search {query}"]
    
    # YouTube search
    if any(word in prompt_lower for word in ['youtube search', 'search on youtube']):
        query = re.sub(r'youtube search|search on youtube', '', prompt_lower).strip()
        return [f"youtube search {query}"]
    
    # Content writing
    if any(word in prompt_lower for word in ['write', 'compose', 'create', 'make', 'draft', 'letter', 'application']):
        return [f"content {prompt}"]
    
    # Exit commands
    if any(word in prompt_lower for word in ['bye', 'goodbye', 'exit', 'quit']):
        return ['exit']
    
    # System commands (volume, mute, etc.)
    if any(word in prompt_lower for word in ['volume', 'mute', 'unmute']):
        if 'mute' in prompt_lower:
            return ['system mute']
        elif 'unmute' in prompt_lower:
            return ['system unmute']
        elif 'volume up' in prompt_lower or 'increase volume' in prompt_lower:
            return ['system volume_up']
        elif 'volume down' in prompt_lower or 'decrease volume' in prompt_lower:
            return ['system volume_down']
    
    # Real-time queries (require current information)
    realtime_keywords = [
        'current', 'today\'s', 'latest', 'recent', 'now', 'present',
        'prime minister', 'president', 'news', 'headline', 'covid', 'coronavirus',
        'stock', 'price', 'who is', 'what is today', 'how is', 'tell me about'
    ]
    
    # Check for proper nouns (names of people, places, companies)
    proper_nouns = re.findall(r'\b[A-Z][a-z]+\b', prompt)
    has_proper_noun = len(proper_nouns) > 0 and len(proper_nouns[0]) > 2
    
    if any(keyword in prompt_lower for keyword in realtime_keywords) or has_proper_noun:
        return [f"realtime {prompt}"]
    
    # General queries (everything else)
    return [f"general {prompt}"]


if __name__ == "__main__":
    print("Decision Making Model is running...")
    print("Available functions:", funcs)
    print("Type 'quit' to exit\n")
    
    # Test cases
    test_queries = [
        "open chrome",
        "play shape of you",
        "what is the weather in mumbai",
        "send message to dad that I will be late",
        "who is the prime minister of india",
        "how are you today",
        "take a screenshot",
        "generate image of a mountain",
        "search for restaurants near me",
        "bye"
    ]
    
    print("Testing decision system:")
    for query in test_queries:
        result = FirstLayerDMM(query)
        print(f"'{query}' -> {result}")
    print()
    
    while True:
        try:
            user_input = input(">>> ").strip()
            if user_input.lower() in ['quit', 'exit', 'bye']:
                print("Goodbye!")
                break
            if user_input:
                result = FirstLayerDMM(user_input)
                print(f"Decision: {result}")
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")