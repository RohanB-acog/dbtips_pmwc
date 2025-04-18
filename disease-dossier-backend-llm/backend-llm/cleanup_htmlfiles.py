import os
import json
from pathlib import Path
from redis import Redis

# Path to your static directory
STATIC_DIR = Path("static")  

def list_conversations(redis_conn: Redis) -> list:
    """
    Fetch all conversations from Redis.
    """
    try:
        cursor = '0'
        conversations = []
        while cursor != 0:  
            cursor, keys = redis_conn.scan(cursor=cursor, match="conversation:*")
            for key in keys:
                conversation_data = redis_conn.get(key)
                if conversation_data:
                    conversation = json.loads(conversation_data)
                    conversations.append(conversation)
        return conversations
    except Exception as e:
        print(f"An error occurred while fetching conversations: {e}")
        return []

def cleanup_unused_files(redis_conn: Redis):
    """
    Deletes unused HTML files in the static directory.
    """
    try:
        conversations = list_conversations(redis_conn)
        saved_urls = set()

        for conversation in conversations:
            for message in conversation.get("chat", []):
                if message.get("role") == "assistant":
                    svg_urls = message.get("message", {}).get("svgUrls", [])
                    for url in svg_urls:
                        absolute_path = (STATIC_DIR.parent / url.lstrip("/")).resolve()
                        saved_urls.add(absolute_path)

        all_files = {file.resolve() for file in STATIC_DIR.glob("*.html")}

        print(f"Saved URLs (absolute): {saved_urls}")
        print(f"All files (absolute): {all_files}")
        unused_files = all_files - saved_urls

        print(f"Unused files (absolute): {unused_files}")

        # for file in unused_files:
        #     try:
        #         file.unlink() 
        #         print(f"Deleted unused file: {file}")
        #     except Exception as e:
        #         print(f"Failed to delete file {file}: {e}")

        print("Cleanup completed.")
    except Exception as e:
        print(f"An error occurred during cleanup: {e}")

if __name__ == "__main__":
    redis_conn =  Redis(host='127.0.0.1', port=6379, db=0, decode_responses=True)
    cleanup_unused_files(redis_conn)
