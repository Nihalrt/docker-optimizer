with open('large-file.bin', 'wb') as f:
    f.seek(100 * 1024 * 1024 - 1)  # 100MB
    f.write(b'\0')