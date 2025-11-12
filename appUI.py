import chainlit as cl
import os
import asyncio

# Placeholder for missing modules. Replace these with your actual implementations.
from chat.conversation_handler import run_conversation
from config import initialize_settings
from graph.visualization import visualize_graph_message
from file_handlers.pdf_hanlder import process_pdf
from file_handlers.docx_handler import process_doc
from agents.agents import create_agents

INPUT_DIR = "input"


@cl.step(type="tool")
async def initialize_graphrag():
    await cl.Message(
        "# Welcome to Alpha Assistant! 🚀\n\nI'm here to help you with your queries using advanced retrieval techniques.").send()
    await asyncio.sleep(0.5)

    await initialize_settings()
    await asyncio.sleep(0.5)

    await create_agents()

    await cl.Message(
        content="You can upload PDF or DOC files for processing at any time during our conversation.",
        actions=[cl.Action(name="upload", value="upload", label="📤 Upload File")]
    ).send()
    await asyncio.sleep(0.5)

    if cl.user_session.get("Visualize_graph"):
        await visualize_graph_message()

    return "GraphRAG Assistant initialized successfully"


@cl.on_chat_start
async def on_chat_start():
    try:
        result = await initialize_graphrag()
        await cl.Message(content=f"{result}\nWhat can I help you with today?").send()
    except Exception as e:
        print("Error: ", e)
        await cl.Message(content=f"An error occurred during initialization: {str(e)}").send()


@cl.on_message
async def handle_message(message: cl.Message):
    @cl.step(type="process")
    async def process_query():
        return f"User query: {message.content}"

    @cl.step(type="llm")
    async def run_conversation_step():
        response = await run_conversation(message)
        await cl.Message(content=response).send()
        return response, "Conversation processing complete"

    query_info = await process_query()
    response, conversation_result = await run_conversation_step()

    cl.user_session.set("last_response", response)


@cl.action_callback("upload")
async def on_upload(action):
    @cl.step(name="File Upload" , type="tool")
    async def upload_files():
        files = await cl.AskFileMessage(
            content="Please upload PDF or DOC files for processing.",
            accept=["application/pdf", "application/msword",
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"],
            max_size_mb=20,
            max_files=5,
        ).send()
        return files

    @cl.step(name="Process Files",  type="tool")
    async def process_files(files):
        if files:
            for file in files:
                await process_uploaded_file(file)
            await cl.Message(content="Files processed. How can I assist you with the uploaded content?").send()
            return "Files processed successfully"
        else:
            return "No files were uploaded"

    files = await upload_files()
    result = await process_files(files)
    await cl.Message(content=result).send()


async def process_uploaded_file(file):
    @cl.step(name=f"Process {file.name}",  type="tool")
    async def process_file():
        file_extension = os.path.splitext(file.name)[1].lower()
        if file_extension == '.pdf':
            await process_pdf(file, INPUT_DIR)
        elif file_extension in ['.doc', '.docx']:
            await process_doc(file, INPUT_DIR)
        else:
            await cl.Message(f"Unsupported file type: {file_extension}").send()
        return f"File {file.name} processed"

    return await process_file()


