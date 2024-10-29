# home/consumers.py
import json
import pymysql
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async

class ChatConsumer(AsyncWebsocketConsumer):
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        # Assuming advocate_id and client_id are passed correctly
        client_id = self.scope['url_route']['kwargs']['client_id']
        advocate_id = self.scope['url_route']['kwargs']['advocate_id']

        # Debug: Check if receive method is working
        print(f"Received message: {message} from client {client_id} to advocate {advocate_id}")

        # Call the save_message function to insert the message into the database
        self.save_message(client_id, advocate_id, message)

        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message
            }
        )

    def save_message(self, client_id, advocate_id, message):
        # Debug: Check if method is called
        print("save_message method called")
        
        try:
            # Establish connection to MySQL database
            connection = pymysql.connect(
                host='localhost',
                user='root',
                password='',
                db='legal_advisor',
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor
            )
            print("Database connection established")

            try:
                with connection.cursor() as cursor:
                    sql = """
                    INSERT INTO tbl_chat (sender_id, receiver_id, message, timestamp, is_read)
                    VALUES (%s, %s, %s, NOW(), 0)
                    """
                    print(f"Inserting into DB: advocate_id={advocate_id}, client_id={client_id}, message={message}")
                    cursor.execute(sql, (advocate_id, client_id, message))
                connection.commit()
                print("Message inserted into DB")

            except Exception as e:
                print(f"Error executing SQL: {e}")

        except Exception as e:
            print(f"Error connecting to database: {e}")

        finally:
            connection.close()
            print("Database connection closed")


    # Receive message from room group
    async def chat_message(self, event):
        message = event['message']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message
        }))
