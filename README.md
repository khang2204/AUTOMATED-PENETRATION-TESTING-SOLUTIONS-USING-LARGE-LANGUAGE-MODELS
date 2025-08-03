# Thông tin Nhóm

## Tên đề tài  
**Nghiên cứu giải pháp tự động hóa kiểm thử thâm nhập sử dụng mô hình ngôn ngữ lớn**

## Thành viên nhóm

| STT | Họ và tên               | MSSV     |
|-----|-------------------------|----------|
| 1   | Trần Vỹ Khang           | 22520628 |
| 2   | Nguyễn Đặng Nguyên Khang| 22520617 |

---

# Hướng Dẫn Cài Đặt & Chạy Hệ Thống VulnBot

## 🧠 Phần 1: Cài và Chạy VulnBot

> ⚙️ **Yêu cầu:** Chạy trên máy chủ chính (bất kỳ OS nào có Python 3.8+)

### 1. Truy cập vào thư mục VulnBot
```bash
cd vulnbot
```

### 2. Cài đặt thư viện cần thiết
```bash
pip install -r requirements.txt
```

### 3. Khởi tạo dự án VulnBot
```bash
python cli.py init
```

### 4. Chạy VulnBot
```bash
python cli.py vulnbot -m {max_interactions}
```

Thay `{max_interactions}` bằng số lượt tương tác tối đa mong muốn (ví dụ: `10`, `50`, `100`, ...)

---

## 🤖 Phần 2: Cài và Chạy Agents

> ⚠️ **Yêu cầu bắt buộc:** Máy chạy Agents phải là **Kali Linux**

### 1. Tạo Python Virtual Environment
```bash
python3 -m venv env
source env/bin/activate
```

### 2. Cài đặt thư viện cần thiết
```bash
pip install -r requirements.txt
```

### 3. Khởi động Agent Server (API)
```bash
python3 -m api_server.main
```

Tùy theo mô hình sử dụng, bạn cần cấu hình file `vulnbot/model_config.yaml` như sau:

### ✅ Dùng OpenAI (gpt-4o-mini)

```yaml
api_key: YOUR_API_KEY_HERE
llm_model: openai
base_url: https://api.openai.com/v1
llm_model_name: gpt-4o-mini
embedding_models: maidalun1020/bce-embedding-base_v1
embedding_type: local
context_length: 120000
embedding_url: ''
rerank_model: maidalun1020/bce-reranker-base_v1
temperature: 0.5
history_len: 5
timeout: 600
proxies: {}
```

### ✅ Dùng LLaMA 3.2 (qua Ollama)

```yaml
api_key: 
llm_model: ollama
base_url: http://localhost:11434
llm_model_name: llama3.2-lora
embedding_models: maidalun1020/bce-embedding-base_v1
embedding_type: local
context_length: 120000
embedding_url: ''
rerank_model: maidalun1020/bce-reranker-base_v1
temperature: 0.5
history_len: 5
timeout: 600
proxies: {}
```

## 🛠️ Tạo Mô Hình `llama3.2-lora` với Ollama
### 📁 Bước 1: Truy cập thư mục chứa `Modelfile`
```bash
cd llama32
```
### ⚙️ Bước 2: Tạo mô hình từ `Modelfile`

```bash
ollama create llama3.2-lora -f Modelfile
```