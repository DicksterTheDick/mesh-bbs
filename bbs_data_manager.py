# bbs_data_manager.py (REVISED)

import json
import time
import os

# Define the file path for persistent message storage
BBS_DATA_FILE = 'bbs_messages.json'

# NOTE: This should match auto_responder.py, but is included here for data integrity.
TOPIC_KEYS = ['G', 'N', 'T', 'O', 'H'] 

class BBSData:
    """
    Manages the message board data, including loading from and saving to a JSON file.
    It keeps the data structure in memory for fast access.
    """
    def __init__(self, page_size=5):
        # page_size defines how many messages are displayed per page when reading a topic
        self.page_size = page_size
        self._user_id = "0000"  # Temporary placeholder for the current poster
        self.messages = {}       # The main data structure: {'TopicID': [list of message dicts]}
        self.load_data()

    @property
    def user_id(self):
        """Getter for the user ID."""
        return self._user_id

    @user_id.setter
    def user_id(self, new_id):
        """Setter for the user ID (set by the auto_responder before posting)."""
        self._user_id = new_id

    def _get_welcome_message(self):
        """
        Creates the pre-canned welcome message structure.
        """
        return {
            # Use a generic or system ID for the welcome message
            'user_id': 'SYSOP', 
            'timestamp': time.time(),
            # Max 28 chars for subject
            'subject': 'Welcome to the Mesh-BBS!', 
            # Max 160 chars for body (for safe single-chunk reading)
            'body': 'Hello, and welcome to the Mesh BBS! This is a decentralized message board running on the Meshtastic network. Enjoy connecting with other nodes.', 
        }

    def _get_initial_data_structure(self):
        """
        Creates an empty data structure for all defined topics.
        """
        initial_data = {k: [] for k in TOPIC_KEYS}
        return initial_data
        
    def load_data(self):
        """Loads messages from the JSON persistence file, starting fresh with welcome message if not found."""
        
        loaded_data = None
        if os.path.exists(BBS_DATA_FILE):
            try:
                with open(BBS_DATA_FILE, 'r') as f:
                    loaded_data = json.load(f)
                
                print(f"BBS Data Manager: Loaded {sum(len(v) for v in loaded_data.values())} messages from {BBS_DATA_FILE}")
            except (json.JSONDecodeError, IOError) as e:
                print(f"BBS Data Manager: Error loading data ({e}). Starting with fresh structure and welcome message.")
                loaded_data = None
        else:
            print("BBS Data Manager: No message file found. Starting fresh with welcome message.")

        # 1. Start with an empty structure for all topics
        self.messages = self._get_initial_data_structure()
        
        # 2. Update with all messages from the file if loaded successfully
        if loaded_data:
            for topic_id, messages in loaded_data.items():
                if topic_id in self.messages and messages:
                    # NOTE: This replaces the empty list with the loaded messages
                    self.messages[topic_id] = messages
        
        # 3. CRITICAL: Add the welcome message ONLY IF 'G' is currently empty (first run or file wipe)
        if not self.messages.get('G'):
            self.messages['G'].append(self._get_welcome_message())
            print("BBS Data Manager: Added default welcome message to General Chat.")

    def save_data(self):
        """Saves the current messages to the JSON persistence file."""
        try:
            with open(BBS_DATA_FILE, 'w') as f:
                json.dump(self.messages, f, indent=4)
        except IOError as e:
            print(f"BBS Data Manager: Error saving data: {e}")


    def post_message(self, topic_id: str, subject: str, body: str):
        """
        Creates a new message and prepends it to the specified topic list.
        """
        if topic_id not in self.messages:
            print(f"BBS Data Manager: Error: Invalid topic ID {topic_id}")
            return

        new_message = {
            'timestamp': time.time(),
            'user_id': self._user_id,
            'subject': subject,
            'body': body
        }

        # Prepend the message to the list so the newest messages are read first
        self.messages[topic_id].insert(0, new_message)
        print(f"BBS Data Manager: New message posted to topic {topic_id} by {self._user_id[-4:]}")


# The unused get_topic_messages method has been REMOVED.

# Example usage (for testing purposes, not run during normal operation)
if __name__ == '__main__':
    # Delete the old file to force the welcome message to appear for testing
    if os.path.exists(BBS_DATA_FILE):
        os.remove(BBS_DATA_FILE)
        print(f"Removed {BBS_DATA_FILE} for fresh start test.")

    bbs = BBSData()
    
    # Check if the welcome message is present
    welcome_msg = bbs.messages.get('G', [])[-1] # Welcome is now at the END
    print(f"\nWelcome Message Check: Subject='{welcome_msg['subject']}'")
    
    bbs.user_id = "f00b299e"
    bbs.post_message('G', 'User Test Post 1', 'This message should appear before the welcome message.')
    
    # Save the data to disk
    bbs.save_data()
    
    # Reload to test persistence
    new_bbs = BBSData()
    print(f"\nReload check: Total messages in 'G': {len(new_bbs.messages.get('G', []))}")
    
    # Check the order: New post (index 0) should be before welcome (index 1)
    print(f"Message 1 (newest): {new_bbs.messages.get('G', [])[0]['subject']}")
    print(f"Message 2 (oldest): {new_bbs.messages.get('G', [])[1]['subject']}")
