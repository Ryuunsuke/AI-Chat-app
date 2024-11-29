from fastapi import FastAPI
from pydantic import BaseModel
import json
import openai
import random
import os
import time
import sqlite3
import sys
import os

file_path = r"D:\ENV\ai-chat-app\web-service\app"
sys.path.append(file_path)

import qf

app = FastAPI()
# Model for a single message
class Message(BaseModel):
    role: str
    content: str
    assist_id: str
    api_key: str

# Receive a dummy message and return a test response from the virtual assistant
@app.post("/send-message/")
async def process_message_and_respond(thread_id: str, message: str, assist_id: str, api_key: str):
    """
    Receive a message from the user and return a test response from the virtual assistant.

    Args:
        thread_id (str): The ID of the conversation thread.
        message (str): The message sent by the user.

    Returns:
        dict: A dictionary containing the thread ID, the assistant's test response, and the original message.
    """

    # Currently returns dummy data.
    # Goal: your actual method should add the user message to the conversation history,
    # and also return a response from the assistant
    openai.api_key = api_key
    message = openai.beta.threads.messages.create(
		thread_id=thread_id,
		role="user",
		content=message
	)
	
    run = openai.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=assist_id
    )

    attempt = 1
    while run.status != "completed":
        print(f"Run status: {run.status}, attempt: {attempt}")
        run = openai.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run.id)

        if run.status == "requires_action":
            break

        if run.status == "failed":

            if hasattr(run, 'last_error') and run.last_error is not None:
                error_message = run.last_error.message
            else:
                error_message = "No error message found..."

            print(f"Run {run.id} failed! Status: {run.status}\n  thread_id: {run.thread_id}\n  assistant_id: {run.assistant_id}\n  error_message: {error_message}")
            print(str(run))

        attempt += 1
        time.sleep(5)
        
    if run.status == "requires_action":
        print("Run requires action, assistant wants to use a tool")
    conn = sqlite3.connect('user_data.db')
    cursor = conn.cursor()
    qf.startup(cursor)

    if run.required_action:

        tool_outputs = []
        for tool_call in run.required_action.submit_tool_outputs.tool_calls:
            if tool_call.function.name == "read_rec":
                print("  read_rec called")
                output = qf.read_rec(cursor)
            elif tool_call.function.name == "delete_rec":
                print("  delete_rec called")
                output = qf.delete_rec(cursor)
            elif tool_call.function.name == "insert_rec":
                print("  insert_rec called")
                output = qf.insert_rec(cursor)
            elif tool_call.function.name == "update_rec":
                print("  update_rec called")
                output = qf.update_rec(cursor)
            else:
                print("Unknown function call")
            print(f"  Generated output: {output}")


            tool_outputs.append({
                "tool_call_id": tool_call.id,
                "output": str(output)
            })


        openai.beta.threads.runs.submit_tool_outputs(
            thread_id=thread_id,
            run_id=run.id,
            tool_outputs=tool_outputs 
        )
    conn.close()

    if run.status == "requires_action":

     
        run = openai.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run.id)
        attempt = 1
        while run.status not in ["completed", "failed"]:
            print(f"Run status: {run.status}, attempt: {attempt}")
            time.sleep(2)
            run = openai.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run.id)
            attempt += 1

    if run.status == "completed":

        messages = openai.beta.threads.messages.list(thread_id=thread_id)
        final_answer = messages.data[0].content[0].text.value
    elif run.status == "failed":

        if hasattr(run, 'last_error') and run.last_error is not None:
            error_message = run.last_error.message
        else:
            error_message = "No error message found..."

        print(f"Run {run.id} failed! Status: {run.status}\n  thread_id: {run.thread_id}\n  assistant_id: {run.assistant_id}\n  error_message: {error_message}")
        print(str(run))
    else:
        print(f"Unexpected run status: {run.status}")
    
    return {
        "thread_id": thread_id,
        "response": final_answer,
        "message_received": message
    }

# Retrieve a conversation history based on the thread ID, 5 messages from the user, 5 from the assistant
@app.get("/conversation-history/")
async def conversation_history(thread_id: str):
    """
    Retrieve the conversation history for a specific thread.

    Args:
        thread_id (str): The ID of the conversation thread.

    Returns:
        dict: A dictionary containing the thread ID and a list of conversation messages, including both user and assistant messages.
    """

    # Fill the message history with dummy messages
    user_messages = [f"User message {i} in thread {thread_id}" for i in range(1, 6)]
    assistant_messages = [f"Assistant message {i} in thread {thread_id}" for i in range(1, 6)]
    conversation_history = []
    for i in range(5):
        conversation_history.append({"sender": "user", "content": user_messages[i]})
        conversation_history.append({"sender": "assistant", "content": assistant_messages[i]})

    return {
        "thread_id": thread_id,
        "conversation_history": conversation_history
    }