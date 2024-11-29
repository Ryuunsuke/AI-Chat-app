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

def startup(cursor):
	cursor.execute('''
	CREATE TABLE IF NOT EXISTS users (
		id INTEGER PRIMARY KEY AUTOINCREMENT,
		name TEXT NOT NULL,
		age INTEGER,
		city TEXT
	)
	''')

def return_name(cursor):
    cursor.execute('SELECT name FROM users WHERE age = 25')
    names = cursor.fetchall()
    return names

def return_integer(cursor):
    cursor.execute("SELECT age FROM users WHERE city = 'Chicago'")
    ages = cursor.fetchall()
    return ages

def insert_rec(cursor):
    cursor.execute('''
    INSERT INTO users (name, age, city)
    VALUES ('Jake', 20, 'California')
    ''')
    rec = read_rec(cursor)
    return rec

def read_rec(cursor):
    cursor.execute('''
    SELECT name, age, city FROM users WHERE name = 'Jake'
    ''')
    rec = cursor.fetchall()
    return rec

def update_rec(cursor):
    cursor.execute('''
    UPDATE users
    SET name = 'James'
    WHERE name = 'Jake'
    ''')
    rec = read_rec(cursor)
    return rec

def delete_rec(cursor):
    cursor.execute('''
    DELETE FROM users
    WHERE name = 'Jake'
    ''')
    res = "Successfully deleted"
    return res
 
def add_message_to_thread(thread_id, message_content):
	
    # Check for active runs
    active_runs = openai.beta.threads.runs.list(thread_id=thread_id)
    for run in active_runs.data:
        if run.status not in ["completed", "failed"]:
            print(f"Run {run.id} is still active. Waiting for completion...")
            # Wait for run to complete
            while run.status not in ["completed", "failed"]:
                time.sleep(5)
                run = openai.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run.id)

            if run.status == "failed":
                print(f"Run {run.id} failed. Proceeding to add the message.")
            elif run.status == "completed":
                print(f"Run {run.id} completed. Proceeding to add the message.")
    
    # Add the message to the thread
    message = openai.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=message_content
    )
    return message