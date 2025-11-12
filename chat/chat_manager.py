# filename: chat/chat_manager.py

import autogen
from config import local_llm_config
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def create_group_chat_manager(user_proxy, retriever, tester, coder, code_reviewer):
    def state_transition(last_speaker, groupchat):
        messages = groupchat.messages
        logger.debug(f"Selecting next speaker. Last speaker: {last_speaker.name if last_speaker else 'None'}")

        if last_speaker is user_proxy and "RETRIEVAL_COMPLETE" in messages[-1].get("content", ""):
            return tester
        if last_speaker is user_proxy:
            return retriever
        elif last_speaker is retriever:
            if messages and "RETRIEVAL_COMPLETE" in messages[-1].get("content", ""):
                logger.info("Retrieval complete. Moving to tester.")
                return tester
            elif len([m for m in messages if m["name"] == retriever.name]) >= 4:
                logger.info("Retriever has spoken 7 times without completion. Moving to Tester.")
                return tester
            return user_proxy  # Continue user_proxy process
        elif last_speaker is tester:
            if messages and "TESTS COMPLETED" in messages[-1].get("content", ""):
                logger.info("Tests completed. Moving to Coder.")
                return coder
            return tester
        elif last_speaker is coder:
            if messages and "CODE_IMPLEMENTATION_COMPLETE" in messages[-1].get("content", ""):
                logger.info("Code implementation complete. Moving to Code Reviewer.")
                return code_reviewer
            return coder
        elif last_speaker is code_reviewer:
            if messages and "CODE_REVIEW_COMPLETE" in messages[-1].get("content", ""):
                logger.info("Code review complete. Ending conversation.")
                return None
            elif messages and "CODE_REVIEW_INCOMPLETE" in messages[-1].get("content", ""):
                logger.info("Code review incomplete. Moving back to Coder.")
                return coder
            return code_reviewer
        else:
            logger.warning(f"Unexpected last speaker: {last_speaker.name if last_speaker else 'None'}")
            return user_proxy

    groupchat = autogen.GroupChat(
        agents=[user_proxy, retriever, tester, coder, code_reviewer],
        messages=[],
        max_round=60,
        speaker_selection_method=state_transition,
        allow_repeat_speaker=True,
        send_introductions=True
    )

    class OptimizedGroupChatManager(autogen.GroupChatManager):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.max_tokens = 128000  # Mistral Large 2's context window
            self.current_token_count = 0

        def estimate_tokens(self, text):
            # Rough estimate: 1 token ≈ 4 characters for English
            return len(text) // 4 if text else 0

        def send(self, message=None, recipient=None, request_reply=True, silent=False):
            try:
                logger.debug(f"Sending message to {recipient.name if recipient else 'None'}")
                logger.debug(f"Original message: {message}")

                if not self.groupchat.messages:
                    logger.warning("Groupchat messages is empty in send method.")
                    if not message:
                        logger.warning("No message to send. Skipping.")
                        return None
                    return super().send(message, recipient, request_reply, silent)

                estimated_tokens = self.estimate_tokens(message)

                if self.current_token_count + estimated_tokens > self.max_tokens:
                    logger.warning("Approaching token limit. Clearing older messages.")
                    self.groupchat.messages = self.groupchat.messages[-5:]  # Keep last 5 messages for context
                    self.current_token_count = sum(
                        self.estimate_tokens(m.get('content', '')) for m in self.groupchat.messages)

                self.current_token_count += estimated_tokens

                if recipient:
                    if recipient == self.groupchat.agents[1]:  # Retriever
                        message = self.prepare_retriever_message()
                    elif recipient == self.groupchat.agents[2]:  # Tester
                        message = self.prepare_tester_message()
                    elif recipient == self.groupchat.agents[3]:  # Coder
                        message = self.prepare_coder_message()
                    elif recipient == self.groupchat.agents[4]:  # Code Reviewer
                        message = self.prepare_reviewer_message()

                logger.debug(f"Final message being sent: {message}")
                return super().send(message, recipient, request_reply, silent)
            except Exception as e:
                logger.error(f"Error in send method: {str(e)}")
                return None

        def prepare_retriever_message(self):
            user_messages = [m['content'] for m in reversed(self.groupchat.messages)
                             if m.get('name') == "User_Proxy_Agent" and m.get('content')]
            context = user_messages[0] if user_messages else "No context available."

            return f"""Based on the following user requirement, use your retrieval capabilities to fetch relevant information:

            Context:
            {context}

            Please provide comprehensive information related to this requirement. 
            Once you have fetched and provided all relevant information, end your response with 'RETRIEVAL_COMPLETE'."""

        def prepare_tester_message(self):
            context = self.get_context(["User_Proxy_Agent", "Retriever_Agent"])
            return f"""Based on the following conversation context and the information fetched by the retriever, generate relevant test scenarios:

            Context:
            {context}

            Remember to follow the guidelines in your system message for creating comprehensive test scenarios.
            Once you have generated all relevant test scenarios, end your response with '**TESTS COMPLETED.**'."""

        def prepare_coder_message(self):
            context = self.get_context(["User_Proxy_Agent", "Retriever_Agent", "Tester_Agent"])
            return f"""Implement the following requirements in a Java Spring application:

            Context:
            {context}

            Please follow these guidelines:
            1. Create Delegate and Service classes following the Spring application pattern.
            2. Use appropriate annotations (@Named, @Scope, @Inject) for dependency injection.
            3. Implement key methods in Service classes: validate(), inputMapping(), executeImpl(), and outputMapping().
            4. Use proper error handling with custom exceptions and logging.
            5. Implement asynchronous operations and caching where appropriate.
            6. Follow consistent naming conventions and code structure.
            7. Provide comments explaining complex logic or decisions.

            Once you have completed the implementation, end your response with 'CODE_IMPLEMENTATION_COMPLETE'.
             or 'CODE_IMPLEMENTATION_INCOMPLETE' if the code needs further modification."""

        def prepare_reviewer_message(self):
            context = self.get_context(["User_Proxy_Agent", "Retriever_Agent", "Tester_Agent", "Coder_Agent"])
            return f"""Review the following Java Spring application implementation:

            Context:
            {context}

            Please follow these guidelines for your review:
            1. Verify the overall structure follows the Spring application pattern (Delegate and Service classes).
            2. Check for proper use of annotations and dependency injection.
            3. Ensure implementation of key methods in Service classes.
            4. Assess error handling, logging, and asynchronous operations.
            5. Evaluate code quality, efficiency, and adherence to best practices.
            6. Identify any potential bugs, security issues, or performance bottlenecks.
            7. Provide constructive feedback and suggestions for improvement.

            Once you have completed the review, end your response with 'CODE_REVIEW_COMPLETE' if no further changes 
            are needed, or 'CODE_REVIEW_INCOMPLETE' if the code needs further modification."""

        def get_context(self, agent_names):
            return "\n".join([f"{m.get('name', 'Unknown')}: {m.get('content', '')}"
                              for m in self.groupchat.messages
                              if m.get('name') in agent_names and m.get('content')])

    return OptimizedGroupChatManager(
        groupchat=groupchat,
        llm_config=local_llm_config,
        is_termination_msg=lambda x: x and x.get("content", "") and "CODE_REVIEW_COMPLETE" in x.get("content", ""),
    )
