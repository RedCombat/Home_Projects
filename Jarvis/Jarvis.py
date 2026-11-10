import speech_recognition as sr
import pyttsx3
import ollama
import re
from duckduckgo_search import DDGS

# Initialize the Text-to-Speech Engine
engine = pyttsx3.init()
voices = engine.getProperty('voices')
for voice in voices:
    if "male" in voice.name.lower():
        engine.setProperty('voice', voice.id)
        break
engine.setProperty('rate', 220)

def speak(text):
    print(f"Jarvis: {text}")
    clean_text = text.replace("*", "")
    clean_text = clean_text.replace("°C", " degrees Celsius")
    clean_text = clean_text.replace("°F", " degrees Fahrenheit")
    clean_text = clean_text.replace("-", " minus ")
    clean_text = re.sub(r'[\(\)\[\]]', '', clean_text)

    engine = pyttsx3.init()
    voices = engine.getProperty('voices')
    for voice in voices:
        if "male" in voice.name.lower():
            engine.setProperty('voice', voice.id)
            break
    engine.setProperty('rate', 220)
    engine.say(clean_text)
    engine.runAndWait()
    engine.stop()

def listen():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("\nListening...")
        recognizer.adjust_for_ambient_noise(source, duration=1)
        audio = recognizer.listen(source)
        
    try:
        print("Recognizing...")
        query = recognizer.recognize_google(audio)
        print(f"You: {query}")
        return query
    except sr.UnknownValueError:
        return None
    except sr.RequestError:
        speak("Sir, I am having trouble accessing the speech service.")
        return None

# --- FIXED: Live Web Search Tool ---
def search_the_web(query: str) -> str:
    """Searches the internet for real-time information on a given topic."""
    print(f"[Jarvis is browsing the web for: '{query}']...")
    try:
        # Import the class from the newly updated package name
        from ddgs import DDGS
        with DDGS() as ddgs:
            # The newest ddgs package expects the positional 'query' parameter
            results = list(ddgs.text(query, max_results=3))
            
            if not results:
                return "No search results found."
            
            # Combine the snippets from the top 3 results
            snippets = [f"- {res['body']}" for res in results if 'body' in res]
            return "\n".join(snippets)
    except Exception as e:
        return f"Failed to search the web: {str(e)}"

def chat_with_jarvis():
    speak("Jarvis system initialized. Live web protocols online. How can I help you, sir?")
    
    system_prompt = (
        "You are Jarvis, a brilliant, concise, and helpful AI assistant. Respond sharply. "
        "You have access to a web search tool. If the user asks about current events, live data, "
        "weather, or anything you do not know, you MUST use the search tool to find the answer before replying."
    )
    
    conversation_history = [{'role': 'system', 'content': system_prompt}]

    # Define the tool structure so Ollama knows it exists
    web_search_tool = {
        'type': 'function',
        'function': {
            'name': 'search_the_web',
            'description': 'Search the internet for live, current, or real-time information.',
            'parameters': {
                'type': 'object',
                'properties': {
                    'query': {
                        'type': 'string',
                        'description': 'The search query to look up on the web.',
                    },
                },
                'required': ['query'],
            },
        },
    }

    while True:
        user_input = listen()
        if not user_input:
            continue
            
        if "exit" in user_input.lower() or "shutdown" in user_input.lower():
            speak("Powering down systems. Goodbye, sir.")
            break

        conversation_history.append({'role': 'user', 'content': user_input})

        try:
            # Step 1: Give the model the conversation AND the tool definition
            response = ollama.chat(
                model='llama3.2', 
                messages=conversation_history,
                tools=[web_search_tool]
            )
            
            # Step 2: Check if the model decided it needs to use the web search tool
            if response.get('message', {}).get('tool_calls'):
                for tool in response['message']['tool_calls']:
                    if tool['function']['name'] == 'search_the_web':
                        # Extract the query the AI wants to search for
                        search_query = tool['function']['arguments']['query']
                        
                        # Run the actual Python search function
                        search_results = search_the_web(search_query)
                        
                        # Add the tool's choice and the live results back to the AI history
                        conversation_history.append(response['message'])
                        conversation_history.append({
                            'role': 'tool',
                            'content': search_results,
                            'name': 'search_the_web'
                        })
                        
                        # Query Ollama one final time with the live web data included
                        final_response = ollama.chat(
                            model='llama3.2',
                            messages=conversation_history
                        )
                        reply = final_response['message']['content']
            else:
                # If no tool was needed, just take the standard response
                reply = response['message']['content']
                
            speak(reply)
            conversation_history.append({'role': 'assistant', 'content': reply})
            
        except Exception as e:
            speak("An error occurred in my processing core.")
            print(f"Error: {e}")

if __name__ == "__main__":
    import sys
    # Fix potential encoding issues in terminal printing
    sys.stdout.reconfigure(encoding='utf-8')
    chat_with_jarvis()