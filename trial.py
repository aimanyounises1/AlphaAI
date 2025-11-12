# filename: agent_creation.py

import autogen
import chainlit as cl
from config import local_llm_config
from utils.chainlit_agents import ChainlitUserProxyAgent, ChainlitAssistantAgent
import logging
import json
from autogen.agentchat.contrib.retrieve_user_proxy_agent import RetrieveUserProxyAgent
from graphrag.query.cli import run_local_search, run_global_search

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EnhancedRetrieveUserProxyAgent(RetrieveUserProxyAgent, ChainlitUserProxyAgent):
    def __init__(self, name, graphrag_config, **kwargs):
        RetrieveUserProxyAgent.__init__(self, name=name, **kwargs)
        ChainlitUserProxyAgent.__init__(self, name=name, **kwargs)
        self.graphrag_config = graphrag_config

    async def query_graphRAG(self, question: str) -> str:
        print(f"Running GraphRAG query for question: {question}")
        if self.graphrag_config.get('LOCAL_SEARCH', True):
            result = run_local_search(
                self.graphrag_config.get('INPUT_DIR'),
                self.graphrag_config.get('ROOT_DIR', '.'),
                self.graphrag_config.get('COMMUNITY'),
                self.graphrag_config.get('RESPONSE_TYPE'),
                question
            )
        else:
            result = run_global_search(
                self.graphrag_config.get('INPUT_DIR'),
                self.graphrag_config.get('ROOT_DIR', '.'),
                self.graphrag_config.get('COMMUNITY'),
                self.graphrag_config.get('RESPONSE_TYPE'),
                question
            )

        if result is None:
            logger.error("GraphRAG query returned None")
            return "Sorry, I couldn't find any relevant information."

        print(f"GraphRAG query result: {result}")
        return result

    async def retrieve_and_process(self, problem: str) -> str:
        graphrag_result = await self.query_graphRAG(problem)
        processed_result = f"GraphRAG retrieval result:\n{graphrag_result}\n\nPlease provide a response based on this information."
        return processed_result


def create_agent(name, agent_class, **kwargs):
    try:
        if 'name' in kwargs:
            del kwargs['name']  # Remove 'name' from kwargs if it exists

        # Use ChainlitAssistantAgent for AssistantAgent
        if agent_class == autogen.AssistantAgent:
            agent_class = ChainlitAssistantAgent

        agent = agent_class(name=name, **kwargs)
        cl.user_session.set(name, agent)
        logger.info(f"Created agent: {name} of type {agent_class.__name__}")
        return agent
    except Exception as e:
        logger.error(f"Error creating agent {name}: {str(e)}")
        raise


async def create_agents():
    graphrag_config = {
        'LOCAL_SEARCH': True,
        'INPUT_DIR': None,
        'ROOT_DIR': '.',
        'COMMUNITY': 'your_community',
        'RESPONSE_TYPE': 'your_response_type'
    }

    agents = {
        "User_Proxy_Agent": (EnhancedRetrieveUserProxyAgent, {
            "human_input_mode": "TERMINATE",
            "llm_config": local_llm_config,
            "is_termination_msg": lambda x: x.get("content", "").rstrip().endswith("TERMINATE"),
            "code_execution_config": False,
            "system_message": """You are a human admin interacting with the retriever and other agents. 
                Your role is to provide context, clarify requirements, and ensure all technical aspects are covered. 
                To provide a new or modified query, always start your message with either:
                - "New query:" followed by the new query text
                - "Process query:" followed by the modified query text
                If you don't have a new query, you can ask for clarification or provide additional context.
                Always ask for clarification on technical parameters and implementation details if they're not provided.""",
            "description": "User Proxy Agent facilitating detailed technical discussions and query refinement",
            "graphrag_config": graphrag_config,
        }),
        "Retriever_Agent": (autogen.AssistantAgent, {
            "llm_config": local_llm_config,
            "system_message": """You're a Retriever. Your primary function is to execute query_graphRAG to find relevant context. 
                Always include technical details and parameters in your responses. 
                Output 'RETRIEVAL_COMPLETE' when a comprehensive answer has been provided.""",
            "max_consecutive_auto_reply": None,
            "human_input_mode": "NEVER",
            "description": "Retriever Agent specializing in graph-based information retrieval"
        }),
        # ... (other agents remain unchanged)
    }

    created_agents = {}
    for name, (agent_class, config) in agents.items():
        try:
            created_agents[name] = create_agent(name, agent_class, **config)
        except Exception as e:
            logger.error(f"Failed to create agent {name}: {str(e)}")

    # Log the creation of agents with their configurations
    agent_configs = {name: {**config, "type": agent_class.__name__} for name, (agent_class, config) in agents.items()}
    logger.info(f"Agents created with configurations: {json.dumps(agent_configs, indent=2, default=str)}")

    return tuple(created_agents.values())


# Add this function to run the conversation
async def run_conversation(initial_message: str):
    agents = await create_agents()
    user_proxy = next(agent for agent in agents if isinstance(agent, EnhancedRetrieveUserProxyAgent))

    # Create a group chat manager
    groupchat = autogen.GroupChat(agents=agents, messages=[], max_round=60)
    manager = autogen.GroupChatManager(groupchat=groupchat, llm_config=local_llm_config)

    # Start the conversation with the initial message
    enhanced_message = await user_proxy.retrieve_and_process(initial_message)
    chat_result = await user_proxy.initiate_chat(
        manager,
        message=enhanced_message,
        clear_history=True
    )

    return chat_result


# Usage example
if __name__ == "__main__":
    initial_message = "What is the capital of France?"
    conversation_result = run_conversation(initial_message)

    for message in conversation_result:
        print(f"{message['name']}: {message['content']}")
