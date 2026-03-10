from pydantic_ai import Agent
from dotenv import load_dotenv
import random

SYSTEM_PROMPT = """
You are a helpful AI agent.
""".strip()

# Setup the agent
agent = Agent(
    system_prompt=SYSTEM_PROMPT,
    output_type=str,
)


# Define a tool
@agent.tool_plain
def roll_dice() -> str:
    """Roll a six-sided die and return the result."""
    return str(random.randint(1, 6))


# Convert to chat interface
load_dotenv()  # Load API keys
app = agent.to_web(
    models=[
        # "openai:gpt-5.2",
        # "anthropic:claude-sonnet-4-5",
        "google-gla:gemini-3-flash-preview",
    ]
)
