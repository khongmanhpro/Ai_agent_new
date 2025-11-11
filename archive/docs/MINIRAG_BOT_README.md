# 🤖 Insurance Bot - MiniRAG Integration

Bot tư vấn bảo hiểm sử dụng **MiniRAG Framework** thay vì truy cập trực tiếp Neo4J.

## 🎯 Tại Sao Dùng MiniRAG?

- ✅ **Framework chuyên nghiệp**: MiniRAG là RAG framework được thiết kế cho small models
- ✅ **Heterogeneous Graph Indexing**: Kết hợp text chunks và named entities
- ✅ **Lightweight Topology-enhanced Retrieval**: Retrieval hiệu quả không cần semantic understanding cao
- ✅ **Tích hợp dễ dàng**: Chỉ cần khởi tạo MiniRAG và query

## 🏗️ Kiến Trúc

```
Insurance Bot (insurance_bot_minirag.py)
    ↓
MiniRAG Framework
    ↓
Neo4J → MiniRAG (load_neo4j_to_minirag.py)
```

## 📁 Files

### Core Files
- `insurance_bot_minirag.py` - Bot chính sử dụng MiniRAG
- `load_neo4j_to_minirag.py` - Script load data từ Neo4J vào MiniRAG

### Configuration
- `insurance_config.ini` - Config với OPENAI_API_BASE cho MiniRAG

## 🚀 Cách Sử Dụng

### 1. Load Data từ Neo4J vào MiniRAG

```bash
cd /Volumes/data/MINIRAG
python load_neo4j_to_minirag.py
```

### 2. Chạy Bot

```bash
python insurance_bot_minirag.py
```

### 3. Test Bot

```bash
python tests/test_bot_cuoi_cung.py
```

## ⚙️ Configuration

### Environment Variables
```ini
# MiniRAG cần OPENAI_API_BASE (không phải OPENAI_BASE_URL)
OPENAI_API_BASE=https://gpt1.shupremium.com/v1
OPENAI_API_KEY=sk-xxx
```

### MiniRAG Settings
```ini
WORKING_DIR=./insurance_rag
EMBEDDING_MODEL=text-embedding-3-small
OPENAI_LLM_MODEL=gpt-4o-mini
```

## 🔧 Technical Details

### Embedding Function
MiniRAG yêu cầu async embedding function:

```python
async def embedding_func(texts):
    # Call OpenAI API
    return embeddings_list
```

### Query Mode
Sử dụng `QueryParam(mode="mini")` cho retrieval hiệu quả:

```python
from minirag import QueryParam
answer = await rag.aquery(question, param=QueryParam(mode="mini"))
```

## 📊 Performance

- **Framework**: MiniRAG (Heterogeneous Graph Indexing)
- **Embedding**: OpenAI text-embedding-3-small (1536 dim)
- **LLM**: GPT-4o-mini
- **Storage**: Nano Vector DB
- **Retrieval**: Topology-enhanced với cosine similarity

## 🎯 Advantages Over Direct Neo4J

| Feature | Direct Neo4J | MiniRAG |
|---------|-------------|---------|
| Query Language | Cypher | Natural Language |
| Retrieval | Keyword-based | Semantic + Graph |
| Performance | Fast but limited | Better context |
| Maintenance | Complex queries | Simple API calls |
| Scalability | Good | Optimized for RAG |

## 🚨 Troubleshooting

### Lỗi "OPENAI_API_BASE"
- Thêm `OPENAI_API_BASE=https://gpt1.shupremium.com/v1` vào config

### Lỗi "object list can't be used in 'await'"
- Embedding function phải là async và return list of embeddings

### Bot trả về "Sorry, I'm not able to provide an answer"
- Kiểm tra data đã được load vào MiniRAG chưa
- Kiểm tra embedding function hoạt động đúng
- Thử với query đơn giản hơn

## 🔄 Migration Process

1. ✅ Load data từ Neo4J → MiniRAG
2. ✅ Test MiniRAG với dummy embedding
3. ✅ Implement async embedding function
4. ✅ Update Insurance Bot to use MiniRAG
5. ✅ Test end-to-end functionality

## 📈 Next Steps

- [ ] Fine-tune retrieval parameters
- [ ] Add more document types
- [ ] Implement conversation memory
- [ ] Add evaluation metrics
- [ ] Deploy to production

---

**🎉 Insurance Bot giờ đã sử dụng MiniRAG framework chuyên nghiệp!**
