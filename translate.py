import sqlite3
import csv

conn = sqlite3.connect('flashcards_database.db')
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS Cards (
        CardId INTEGER PRIMARY KEY AUTOINCREMENT,
        Phonetic TEXT,
        Word TEXT NOT NULL,
        Sentence TEXT,
        Audio_url TEXT
    )
''')
# 因为音标符号有点特殊，所以需要加上编码方式，不然有些会出现乱码
with open('data/url_file.csv', 'r', encoding="utf-8") as csvfile:
    csvreader = csv.reader(csvfile)
    next(csvreader)  # 跳过CSV文件的标题行（如果有）
    for row in csvreader:
        # 不包括 id 列
        cursor.execute("INSERT INTO Cards (Phonetic, Word, Sentence, Audio_url )VALUES (?, ?, ?, ?)", row)

cursor.execute('''
    CREATE TABLE IF NOT EXISTS Users (
        UserID INTEGER PRIMARY KEY AUTOINCREMENT,
        Username VARCHAR NOT NULL,
        Password VARCHAR,
        RegistrationDate DATE
    )
''')

cursor.execute("""
CREATE TABLE IF NOT EXISTS UserWordCard (
    RecordID INTEGER PRIMARY KEY,
    UserID INTEGER,
    CardID INTEGER,
    StudyDate DATE,
    NextReviewDate DATE,
    StudyStatus INTEGER
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS StudyRecords (
    RecordID INTEGER PRIMARY KEY,
    UserID INTEGER,
    CardID INTEGER,
    StudyDate DATE,
    StudyCount INTEGER,
    ReviewCount INTEGER
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS ReviewPlans (
    PlanID INTEGER PRIMARY KEY,
    UserID INTEGER,
    CardID INTEGER,
    StudyStatus INTEGER,
    ReviewCount INTEGER,
    NextReviewDate DATE
)
""")

# 提交所有的插入操作
conn.commit()

# 关闭数据库连接
conn.close()
