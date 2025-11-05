# games.py (Blackjack Implementation - FINAL with Manual Betting & Q to Games Menu)

import random

# --- GAME CONSTANTS & CONFIGURATION ---
CARDS = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
SUITS = ['C', 'D', 'H', 'S'] 
STARTING_CHIPS = 100 
# -------------------------------------

# --- NEW: GAMES MENU CONSTANT ---
GAMES_MENU_ASCII = """
-=( Games Center )=-
----------------------------------

[B] Blackjack
[V] Video Poker (Coming Soon!)

[M] Back to Main Menu

----------------------------------"""
# --------------------------------

# --- BLACKJACK HELPER FUNCTIONS ---

def create_and_shuffle_deck():
    """Creates a new 52-card deck and shuffles it."""
    deck = [c for c in CARDS for s in SUITS] 
    random.shuffle(deck)
    return deck

def get_hand_value(hand):
    """Calculates the value of a Blackjack hand, handling Aces (1 or 11)."""
    value = 0
    num_aces = 0
    
    for card in hand:
        # Check for 10, Jack, Queen, or King (all value 10)
        if card in ('10', 'J', 'Q', 'K'):
            value += 10
        elif card == 'A':
            value += 11
            num_aces += 1
        else:
            # All other cards (2-9) are numeric
            try:
                value += int(card)
            except ValueError:
                print(f"ERROR: Invalid card '{card}' found in hand!")
            
    # Adjust for Aces if the value is over 21
    while value > 21 and num_aces > 0:
        value -= 10 # Change Ace from 11 to 1
        num_aces -= 1
        
    return value

# --- BLACKJACK GAME LOGIC ---

def start_blackjack(fromId, USER_STATES, GAMES_MENU_ASCII, MAIN_MENU_ASCII, LOGOFF_ASCII):
    """
    Initializes the Blackjack game state, sets up chips, and prompts for a bet.
    """
    state_data = USER_STATES[fromId]
    
    # Retrieve chips or initialize to the STARTING_CHIPS value (100)
    chips = state_data.get('game_data', {}).get('chips', STARTING_CHIPS)
    
    # Store initial/updated game state for betting
    state_data['state'] = 'game_blackjack_betting'
    state_data['last_menu'] = 'GAME_ACTIVE' 
    
    # Initialize game data structure if it doesn't exist (e.g., first time loading game)
    if 'game_data' not in state_data:
        state_data['game_data'] = {
            'deck': [], 
            'player_hand': [],
            'dealer_hand': [],
            'chips': chips, 
            'bet': 0, 
        }
    else:
        # If it exists, ensure it has the current chip count
        state_data['game_data']['chips'] = chips

    # Check for 0 chips
    if chips <= 0:
         # Clear state and return to games menu (Q equivalent logic)
        del state_data['state']
        if 'game_data' in state_data:
            del state_data['game_data']
        state_data['last_menu'] = 'GAMES' # Return to Games Menu!
        return f"** YOU ARE OUT OF CHIPS! **\n{GAMES_MENU_ASCII}" # Show games menu after message


    # Prompt for bet
    reply = (
        f"** BLACKJACK (Chips: {chips}) **\n"
        f"Enter your bet amount (1 - {chips}):\n"
        f"[Q] Quit to Games Menu"
    )
    return reply


def process_blackjack_betting(fromId, command_input, USER_STATES, GAMES_MENU_ASCII, MAIN_MENU_ASCII, LOGOFF_ASCII):
    """
    Handles the user's numeric bet input, validates it, and starts the game.
    """
    state_data = USER_STATES[fromId]
    game_data = state_data['game_data']
    chips = game_data['chips']
    
    # 1. Validate Command as a Number
    try:
        bet = int(command_input.split()[0])
    except ValueError:
        return f"Invalid input. Please enter a whole number between 1 and {chips} to bet.\n[Q] Quit to Games Menu"

    # 2. Validate Bet Amount
    if bet <= 0:
        return f"Bet must be at least 1 chip.\nEnter your bet amount (1 - {chips}):\n[Q] Quit to Games Menu"
    
    if bet > chips:
        return f"You only have {chips} chips. Bet cannot exceed your chips.\nEnter your bet amount (1 - {chips}):\n[Q] Quit to Games Menu"
        
    # 3. Valid Bet - Set State and Deal Cards
    
    # Setup deck and deal cards
    deck = create_and_shuffle_deck()
    player_hand = [deck.pop(), deck.pop()]
    dealer_hand = [deck.pop(), deck.pop()]
    player_value = get_hand_value(player_hand)

    # Update game_data with the new hand and bet
    game_data['deck'] = deck
    game_data['player_hand'] = player_hand
    game_data['dealer_hand'] = dealer_hand
    game_data['bet'] = bet # Store the accepted bet
    
    # Transition to the playing state
    state_data['state'] = 'game_blackjack_turn'

    # Check for immediate Player Blackjack
    if player_value == 21:
        # Pass to the final processor to handle dealer and payout
        return _process_blackjack_end(fromId, USER_STATES, GAMES_MENU_ASCII, MAIN_MENU_ASCII, LOGOFF_ASCII, immediate_blackjack=True)

    # Format the initial deal message
    reply = (
        f"** BLACKJACK (Chips: {chips}) **\n"
        f"Bet: {bet}\n"
        f"Dealer: [{dealer_hand[0]}, ?]\n"
        f"You: {player_hand} (Score: {player_value})\n"
        f"Commands: [H] Hit, [S] Stand, [Q] Quit to Games Menu"
    )
    return reply


def process_blackjack_turn(fromId, command_input, USER_STATES, GAMES_MENU_ASCII, MAIN_MENU_ASCII, LOGOFF_ASCII):
    """Handles H (Hit), S (Stand), and checks for busts/wins/ends the game."""
    
    state_data = USER_STATES[fromId]
    game_data = state_data['game_data']
    command = command_input[0]
    
    # Retrieve current chips and bet for display
    bet = game_data['bet']

    if command == 'H':
        # Player Hits
        if not game_data['deck']:
            return "ERROR: Deck is empty. Cannot Hit. Use S to Stand.\n[Q] Quit to Games Menu"
            
        new_card = game_data['deck'].pop()
        game_data['player_hand'].append(new_card)
        player_value = get_hand_value(game_data['player_hand'])

        if player_value > 21:
            # Player Busts - Game Over
            return _process_blackjack_end(fromId, USER_STATES, GAMES_MENU_ASCII, MAIN_MENU_ASCII, LOGOFF_ASCII, result_message="BUST! You went over 21.")
        
        # Player continues
        reply = (
            f"You Hit and got a {new_card}.\n"
            f"Dealer: [{game_data['dealer_hand'][0]}, ?]\n"
            f"You: {game_data['player_hand']} (Score: {player_value})\n"
            f"Commands: [H] Hit, [S] Stand, [Q] Quit to Games Menu"
        )
        return reply

    elif command == 'S':
        # Player Stands - Dealer plays
        return _process_blackjack_end(fromId, USER_STATES, GAMES_MENU_ASCII, MAIN_MENU_ASCII, LOGOFF_ASCII)

    elif command == 'Q':
        # Quit Game (cleanup and return to Games Menu)
        del state_data['state']
        if 'game_data' in state_data:
            # We save the chips, but clear the hand/deck/bet data
            del state_data['game_data']
        state_data['last_menu'] = 'GAMES'
        return GAMES_MENU_ASCII
        
    else:
        player_value = get_hand_value(game_data['player_hand'])
        return (f"Invalid command. Your hand: {game_data['player_hand']} (Score: {player_value})\n"
                f"Bet: {bet}. Use [H] Hit, [S] Stand, or [Q] Quit to Games Menu.")


def _process_blackjack_end(fromId, USER_STATES, GAMES_MENU_ASCII, MAIN_MENU_ASCII, LOGOFF_ASCII, result_message=None, immediate_blackjack=False):
    """
    Handles dealer's turn, final scoring, payout, and resets the game state.
    """
    state_data = USER_STATES[fromId]
    game_data = state_data['game_data']
    
    player_hand = game_data['player_hand']
    dealer_hand = game_data['dealer_hand']
    deck = game_data['deck']
    
    player_value = get_hand_value(player_hand)
    dealer_value = get_hand_value(dealer_hand)
    bet = game_data['bet']
    
    final_result = ""
    payout = 0
    
    # 1. Dealer's Turn (only if player didn't bust immediately)
    if player_value <= 21:
        # Dealer must hit until 17 or more
        while dealer_value < 17 and deck:
            dealer_hand.append(deck.pop())
            dealer_value = get_hand_value(dealer_hand)
            
        if dealer_value > 21:
            final_result = "DEALER BUSTS! YOU WIN!"
            payout = bet * 2
        elif immediate_blackjack:
            if dealer_value == 21:
                final_result = "PUSH! (Dealer and You got Blackjack)"
                payout = bet
            else:
                final_result = "BLACKJACK! You Win 1.5x!"
                payout = bet + int(bet * 1.5)
        elif player_value > dealer_value:
            final_result = "YOU WIN!"
            payout = bet * 2
        elif player_value < dealer_value:
            final_result = "DEALER WINS!"
            payout = 0
        else: # Tie
            final_result = "PUSH (Tie)."
            payout = bet
            
    # If player busted
    elif player_value > 21 and result_message:
        final_result = result_message 
        payout = 0 
        
    # 2. Update Chips
    net_change = payout - bet
    game_data['chips'] += net_change
    current_chips = game_data['chips']

    # 3. Format End Message
    end_message = (
        f"--- GAME OVER ---\n"
        f"Dealer: {dealer_hand} (Score: {dealer_value})\n"
        f"You: {player_hand} (Score: {player_value})\n"
        f"\n** {final_result} **\n"
        f"Chips Change: {net_change:+}\n" 
        f"Current Chips: {current_chips}\n"
        f"[N] New Game, [M] Main Menu, [Q] Quit to Games Menu" # Updated prompt
    )
    
    # 4. Reset state for next game (keeps chips, but moves to the end state)
    state_data['state'] = 'game_blackjack_end'
    
    return end_message

# --- EXTERNAL ROUTER ---

def handle_game_command(fromId, command_input, USER_STATES, GAMES_MENU_ASCII, MAIN_MENU_ASCII, LOGOFF_ASCII):
    """
    Routes commands based on the active game state (Blackjack only for now).
    """
    state_data = USER_STATES[fromId]
    active_state = state_data.get('state', 'none')
    command = command_input[0]
    
    # In-game command (Hit/Stand/Quit)
    if active_state == 'game_blackjack_turn':
        return process_blackjack_turn(fromId, command_input, USER_STATES, GAMES_MENU_ASCII, MAIN_MENU_ASCII, LOGOFF_ASCII)
        
    # Waiting for bet input
    elif active_state == 'game_blackjack_betting':
        # Check for menu commands first
        if command == 'M':
            del state_data['state']
            if 'game_data' in state_data:
                # Save the chips, but clear the game data state
                del state_data['game_data']
            state_data['last_menu'] = 'MAIN'
            return MAIN_MENU_ASCII
        elif command == 'Q':
            # Quit to Games Menu (Q logic for betting phase)
            del state_data['state']
            if 'game_data' in state_data:
                del state_data['game_data']
            state_data['last_menu'] = 'GAMES'
            return GAMES_MENU_ASCII
        
        # If it's not a menu command, assume it's the bet amount
        return process_blackjack_betting(fromId, command_input, USER_STATES, GAMES_MENU_ASCII, MAIN_MENU_ASCII, LOGOFF_ASCII)

    # Game finished, waiting for New Game/Menu command
    elif active_state == 'game_blackjack_end':
        if command == 'N':
            # N now sends the user to the betting prompt
            return start_blackjack(fromId, USER_STATES, GAMES_MENU_ASCII, MAIN_MENU_ASCII, LOGOFF_ASCII)
        elif command == 'M':
            del state_data['state']
            if 'game_data' in state_data:
                del state_data['game_data']
            state_data['last_menu'] = 'MAIN'
            return MAIN_MENU_ASCII
        elif command == 'Q':
            # Quit to Games Menu (Q logic for end-of-game phase)
            del state_data['state']
            if 'game_data' in state_data:
                del state_data['game_data']
            state_data['last_menu'] = 'GAMES'
            return GAMES_MENU_ASCII
        else:
            return f"Game finished. Use [N] New Game, [M] Main Menu, or [Q] Quit to Games Menu."

    # Fallback
    state_data['last_menu'] = 'GAMES'
    return GAMES_MENU_ASCII
