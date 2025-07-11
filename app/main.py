from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pika
import json
import traceback
import requests
from datetime import datetime

app = FastAPI()

class Task(BaseModel):
    title: str
    description: str

class ChatRequest(BaseModel):
    message: str

def send_to_queue(task_data):
    connection = pika.BlockingConnection(pika.ConnectionParameters("rabbitmq"))
    channel = connection.channel()
    channel.queue_declare(queue="task_queue")
    channel.basic_publish(
        exchange='',
        routing_key='task_queue',
        body=json.dumps(task_data)
    )
    connection.close()

@app.post("/submit-task")
async def submit_task(task: Task):
    try:
        send_to_queue(task.model_dump())
        return {"message": "Task submitted successfully"}
    except Exception as e:
        print(e) 
        print("Task failed to send to queue.")

@app.post("/chat")
async def chat(chat_request: ChatRequest):
    
    chat_data = {
        "message": chat_request.message,
        "timestamp": str(datetime.now()),
        "type": "chat_request"
    }
    send_to_queue(chat_data)
    return {"message": "Chat request submitted to queue successfully"}
        
