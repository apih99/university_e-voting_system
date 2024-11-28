import os

dirs = ['static', 'media', 'templates']
for dir_name in dirs:
    os.makedirs(dir_name, exist_ok=True)
