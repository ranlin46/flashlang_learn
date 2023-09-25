import sqlite3
import random
import pygame

# 初始化pygame
pygame.init()
# 连接到数据库文件
conn = sqlite3.connect('flashcards_database.db')
cursor = conn.cursor()

learning_table_name = "Table2"  # 学习历史表的表名


class Flashcard:
    def __init__(self, id, status, phonetic, word, sentence, audio_url, date):
        self.id = id
        self.status = status
        self.phonetic = phonetic
        self.word = word
        self.sentence = sentence
        self.audio_url = audio_url
        self.date = date


def initialize_tables():
    # 检查并创建表2
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

    inserted_card_ids = set()  # 用于跟踪已经插入的卡片的集合

    # 插入初始数据，确保表2中有10条不重复的数据
    while not enough_data_in_table2():
        flashcard = random.choice(load_flashcards())

        # 检查是否已经插入过该卡片，如果是，则重新选择一个
        while flashcard.id in inserted_card_ids:
            flashcard = random.choice(load_flashcards())

        # 插入数据
        cursor.execute('''
            INSERT INTO Table2 (LearnDate, CardID, YesCount, NoCount, LearningStatus)
            VALUES (?, ?, ?, ?, ?)
        ''', (flashcard.date, flashcard.id, 0, 0, flashcard.status))

        inserted_card_ids.add(flashcard.id)  # 将插入的卡片ID添加到集合中
        conn.commit()

    conn.commit()


def enough_data_in_table2():
    cursor.execute("SELECT COUNT(*) FROM Table2")
    count = cursor.fetchone()[0]
    return count >= 10


def load_flashcards():
    cursor.execute("SELECT * FROM flashcards_database WHERE status IN (1, 2)")
    records = cursor.fetchall()
    flashcards = [Flashcard(*record) for record in records]
    random.shuffle(flashcards)
    return flashcards


def get_flashcards(learning_table_name):
    # 从表2中获取所有的 card_id
    cursor.execute(f"SELECT DISTINCT CardID FROM {learning_table_name}")
    card_ids = [row[0] for row in cursor.fetchall()]

    flashcards = []

    # 根据表2中的 card_id 从表1中加载对应的内容
    for card_id in card_ids:
        cursor.execute("SELECT * FROM flashcards_database WHERE id = ? ", (card_id,))
        record = cursor.fetchone()
        if record:
            flashcard = Flashcard(*record)
            flashcards.append(flashcard)

    random.shuffle(flashcards)
    return flashcards


def show_flashcard(flashcard):
    print(f"Phonetic: {flashcard.phonetic}")
    print(f"Word: {flashcard.word}")
    print(f"Sentence: {flashcard.sentence}")

    # 播放音频
    pygame.mixer.music.load(flashcard.audio_url)  # 使用音频文件的路径
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        pygame.time.delay(100)  # 每100毫秒检查一次音乐是否仍在播放


def update_status(choice, learning_table_name, flashcard):
    if choice == "yes":
        cursor.execute(f"UPDATE {learning_table_name} SET YesCount = YesCount + 1 WHERE CardID = ?",
                       (flashcard.id,))
    elif choice == "no":
        cursor.execute(f"UPDATE {learning_table_name} SET NoCount = NoCount + 1 WHERE CardID = ?",
                       (flashcard.id,))
    else:
        print("无效的选项")

    # 更新学习历史记录中的数据
    cursor.execute(
        f"UPDATE {learning_table_name} SET LearnDate = date('now'), LearningStatus = ? WHERE CardID = ?",
        (decide_learning_status(learning_table_name, flashcard), flashcard.id))

    # 提交更改到数据库
    conn.commit()


def decide_learning_status(learning_table_name, flashcard):
    # 查询学习历史表格中的 "YesCount" 和 "NoCount" 数量
    cursor.execute(f"SELECT YesCount, NoCount FROM {learning_table_name} WHERE CardID = ?", (flashcard.id,))
    result = cursor.fetchone()
    yes_count = result[0] if result else 0
    no_count = result[1] if result else 0

    # 根据 "YesCount" 和 "NoCount" 的数量关系选择学习状态
    if yes_count - no_count > 0:
        return 2
    else:
        return 1


def main():
    initialize_tables()  # 初始化表2
    flashcards = get_flashcards(learning_table_name)
    quit_program = False  # 添加一个标志来控制是否退出程序

    while flashcards and not quit_program:
        flashcard = random.choice(flashcards)  # 随机选择一个卡片
        show_flashcard(flashcard)
        choice = input("\nChoose an action (yes/no) or press 'q' to quit: ").lower()

        if choice == 'q':
            for flashcard in flashcards:
                # 计算学习状态
                status = decide_learning_status(learning_table_name, flashcard)

                # 更新表1的状态和日期
                cursor.execute("UPDATE flashcards_database SET status = ?, date = date('now') WHERE id = ?",
                               (status, flashcard.id))
                conn.commit()

            quit_program = True
        else:
            update_status(choice, learning_table_name, flashcard)

    conn.close()
    print("学习完成！")


if __name__ == "__main__":
    main()
