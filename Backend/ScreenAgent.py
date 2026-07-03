# Backend/ScreenAgent.py
# Koragg Screen Reader + Coding Assistant Agent  

import pyautogui
import pygetwindow as gw
import pyperclip
import time
import os
import re
from PIL import Image
from dotenv import dotenv_values

pyautogui.FAILSAFE = True

# ── Load Environment Variables ───────────────────────────────────────────────
env_vars = dotenv_values(".env")
GEMINI_API_KEY = env_vars.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")

SCREENSHOT_DELAY = 1.2
_LAST_TARGET_WINDOW_TITLE = ""

def _get_active_window_title() -> str:
    try:
        w = gw.getActiveWindow()
        return w.title.lower() if w else ""
    except Exception:
        return ""

def _capture_screenshot() -> Image.Image:
    global _LAST_TARGET_WINDOW_TITLE
    initial_title = _get_active_window_title()
    if initial_title and "koragg" not in initial_title:
        _LAST_TARGET_WINDOW_TITLE = initial_title

    koragg_wins = []
    try:
        koragg_wins = gw.getWindowsWithTitle("Koragg")
        for w in koragg_wins:
            w.minimize()
    except Exception:
        pass

    time.sleep(SCREENSHOT_DELAY)
    
    if not _LAST_TARGET_WINDOW_TITLE or "koragg" in _LAST_TARGET_WINDOW_TITLE:
        _LAST_TARGET_WINDOW_TITLE = _get_active_window_title()

    img = pyautogui.screenshot()

    try:
        for w in koragg_wins:
            w.restore()
    except Exception:
        pass

    return img

_VISION_PROMPT = """You are a precise screen-reading assistant for a coding tool.
Analyse this screenshot and respond ONLY in the following format with these exact labels.
Do not add any other text outside these labels.

PLATFORM: <website or application name>
LANGUAGE: <programming language selected in the editor>
PROBLEM_TITLE: <exact title of the coding problem if visible, else NONE>
PROBLEM_STATEMENT: <copy the FULL problem statement word for word, else NONE>
EXISTING_CODE: <copy every line of code visible in the code editor exactly as formatted, else EMPTY>
ERROR_OR_OUTPUT: <copy any error message or test result visible, else NONE>
"""

def _read_screen_structured(img: Image.Image) -> dict:
    empty = {
        "platform": "", "language": "UNKNOWN",
        "problem_title": "", "problem_statement": "",
        "existing_code": "EMPTY", "error_or_output": "NONE"
    }

    if not GEMINI_API_KEY:
        print("[ScreenAgent] Vision API Error: GEMINI_API_KEY is missing in .env file.")
        return empty

    try:
        from google import genai
        client = genai.Client(api_key=GEMINI_API_KEY)
        response = client.models.generate_content(
            model='gemini-3.5-flash',
            contents=[_VISION_PROMPT, img]
        )
        raw = response.text
    except Exception as e:
        print(f"[ScreenAgent] Vision error: {e}")
        return empty

    result = dict(empty)
    label_map = {
        "PLATFORM": "platform", "LANGUAGE": "language",
        "PROBLEM_TITLE": "problem_title", "PROBLEM_STATEMENT": "problem_statement",
        "EXISTING_CODE": "existing_code", "ERROR_OR_OUTPUT": "error_or_output",
    }
    
    for label, key in label_map.items():
        pattern = rf"{label}:\s*(.*?)(?=\n[A-Z_]+:|$)"
        match = re.search(pattern, raw, re.DOTALL)
        if match: 
            result[key] = match.group(1).strip()
            
    return result

def _resolve_language(screen_data: dict, user_hint: str) -> str:
    hint_lower = user_hint.lower()
    for lang in ["java", "python", "javascript", "cpp", "csharp", "typescript", "rust", "go", "kotlin", "swift", "ruby", "php", "sql"]:
        if lang in hint_lower: return lang

    screen_lang = screen_data.get("language", "UNKNOWN").lower().strip()
    if screen_lang and screen_lang != "unknown":
        if "c++" in screen_lang: return "cpp"
        if "c#" in screen_lang: return "csharp"
        if "java" in screen_lang and "script" not in screen_lang: return "java"
        if "javascript" in screen_lang or "js" == screen_lang: return "javascript"
        return screen_lang

    code = screen_data.get("existing_code", "").lower()
    if "class solution" in code or "public void" in code or "public class" in code or "system.out" in code: 
        return "java"
    if "def " in code or "import " in code: return "python"
    if "#include" in code and "cout" in code: return "cpp"
    return "python"

def _detect_context(screen_data: dict, window_title: str) -> str:
    has_problem = screen_data.get("problem_statement", "NONE") not in ("NONE", "")
    if has_problem:
        return "browser_judge"
    return "local_editor"

def _solve_problem(screen_data: dict, language: str, user_hint: str) -> str:
    problem   = screen_data.get("problem_statement", "")
    title     = screen_data.get("problem_title", "")
    existing  = screen_data.get("existing_code", "EMPTY")

    prompt = f"""You are a strict code completion tool.
Task: Complete the exact coding problem provided.
Language: {language}
Problem Title: {title}
User Hint: {user_hint}

EXISTING CODE STUB (YOU MUST KEEP THIS EXACT CLASS AND METHOD SIGNATURE):
{existing}

RULES:
1. Output ONLY valid, executable {language} code. 
2. Do NOT output any conversational text, explanations, or markdown formatting blocks (no ```).
3. Do NOT change the problem. Solve ONLY what is defined in the title and stub.
"""

    if not GEMINI_API_KEY:
        return "// ERROR: GEMINI_API_KEY missing in .env file."

    try:
        from google import genai
        from google.genai import types
        
        client = genai.Client(api_key=GEMINI_API_KEY)
        full_prompt = f"SYSTEM INSTRUCTION: You are a strict code completion tool. Output RAW code only, no markdown.\n\n{prompt}"
        
        response = client.models.generate_content(
            model='gemini-3.5-flash', 
            contents=full_prompt,
            config=types.GenerateContentConfig(temperature=0.0)
        )
        
        clean_code = response.text.strip()
        clean_code = re.sub(r"^```[a-zA-Z]*\n", "", clean_code)
        clean_code = re.sub(r"```$", "", clean_code)
        
        return clean_code.strip()
    except Exception as e:
        return f"// API error: {e}"

def _fix_bug(screen_data: dict, language: str, user_hint: str) -> str:
    code  = screen_data.get("existing_code", "")
    error = screen_data.get("error_or_output", "NONE")

    prompt = f"""You are an expert code debugger. Fix this {language} script.
BUGGY BLOCK:
{code}
ERROR LOG CONTEXT:
{error}
USER COMMENTS: {user_hint}

RULES:
1. Return fixed raw {language} code directly.
2. Output ONLY code. NO markdown formatting blocks (no ```) and no conversational text.
"""
    if not GEMINI_API_KEY:
        return "// ERROR: GEMINI_API_KEY missing in .env file."

    try:
        from google import genai
        from google.genai import types
        
        client = genai.Client(api_key=GEMINI_API_KEY)
        full_prompt = f"SYSTEM INSTRUCTION: You are a strict bug fixing tool. Output RAW code only, no markdown.\n\n{prompt}"
        
        response = client.models.generate_content(
            model='gemini-3.5-flash', 
            contents=full_prompt,
            config=types.GenerateContentConfig(temperature=0.0)
        )
        
        clean_code = response.text.strip()
        clean_code = re.sub(r"^```[a-zA-Z]*\n", "", clean_code)
        clean_code = re.sub(r"```$", "", clean_code)
        
        return clean_code.strip()
    except Exception as e:
        return f"// API error: {e}"

def _find_editor_region(context: str) -> tuple:
    screen_w, screen_h = pyautogui.size()
    if context == "browser_judge":
        return (int(screen_w * 0.75), int(screen_h * 0.30))
    elif context == "local_editor":
        return (int(screen_w * 0.60), int(screen_h * 0.40))
    return (int(screen_w * 0.50), int(screen_h * 0.60))

def _type_into_editor(code: str, context: str, language: str) -> bool:
    try:
        pyperclip.copy(code)
    except Exception as e:
        print(f"[ScreenAgent] Clipboard error: {e}")
        return False

    koragg_wins = []
    try:
        koragg_wins = gw.getWindowsWithTitle("Koragg")
        for w in koragg_wins:
            w.minimize()
    except Exception:
        pass

    time.sleep(0.5)

    click_pos = _find_editor_region(context)
    if not click_pos:
        return False

    pyautogui.click(click_pos[0], click_pos[1])
    time.sleep(0.3)
    pyautogui.click(click_pos[0], click_pos[1])
    time.sleep(0.4)

    if "koragg" in _get_active_window_title():
        print("[ScreenAgent] Aborting paste sequence — Window blocked.")
        return False

    pyautogui.hotkey("ctrl", "a")
    time.sleep(0.2)
    pyautogui.press("backspace")
    time.sleep(0.2)
    pyautogui.hotkey("ctrl", "v")
    time.sleep(0.3)

    try:
        for w in koragg_wins:
            w.restore()
    except Exception:
        pass

    return True

def ScreenRead(user_question: str = "") -> str:
    img = _capture_screenshot()
    data = _read_screen_structured(img)
    parts = []
    if data["platform"]: parts.append(f"You have {data['platform']} open.")
    if data["problem_title"] and data["problem_title"] != "NONE":
        parts.append(f"The problem is: {data['problem_title']}.")
    return " ".join(parts) if parts else "I see your screen."

def ScreenCode(user_hint: str = "", language: str = "", speak_fn=None) -> str:
    global _LAST_TARGET_WINDOW_TITLE
    if speak_fn: speak_fn("Reading your screen now, one moment.")

    img = _capture_screenshot()
    screen_data = _read_screen_structured(img)
    
    context = _detect_context(screen_data, _LAST_TARGET_WINDOW_TITLE)
    resolved_lang = _resolve_language(screen_data, user_hint)

    title = screen_data.get("problem_title", "")
    platform = screen_data.get("platform", "the screen")

    if title and title != "NONE":
        perm_msg = f"I can see the problem '{title}' on {platform}. Shall I write the solution in {resolved_lang} directly into your editor panel? Say yes to proceed."
    else:
        perm_msg = f"I can see an open file editor framework. Shall I complete the code solution in {resolved_lang}? Say yes to proceed."

    if speak_fn: speak_fn(perm_msg)
    import json
    return f"__PERMISSION_REQUIRED__|{context}|{json.dumps(screen_data)}|{user_hint}|{resolved_lang}"

def ScreenCodeExecute(context_type: str, screen_desc: str, user_hint: str = "", language: str = "python", clipboard_code: str = "") -> str:
    import json
    try:
        screen_data = json.loads(screen_desc)
    except Exception:
        screen_data = {"platform": "", "language": language, "problem_statement": screen_desc, "existing_code": "EMPTY"}

    if context_type == "browser_judge":
        code = _solve_problem(screen_data, language, user_hint)
    else:
        code = _fix_bug(screen_data, language, user_hint)

    if not code or "error" in code[:20].lower(): return code

    typed_ok = _type_into_editor(code, context_type, language)
    if typed_ok:
        return f"Done. I have safely injected the complete functional {language} script directly into your web editor field context."
    return "I compiled the script solution context onto your clipboard layout profile stack, please manually click paste input via 'Ctrl+V'."

def DetectLanguageFromScreen(screen_desc: str, window_title: str) -> str:
    import json
    try:
        return _resolve_language(json.loads(screen_desc), "")
    except Exception:
        return "python"