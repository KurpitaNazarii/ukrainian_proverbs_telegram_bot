
def read(file_name):
    with open(file_name, "r", encoding='utf8') as f:
        lines = f.readlines()
        text = '\n'.join(lines)
        return text
