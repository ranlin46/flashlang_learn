import sqlite3
import random
import pygame
from datetime import datetime, timedelta

pygame.init()

conn = sqlite3.connect('flashcards_database.db')
cursor = conn.cursor()


class Flashcard:
    def __init__(self, card_id, phonetic, word, sentence, audio_url):
        self.id = card_id
        self.phonetic = phonetic
        self.word = word
        self.sentence = sentence
        self.audio_url = audio_url


def get_flashcards():
    query = "SELECT * FROM Cards ORDER BY RANDOM() LIMIT 4"
    cursor.execute(query)

    flashcards = []
    for row in cursor.fetchall():
        card_id, phonetic, word, sentence, audio_url = row
        flashcard = Flashcard(card_id, phonetic, word, sentence, audio_url)
        flashcards.append(flashcard)

    return flashcards


def show_flashcard(flashcard):
    print(f"\nPhonetic: {flashcard.phonetic}")
    print(f"Word: {flashcard.word}")
    print(f"Sentence: {flashcard.sentence}")
    pygame.mixer.music.load(flashcard.audio_url)
    pygame.mixer.music.play()

    while pygame.mixer.music.get_busy():
        pygame.time.delay(100)


def check_user_existence(username):
    cursor.execute("SELECT COUNT(*) FROM Users WHERE Username = ?", (username,))
    count = cursor.fetchone()[0]
    return count > 0


def insert_user(username, password, registration_date):
    cursor.execute("INSERT INTO Users (Username, Password, RegistrationDate) VALUES (?, ?, ?)",
                   (username, password, registration_date))
    conn.commit()


def insert_study_record(user_id, card_id, study_count, review_count):
    current_date = datetime.now().strftime("%Y-%m-%d")

    # 检查是否已经有记录
    cursor.execute("SELECT StudyCount, ReviewCount FROM StudyRecords WHERE UserID = ? AND CardID = ? AND StudyDate = ?",
                   (user_id, card_id, current_date))
    existing_record = cursor.fetchone()

    if existing_record:
        # 如果有现有记录，更新它
        existing_study_count, existing_review_count = existing_record
        study_count += existing_study_count
        review_count += existing_review_count
        cursor.execute(
            "UPDATE StudyRecords SET StudyCount = ?, ReviewCount = ? WHERE UserID = ? AND CardID = ? AND StudyDate = ?",
            (study_count, review_count, user_id, card_id, current_date))
    else:
        # 如果没有现有记录，插入新记录
        cursor.execute(
            "INSERT INTO StudyRecords (UserID, CardID, StudyDate, StudyCount, ReviewCount) VALUES (?, ?, ?, ?, ?)",
            (user_id, card_id, current_date, study_count, review_count))

    conn.commit()


def calculate_study_status(study_count, review_count):
    if study_count == 0 and review_count == 0:
        return 1
    elif study_count - review_count > 0:
        return 1
    else:
        return 2


def insert_review_plan(user_id, card_id, study_count, review_count):
    study_status = calculate_study_status(study_count, review_count)
    next_review_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    cursor.execute(
        "INSERT INTO ReviewPlans (UserID, CardID, StudyStatus, ReviewCount, NextReviewDate) VALUES (?, ?, ?, ?, ?)",
        (user_id, card_id, study_status, review_count, next_review_date))
    conn.commit()


def get_next_review_date_and_status(user_id, card_id):
    cursor.execute("SELECT NextReviewDate, StudyStatus FROM ReviewPlans WHERE UserID = ? AND CardID = ?",
                   (user_id, card_id))
    review_plan = cursor.fetchone()
    if review_plan:
        return review_plan[0], review_plan[1]
    return None, None


def get_study_date(user_id, card_id):
    cursor.execute("SELECT StudyDate FROM StudyRecords WHERE UserID = ? AND CardID = ?",
                   (user_id, card_id))
    study_record = cursor.fetchone()
    if study_record:
        return study_record[0]
    return None


def insert_or_update_user_word_card(user_id, card_id):
    next_review_date, study_status = get_next_review_date_and_status(user_id, card_id)
    study_date = get_study_date(user_id, card_id)

    if next_review_date is not None:
        cursor.execute(
            "INSERT OR REPLACE INTO UserWordCard (UserID, CardID, StudyDate, NextReviewDate, StudyStatus) VALUES (?, ?, ?, ?, ?)",
            (user_id, card_id, study_date, next_review_date, study_status))
        conn.commit()


def main():
    username = input("请输入用户名: ")
    user_exists = check_user_existence(username)

    if not user_exists:
        password = input("请输入密码: ")
        registration_date = datetime.now().strftime("%Y-%m-%d")
        insert_user(username, password, registration_date)
        print("用户已注册!")

    flashcards = get_flashcards()
    user_id = cursor.execute("SELECT UserID FROM Users WHERE Username = ?", (username,)).fetchone()[0]
    quit_program = False

    while flashcards and not quit_program:
        flashcard = random.choice(flashcards)
        show_flashcard(flashcard)
        choice = input("\nChoose an action (1/2/3) or press 'q' to quit: ")

        if choice == '1':
            insert_study_record(user_id, flashcard.id, 1, 0)
        elif choice == '2':
            insert_study_record(user_id, flashcard.id, 0, 1)
        elif choice == '3':
            # 如果用户选择 '3'，标记卡片状态为 '已学会' 并从学习卡片列表中移除
            cursor.execute(
                "INSERT INTO ReviewPlans (UserID, CardID, StudyStatus) VALUES (?, ?, ?)",
                (user_id, flashcard.id, 3))
            conn.commit()

            flashcards.remove(flashcard)

        elif choice == 'q':
            quit_program = True

    # 在退出时，为每个卡片创建复习计划
    for flashcard in flashcards:
        study_record = cursor.execute(
            "SELECT StudyCount, ReviewCount FROM StudyRecords WHERE UserID = ? AND CardID = ?",
            (user_id, flashcard.id)).fetchone()
        if study_record:
            study_count, review_count = study_record
            insert_review_plan(user_id, flashcard.id, study_count, review_count)
            insert_or_update_user_word_card(user_id, flashcard.id)

    conn.commit()


if __name__ == "__main__":
    main()
