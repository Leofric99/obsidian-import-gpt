import os
import json


def get_chat_key(chat):
    if isinstance(chat, dict):
        return str(chat.get("id") or chat.get("create_time"))
    return str(chat)


def extract_chats(export_folder):

    conversations_path = os.path.join(export_folder, "conversations.json")
    if not os.path.isfile(conversations_path):
        print(f"No conversations.json found in {export_folder}")
        return {}

    with open(conversations_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        return data
    

def log_chats_to_cache(chat_dict):
    cache_file = ".cache/seen_chats.json"
    os.makedirs(os.path.dirname(cache_file), exist_ok=True)
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(chat_dict, f, ensure_ascii=False, indent=2)


def extract_conversation(item, conversation_id=1):
    mapping = item["mapping"]
    root_id = "client-created-root"
    convo = []

    if root_id not in mapping:
        raise ValueError("Could not find root message")

    current_id = mapping[root_id]["children"][0] if mapping[root_id]["children"] else None

    while current_id:
        node = mapping[current_id]
        message = node.get("message")
        if message and "author" in message and "role" in message["author"] and message["author"]["role"] != "":
            role = message["author"]["role"]
            parts = message["content"].get("parts", [])
            text = "\n".join(parts)

            # Only include user and assistant messages in alternation, and skip empty messages
            if role in {"user", "assistant"} and text.strip():
                convo.append({
                    "role": role,
                    "text": text,
                    "conversation_id": conversation_id  # add conversation_id here
                })

        # Traverse linearly to the next message in the chain
        children = node.get("children", [])
        current_id = children[0] if children else None

    # Now enforce strict alternation: user -> assistant -> user -> assistant
    filtered = []
    expecting = "user"
    for msg in convo:
        if msg["role"] == expecting:
            filtered.append(msg)
            expecting = "assistant" if expecting == "user" else "user"

    return filtered



def main():

    cache_file = ".cache/seen_chats.json"
    input_folder = "input"
    export_folder = ""

    if not os.path.isdir(input_folder) or not os.listdir(input_folder):
        export_folder = input(f"Please enter the location of your ChatGPT export folder:\n>")

    if export_folder != "":
        print(f"Importing from {export_folder}...")

    else:
        subfolders = [f for f in os.listdir(input_folder) if os.path.isdir(os.path.join(input_folder, f))]
        if not subfolders:
            print("No folders found inside the input directory.")
            return
        export_folder = os.path.join(input_folder, subfolders[0])

    chat_dict = extract_chats(export_folder)

    seen_chats = {}
    if os.path.isfile(cache_file):
        with open(cache_file, "r", encoding="utf-8") as f:
            seen_chats = json.load(f)

    seen_keys = set(get_chat_key(chat) for chat in seen_chats.values()) if isinstance(seen_chats, dict) else set()
    new_chats_list = [chat for chat in chat_dict if get_chat_key(chat) not in seen_keys]

    # For caching, convert list to dict keyed by chat key
    new_chats = {get_chat_key(chat): chat for chat in new_chats_list}

    if not new_chats:
        print("All chats already present in cache.")
    else:
        print(f"Found {len(new_chats)} new chat(s) not present in cache.")
        # Only assign unseen chats to chat_dict
        chat_dict = new_chats

    for item in chat_dict.values():
        chat = extract_conversation(item)
        for statement in chat:
            print(f"Role: {statement['role']}, Text: {statement['text']}, Conversation ID: {statement['conversation_id']}")
            print("\n---\n")
            input()


    # log_chats_to_cache(chat_dict)


if __name__ == "__main__":
    main()