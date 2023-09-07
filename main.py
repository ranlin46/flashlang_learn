import sqlite3
import random
import pygame

# 初始化pygame
pygame.init()
# 连接到数据库文件
conn = sqlite3.connect('flashcards_database.db')
cursor = conn.cursor()


class Flashcard:
    def __init__(self, id, status, phonetic, word, sentence, audio_url, study_count):
        self.id = id
        self.status = status
        self.phonetic = phonetic
        self.word = word
        self.sentence = sentence
        self.audio_url = audio_url
        self.study_count = study_count


def load_flashcards():
    cursor.execute("SELECT * FROM flashcards_database WHERE status IN (0, 1, 2)")
    records = cursor.fetchall()
    flashcards = [Flashcard(*record) for record in records]
    random.shuffle(flashcards)
    return flashcards


def show_flashcard(flashcard):
    print(f"Phonetic: {flashcard.phonetic}")
    print(f"Word: {flashcard.word}")
    print(f"Sentence: {flashcard.sentence}")
    print(f"Audio URL: {flashcard.audio_url}")

    # 播放音频
    pygame.mixer.music.load(flashcard.audio_url)  # 使用音频文件的路径
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        pygame.time.delay(100)  # 每100毫秒检查一次音乐是否仍在播放


def update_status(flashcard, choice):
    if choice == "familiar":
        flashcard.status = 3  # 掌握
    elif choice == "review":
        flashcard.status = 2  # 复习
        flashcard.study_count += 1
    elif choice == "learn":
        flashcard.status = 1  # 学习
        flashcard.study_count += 1


def main():
    flashcards = load_flashcards()
    quit_program = False  # 添加一个标志来控制是否退出程序

    while flashcards and not quit_program:
        flashcard = random.choice(flashcards)  # 随机选择一个卡片
        show_flashcard(flashcard)
        choice = input("\nChoose an action (learn/review/familiar) or press 'q' to quit: ").lower()

        if choice == 'q':
            quit_program = True
        else:
            update_status(flashcard, choice)
            cursor.execute("UPDATE flashcards SET status = ?, study_count = ? WHERE id = ?",
                           (flashcard.status, flashcard.study_count, flashcard.id))
            conn.commit()

    conn.close()
    print("学习完成！")


if __name__ == "__main__":
    main()
