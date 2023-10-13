import sqlite3
import random
import pygame
from datetime import datetime, timedelta

pygame.init()

conn = sqlite3.connect('flashcards_database.db')
cursor = conn.cursor()

LEARNING_TABLE_NAME = "Table2"


class Flashcard:
    def __init__(self, id, status, phonetic, word, sentence, audio_url, learn_date, next_review_date):
        self.id = id
        self.status = status
        self.phonetic = phonetic
        self.word = word
        self.sentence = sentence
        self.audio_url = audio_url
        self.learn_date = learn_date
        self.next_review_date = next_review_date


def initialize_tables():
    create_learning_history_table()
    insert_initial_data()


def create_learning_history_table():
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Table2 (
            RecordID INTEGER PRIMARY KEY,
            LearnDate DATE,
            CardID INTEGER,
            YesCount INTEGER,
            NoCount INTEGER,
            LearningStatus INTEGER
        )
    ''')


def execute_query(query, params=()):
    cursor.execute(query, params)
    conn.commit()


def fetch_all(query, params=()):
    cursor.execute(query, params)
    return cursor.fetchall()


def load_flashcards():
    today = datetime.now().date()
    query = "SELECT * FROM flashcards_database WHERE status IN (1, 2) AND NextReviewDate = ?"
    records = fetch_all(query, (today,))

    query = "SELECT DISTINCT CardID FROM Table2"
    card_ids_in_table2 = [row[0] for row in fetch_all(query)]

    filtered_records = []
    for record in records:
        card_id = record[0]
        if card_id not in card_ids_in_table2:
            filtered_records.append(record)

    if not filtered_records:
        query = "SELECT * FROM flashcards_database WHERE status IN (1, 2)"
        records = fetch_all(query)
        for record in records:
            card_id = record[0]
            if card_id not in card_ids_in_table2:
                filtered_records.append(record)

    flashcards = [Flashcard(*record) for record in filtered_records]
    random.shuffle(flashcards)
    return flashcards


def enough_data_in_table2():
    query = "SELECT COUNT(*) FROM Table2"
    count = fetch_all(query)[0][0]
    return count >= 10


def insert_initial_data():
    query = "SELECT DISTINCT CardID FROM Table2"
    inserted_card_ids = [row[0] for row in fetch_all(query)]

    while not enough_data_in_table2():
        flashcard = random.choice(load_flashcards())
        while flashcard.id in inserted_card_ids:
            flashcard = random.choice(load_flashcards())

        query = "INSERT INTO Table2 (LearnDate, CardID, YesCount, NoCount, LearningStatus) VALUES (?, ?, ?, ?, ?)"
        execute_query(query, (0, flashcard.id, 0, 0, flashcard.status))
        inserted_card_ids.append(flashcard.id)


def get_flashcards():
    query = f"SELECT DISTINCT CardID FROM {LEARNING_TABLE_NAME}"
    card_ids = [row[0] for row in fetch_all(query)]
    flashcards = []

    for card_id in card_ids:
        query = "SELECT * FROM flashcards_database WHERE id = ?"
        record = fetch_all(query, (card_id,))
        if record:
            flashcard = Flashcard(*record[0])
            flashcards.append(flashcard)

    random.shuffle(flashcards)
    return flashcards


def show_flashcard(flashcard):
    print(f"\nPhonetic: {flashcard.phonetic}")
    print(f"Word: {flashcard.word}")
    print(f"Sentence: {flashcard.sentence}")
    pygame.mixer.music.load(flashcard.audio_url)
    pygame.mixer.music.play()

    while pygame.mixer.music.get_busy():
        pygame.time.delay(100)


def record_count(choice, flashcard):
    if choice == "yes":
        query = f"UPDATE {LEARNING_TABLE_NAME} SET YesCount = YesCount + 1 WHERE CardID = ?"
        execute_query(query, (flashcard.id,))
    elif choice == "no":
        query = f"UPDATE {LEARNING_TABLE_NAME} SET NoCount = NoCount + 1 WHERE CardID = ?"
        execute_query(query, (flashcard.id,))
    else:
        print("Invalid choice")

    status = decide_learning_status(flashcard)
    query = f"UPDATE {LEARNING_TABLE_NAME} SET LearnDate = date('now'), LearningStatus = ? WHERE CardID = ?"
    execute_query(query, (status, flashcard.id))


def decide_learning_status(flashcard):
    query = f"SELECT YesCount, NoCount FROM {LEARNING_TABLE_NAME} WHERE CardID = ?"
    result = fetch_all(query, (flashcard.id,))
    yes_count, no_count = result[0] if result else (0, 0)

    if yes_count - no_count > 0:
        return 2
    else:
        return 1


def create_individual_learning_tables():
    query = f"SELECT DISTINCT CardID FROM {LEARNING_TABLE_NAME}"
    card_ids = [row[0] for row in fetch_all(query)]

    for card_id in card_ids:
        query = f"SELECT * FROM {LEARNING_TABLE_NAME} WHERE CardID = ?"
        record = fetch_all(query, (card_id,))

        if record[0][1] != 0:
            table_name = f"individual_record_{card_id}"

            cursor.execute(f'''
                CREATE TABLE IF NOT EXISTS {table_name} (
                    RecordID INTEGER PRIMARY KEY,
                    CardID INTEGER,
                    LearnDate DATE,
                    YesCount INTEGER,
                    NoCount INTEGER,
                    LearningStatus INTEGER,
                    NextReviewDate DATE
                )
            ''')


def record_learning_status_for_individual_tables():
    query = f"SELECT * FROM {LEARNING_TABLE_NAME}"
    records = fetch_all(query)

    for record in records:
        card_id = record[2]
        learn_date = record[1]
        table_name = f"individual_record_{card_id}"
        if learn_date != 0:
            query = f"SELECT COUNT(*) FROM {table_name}"
            count = fetch_all(query)[0][0]
            if count == 0:
                query = f'''
                    INSERT INTO {table_name} (CardID, LearnDate, YesCount, NoCount, LearningStatus)
                    VALUES (?, ?, ?, ?, ?)'''
                execute_query(query, (card_id, learn_date, record[3], record[4], record[5]))

                query = f"SELECT COUNT(*) FROM {table_name}"
                count = fetch_all(query)[0][0]

                if count == 1:
                    insert_initial_review_dates(card_id)
            else:
                query = f'''
                    UPDATE {table_name}
                    SET YesCount = ?, NoCount = ?, LearningStatus = ?, LearnDate = ?
                    WHERE NextReviewDate = ?'''
                execute_query(query, (record[3], record[4], record[5], learn_date, learn_date))

            update_next_review_date(card_id)


def insert_initial_review_dates(card_id):
    review_list = [1, 2, 3, 4, 7, 8, 15, 30]
    table_name = f"individual_record_{card_id}"

    query = f"SELECT LearnDate FROM {table_name}"
    learn_date_str = fetch_all(query)[0][0]
    current_study_date = datetime.strptime(learn_date_str, '%Y-%m-%d').date()

    for interval in review_list:
        next_review_date = current_study_date + timedelta(days=interval)
        query = f"INSERT INTO {table_name} (CardID, NextReviewDate) VALUES (?, ?)"
        execute_query(query, (card_id, next_review_date))


def update_next_review_date(card_id):
    table_name = f"individual_record_{card_id}"
    query = f'''
        SELECT NextReviewDate
        FROM {table_name}
        WHERE CardID = ? AND LearnDate IS NULL
        ORDER BY NextReviewDate ASC
        LIMIT 1
    '''
    result = fetch_all(query, (card_id,))

    if result:
        next_review_date = result[0][0]
        query = "UPDATE flashcards_database SET NextReviewDate = ? WHERE id = ?"
        execute_query(query, (next_review_date, card_id))
    else:
        query = "UPDATE flashcards_database SET status = 3 WHERE id = ?"
        execute_query(query, (card_id,))


def record_flashcard_count(choice, flashcard):
    if choice in ('yes', 'no'):
        record_count(choice, flashcard)
    else:
        print("Invalid choice")


def should_update_flashcard(flashcard):
    query = f"SELECT YesCount, NoCount FROM {LEARNING_TABLE_NAME} WHERE CardID = ?"
    result = fetch_all(query, (flashcard.id,))
    yes_count, no_count = result[0] if result else (0, 0)

    if yes_count > 0 or no_count > 0:
        return True
    else:
        return False


def cleanup_and_exit(flashcards):
    for flashcard in flashcards:
        if should_update_flashcard(flashcard):
            status = decide_learning_status(flashcard)
            query = f"""
                UPDATE flashcards_database
                SET status = ?, LearnDate = (SELECT LearnDate FROM {LEARNING_TABLE_NAME} WHERE CardID = ?)
                WHERE id = ?
            """
            execute_query(query, (status, flashcard.id, flashcard.id))
    create_individual_learning_tables()
    record_learning_status_for_individual_tables()

    query = f"DELETE FROM {LEARNING_TABLE_NAME} WHERE LearningStatus = 2 AND (YesCount > 0 OR NoCount > 0)"
    execute_query(query)
    conn.close()
    print("学习完成！")


def main():
    initialize_tables()
    flashcards = get_flashcards()
    quit_program = False

    while flashcards and not quit_program:
        flashcard = random.choice(flashcards)
        show_flashcard(flashcard)
        choice = input("\nChoose an action (yes/no) or press 'q' to quit: ").lower()

        if choice == 'q':
            quit_program = True
        else:
            record_flashcard_count(choice, flashcard)

    cleanup_and_exit(flashcards)


if __name__ == "__main__":
    main()
