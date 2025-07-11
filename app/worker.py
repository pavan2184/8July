import pika
import json
import requests
from db import collection

def callback(ch, method, properties, body):
    data = json.loads(body)
    print("Received message:", data)
    
    if data.get("type") == "chat_request":
        print("Processing chat request...")
        process_chat_request(data)
    else:
        
        print("Processing regular task...")
        collection.insert_one(data)
        print("Stored in MongoDB")

def process_chat_request(chat_data):
    
    try:
        response = requests.post(
            "http://ollama:11434/api/generate",
            json={
                "model": "medical-mistral",
                "prompt": chat_data["message"],
                "stream": True
            },
            stream=True,
            timeout=30
        )
        if response.status_code == 200:
            # Collect the full response from stream
            full_response = ""
            for line in response.iter_lines():
                if line:
                    try:
                        data = json.loads(line.decode('utf-8'))
                        if 'response' in data:
                            full_response += data['response']
                        if data.get('done', False):
                            break
                    except json.JSONDecodeError:
                        continue
            
            print(f"AI Response: {full_response}")

            chat_interaction = {
                "user_message": chat_data["message"],
                "ai_response": full_response,
                "timestamp": chat_data.get("timestamp"),
                "type": "chat_interaction"
            }
            collection.insert_one(chat_interaction)
            return full_response
        else:
            print(f"Ollama API error: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error processing chat request: {e}")
        return None



def main():
    connection = pika.BlockingConnection(pika.ConnectionParameters("rabbitmq"))
    channel = connection.channel()
    channel.queue_declare(queue="task_queue")
    channel.basic_consume(queue="task_queue", on_message_callback=callback, auto_ack=True)
    print("worker started")
    channel.start_consuming()

if __name__ == "__main__":
    main()
