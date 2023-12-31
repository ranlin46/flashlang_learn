import sqlite3
import random
import pygame
from datetime import datetime, timedelta

pygame.init()

# 连接数据库
conn = sqlite3.connect('flashcards_database.db')
cursor = conn.cursor()


# 定义Flashcard类表示单词卡片
class Flashcard:
    def __init__(self, card_id, phonetic, word, sentence, audio_url):
        self.id = card_id
        self.phonetic = phonetic
        self.word = word
        self.sentence = sentence
        self.audio_url = audio_url


# 数据库操作相关函数
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

    cursor.execute("SELECT StudyCount, ReviewCount FROM StudyRecords WHERE UserID = ? AND CardID = ? AND StudyDate = ?",
                   (user_id, card_id, current_date))
    existing_record = cursor.fetchone()

    if existing_record:
        existing_study_count, existing_review_count = existing_record
        study_count += existing_study_count
        review_count += existing_review_count
        cursor.execute(
            "UPDATE StudyRecords SET StudyCount = ?, ReviewCount = ? WHERE UserID = ? AND CardID = ? AND StudyDate = ?",
            (study_count, review_count, user_id, card_id, current_date))
    else:
        cursor.execute(
            "INSERT INTO StudyRecords (UserID, CardID, StudyDate, StudyCount, ReviewCount) VALUES (?, ?, ?, ?, ?)",
            (user_id, card_id, current_date, study_count, review_count))

    conn.commit()


# 学习状态和计划相关函数
def calculate_study_status(study_count, review_count):
    if study_count == 0 and review_count == 0:
        return 1
    elif study_count - review_count > 0:
        return 1
    else:
        return 2


def calculate_next_review_date():
    return (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")


def calculate_review_plan(user_id, card_id, study_count, review_count):
    study_status = calculate_study_status(study_count, review_count)
    next_review_date = calculate_next_review_date()
    check_review_plan(user_id, card_id, study_status, next_review_date)


def check_review_plan(user_id, card_id, study_status, next_review_date, optional_param=None):
    row_count = get_row_count(user_id, card_id)
    existing_record_count = get_existing_record_count(user_id, card_id, row_count, next_review_date)
    if optional_param is not None:
        change_review_plan(user_id, card_id, study_status, next_review_date, row_count, existing_record_count, True)
    else:
        change_review_plan(user_id, card_id, study_status, next_review_date, row_count, existing_record_count, False)


def change_review_plan(user_id, card_id, study_status, next_review_date, row_count, existing_record_count,
                       only_insert_update=False):
    if only_insert_update:
        if existing_record_count == 0:
            insert_review_plan_record(user_id, card_id, 3, row_count, 0)
        else:
            update_review_plan_record(user_id, card_id, 3, row_count, 0)
    else:
        if existing_record_count == 0:
            insert_review_plan_record(user_id, card_id, study_status, row_count, next_review_date)
        else:
            update_review_plan_record(user_id, card_id, study_status, row_count, next_review_date)

    conn.commit()


def insert_review_plan_record(user_id, card_id, study_status, row_count, next_review_date):
    cursor.execute(
        "INSERT INTO ReviewPlans (UserID, CardID, StudyStatus, TotalReviewCount, NextReviewDate) "
        "VALUES (?, ?, ?, ?, ?)",
        (user_id, card_id, study_status, row_count, next_review_date))


def update_review_plan_record(user_id, card_id, study_status, row_count, next_review_date):
    cursor.execute(
        "UPDATE ReviewPlans SET StudyStatus = ?, TotalReviewCount = ?, NextReviewDate = ? "
        "WHERE UserID = ? AND CardID = ?",
        (study_status, row_count, next_review_date, user_id, card_id))


def get_next_review_date_and_status(user_id, card_id):
    cursor.execute("SELECT NextReviewDate, StudyStatus FROM ReviewPlans WHERE UserID = ? AND CardID = ?",
                   (user_id, card_id))
    review_plan = cursor.fetchone()
    if review_plan:
        return review_plan[0], review_plan[1]
    return None, None


def get_row_count(user_id, card_id):
    cursor.execute("SELECT COUNT(*) FROM StudyRecords WHERE UserID = ? AND CardID = ?", (user_id, card_id))
    return cursor.fetchone()[0] - 1


def get_existing_record_count(user_id, card_id, row_count, next_review_date):
    cursor.execute(
        "SELECT COUNT(*) FROM ReviewPlans "
        "WHERE UserID = ? AND CardID = ?  AND TotalReviewCount = ? AND NextReviewDate = ?",
        (user_id, card_id, row_count, next_review_date))
    return cursor.fetchone()[0]


# 获取学习日期
def get_study_date(user_id, card_id):
    cursor.execute("SELECT StudyDate FROM StudyRecords WHERE UserID = ? AND CardID = ?",
                   (user_id, card_id))
    study_record = cursor.fetchone()
    if study_record:
        return study_record[0]
    return None


# 插入或更新用户单词卡片
def insert_or_update_user_word_card(user_id, card_id):
    next_review_date, study_status = get_next_review_date_and_status(user_id, card_id)
    study_date = get_study_date(user_id, card_id)
    cursor.execute(
        "INSERT OR REPLACE INTO UserWordCard (UserID, CardID, StudyDate, NextReviewDate, StudyStatus) "
        "VALUES (?, ?, ?, ?, ?)",
        (user_id, card_id, study_date, next_review_date, study_status))

    conn.commit()


# 显示卡片相关函数
def show_flashcard(flashcard):
    print(f"\nPhonetic: {flashcard.phonetic}")
    print(f"Word: {flashcard.word}")
    print(f"Sentence: {flashcard.sentence}")
    pygame.mixer.music.load(flashcard.audio_url)
    pygame.mixer.music.play()

    while pygame.mixer.music.get_busy():
        pygame.time.delay(100)


# 处理用户选择和卡片状态相关函数
def handle_user_choice(choice, user_id, flashcard):
    if choice == '1':
        insert_study_record(user_id, flashcard.id, 1, 0)
    elif choice == '2':
        insert_study_record(user_id, flashcard.id, 0, 1)


def handle_mastered_card(user_id, flashcard, flashcards):
    insert_study_record(user_id, flashcard.id, 0, 0)
    cursor.execute(
        "INSERT OR REPLACE INTO UserWordCard (UserID, CardID, StudyDate, NextReviewDate, StudyStatus) "
        "VALUES (?, ?, CURRENT_DATE, ?, ?)",
        (user_id, flashcard.id, 0, 3))
    conn.commit()
    check_review_plan(user_id, flashcard.id, 3, 0, optional_param=True)
    flashcards.remove(flashcard)
    new_flashcard = get_user_study_cards(user_id)[-1]
    flashcards.append(new_flashcard)


def process_remaining_flashcards(user_id, flashcards):
    for flashcard in flashcards:
        study_record = cursor.execute(
            "SELECT StudyCount, ReviewCount FROM StudyRecords WHERE UserID = ? AND CardID = ?",
            (user_id, flashcard.id)).fetchone()
        if study_record:
            study_count, review_count = study_record
            calculate_review_plan(user_id, flashcard.id, study_count, review_count)
            insert_or_update_user_word_card(user_id, flashcard.id)


# 获取用户需要学习的卡片
def get_user_study_cards(user_id):
    query = "SELECT C.CardID, C.Phonetic, C.Word, C.Sentence, C.Audio_URL " \
            "FROM Cards C " \
            "JOIN UserWordCard U ON C.CardID = U.CardID " \
            "WHERE U.UserID = ? AND U.StudyStatus = 1"
    cursor.execute(query, (user_id,))
    flashcards = [Flashcard(*row) for row in cursor.fetchall()]

    query = "SELECT C.CardID, C.Phonetic, C.Word, C.Sentence, C.Audio_URL " \
            "FROM Cards C " \
            "JOIN UserWordCard U ON C.CardID = U.CardID " \
            "WHERE U.UserID = ? AND U.StudyStatus = 2 AND U.NextReviewDate = DATE('now')"
    cursor.execute(query, (user_id,))
    flashcards += [Flashcard(*row) for row in cursor.fetchall()]

    query = "SELECT * FROM Cards " \
            "WHERE CardID NOT IN (SELECT CardID FROM UserWordCard WHERE UserID = ?) ORDER BY RANDOM()"
    cursor.execute(query, (user_id,))
    flashcards += [Flashcard(*row) for row in cursor.fetchall()]

    return flashcards[:5]


def main():
    username = input("请输入用户名: ")
    user_exists = check_user_existence(username)

    if not user_exists:
        password = input("请输入密码: ")
        registration_date = datetime.now().strftime("%Y-%m-%d")
        insert_user(username, password, registration_date)
        print("用户已注册!")

    user_id = cursor.execute("SELECT UserID FROM Users WHERE Username = ?", (username,)).fetchone()[0]
    flashcards = get_user_study_cards(user_id)

    quit_program = False

    while flashcards and not quit_program:
        flashcard = random.choice(flashcards)
        show_flashcard(flashcard)
        choice = input("\nChoose an action (1/2/3) or press 'q' to quit: ")

        if choice in {'1', '2'}:
            handle_user_choice(choice, user_id, flashcard)
        elif choice == '3':
            handle_mastered_card(user_id, flashcard, flashcards)
        elif choice == 'q':
            quit_program = True

    process_remaining_flashcards(user_id, flashcards)

    conn.commit()


if __name__ == "__main__":
    main()
