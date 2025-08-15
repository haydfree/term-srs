import json
import datetime
import os
import random
import sys

# --- Config ---
DECK_FOLDER = "decks"
DEFAULT_EASE_FACTOR = 2.5
QUALITY_MAP = {
	'1': 0,  # Again: Complete failure to recall
	'2': 3,  # Hard: Correct response after significant difficulty
	'3': 4,  # Good: Correct response with slight hesitation
	'4': 5   # Easy: Correct response with perfect recall
}

def clear_screen():
	"""Clears the terminal screen."""
	os.system('cls' if os.name == 'nt' else 'clear')

def get_deck_path(deck_name):
	"""Constructs the full path for a given deck name."""
	return os.path.join(DECK_FOLDER, f"{deck_name}.json")

def load_deck(deck_name):
	"""Loads a deck from a .json file."""
	filepath = get_deck_path(deck_name)
	if not os.path.exists(filepath):
		return []
	with open(filepath, 'r') as f:
		return json.load(f)

def save_deck(deck_name, deck_data):
	"""Saves a deck to a .json file."""
	if not os.path.exists(DECK_FOLDER):
		os.makedirs(DECK_FOLDER)
	filepath = get_deck_path(deck_name)
	with open(filepath, 'w') as f:
		json.dump(deck_data, f, indent=2)

def review_card(card):
	"""
	Updates a card's review data based on user performance.
	Uses a simplified SM-2 algorithm.
	"""
	quality = QUALITY_MAP.get(input("\nQuality (1:Again, 2:Hard, 3:Good, 4:Easy): ").strip())
	while quality is None:
		quality = QUALITY_MAP.get(input("Invalid input. Please enter 1, 2, 3, or 4: ").strip())

	if quality < 3:
		card['repetitions'] = 0
		card['interval'] = 1
	else:
		if card['repetitions'] == 0:
			card['interval'] = 1
		elif card['repetitions'] == 1:
			card['interval'] = 6
		else:
			card['interval'] = round(card['interval'] * card['ease_factor'])
		
		card['repetitions'] += 1

	card['ease_factor'] = max(1.3, card['ease_factor'] + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)))
	
	next_review_delta = datetime.timedelta(days=card['interval'])
	card['next_review_date'] = (datetime.date.today() + next_review_delta).isoformat()
	
	return card

def add_new_card(deck_name):
	"""Adds a new card to the specified deck."""
	deck = load_deck(deck_name)
	
	try:
		front = input("Enter front of card (question): ")
		back = input("Enter back of card (answer): ")
	except (KeyboardInterrupt, EOFError):
		print("\nCard creation cancelled.")
		return

	new_card = {
		"front": front,
		"back": back,
		"next_review_date": datetime.date.today().isoformat(),
		"repetitions": 0,
		"interval": 1,
		"ease_factor": DEFAULT_EASE_FACTOR
	}
	deck.append(new_card)
	save_deck(deck_name, deck)
	print(f"\nCard added to '{deck_name}'.")

def run_review_session(deck_name):
	"""Starts a review session for the specified deck."""
	deck = load_deck(deck_name)
	if not deck:
		print(f"Deck '{deck_name}' is empty or does not exist.")
		return

	today_iso = datetime.date.today().isoformat()
	due_cards = [card for card in deck if card['next_review_date'] <= today_iso]
	
	if not due_cards:
		print(f"No cards due for review in '{deck_name}' today. Great work! ✨")
		return

	random.shuffle(due_cards)
	updated_cards = []

	print(f"\n--- Starting Review for '{deck_name}' ({len(due_cards)} cards due) ---")
	
	try:
		for i, card in enumerate(due_cards):
			clear_screen()
			print(f"Card {i+1}/{len(due_cards)}")
			print("\n" + "="*20)
			print(f"FRONT: {card['front']}")
			print("="*20)
			input("\nPress Enter to reveal answer...")
			
			print(f"\nBACK: {card['back']}")
			
			updated_card = review_card(card)
			updated_cards.append(updated_card)

		card_map = { (c['front'], c['back']): c for c in updated_cards }
		for i, card in enumerate(deck):
			key = (card['front'], card['back'])
			if key in card_map:
				deck[i] = card_map[key]

		save_deck(deck_name, deck)
		print("\nReview session complete! Your progress has been saved.")

	except (KeyboardInterrupt, EOFError):
		card_map = { (c['front'], c['back']): c for c in updated_cards }
		for i, card in enumerate(deck):
			key = (card['front'], card['back'])
			if key in card_map:
				deck[i] = card_map[key]
		
		save_deck(deck_name, deck)
		print("\n\nSession interrupted. Your progress so far has been saved.")
		sys.exit(0)


def main():
	if len(sys.argv) < 3:
		print("Usage:")
		print("  python main.py add <deck_name>")
		print("  python main.py review <deck_name>")
		sys.exit(1)

	command = sys.argv[1].lower()
	deck_name = sys.argv[2]

	if command == "add":
		add_new_card(deck_name)
	elif command == "review":
		run_review_session(deck_name)
	else:
		print(f"Unknown command: '{command}'")
		sys.exit(1)

if __name__ == "__main__":
	main()
