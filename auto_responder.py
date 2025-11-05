# auto_responder.py (FINAL VERIFIED - Games Center with Blackjack & Minesweeper)

# -*- coding: utf-8 -*-
import meshtastic.serial_interface
from pubsub import pub
import time
import logging
import sys
from bbs_data_manager import BBSData
from math import ceil
import argparse

# --- NEW: Import the games module for constants and handlers ---
import games
# --------------------------------------------------------------

# --- CONFIGURATION & CONSTANTS ---

# --- REVISED WELCOME MESSAGE (G is now active) ---
MAIN_MENU_ASCII = """
-=( MESH-BBS )=-
---------------------------

[B] BBS & Messaging
[G] Games Center
[X] Logoff / Exit

---------------------------"""
# ----------------------------------

# ... (LOGOFF_ASCII, BBS_SECTION_MENU_ASCII remain the same) ...
LOGOFF_ASCII = """
▓▒░ SESSION ENDED! ░▒▓
      THANKS FOR CALLING
              MESH-BBS

          You've Logged Off
▓▒░     Successfully!     ░▒▓
"""

BBS_SECTION_MENU_ASCII = """
-=( Message Board )=-
----------------------------------

[A] Topic Activity Summary
[R] Read Public Board
[P] Post New Message
[M] Back to Main Menu

----------------------------------"""

# --- REQUEST 1: UPDATED READ_TOPIC_MENU_ASCII ---
READ_TOPIC_MENU_ASCII = """
-=( Read Topic )=-
---------------------------

[G] General Chat
[N] News & Events
[T] Tech & Mesh Info
[O] Off Topic / Fun
[H] Help Desk

[B] Board Menu

---------------------------"""

# --- REQUEST 2: UPDATED POST_TOPIC_MENU_ASCII ---
POST_TOPIC_MENU_ASCII = """
-= POST MESSAGE =-
Select Topic:

[G] General
[N] News
[T] Tech Info
[O] Off Topic
[H] Help

[B] Back to Board

------------------"""


MESHTASTIC_CHAR_LIMIT = 250

TOPIC_NAMES = {
    'G': 'General Chat',
    'N': 'News & Events',
    'T': 'Tech & Mesh Info',
    'O': 'Off Topic / Fun',
    'H': 'Help Desk'
}

# --- GLOBAL USER STATE TRACKING (THE MEMORY) ---
USER_STATES = {}


# Initialize the BBS Data Handler globally
bbs_data_handler = BBSData(page_size=4)


# --- HELPER FUNCTION (CRITICAL for long replies) ---

def chunk_and_send(interface, destId, message, skip_headers=False):
    """
    Splits a message into safe 190-character chunks and sends them sequentially.
    Includes a 2.5 second delay between chunks to prevent packet dropping.
    """
    max_chunk_size = 190 
    min_trailing_chunk_size = 10
    
    lines = message.split('\n')
    current_chunk = ""
    chunks = []
    
    for line in lines:
        line_with_newline = line + "\n"
        
        if len(current_chunk) + len(line_with_newline) > max_chunk_size:
            if current_chunk:
                chunks.append(current_chunk)
            current_chunk = line_with_newline
        else:
            current_chunk += line_with_newline
            
    if current_chunk:
        chunks.append(current_chunk)

    if len(chunks) > 1:
        last_chunk = chunks[-1]
        
        if len(last_chunk) <= min_trailing_chunk_size:
            second_to_last = chunks[-2]
            
            if len(second_to_last) + len(last_chunk) <= max_chunk_size:
                chunks[-2] += last_chunk
                chunks.pop() 

    total_chunks = len(chunks)
    
    print(f"DEBUG: Message is {len(message)} chars, final split into {total_chunks} chunks.")
    print(f"** SENDING REPLY to {destId} ({total_chunks} Chunks) **")
    
    for i, chunk in enumerate(chunks):
        
        if total_chunks > 1 and not skip_headers:
            header = f"[{i+1}/{total_chunks}] "
            final_message = header + chunk
        else:
            final_message = chunk 

        interface.sendText(final_message, destinationId=destId)
        
        time.sleep(2.5) 
        
    print("SUCCESS: Reply sent.")
        
# --- COMMAND HANDLERS (Menu-Driven) ---

def handle_read_topic_menu():
    """Returns the Topic Selection Menu."""
    return READ_TOPIC_MENU_ASCII

def handle_activity_summary():
    """
    Generates a summary of total message counts per topic.
    REQUEST 4: Changed menu prompt from [M] to [B].
    """
    reply_lines = [
        "-=( Board Activity Summary )=-",
        "----------------------------------",
    ]
    total_count = 0
    for topic_id, topic_name in TOPIC_NAMES.items():
        count = len(bbs_data_handler.messages.get(topic_id, []))
        total_count += count
        reply_lines.append(f"[{topic_id}] {topic_name:<15}: {count:>4} msgs")
        
    reply_lines.extend([
        "----------------------------------",
        f"Total Messages: {total_count}",
        "[B] Back to Board "
    ])
    return "\n".join(reply_lines)


def handle_read_subject_list(fromId, topic_id, page_num=0):
    """
    Shows a numbered list of message subjects for a given topic/page in a compact format.
    """
    
    if topic_id not in TOPIC_NAMES:
        return f"Invalid Topic ID '{topic_id}'. Use G, N, T, O, or H. Send R to see options."

    topic_messages = bbs_data_handler.messages.get(topic_id, [])
    total_messages = len(topic_messages)
    
    if total_messages == 0:
        topic_name = TOPIC_NAMES[topic_id]
        status_message = f"Topic '{topic_name}' is empty. Select a topic above or [M] for main menu."
        # This menu should NOT be returned here, as the user is likely in the process of
        # reading, so we just return the status and the menu they just left.
        combined_reply = READ_TOPIC_MENU_ASCII.strip() + "\n\n" + status_message
        return combined_reply

    max_page = ceil(total_messages / bbs_data_handler.page_size)
    
    USER_STATES[fromId]['last_topic'] = topic_id
    USER_STATES[fromId]['current_page'] = page_num
    USER_STATES[fromId]['max_pages'] = max_page 
    
    start_index = page_num * bbs_data_handler.page_size
    end_index = start_index + bbs_data_handler.page_size
    messages_on_page = topic_messages[start_index:end_index]
    
    if not messages_on_page:
        return f"Page {page_num + 1} does not exist. Max page is {int(max_page)}.\n\n{READ_TOPIC_MENU_ASCII}"

    reply_lines = [
        f"*{TOPIC_NAMES[topic_id]} - Page {page_num + 1}/{int(max_page)}*",
        "------------------",
    ]
    
    for i, msg in enumerate(messages_on_page):
        message_number = start_index + i + 1
        reply_lines.append(f"[{message_number}] {msg['subject'][:25]} ({msg['user_id'][-4:]})")
        
    has_next_page = (page_num + 1) < max_page
    
    if has_next_page:
        reply_lines.append(f"[N] Next Page")
    
    reply_lines.append(f"[T] Back to Read Topic")
    
    reply_lines.append(f"[B] Board Menu") 
    reply_lines.append("------------------")
        
    return "\n".join(reply_lines)


def handle_read_full_message(topic_id, msg_index):
    """
    Retrieves and formats the full body of a message.
    """
    topic_messages = bbs_data_handler.messages.get(topic_id, [])
    list_index = msg_index - 1
    
    if list_index < 0 or list_index >= len(topic_messages):
        return f"Invalid message number {msg_index} in Topic {topic_id}."
        
    msg = topic_messages[list_index]
    
    timestamp = time.strftime("%d/%b %I:%M%p", time.localtime(msg['timestamp']))
    
    full_body_content = (
        f"--- Msg {msg_index} in {TOPIC_NAMES[topic_id]} ---\n"
        f"From: {msg['user_id'][-4:]}\n"
        f"Date: {timestamp}\n"
        f"Subject: {msg['subject'][:28]}\n"
        f"----------------------------------------\n"
        f"{msg['body']}\n"
        f"----------------------------------------\n"
        f"[B] Board Menu"
    )
    
    return full_body_content


def handle_post_start(fromId):
    USER_STATES[fromId]['state'] = 'posting_topic'
    return POST_TOPIC_MENU_ASCII

def handle_post_topic_select(fromId, command_input):
    topic_id = command_input[0]
    if topic_id not in TOPIC_NAMES:
        return f"Invalid Topic ID '{topic_id}'.\n{POST_TOPIC_MENU_ASCII}"
    USER_STATES[fromId]['topic'] = topic_id
    USER_STATES[fromId]['state'] = 'posting_subject'
    topic_name = TOPIC_NAMES[topic_id]
    return (f"--- Posting in {topic_name} ---\n\n** Subject Max 28 chars. **\nEnter Subject:")

def handle_post_subject(fromId, text):
    subject = text.strip()
    if not subject:
        return "Subject cannot be empty. Please enter Subject:"
    USER_STATES[fromId]['subject'] = subject[:28] 
    
    USER_STATES[fromId]['state'] = 'posting_body_collect'
    USER_STATES[fromId]['body_chunks'] = []
    
    return (
        f"[BODY] Enter Message Body (Chunk 1).\n"
        f"** Send 'END' as a separate message when finished. **"
    )

def handle_post_body_collect(fromId, text):
    """
    Collects multi-line message body until 'END' is received.
    """
    state = USER_STATES[fromId]
    
    if text.upper().strip() == "END":
        return handle_post_body_final(fromId)

    if text.strip():
        state['body_chunks'].append(text.strip())
    
    collected_chunk_number = len(state['body_chunks']) 
    next_chunk_number = collected_chunk_number + 1
    current_body_length = len("\n\n".join(state['body_chunks']))

    return (
        f"Chunk {collected_chunk_number} collected ({current_body_length} chars).\n"
        f"[BODY] Enter Chunk {next_chunk_number} OR Send 'END'."
    )

def handle_post_body_final(fromId):
    """
    Finalizes the post, stitches chunks, saves, and sends confirmation.
    """
    state = USER_STATES[fromId]
    full_body = "\n\n".join(state['body_chunks']) 
    
    if not full_body:
        if 'state' in state: del state['state']
        if 'body_chunks' in state: del state['body_chunks']
        if 'topic' in state: del state['topic']
        if 'subject' in state: del state['subject']
        return "ERROR: Message body cannot be empty. Send P to start a new post."
        
    topic_id = state.get('topic')
    subject = state.get('subject', 'No Subject')
    
    bbs_data_handler.user_id = fromId
    bbs_data_handler.post_message(topic_id, subject, full_body)
    bbs_data_handler.save_data()
    
    if 'state' in state: del state['state'] 
    if 'body_chunks' in state: del state['body_chunks']
    if 'topic' in state: del state['topic']
    if 'subject' in state: del state['subject']
        
    # --- REQUEST 3 FIX: Concise confirmation message ---
    return f"SUCCESS: Posted '{subject}' to '{TOPIC_NAMES[topic_id]}'.\n\nSend [B] for Board Menu."


# --- MESHTASTIC RECEIVE LISTENER (The Command Router) ---

def onReceive(packet, interface):
    """Called by the Meshtastic library when a message is received."""

    if packet.get('decoded', {}).get('portnum') != 'TEXT_MESSAGE_APP':
        return

    fromId = packet.get('fromId', 'Unknown')
    text = packet['decoded']['text']
    
    print(f"\n{'='*40}")
    print(f"** RECEIVED MESSAGE **")
    print(f"From: {fromId}")
    print(f"Text: \"{text}\"")
    print(f"{'='*40}")

    command_input = text.upper().strip()
    words = command_input.split()
    
    reply_message = None
    needs_chunking = False
    skip_headers = False
    command = words[0] if words else ""
    
    if fromId not in USER_STATES:
        USER_STATES[fromId] = {'first_contact': True, 'last_menu': 'MAIN', 'reset_next': False} 
    
    state_data = USER_STATES[fromId]
    current_state = state_data.get('state')
    
    # --- STAGE 1 (UNIVERSAL WAKE UP / POST-LOGOFF CHECK) ---
    if state_data.pop('first_contact', False) or state_data.pop('reset_next', False):
        reply_message = MAIN_MENU_ASCII
        state_data['last_menu'] = 'MAIN'
        
    # --- STAGE 2 (NORMAL COMMAND ROUTING) ---
    else:
        # --- 0. CHECK USER STATE (INTERACTIVE MODE PRIORITY) ---
        if current_state:
            state = current_state
            
            # --- NEW: Check for Game States (PRIORITY) ---
            if state.startswith('game_blackjack_') or state.startswith('game_minesweeper_'):
                reply_message = games.handle_game_command(fromId, command_input, USER_STATES, games.GAMES_MENU_ASCII, MAIN_MENU_ASCII, LOGOFF_ASCII)
                needs_chunking = True
            # --- END NEW GAME CHECK ---
            
            # Allow user to break out of interactive mode (if not a game command)
            if reply_message is None and command in ("M", "X", "B", "Q"):
                
                # Clear all interactive state data
                if 'state' in state_data: del state_data['state']
                if 'body_chunks' in state_data: del state_data['body_chunks']
                if 'topic' in state_data: del state_data['topic']
                if 'subject' in state_data: del state_data['subject']
                if 'game_data' in state_data: del state_data['game_data'] # Clear any remaining game data
                
                if command == "X":
                    reply_message = LOGOFF_ASCII
                    state_data['last_menu'] = 'MAIN'
                    state_data['reset_next'] = True
                elif command == "B":
                    # B in interactive mode (like POST/READ_TOPIC) goes to BBS menu
                    reply_message = BBS_SECTION_MENU_ASCII
                    state_data['last_menu'] = 'BBS'
                
                # Q and M for Games Context
                elif command in ('Q', 'M') and state_data.get('last_menu') == 'GAMES':
                    if command == 'Q':
                        reply_message = games.GAMES_MENU_ASCII
                        state_data['last_menu'] = 'GAMES'
                    else:
                        reply_message = MAIN_MENU_ASCII
                        state_data['last_menu'] = 'MAIN'
                        
                else:
                    reply_message = MAIN_MENU_ASCII
                    state_data['last_menu'] = 'MAIN'
                
                print(f"INFO: User {fromId} exited interactive mode with '{command}'.")
            
            elif reply_message is None:
                if state == 'posting_topic':
                    reply_message = handle_post_topic_select(fromId, command_input)
                elif state == 'posting_subject':
                    reply_message = handle_post_subject(fromId, text)
                elif state == 'posting_body_collect':
                    reply_message = handle_post_body_collect(fromId, text)
        
        # --- SPECIAL HANDLING FOR X COMMAND (Not in Interactive Mode) ---
        elif command == "X":
            if 'last_topic' in state_data: del state_data['last_topic']
            state_data['last_menu'] = 'MAIN'
            state_data['reset_next'] = True
            reply_message = LOGOFF_ASCII
            
        # --- 1. CONTEXTUAL COMMAND HANDLING (N/T for Paging/Navigation) ---
        
        elif state_data.get('last_menu') == 'READ_SUBJECT' and command == 'T':
            reply_message = handle_read_topic_menu()
            state_data['last_menu'] = 'READ_TOPIC'
        
        elif state_data.get('last_menu') == 'READ_SUBJECT' and command == 'N':
            last_topic = state_data.get('last_topic')
            current_page = state_data.get('current_page', 0)
            max_pages = state_data.get('max_pages', 0)
            next_page = current_page + 1
            
            if last_topic and (next_page < max_pages):
                reply_message = handle_read_subject_list(fromId, last_topic, next_page)
                needs_chunking = True
                state_data['last_menu'] = 'READ_SUBJECT'
            else:
                reply_message = "No next page available."
        
        # Case B: User is in the MAIN menu context and sends 'G'
        elif state_data.get('last_menu') == 'MAIN' and command == 'G':
            reply_message = games.GAMES_MENU_ASCII
            state_data['last_menu'] = 'GAMES'
        
        # --- NEW: Handle Game Selections from the GAMES Menu ---
        elif state_data.get('last_menu') == 'GAMES':
            if command == 'B':
                reply_message = games.start_blackjack(fromId, USER_STATES, games.GAMES_MENU_ASCII, MAIN_MENU_ASCII, LOGOFF_ASCII)
                needs_chunking = True
            elif command == 'W':
                reply_message = games.start_minesweeper(fromId, USER_STATES)
                needs_chunking = True
            elif command == 'M':
                reply_message = MAIN_MENU_ASCII
                state_data['last_menu'] = 'MAIN'
            else:
                reply_message = f"Invalid command in Games Center. Select a game or [M] Back to Main Menu."
                reply_message += "\n\n" + games.GAMES_MENU_ASCII
                state_data['last_menu'] = 'GAMES'
        # --- END NEW GAME SELECTION HANDLING ---

        # Case C: Single Number Read
        elif command.isdigit() and len(words) == 1:
            msg_num = int(command)
            last_topic = state_data.get('last_topic') 
            
            if last_topic:
                reply_message = handle_read_full_message(last_topic, msg_num)
                needs_chunking = True 
            else:
                reply_message = f"** COMMAND '{command}' **\nTo read a message, first send R [Topic] or B for the menu."
                
        # --- 2. MAJOR MENU NAVIGATION (B now handles BBS menu navigation) ---
        
        elif command == "R":
            if len(words) == 1:
                reply_message = handle_read_topic_menu()
                state_data['last_menu'] = 'READ_TOPIC'
            
            elif len(words) >= 2 and words[1] in TOPIC_NAMES:
                topic_id = words[1]
                total_messages = len(bbs_data_handler.messages.get(topic_id, []))
                
                page_or_msg_num = 0
                if len(words) == 3:
                    try:
                        page_or_msg_num = int(words[2])
                    except ValueError:
                        reply_message = "Invalid page/message number. Example: R G 2 or R G 5"
                
                if reply_message is None:
                    if page_or_msg_num >= 1 and page_or_msg_num <= total_messages: 
                        reply_message = handle_read_full_message(topic_id, page_or_msg_num)
                        needs_chunking = True
                    else:
                        page_num = page_or_msg_num - 1 if page_or_msg_num > 0 else 0
                        reply_message = handle_read_subject_list(fromId, topic_id, page_num)  
                        needs_chunking = True
                        state_data['last_menu'] = 'READ_SUBJECT'
            else:
                reply_message = "Invalid READ command format or topic ID. Showing topic selection."
                reply_message += "\n\n" + READ_TOPIC_MENU_ASCII
                state_data['last_menu'] = 'READ_TOPIC'

        elif command in ("P", "POST"):
            reply_message = handle_post_start(fromId)
            state_data['last_menu'] = 'BBS'
            
        elif command == "B":
            # B now handles returning to the BBS section menu (Message Board)
            reply_message = BBS_SECTION_MENU_ASCII
            state_data['last_menu'] = 'BBS'
        
        elif command == "A":
            # A returns the Activity Summary, which now contains the [B] prompt
            reply_message = handle_activity_summary()
            needs_chunking = True
            state_data['last_menu'] = 'BBS'

        elif command == "M":
            reply_message = MAIN_MENU_ASCII
            state_data['last_menu'] = 'MAIN'
            
        # --- 3. Single-Letter Topic Selection ---
        
        elif command in TOPIC_NAMES and len(words) == 1:
            is_nav_command = (state_data.get('last_menu') == 'READ_SUBJECT' and command in ('N', 'T'))
            
            if not is_nav_command and state_data.get('last_menu') in ('READ_TOPIC', 'READ_SUBJECT', 'BBS'):
                reply_message = handle_read_subject_list(fromId, command, 0)  
                
                if READ_TOPIC_MENU_ASCII.strip() in reply_message and "Topic" in reply_message and "is empty" in reply_message:
                    skip_headers = True 
                
                needs_chunking = True
                state_data['last_menu'] = 'READ_SUBJECT'
            else:
                reply_message = None

        # --- 4. Default Fallback ---
        if reply_message is None:
            print(f"** COMMAND '{command_input}' UNRECOGNIZED. Sending Main Menu **")
            reply_message = MAIN_MENU_ASCII
            state_data['last_menu'] = 'MAIN'
    
    
    # --- FINAL MESSAGE SENDING LOGIC ---
    if reply_message:
        if needs_chunking or len(reply_message) > 200: 
            chunk_and_send(interface, fromId, reply_message, skip_headers=skip_headers)
        else:
            print(f"** SENDING REPLY to {fromId} (Single Packet) **")
            interface.sendText(reply_message, destinationId=fromId)
            print("SUCCESS: Reply sent.")
        
# --- ARGPARSE SETUP ---
def parse_args():
    """Parses command line arguments."""
    parser = argparse.ArgumentParser(
        description="Meshtastic BBS Auto Responder Service.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        '--debug', 
        '-d', 
        action='store_true', 
        help=(
            "Enables verbose Meshtastic debugging output.\n"
            "Use: python3 auto_responder.py --debug"
        )
    )
    return parser.parse_args()

# --- MAIN INTERFACE LOOP ---
def main():
    """Initializes the connection and starts listening."""
    args = parse_args()

    if args.debug:
        log_level = logging.DEBUG
        meshtastic_log_level = logging.DEBUG
        print("INFO: Verbose DEBUG logging enabled by --debug flag.")
    else:
        log_level = logging.INFO
        meshtastic_log_level = logging.INFO
    
    logging.basicConfig(
        level=log_level,
        format='[%(levelname)s] %(name)s: %(message)s',
        stream=sys.stdout
    )
    logging.getLogger('pubsub').setLevel(logging.WARNING)
    logging.getLogger('meshtastic').setLevel(meshtastic_log_level)


    interface = None
    try:
        print("\n--- Starting Meshtastic BBS Command Server ---")
        
        bbs_data_handler.load_data() 
        
        interface = meshtastic.serial_interface.SerialInterface()
        
        print("SUCCESS: Connected to Meshtastic node. Waiting 3 seconds for node data sync...")
        time.sleep(3)

        try:
            node_info_dict = interface.localNode.asdict()
            local_name = node_info_dict.get('user', {}).get('longName') or \
                         node_info_dict.get('user', {}).get('shortName') or \
                         f"Node-0x{interface.myInfo.my_node_num:x}"
        except Exception:
            local_name = "Local Node"
        
        pub.subscribe(onReceive, "meshtastic.receive")
        
        print(f"SUCCESS: Connected to node: {local_name}. Now listening for commands...")
        
        print("\n-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-")
        print("INFO: To exit the BBS service, press Ctrl+C at any time.")
        
        if not args.debug:
            print("INFO: Logs are filtered for clarity. To enable verbose debug logs,")
            print("      restart the script with: python3 auto_responder.py --debug")
        print("-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-")
        
        print("----------------------------------------------------------\n")

        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n\n" + "=" * 50)
        print("Keyboard Interrupt Detected. Initiating shutdown...")
        print("=" * 50)
        
        SHUTDOWN_MESSAGES = [
            "[Service Termination Acknowledged] Disconnecting from Mesh Node. The Meshtastic BBS is now offline.",
            "[BBS OFFLINE] To restart the service, run: python3 auto_responder.py",
            "[Exit Complete] All background threads have ceased. You may now close this terminal window."
        ]
        
        for msg in SHUTDOWN_MESSAGES:
            print(msg)
            sys.stdout.flush() 
            time.sleep(3)
            
        print("=" * 50)

    except Exception as e:
        print(f"\nFATAL ERROR: Could not connect to Meshtastic node. Please check USB connection.")
        if args.debug or 'timeout' in str(e).lower() or 'serial' in str(e).lower():
            logging.exception(f"Detailed connection error:")
        else:
             print(f"Details: {e}")
    finally:
        if interface:
            pass

if __name__ == "__main__":
    main()
