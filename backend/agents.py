import os
import google.generativeai as genai
from dotenv import load_dotenv
from google.generativeai.types import FunctionDeclaration, Tool
from .tools import (
    check_room_availability,
    get_facility_info,
    get_menu_items,
    place_restaurant_order,
    create_room_service_request
)

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY") # Keeping the env var name same for simplicity, or user can change it
if not api_key:
    print("CRITICAL WARNING: API Key is not set!")

genai.configure(api_key=api_key)

# --- Tool Wrappers for Gemini ---
# Gemini SDK can accept functions directly, which is much easier!

receptionist_tools_list = [check_room_availability, get_facility_info]
restaurant_tools_list = [get_menu_items, place_restaurant_order]
room_service_tools_list = [create_room_service_request]

# --- Agents ---

class ResortAgent:
    def __init__(self, system_prompt, tools):
        self.system_prompt = system_prompt
        self.tools = tools
        self.model = genai.GenerativeModel(
            model_name='gemini-2.0-flash', # Using Flash for speed/cost
            tools=self.tools,
            system_instruction=self.system_prompt
        )
        self.chat_session = self.model.start_chat(enable_automatic_function_calling=True)

    def process_message(self, history):
        # History management in Gemini is stateful in the object, but our API is stateless per request.
        # For this simple implementation, we will just send the last user message.
        # In a real production app, we'd reconstruct the history properly.
        
        last_user_message = next((m['content'] for m in reversed(history) if m['role'] == 'user'), None)
        
        if not last_user_message:
            return "How can I help you?"

        try:
            response = self.chat_session.send_message(last_user_message)
            return response.text
        except Exception as e:
            return f"I encountered an error: {str(e)}"

# System Prompts
RECEPTIONIST_PROMPT = """You are the Resort Receptionist. 
Your duties: 
1. Answer FAQs (Check-in/out times, Wi-Fi, Parking).
2. Check room availability using the `check_room_availability` tool.
3. Provide facility info (Gym, Spa, Pool, Restaurant) using the `get_facility_info` tool.

Be polite, professional, and welcoming. 
If a guest asks about check-in/out, use the `get_facility_info` tool with arguments "check-in" or "check-out".
If a guest asks for food or room service, politely direct them to the Restaurant or Room Service departments, or allow the router to handle it if the user switches context."""

RESTAURANT_PROMPT = """You are the Resort Restaurant Agent.
Your duties: Show the menu, take food orders.
1. When asked for the menu, call the `get_menu_items` tool. **You MUST display the EXACT output returned by the tool.** Do not summarize or just say "Here is the menu". Show the full list.
2. ALWAYS ask for the Room Number before placing an order.
3. When taking an order, confirm the items and calculate the total bill."""

ROOM_SERVICE_PROMPT = """You are the Resort Room Service Agent.
Your duties: Handle requests for cleaning, laundry, and amenities (towels, soap, etc.).
ALWAYS ask for the Room Number before creating a request.
Confirm the request details with the guest."""

ROUTER_PROMPT = """You are the Main Resort Concierge.
Your job is to classify the user's intent and route them to one of three agents:
1. 'Receptionist': General queries, room availability, facility info.
2. 'Restaurant': Food ordering, menu inquiries.
3. 'RoomService': Cleaning, laundry, amenities.

Analyze the user message.
Return ONLY the name of the agent: 'Receptionist', 'Restaurant', or 'RoomService'.
If unsure, default to 'Receptionist'."""

# --- Main Orchestrator ---

class AgentManager:
    def __init__(self):
        # We create fresh agents for now to avoid state issues in this simple design
        pass

    def get_agent(self, agent_type):
        if agent_type == "Restaurant":
            return ResortAgent(RESTAURANT_PROMPT, restaurant_tools_list)
        elif agent_type == "RoomService":
            return ResortAgent(ROOM_SERVICE_PROMPT, room_service_tools_list)
        else:
            return ResortAgent(RECEPTIONIST_PROMPT, receptionist_tools_list)

    def route_request(self, text):
        model = genai.GenerativeModel('gemini-2.0-flash', system_instruction=ROUTER_PROMPT)
        response = model.generate_content(text)
        intent = response.text.strip()
        # Clean up any extra chars
        if "Restaurant" in intent: return "Restaurant"
        if "RoomService" in intent: return "RoomService"
        return "Receptionist"

    def chat(self, history):
        # Get the latest message
        user_text = next((m['content'] for m in reversed(history) if m['role'] == 'user'), "")
        
        # 1. Route
        agent_name = self.route_request(user_text)
        print(f"Routing '{user_text}' to: {agent_name}")
        
        # 2. Delegate
        agent = self.get_agent(agent_name)
        return agent.process_message(history)

manager = AgentManager()
