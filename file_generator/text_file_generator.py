
def file_with_size(size):
    with open(f'file_{size}kb', 'wb') as f:
        num_chars = 1_000 * size    #1_024 did not gave the same results
        f.write(b'0' * num_chars)

def ask_size():
    size = int(input("Size? (in kb): ").strip())
    return size

def file_check_and_print():
    size = int(input("Size? (in kb): ").strip())
    with open(f'file_{size}kb', 'rb') as f:
        content = f.read()
    print(len(content))

if __name__ == "__main__":
    #file_with_size()
    #file_check_and_print()
    sizes = [1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096, 8192]
    for size in sizes:
        file_with_size(size)

