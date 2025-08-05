"""
This is the main entry point for the agent.
It defines the workflow graph, state, tools, nodes and edges.
"""

from typing import Any, List
from typing_extensions import Literal
from langchain_openai import ChatOpenAI
from langchain_deepseek import ChatDeepSeek
from langchain_core.messages import SystemMessage, BaseMessage
from langchain_core.runnables import RunnableConfig
from langchain.tools import tool
from langgraph.graph import StateGraph, END
from langgraph.types import Command
from langgraph.graph import MessagesState
from langgraph.prebuilt import ToolNode

class AgentState(MessagesState):
    """
    Here we define the state of the agent

    In this instance, we're inheriting from CopilotKitState, which will bring in
    the CopilotKitState fields. We're also adding custom fields for proverbs and weather cards.
    """
    proverbs: List[str] = []
    weather_cards: List[dict] = []
    tools: List[Any]
    # your_custom_agent_state: str = ""

@tool
def get_weather(location: str):
    """
    Get the weather for a given location.
    """
    return f"The weather for {location} is 70 degrees."

# @tool
# def your_tool_here(your_arg: str):
#     """Your tool description here."""
#     print(f"Your tool logic here")
#     return "Your tool response here."

backend_tools = [
    get_weather
    # your_tool_here
]

# Extract tool names from backend_tools for comparison
backend_tool_names = [tool.name for tool in backend_tools]


async def chat_node(state: AgentState, config: RunnableConfig) -> Command[Literal["tool_node", "__end__"]]:
    """
    Standard chat node based on the ReAct design pattern. It handles:
    - The model to use (and binds in CopilotKit actions and the tools defined above)
    - The system prompt
    - Getting a response from the model
    - Handling tool calls

    For more about the ReAct design pattern, see:
    https://www.perplexity.ai/search/react-agents-NcXLQhreS0WDzpVaS4m9Cg
    """

    # 1. Define the model
    model = ChatDeepSeek(model="deepseek-chat")

    # 2. Bind the tools to the model
    model_with_tools = model.bind_tools(
        [
            *state.get("tools", []), # bind tools defined by ag-ui
            *backend_tools,
            # your_tool_here
        ],

        # 2.1 Disable parallel tool calls to avoid race conditions,
        #     enable this for faster performance if you want to manage
        #     the complexity of running tool calls in parallel.
        parallel_tool_calls=False,
    )

    # 3. Define the system message by which the chat model will be run
    system_message = SystemMessage(
        content=f"""You are a helpful assistant. The current proverbs are {state.get('proverbs', [])}.

Available tools:
- Backend tools (handled by server): get_weather
- Frontend tools (handled by UI): add_weather_card_to_center, remove_weather_card, addProverb, setThemeColor

When users ask for weather information:
- Use 'get_weather' to show weather info in chat
- Use 'add_weather_card_to_center' to add persistent weather cards to the page center

When users ask to add weather cards to the page, use the 'add_weather_card_to_center' tool with the location parameter.

Choose the appropriate tool based on user intent. When explaining tool names, use plain text instead of code blocks to avoid HTML nesting issues."""
    )

    # 4. Run the model to generate a response
    response = await model_with_tools.ainvoke([
        system_message,
        *state["messages"],
    ], config)

    # Check if response has tool calls
    tool_calls = getattr(response, "tool_calls", None)
    if tool_calls:
        # Separate backend tools from AG-UI tools
        backend_tool_calls = []
        ag_ui_tool_calls = []
        
        for tool_call in tool_calls:
            tool_name = tool_call.get("name")
            if tool_name in backend_tool_names:
                backend_tool_calls.append(tool_call)
            else:
                # AG-UI tools - these will be handled by frontend
                ag_ui_tool_calls.append(tool_call)
        
        # If we have backend tool calls, route to tool_node
        if backend_tool_calls:
            print(f"routing to tool node for backend tools: {[tc.get('name') for tc in backend_tool_calls]}")
            return Command(
                goto="tool_node",
                update={
                    "messages": [response],
                }
            )
        
        # If we only have AG-UI tool calls, end the graph
        # The frontend will handle these tool calls
        if ag_ui_tool_calls:
            print(f"AG-UI tools will be handled by frontend: {[tc.get('name') for tc in ag_ui_tool_calls]}")
            return Command(
                goto=END,
                update={
                    "messages": [response],
                }
            )

    # 5. No tool calls, so we can end the graph.
    return Command(
        goto=END,
        update={
            "messages": [response],
        }
    )

def route_to_tool_node(response: BaseMessage):
    """
    Route to tool node if any tool call in the response matches a backend tool name.
    AG-UI tools are handled by the frontend, so we only route backend tools to tool_node.
    """
    tool_calls = getattr(response, "tool_calls", None)
    if not tool_calls:
        return False

    for tool_call in tool_calls:
        tool_name = tool_call.get("name")
        # Only route backend tools to tool_node
        # AG-UI tools (like add_weather_card_to_center) are handled by frontend
        if tool_name in backend_tool_names:
            return True
    return False

# Define the workflow graph
workflow = StateGraph(AgentState)
workflow.add_node("chat_node", chat_node)
workflow.add_node("tool_node", ToolNode(tools=backend_tools))
workflow.add_edge("tool_node", "chat_node")
workflow.set_entry_point("chat_node")

graph = workflow.compile()
