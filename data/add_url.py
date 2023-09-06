import re

# 读取文件内容
with open('french_words.csv', 'r') as file:
    file_contents = file.read()

# 使用正则表达式来匹配并替换URL
# 这里使用正则表达式捕获括号中的内容，并将其用于构建文件路径
pattern = r'(\d+,\[([^\]]+)\],(\w+),([^,]+),url,\d+)'
matches = re.findall(pattern, file_contents)

for match in matches:
    full_match = match[0]  # 匹配的完整字符串
    index = match[1]      # 第二列的内容
    word = match[2]       # 第三列的内容
    audio_url = f'data/audio/{index}_{word}.MP3'  # 构建文件路径
    replacement = full_match.replace('url', audio_url)

    # 替换文件内容中的匹配项
    file_contents = file_contents.replace(full_match, replacement)

# 将替换后的内容写回文件
with open('url_file.csv', 'w') as file:
    file.write(file_contents)
