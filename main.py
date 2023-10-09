import sqlite3
import random
import pygame
from datetime import datetime, timedelta

# 初始化pygame
pygame.init()

# 连接到数据库文件
conn = sqlite3.connect('flashcards_database.db')
cursor = conn.cursor()
learning_table_name = "Table2"


# 定义Flashcard类
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


# 初始化数据库表格
def initialize_tables():
    create_learning_history_table()
    insert_initial_data()


# 创建学习历史表格
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


# 加载单词卡片
def load_flashcards():
    cursor.execute("SELECT * FROM flashcards_database WHERE status IN (1, 2) AND NextReviewDate = date('now')")
    records = cursor.fetchall()
    if records:
        flashcards = [Flashcard(*record) for record in records]
    else:
        cursor.execute("SELECT * FROM flashcards_database WHERE status IN (1, 2)")
        records = cursor.fetchall()
        flashcards = [Flashcard(*record) for record in records]
    random.shuffle(flashcards)
    return flashcards


# 检查是否有足够的数据在表2中
def enough_data_in_table2():
    cursor.execute("SELECT COUNT(*) FROM Table2")
    count = cursor.fetchone()[0]
    return count >= 10


# 插入初始数据
def insert_initial_data():
    inserted_card_ids = set()
    while not enough_data_in_table2():
        flashcard = random.choice(load_flashcards())
        while flashcard.id in inserted_card_ids:
            flashcard = random.choice(load_flashcards())
        cursor.execute('''
            INSERT INTO Table2 (LearnDate, CardID, YesCount, NoCount, LearningStatus)
            VALUES (?, ?, ?, ?, ?)
        ''', (0, flashcard.id, 0, 0, flashcard.status))
        inserted_card_ids.add(flashcard.id)
        conn.commit()


# 获取待学习的单词卡片
def get_flashcards():
    cursor.execute(f"SELECT DISTINCT CardID FROM {learning_table_name}")
    card_ids = [row[0] for row in cursor.fetchall()]
    flashcards = []
    for card_id in card_ids:
        cursor.execute("SELECT * FROM flashcards_database WHERE id = ? ", (card_id,))
        record = cursor.fetchone()
        if record:
            flashcard = Flashcard(*record)
            flashcards.append(flashcard)
    random.shuffle(flashcards)
    return flashcards


# 展示单词卡片
def show_flashcard(flashcard):
    print(f"Phonetic: {flashcard.phonetic}")
    print(f"Word: {flashcard.word}")
    print(f"Sentence: {flashcard.sentence}")
    pygame.mixer.music.load(flashcard.audio_url)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        pygame.time.delay(100)


# 更新学习状态
def update_status(choice, flashcard):
    if choice == "yes":
        cursor.execute(f"UPDATE {learning_table_name} SET YesCount = YesCount + 1 WHERE CardID = ?",
                       (flashcard.id,))
    elif choice == "no":
        cursor.execute(f"UPDATE {learning_table_name} SET NoCount = NoCount + 1 WHERE CardID = ?",
                       (flashcard.id,))
    else:
        print("无效的选项")
    cursor.execute(
        f"UPDATE {learning_table_name} SET LearnDate = date('now'), LearningStatus = ? WHERE CardID = ?",
        (decide_learning_status(flashcard), flashcard.id))
    conn.commit()


# 决定学习状态
def decide_learning_status(flashcard):
    cursor.execute(f"SELECT YesCount, NoCount FROM {learning_table_name} WHERE CardID = ?", (flashcard.id,))
    result = cursor.fetchone()
    yes_count = result[0] if result else 0
    no_count = result[1] if result else 0
    if yes_count - no_count > 0:
        return 2
    else:
        return 1


# 创建个体学习记录表格
def create_individual_learning_tables():
    cursor.execute(f"SELECT DISTINCT CardID FROM {learning_table_name}")
    card_ids = [row[0] for row in cursor.fetchall()]
    for card_id in card_ids:
        cursor.execute(f"SELECT * FROM {learning_table_name} WHERE CardID = ?", (card_id,))
        record = cursor.fetchone()
        if record[1] != 0:
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
    conn.commit()


# 记录学习状态到个体学习记录表格
def record_learning_status_for_individual_tables():
    cursor.execute(f"SELECT * FROM {learning_table_name}")
    records = cursor.fetchall()
    for record in records:
        card_id = record[2]
        table_name = f"individual_record_{card_id}"
        if record[1] != 0:
            cursor.execute(f'''
                INSERT INTO {table_name} (CardID, LearnDate, YesCount, NoCount, LearningStatus)
                VALUES (?, ?, ?, ?, ?)
            ''', (record[2], record[1], record[3], record[4], record[5]))
            conn.commit()
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            if count == 1:
                insert_initial_review_dates(card_id)
                update_next_review_date(card_id)
            else:
                update_next_review_date(card_id)
    conn.commit()


# 插入初始复习日期
def insert_initial_review_dates(card_id):
    review_list = [1, 2, 3, 4, 7, 8, 15, 30]
    table_name = f"individual_record_{card_id}"
    cursor.execute(f"SELECT LearnDate FROM {table_name}")
    learn_date_str = cursor.fetchone()[0]
    current_study_date = datetime.strptime(learn_date_str, '%Y-%m-%d').date()
    for interval in review_list:
        next_review_date = current_study_date + timedelta(days=interval)
        cursor.execute(f"INSERT INTO {table_name} (CardID, NextReviewDate) VALUES (?, ?)", (card_id, next_review_date))
    conn.commit()


# 更新下次复习日期
def update_next_review_date(card_id):
    table_name = f"individual_record_{card_id}"
    cursor.execute(f"SELECT NextReviewDate FROM {table_name} WHERE CardID = ? AND LearnDate IS NULL ORDER BY "
                   f"NextReviewDate ASC LIMIT 1", (card_id,))
    result = cursor.fetchone()
    if result:
        next_review_date = result[0]
        cursor.execute("UPDATE flashcards_database SET NextReviewDate = ? WHERE id = ?", (next_review_date, card_id))
        conn.commit()
    else:
        cursor.execute("UPDATE flashcards_database SET status = 3 WHERE id = ?", (card_id,))
        conn.commit()


# 更新单词卡片状态
def update_flashcard_status(choice, flashcard):
    if choice == 'yes' or choice == 'no':
        update_status(choice, flashcard)
    else:
        print("无效的选项")


# 清理数据并退出程序
def cleanup_and_exit(flashcards):
    for flashcard in flashcards:
        status = decide_learning_status(flashcard)
        cursor.execute(f"""
            UPDATE flashcards_database 
            SET status = ?, LearnDate = (SELECT LearnDate FROM {learning_table_name} WHERE CardID = ?)
            WHERE id = ?
        """, (status, flashcard.id, flashcard.id))
        conn.commit()
    create_individual_learning_tables()
    record_learning_status_for_individual_tables()
    cursor.execute(f"DELETE FROM {learning_table_name} WHERE LearningStatus = 2 AND (YesCount > 0 OR NoCount > 0)")
    conn.commit()
    conn.close()
    print("学习完成！")


# 主函数
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
            update_flashcard_status(choice, flashcard)
    cleanup_and_exit(flashcards)


if __name__ == "__main__":
    main()
