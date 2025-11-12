# filename: agent_creation.py

import autogen
import chainlit as cl
from config import local_llm_config
from agents.customized_agents import GraphRAGRetrieverAgent
from utils.chainlit_agents import ChainlitUserProxyAgent, ChainlitAssistantAgent
import logging

from utils.embedding import OpenAIEmbedding

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

graphrag_config = {
    'LOCAL_SEARCH': True,
    'INPUT_DIR': None,
    'ROOT_DIR': '.',
    'COMMUNITY': 0,
    'RESPONSE_TYPE': "multiple-page report"
}


def create_agent(name, agent_class, **kwargs):
    try:
        if 'name' in kwargs:
            del kwargs['name']  # Remove 'name' from kwargs if it exists

        # Use ChainlitAssistantAgent for AssistantAgent
        if agent_class == autogen.AssistantAgent:
            agent_class = ChainlitAssistantAgent
        print(f"Creating agent: {name} of type {agent_class.__name__}")
        agent = agent_class(name=name, **kwargs)
        cl.user_session.set(name, agent)
        logger.info(f"Created agent: {name} of type {agent_class.__name__}")
        return agent
    except Exception as e:
        logger.error(f"Error creating agent {name}: {str(e)}")
        raise


async def create_agents():
    agents = {
        "User_Proxy_Agent": (ChainlitUserProxyAgent, {
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
        }),
        "Retriever_Agent": (GraphRAGRetrieverAgent, {
            "llm_config": local_llm_config,
            "system_message": """You're a Retriever. Your primary function is to execute query_vector_db to find relevant context. 
                Always include technical details and parameters in your responses. 
                Output 'RETRIEVAL_COMPLETE' when a comprehensive answer has been provided.""",
            "max_consecutive_auto_reply": None,
            "human_input_mode": "NEVER",
            "retrieve_config": {
                "task": "code",
                "embedding_function": OpenAIEmbedding(api_key="ollama"),
                "model": "ollama_chat/llama3.1:70b",
            },
            "code_execution_config": False,
            "is_termination_msg": lambda x: x.get("content", "").rstrip().endswith("RETRIEVAL_COMPLETE") or x.get(
                "content", "").rstrip().endswith("TERMINATE"),
            "description": "Retriever Agent specializing in graph-based information retrieval",
            "graphrag_config": graphrag_config
        }),
        "Tester_Agent": (autogen.AssistantAgent, {
            "llm_config": local_llm_config,
            "max_consecutive_auto_reply": 5,
            "human_input_mode": "NEVER",
            "system_message": """You're a PRO Tester Engineer. Your task is to generate comprehensive test scenarios based on the context provided. Follow these guidelines:
                1. Analyze the provided context to understand the requirements, features, and technical specifications discussed.
                2. Generate relevant test scenarios that cover functional, performance, security, and user experience aspects.
                3. Include positive cases, negative cases, edge cases, and stress tests in your scenarios.
                4. Format your response as a numbered list of test scenarios, each containing:
                   a) Scenario description
                   b) Preconditions and setup requirements
                   c) Step-by-step test procedure
                   d) Expected results
                   e) Technical parameters to be monitored or measured
                   f) Potential automation approaches
                5. Provide a brief rationale for each test scenario, explaining its importance and what it verifies.
                6. Ensure your scenarios are directly related to the specific features, requirements, and technical specifications discussed.
                7. Include relevant API endpoints, database queries, network configurations, or other technical details where applicable.
                8. Suggest monitoring and logging requirements for each scenario.
                9. Propose performance benchmarks and acceptance criteria where relevant.
                10. Output '**TESTS COMPLETED.**' when you have finished generating all relevant test scenarios.""",
            "description": "Test Scenario Generator Agent specializing in comprehensive technical testing"
        }),
        "Coder_Agent": (autogen.AssistantAgent, {
            "llm_config": local_llm_config,
            "system_message": """You are a skilled Java developer specializing in Spring applications. Your task is to implement the requirements provided in Java code. Follow these guidelines for structuring your code:

            1. Create two main types of classes: Delegates and Services.

            2. Delegate class structure:
               - Use @Named and @Scope("prototype") annotations
               - Implement an interface defining the main operation
               - Inject the corresponding Service using @Inject
               - Implement an execute method that calls service methods and handles the response

            3. Service class structure:
               - Use @Named and @Scope("prototype") annotations
               - Extend a base service class
               - Inject dependencies using @Inject (services, helpers, invokers, etc.)
               - Implement these key methods:
                 a. validate(): Check input validity
                 b. inputMapping(): Prepare input data
                 c. executeImpl(): Core business logic
                 d. outputMapping(): Prepare the output

            4. Utilize dependency injection throughout:
               - Inject services, helpers, mappers, and other components
               - Use constructor injection or field injection as appropriate

            5. Implement error handling and logging:
               - Use custom exception classes
               - Implement logging using a logger interface

            6. Utilize asynchronous operations where beneficial:
               - Use thread pools and Future objects for concurrent operations
               - Implement caching mechanisms to optimize performance

            7. Follow consistent naming conventions and code structure:
               - Use suffixes to indicate customized or extended classes
               - Create helper methods for specific functionalities

            8. Include all necessary imports and use appropriate annotations

            When implementing, focus on the structure and patterns rather than specific class names. Provide comments explaining your design choices and any complex logic.

            Output your code within ```java ``` blocks and explain your implementation approach.

            Output 'CODE_IMPLEMENTATION_COMPLETE' when you've finished writing the code.""",
            "max_consecutive_auto_reply": 3,
            "human_input_mode": "NEVER",
            "description": "Java Coding Agent for implementing Spring application requirements with focus on structure"
        }),
        "Code_Reviewer_Agent": (autogen.AssistantAgent, {
            "llm_config": local_llm_config,
            "system_message": """You are an experienced code reviewer specializing in Java Spring applications. Your task is to review the code implemented by the Coding Agent. Follow these guidelines:

            1. Analyze the code against the original requirements and context.
            2. Verify the overall structure follows the Spring application pattern:
               a. Check for proper use of Delegate and Service classes
               b. Ensure correct use of annotations (@Named, @Scope, @Inject)
               c. Verify the implementation of key methods in Service classes (validate, inputMapping, executeImpl, outputMapping)
            3. Review dependency injection practices:
               a. Confirm appropriate use of @Inject for services, helpers, invokers, etc.
               b. Check for any potential circular dependencies
            4. Assess error handling and logging:
               a. Verify use of custom exceptions (e.g., BadRequestError)
               b. Ensure proper logging using an appropriate logger interface
            5. Evaluate asynchronous operations and caching:
               a. Check proper use of thread pools and Future objects
               b. Review any implemented caching mechanisms
            6. Examine code quality and efficiency:
               a. Verify adherence to Java best practices and clean code principles
               b. Check for appropriate comments explaining complex logic
            7. Ensure consistent naming conventions and code structure
            8. Identify any potential bugs, security issues, or performance bottlenecks
            9. Verify that all necessary imports are included
            10. Provide constructive feedback and suggestions for improvement
            11. If you find any issues, explain them clearly and suggest corrections
            12. If the code meets all requirements and best practices, approve it

            Be thorough in your review, focusing on both the overall structure and specific implementation details. Provide clear explanations for any issues found or improvements suggested.

            Output 'CODE_REVIEW_COMPLETE' when you've finished the review.""",
            "max_consecutive_auto_reply": 2,
            "human_input_mode": "NEVER",
            "description": "Code Review Agent for Java Spring application implementations"
        })

    }

    created_agents = {}
    for name, (agent_class, config) in agents.items():
        try:
            created_agents[name] = create_agent(name, agent_class, **config)
        except Exception as e:
            logger.error(f"Failed to create agent {name}: {str(e)}")

    # Log the creation of agents with their configurations
    # agent_configs = {name: {**config, "type": agent_class.__name__} for name, (agent_class, config) in agents.items()}
    # logger.info(f"Agents created with configurations: {json.dumps(agent_configs, indent=2, default=str)}")

    return tuple(created_agents.values())
