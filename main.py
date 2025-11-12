import asyncio
from agents_creation import run_conversation
import chainlit as cl


@cl.on_chat_start
async def start():
    cl.user_session.set("chat_history", [])


@cl.on_message
async def main(message: cl.Message):
    chat_history = cl.user_session.get("chat_history")
    chat_history.append(f"Human: {message.content}")

    conversation_result = await run_conversation(message.content)

    for msg in conversation_result:
        chat_history.append(f"{msg['name']}: {msg['content']}")
        await cl.Message(content=msg['content'], author=msg['name']).send()

    cl.user_session.set("chat_history", chat_history)


if __name__ == "__main__":
    asyncio.run(main())
