from typing import Annotated, List, Any, Optional, Dict
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from dotenv import load_dotenv
from langgraph.prebuilt import ToolNode
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from pydantic import BaseModel, Field
from edu_agent_tools import playwright_tool, other_tools
from edu_agent_tools import get_edu_extra_tools
from edu_agent_prompts import get_system_prompt
import uuid
import asyncio
from datetime import datetime

from langchain_google_genai import ChatGoogleGenerativeAI
import os

load_dotenv(override=True)

NVIDIA_NIM_API_KEY = os.getenv("NVIDIA_NIM_API_KEY")


# ─────────────────────────────────────────────
#  STATE
# ─────────────────────────────────────────────

class State(TypedDict):
    messages: Annotated[List[Any], add_messages]
    success_criteria: str
    feedback_on_work: Optional[str]
    success_criteria_met: bool
    user_input_needed: bool
    interview: bool          # True = interview mode / False = guide mode
    student_profile: Optional[Dict]  # filled as interview progresses


# ─────────────────────────────────────────────
#  EVALUATOR OUTPUT SCHEMA
# ─────────────────────────────────────────────

class EvaluatorOutput(BaseModel):
    feedback: str = Field(description="Feedback on the assistant's response")
    success_criteria_met: bool = Field(description="Whether the success criteria has been met")
    user_input_needed: bool = Field(
        description="True if more input is needed from the user, clarifications, or the assistant is stuck"
    )


# ─────────────────────────────────────────────
#  EDUAGENT
# ─────────────────────────────────────────────

class EduAgent:
    def __init__(self, interview: bool = True):
        """
        Args:
            interview: True  → structured intake interview mode
                       False → free expert German university guide mode
        """
        self.interview = interview
        self.worker_llm_with_tools = None
        self.evaluator_llm_with_output = None
        self.tools = None
        self.graph = None
        self.agent_id = str(uuid.uuid4())
        self.memory = MemorySaver()
        self.browser = None
        self.playwright = None

    def get_greeting(self) -> str:
        """Return the opening message shown when a session starts or resets."""
        if self.interview:
            return (
                "Hello! I'm EduAgent. I'll help you build your German university application profile. "
                "To start, are you applying for a Bachelor's or a Master's program?"
            )
        return (
            "Hello! I'm EduAgent. Ask me anything about German university applications, "
            "APS, deadlines, fees, or university options, and I'll guide you."
        )

    def get_initial_chat(self) -> list[dict]:
        """Return the first assistant message for the current mode."""
        return [{"role": "assistant", "content": self.get_greeting()}]

    async def setup(self):
        self.tools, self.browser, self.playwright = await playwright_tool()
        self.tools += await other_tools()
        self.tools += get_edu_extra_tools()


        worker_llm = ChatGoogleGenerativeAI(
            model = "gemini-2.5-flash",
            temperature = 0
        )

        # worker_llm = ChatOpenAI(
        #     model="gpt-4o-mini"
        #     # model="nvidia/nemotron-3-nano-omni-30b-a3b-reasoning",
        #     # base_url="https://integrate.api.nvidia.com/v1",
        #     # api_key=NVIDIA_NIM_API_KEY,
        # )
        self.worker_llm_with_tools = worker_llm.bind_tools(self.tools)

        evaluator_llm = ChatGoogleGenerativeAI(
            model = "gemini-2.5-flash",
            temperature = 0
        )

        # evaluator_llm = ChatOpenAI(
        #     model="gpt-4o-mini"
        #     # model="nvidia/nemotron-3-nano-omni-30b-a3b-reasoning",
        #     # base_url="https://integrate.api.nvidia.com/v1",
        #     # api_key=NVIDIA_NIM_API_KEY,
        # )
        self.evaluator_llm_with_output = evaluator_llm.with_structured_output(EvaluatorOutput)

        await self.build_graph()

    # ── WORKER ──────────────────────────────────

    def worker(self, state: State) -> Dict[str, Any]:
        # Pick the right system prompt based on current mode
        system_message_content = get_system_prompt(interview=state["interview"])

        # Append success criteria and feedback if available
        system_message_content += f"""

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SUCCESS CRITERIA FOR THIS SESSION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{state["success_criteria"]}
"""
        if state.get("feedback_on_work"):
            system_message_content += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PREVIOUS ATTEMPT FEEDBACK
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Your previous response was rejected. Here is why:
{state["feedback_on_work"]}
Please correct this and try again.
"""

        # Inject or update system message in history
        messages = state["messages"]
        found = False
        for message in messages:
            if isinstance(message, SystemMessage):
                message.content = system_message_content
                found = True

        if not found:
            messages = [SystemMessage(content=system_message_content)] + messages

        response = self.worker_llm_with_tools.invoke(messages)
        return {"messages": [response]}

    # ── WORKER ROUTER ────────────────────────────

    def worker_router(self, state: State) -> str:
        last_message = state["messages"][-1]
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        return "evaluator"

    # ── CONVERSATION FORMATTER ───────────────────

    def format_conversation(self, messages: List[Any]) -> str:
        conversation = "Conversation history:\n\n"
        for message in messages:
            if isinstance(message, HumanMessage):
                conversation += f"User: {message.content}\n"
            elif isinstance(message, AIMessage):
                text = message.content or "[Tool use]"
                conversation += f"Assistant: {text}\n"
        return conversation

    # ── EVALUATOR ────────────────────────────────

    def evaluator(self, state: State) -> State:
        last_response = state["messages"][-1].content
        mode = "interview" if state["interview"] else "guide"

        system_message = """You are an evaluator checking whether an AI assistant has responded
correctly. Assess the response based on the success criteria and provide structured feedback."""

        # Evaluator criteria differ by mode
        if state["interview"]:
            mode_criteria = """
The assistant is in INTERVIEW MODE. A good response:
- Asks exactly ONE question at a time (never two)
- Stays on the interview flow — does not skip steps
- If the student lacks APS, provides guidance but still continues the interview
- Does not give general advice or go off-topic
- Is warm and professional in tone
"""
        else:
            mode_criteria = """
The assistant is in GUIDE MODE. A good response:
- Answers the student's question thoroughly and accurately
- Gives specific, actionable advice about German university applications
- Mentions APS certificate requirement when relevant
- Is honest when uncertain and directs to official sources
"""

        user_message = f"""Evaluate this conversation between a student and EduAgent.

{self.format_conversation(state["messages"])}

Agent mode: {mode}
{mode_criteria}

Success criteria: {state["success_criteria"]}

Final assistant response being evaluated:
{last_response}

Provide feedback and decide:
1. Has the success criteria been met?
2. Is user input needed (student asked something, agent is stuck, or clarification required)?

Give the assistant benefit of the doubt if the response is directionally correct.
"""
        if state.get("feedback_on_work"):
            user_message += f"\nPrior feedback given: {state['feedback_on_work']}\n"
            user_message += "If the agent is repeating the same mistake, mark user_input_needed as True."

        evaluator_messages = [
            SystemMessage(content=system_message),
            HumanMessage(content=user_message),
        ]

        eval_result = self.evaluator_llm_with_output.invoke(evaluator_messages)

        return {
            "messages": [
                {
                    "role": "assistant",
                    "content": f"Evaluator Feedback: {eval_result.feedback}",
                }
            ],
            "feedback_on_work": eval_result.feedback,
            "success_criteria_met": eval_result.success_criteria_met,
            "user_input_needed": eval_result.user_input_needed,
        }

    # ── EVALUATION ROUTER ────────────────────────

    def route_based_on_evaluation(self, state: State) -> str:
        if state["success_criteria_met"] or state["user_input_needed"]:
            return "END"
        return "worker"

    # ── GRAPH ────────────────────────────────────

    async def build_graph(self):
        graph_builder = StateGraph(State)

        graph_builder.add_node("worker", self.worker)
        graph_builder.add_node("tools", ToolNode(tools=self.tools))
        graph_builder.add_node("evaluator", self.evaluator)

        graph_builder.add_conditional_edges(
            "worker", self.worker_router, {"tools": "tools", "evaluator": "evaluator"}
        )
        graph_builder.add_edge("tools", "worker")
        graph_builder.add_conditional_edges(
            "evaluator",
            self.route_based_on_evaluation,
            {"worker": "worker", "END": END},
        )
        graph_builder.add_edge(START, "worker")

        self.graph = graph_builder.compile(checkpointer=self.memory)

    # ── RUN ──────────────────────────────────────

    async def run(self, message: str, success_criteria: str, history: list | None) -> list:
        config = {"configurable": {"thread_id": self.agent_id}}

        # Success criteria defaults differ by mode
        if not success_criteria:
            if self.interview:
                success_criteria = (
                    "The agent asked exactly one question, stayed on the interview flow, "
                    "and collected the required information without skipping any step."
                )
            else:
                success_criteria = (
                    "The agent gave an accurate, helpful, and specific answer "
                    "about German university applications."
                )

        state = {
            "messages": [HumanMessage(content=message)],
            "success_criteria": success_criteria,
            "feedback_on_work": None,
            "success_criteria_met": False,
            "user_input_needed": False,
            "interview": self.interview,
            "student_profile": {},
        }

        result = await self.graph.ainvoke(state, config=config)

        history = history or []
        user = {"role": "user", "content": message}
        reply = {"role": "assistant", "content": result["messages"][-2].content}
        feedback = {"role": "assistant", "content": result["messages"][-1].content}

        return history + [user, reply, feedback]

    def set_mode(self, interview: bool):
        """Switch between interview and guide mode mid-session."""
        self.interview = interview

    # ── CLEANUP ──────────────────────────────────

    def cleanup(self):
        if self.browser:
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(self.browser.close())
                if self.playwright:
                    loop.create_task(self.playwright.stop())
            except RuntimeError:
                asyncio.run(self.browser.close())
                if self.playwright:
                    asyncio.run(self.playwright.stop())
