from cryptography.fernet import Fernet


class FernetCipher:
    def __init__(self, key):
        self.key = key

    def decrypt(self, enc: str):
        return Fernet(self.key).decrypt(enc.encode()).decode()


if __name__ == '__main__':
    print(b"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=")
    print(str.encode("AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="))
    aes = FernetCipher(b"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=").decrypt(
        "gAAAAABi5cDlDZ89s4Af5A9FMwbIb2NF/h8YAIGzpD/RrKdx86zLK6OHrRdW2g1LVin2WTkIzbnmObew/DBkqXNLbzm7EXWME6oNH7OuuGbZkUphczx5JPMfpmMcChtPHtRr7tN2IdiP2Cu1KgmZh0NET4+d5Qp1hg==")
