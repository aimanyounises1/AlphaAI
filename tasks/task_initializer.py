import chainlit as cl
from chainlit import TaskList, Task, TaskStatus


async def initialize_tasks():
    task_list = cl.TaskList()
    processing_task = cl.Task(title="Processing Prompt", status=TaskStatus.READY)
    retriever_task = cl.Task(title="Retriever Agent", status=TaskStatus.READY)
    user_proxy_task = cl.Task(title="SolutionBook Proxy Agent", status=TaskStatus.READY)
    testing_agent_task = cl.Task(title="Testing Agent", status=TaskStatus.READY)
    coding_agent_task = cl.Task(title="Coding Agent", status=TaskStatus.READY)
    code_review_agent_task = cl.Task(title="Code Review Agent", status=TaskStatus.READY)

    await task_list.add_task(processing_task)
    await task_list.add_task(retriever_task)
    await task_list.add_task(user_proxy_task)
    await task_list.add_task(testing_agent_task)
    await task_list.add_task(coding_agent_task)
    await task_list.add_task(code_review_agent_task)

    return task_list, processing_task, retriever_task, user_proxy_task, testing_agent_task, coding_agent_task, code_review_agent_task
