# langchain_agent.py
# Agent that orchestrates the Drug-Reporter tools
# Compatible with LangChain 1.0+

from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, AIMessage
from dotenv import load_dotenv

from langchain_tools import all_tools

load_dotenv()

# Setup LLM with tools bound
llm = ChatAnthropic(model="claude-sonnet-4-20250514")
llm_with_tools = llm.bind_tools(all_tools)

# System prompt
SYSTEM_PROMPT = """You are a drug safety alert coordinator.

Your workflow:
1. First call load_sample_pharmacies (if not done)
2. Create a drug report with create_drug_report
3. Send alert using:
   - broadcast_alert: for critical/widespread issues (ALL pharmacies)
   - targeted_alert: for regional issues (SPECIFIC regions)
4. Check status with check_delivery_statistics
5. Use send_followup_reminders for pending acknowledgments

Always choose the right alert type based on severity and scope.
Use tools to complete the task. Call tools one at a time and wait for results."""


def run(user_input: str) -> dict:
  """Run the agent with natural language input."""

  messages = [
    {"role": "system", "content": SYSTEM_PROMPT},
    {"role": "user", "content": user_input}
  ]

  # Tool name to function mapping
  tool_map = {tool.name: tool for tool in all_tools}

  max_iterations = 10
  iteration = 0

  while iteration < max_iterations:
    iteration += 1

    # Get response from LLM
    response = llm_with_tools.invoke(messages)

    # Check if there are tool calls
    if not response.tool_calls:
      # No more tool calls, return final response
      return {
        "output": response.content,
        "iterations": iteration
      }

    # Add assistant message with tool calls
    messages.append(response)

    # Process each tool call
    for tool_call in response.tool_calls:
      tool_name = tool_call["name"]
      tool_args = tool_call["args"]

      print(f"[Tool Call] {tool_name}: {tool_args}")

      # Execute the tool
      if tool_name in tool_map:
        try:
          tool_result = tool_map[tool_name].invoke(tool_args)
        except Exception as e:
          tool_result = f"Error: {str(e)}"
      else:
        tool_result = f"Error: Unknown tool {tool_name}"

      print(f"[Tool Result] {tool_result[:200]}...")

      # Add tool result to messages
      messages.append({
        "role": "tool",
        "tool_call_id": tool_call["id"],
        "content": str(tool_result)
      })

  return {
    "output": "Max iterations reached",
    "iterations": iteration
  }


if __name__ == "__main__":
  print("=" * 60)
  print("TEST: Broadcast Alert Workflow")
  print("=" * 60)

  result = run("""
        Load pharmacies, create a high severity recall for 
        Metformin XR 500mg due to glass contamination, 
        then broadcast to all pharmacies.
    """)
  print(f"\nFinal Result: {result['output']}\n")