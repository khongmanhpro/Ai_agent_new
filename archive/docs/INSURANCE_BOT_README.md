# 🤖 Insurance Bot - Bot Tư Vấn Bảo Hiểm FISS

Bot tư vấn bảo hiểm sử dụng **OpenAI LLM + Neo4J RAG** để trả lời câu hỏi khách hàng một cách chuyên nghiệp và chính xác.

## 🚀 Tính Năng

- ✅ Tư vấn chuyên nghiệp về sản phẩm bảo hiểm
- ✅ Tìm kiếm thông tin từ cơ sở dữ liệu Neo4J
- ✅ Sinh câu trả lời hay bằng OpenAI GPT-4
- ✅ Tuân thủ phong cách giao tiếp của nhân viên FISS
- ✅ Memory cache để tăng tốc độ phản hồi
- ✅ Không hiển thị nguồn tài liệu (References)

## 📋 Yêu Cầu

- Python 3.8+
- Neo4J database với dữ liệu bảo hiểm
- OpenAI API key (hoặc compatible service)

## ⚙️ Cấu Hình

Đã cấu hình trong `insurance_config.ini`:

```ini
# OpenAI API Configuration
OPENAI_API_KEY=sk-5cAvNNn5Vqab3EjyAz7lQ1SZn10uYrds4QzRJYbwsM1VuPKY
OPENAI_BASE_URL=https://gpt1.shupremium.com/v1

# OpenAI LLM Configuration
OPENAI_LLM_MODEL=gpt-4o-mini
OPENAI_LLM_MAX_TOKENS=1000
OPENAI_LLM_TEMPERATURE=0.7
```

## 🎯 Cách Sử Dung

### Chạy Bot Interactive:

```bash
cd /Volumes/data/MINIRAG
python insurance_bot.py
```

### Sử dụng trong Code:

```python
from insurance_bot import InsuranceBot
import asyncio

async def main():
    bot = InsuranceBot()
    try:
        answer = await bot.chat("Bảo hiểm xe máy là gì?")
        print(answer)
    finally:
        await bot.close()

asyncio.run(main())
```

## 💬 Ví Dụ Tương Tác

**Khách hàng:** "Bảo hiểm xe máy là gì?"

**Bot:** "Dạ, em xin giải đáp thắc mắc của anh/chị về bảo hiểm xe máy. Bảo hiểm xe máy là sản phẩm bảo hiểm giúp bảo vệ người sử dụng xe máy khỏi những rủi ro như tai nạn giao thông, hư hỏng xe, hoặc thiệt hại tài sản của bên thứ ba. Khi tham gia bảo hiểm xe máy, bạn sẽ được bồi thường chi phí sửa chữa, điều trị thương tích, hoặc bồi thường cho bên bị thiệt hại trong trường hợp xảy ra sự cố. Đây là giải pháp giúp bạn yên tâm hơn khi tham gia giao thông. Anh/chị có muốn em tư vấn thêm về các gói bảo hiểm xe máy phù hợp không ạ?"

## 🏗️ Kiến Trúc

```
User Query → Keyword Extraction → Neo4J Search → Context Retrieval → OpenAI Generation → Professional Response
```

### Components:

1. **Keyword Extraction**: Phân tích câu hỏi, trích xuất từ khóa quan trọng
2. **Neo4J Search**: Tìm kiếm documents liên quan trong database
3. **Context Retrieval**: Lấy nội dung relevant, loại bỏ metadata
4. **OpenAI Generation**: Sinh câu trả lời dựa trên prompt template
5. **Response Cache**: Lưu cache để tăng tốc cho câu hỏi đã trả lời

## 🎨 Prompt Template

Bot sử dụng prompt chi tiết định nghĩa:
- Vai trò: Nhân viên tư vấn FISS
- Phong cách giao tiếp: Thân thiện, chuyên nghiệp
- Nguyên tắc: Chỉ trả lời dựa trên kiến thức có sẵn
- Cấu trúc trả lời: Chuẩn hóa theo format FISS

## 📊 Thống Kê

- **Documents**: 12 (Legal + Insurance Rules + Insurance)
- **Nodes**: 1,183
- **Relationships**: 1,168
- **Response Time**: ~2-3 giây
- **Accuracy**: Cao (dựa trên context từ Neo4J)

## 🔧 Customization

### Thay đổi Model:

```ini
OPENAI_LLM_MODEL=gpt-4  # Hoặc gpt-3.5-turbo
```

### Điều chỉnh Temperature:

```ini
OPENAI_LLM_TEMPERATURE=0.3  # Thấp hơn = chính xác hơn
```

### Thay đổi Prompt:

Sửa `INSURANCE_BOT_PROMPT` trong `insurance_bot.py`

## 🚨 Lưu Ý Quan Trọng

- **Không tiết lộ**: Không đề cập đến database hay references
- **Tuân thủ pháp luật**: Chỉ cung cấp thông tin chính xác
- **Bảo mật**: Không xử lý thông tin nhạy cảm qua chat
- **Fallback**: Có cơ chế fallback khi không tìm thấy thông tin

## 📞 Hỗ Trợ

- Hotline: 0385 10 10 18
- Email: cskh@fiss.com.vn
- Zalo: 033 6691379

---

**🎉 Insurance Bot đã sẵn sàng phục vụ khách hàng!**
