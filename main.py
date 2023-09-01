import pandas
import random

current_card = {}
try:
    data = pandas.read_csv('data/words_to_learn.csv')
except FileNotFoundError:
    original_data = pandas.read_csv('data/french_words.csv')
    to_learn = original_data.to_dict('records')
else:
    to_learn = data.to_dict('records')


def next_card():
    global current_card
    current_card = random.choice(to_learn)
    print("\nFrench: ", current_card['French'])
    input("Press Enter to see the English translation...")
    print("English: ", current_card['English'])


def is_known():
    to_learn.remove(current_card)
    data_k = pandas.DataFrame(to_learn)
    data_k.to_csv("data/words_to_learn.csv", index=False)


print("Welcome to Flashy - Command Line Version")

while to_learn:
    next_card()
    response = input("\nDid you know this word? (y/n): ").lower()
    if response == 'y':
        is_known()
    elif response == 'n':
        continue
    else:
        print("Invalid input. Please enter 'y' or 'n'.")

print("Congratulations! You've learned all the words.")
