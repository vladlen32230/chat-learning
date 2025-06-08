### What does it do?

![Screenshot](https://github.com/vladlen32230/vladlen32230/blob/main/Screenshot%20from%202025-06-08%2008-06-41.png)

Accepts several images or pdf files, converts it to text, chunking into logical parts and choosing chat character to talk with about this part. It also has STT and TTS. Suitable for education.

### Used Technologies:
- Mistral OCR
- qwen2.5 72B
- gemini 2.5 flash OR gemini 2.5 pro
- kokoro TTS
- whisper STT
- streamlit
- fastapi
- sqlite

### How to run:
- Set your API keys in docker-compose.yaml file
- ```bash
  docker compose up
  ```
- Go to http://localhost:8516
