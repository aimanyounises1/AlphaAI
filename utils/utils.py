from autogen import ChatResult


def process_and_merge_responses(responses):
    merged_response = "Merged Response \n\n "
    for response in responses:
        if isinstance(response, ChatResult):
            for item in response.chat_history:
                if 'content' in item and item['content']:
                    merged_response += item['content'] + "\n\n"
        elif isinstance(response, dict) and 'content' in response:
            merged_response += response['content'] + "\n\n"
        elif isinstance(response, str):
            merged_response += response + "\n\n"
        else:
            merged_response += str(response) + "\n\n"
    return merged_response.strip(), responses
