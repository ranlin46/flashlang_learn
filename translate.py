import sqlite3
import csv

conn = sqlite3.connect('flashcards_database.db')
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS flashcards_database (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        status INTEGER,
        phonetic TEXT,
        word TEXT NOT NULL,
        sentence TEXT,
        audio_url TEXT,
        study_count INTEGER
    )
''')

with open('data/url_file.csv', 'r') as csvfile:
    csvreader = csv.reader(csvfile)
    next(csvreader)  # 跳过CSV文件的标题行（如果有）
    for row in csvreader:
        # 不包括 id 列
        cursor.execute("INSERT INTO flashcards_database (status, phonetic, word, sentence, audio_url, study_count) "
                       "VALUES (?, ?, ?, ?, ?, ?)", row)

# 提交所有的插入操作
conn.commit()

# 关闭数据库连接
conn.close()
