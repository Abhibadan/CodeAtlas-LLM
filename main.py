import subprocess

def main():
    subprocess.Popen(["python", "server.py"])
    subprocess.Popen(["python", "vectorizer.py"])

if __name__ == "__main__":
    main()
