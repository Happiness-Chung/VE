import requests

def get_file_size(url):
    response = requests.head(url)
    size = response.headers.get('Content-Length', None)
    if size:
        size_in_mb = int(size) / (1024 * 1024)
        print(f"File size: {size_in_mb:.2f} MB")
    else:
        print("Could not determine the file size.")

url = "https://agi.gpt4.org/llama/LLaMA/7B/checklist.chk"  # 다운로드 URL을 넣으세요.
get_file_size(url)
