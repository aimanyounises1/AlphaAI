# filename: chat/conversation_handler.py

import chainlit as cl
from chainlit import TaskStatus
from typing_extensions import Annotated

from utils.utils import process_and_merge_responses
from graphrag.query.cli import run_local_search, run_global_search
from chat.chat_manager import create_group_chat_manager
from database.db_connection import save_to_supabase
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@cl.step(name="Conversation Processing", type="run")
async def run_conversation(message: cl.Message):
    global merged_response
    try:
        task_list = cl.user_session.get("task_list")
        processing_task = cl.user_session.get("processing_task")
        retriever_task = cl.user_session.get("retriever_task")
        user_proxy_task = cl.user_session.get("user_proxy_task")
        testing_agent_task = cl.user_session.get("testing_agent_task")
        coding_agent_task = cl.user_session.get("coding_agent_task")
        code_review_agent_task = cl.user_session.get("code_review_agent_task")

        @cl.step(name="Update Task Statuses")
        async def update_task_statuses(status):
            processing_task.status = status
            retriever_task.status = status
            user_proxy_task.status = status
            testing_agent_task.status = status
            coding_agent_task.status = status
            code_review_agent_task.status = status
            await task_list.send()

        await update_task_statuses(TaskStatus.RUNNING)

        INPUT_DIR = None
        ROOT_DIR = '.'
        CONTEXT = message.content
        RESPONSE_TYPE = cl.user_session.get("Gen_type")
        COMMUNITY = cl.user_session.get("Community")
        LOCAL_SEARCH = cl.user_session.get("Search_type")
        user_proxy = cl.user_session.get("User_Proxy_Agent")
        retriever = cl.user_session.get("Retriever_Agent")
        tester = cl.user_session.get("Tester_Agent")
        coder = cl.user_session.get("Coder_Agent")
        code_reviewer = cl.user_session.get("Code_Reviewer_Agent")

        @cl.step(name="GraphRAG Query", type="tool")
        async def query_graphRAG(
                question: Annotated[str, 'Query string containing information that you want from RAG search']
        ) -> str:
            print(f"Running GraphRAG query for question: {question}")
            if LOCAL_SEARCH:
                result = run_local_search(INPUT_DIR, ROOT_DIR, COMMUNITY, RESPONSE_TYPE, question)
            else:
                result = run_global_search(INPUT_DIR, ROOT_DIR, COMMUNITY, RESPONSE_TYPE, question)
            msg = cl.Message(content=result)
            if result is None:
                logger.error("GraphRAG query returned None")
                return "Sorry, I couldn't find any relevant information."
            print(f"GraphRAG query result: {result}")
            for token in result.split():
                await msg.stream_token(token + " ")
            await msg.send()
            return result

        @cl.step(name="Register Agents", type="tool")
        async def register_agents():
            agents_to_register = [
                ("user_proxy", user_proxy),
                ("retriever", retriever),
                ("tester", tester),
                ("coder", coder),
                ("code_reviewer", code_reviewer)
            ]

            for agent_name, agent in agents_to_register:
                if agent is None:
                    logger.error(f"{agent_name} is None. Make sure it's properly initialized.")
                    raise ValueError(f"{agent_name} is not initialized")

                if not hasattr(agent, 'register_for_execution'):
                    logger.error(f"{agent_name} does not have 'register_for_execution' method")
                    raise AttributeError(f"{agent_name} does not have 'register_for_execution' method")
                #print(f"Registering {agent_name}")
                try:
                    if agent_name in ["retriever", "user_proxy"]:
                        d_retrieve_content = agent.register_for_llm(
                            description="retrieve content for code generation and question answering.",
                            api_style="function"
                        )(query_graphRAG)

                        agent.register_for_execution()(d_retrieve_content)
                        logger.info(f"Successfully registered {agent_name}")
                except Exception as e:
                    logger.error(f"Error registering {agent_name}: {str(e)}")
                    raise

        await register_agents()

        manager = create_group_chat_manager(user_proxy, retriever, tester, coder, code_reviewer)
        all_responses = []

        typing_message = cl.Message(content="Thinking...")
        await typing_message.send()

        try:
            @cl.step(name="Agent Interaction", type="llm")
            async def agent_interaction():
                if len(manager.groupchat.messages) == 0:
                    response = await cl.make_async(user_proxy.initiate_chat)(manager, message=CONTEXT,
                                                                             summary_method="reflection_with_llm",
                                                                             clear_history=True)
                else:
                    response = await cl.make_async(user_proxy.send)(manager, message=CONTEXT)
                all_responses.append(response)

            await agent_interaction()

            @cl.step(name="Response Processing", type="tool")
            async def process_response():
                merged_response, original_responses = process_and_merge_responses(all_responses)
                logger.info(f"Context: {CONTEXT}")
                save_to_supabase("N/A", CONTEXT, merged_response, "N/A")
                await typing_message.remove()
                final_message = cl.Message(content=merged_response)
                await final_message.send()
                cl.user_session.set("merged_response", merged_response)
                return merged_response

            merged_response = await process_response()

            @cl.step(name="Feedback Request")
            async def request_feedback():
                feedback_actions = [
                    cl.Action(name="thumbs_up", value="👍", label="👍 Helpful"),
                    cl.Action(name="thumbs_down", value="👎", label="👎 Not Helpful"),
                ]
                await cl.Message(content="Was this response helpful?", actions=feedback_actions).send()

            await request_feedback()

        except Exception as e:
            logger.error(f"Error during conversation: {str(e)}")
            await typing_message.remove()
            error_msg = f"An error occurred during the conversation: {str(e)}"
            await cl.Message(content=error_msg).send()

        finally:
            await update_task_statuses(TaskStatus.DONE)

        return merged_response

    except Exception as e:
        logger.error(f"Error in run_conversation: {str(e)}")
        error_msg = f"An error occurred during the conversation: {str(e)}"
        await cl.Message(content=error_msg).send()
        return error_msg


@cl.on_message
async def handle_message(message: cl.Message):
    async with cl.Step(name="Conversation Processing", type="run") as conv_step:
        conv_step.input = f"Processing user query: {message.content}"

        task_list = cl.user_session.get("task_list")
        processing_task = cl.user_session.get("processing_task")
        retriever_task = cl.user_session.get("retriever_task")
        user_proxy_task = cl.user_session.get("user_proxy_task")
        testing_agent_task = cl.user_session.get("testing_agent_task")
        coding_agent_task = cl.user_session.get("coding_agent_task")
        code_review_agent_task = cl.user_session.get("code_review_agent_task")

        processing_task.status = TaskStatus.RUNNING
        retriever_task.status = TaskStatus.RUNNING
        user_proxy_task.status = TaskStatus.RUNNING
        testing_agent_task.status = TaskStatus.READY
        coding_agent_task.status = TaskStatus.READY
        code_review_agent_task.status = TaskStatus.READY
        await task_list.send()

        try:
            async with cl.Step(name="Query Processing", type="tool") as query_step:
                query_step.input = message.content
                query_result = message.content
                query_step.output = "Query processed"

            async with cl.Step(name="Agent Interaction", type="agent") as agent_step:
                agent_step.input = query_result
                response = await cl.make_async(run_conversation)(message)
                agent_step.output = "Agent interaction completed"

            async with cl.Step(name="Response Generation", type="llm") as response_step:
                response_step.input = response
                final_response = response
                response_step.output = "Response generated"

            conv_step.output = "Conversation processing completed"
            await cl.Message(content=final_response).send()

        except Exception as e:
            logger.error(f"Error in handle_message: {str(e)}")
            error_msg = f"An error occurred during the conversation: {str(e)}"
            await cl.Message(content=error_msg).send()
        finally:
            processing_task.status = TaskStatus.DONE
            retriever_task.status = TaskStatus.DONE
            user_proxy_task.status = TaskStatus.DONE
            testing_agent_task.status = TaskStatus.DONE
            coding_agent_task.status = TaskStatus.DONE
            code_review_agent_task.status = TaskStatus.DONE
            await task_list.send()

    cl.user_session.set("last_response", final_response)

