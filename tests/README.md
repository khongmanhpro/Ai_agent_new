# 📋 Hướng Dẫn File Test

## 🎯 **Tổng Quan**

Thư mục `tests/` chứa tất cả các file test để kiểm tra và debug bot Insurance RAG.

## 📁 **Danh Sách File Test**

### 🤖 **Test Bot Chính**
| File | Mô tả | Cách chạy |
|------|--------|-----------|
| `test_bot_cuoi_cung.py` | Test bot hoàn chỉnh với MiniRAG | `python tests/test_bot_cuoi_cung.py` |
| `test_bot_bao_hiem.py` | Test các chức năng bot bảo hiểm | `python tests/test_bot_bao_hiem.py` |
| `test_bot_bao_hiem_mot_lan.py` | Test bot với một câu hỏi duy nhất | `python tests/test_bot_bao_hiem_mot_lan.py` |

### 🔧 **Test Debug & Sửa Lỗi**
| File | Mô tả | Cách chạy |
|------|--------|-----------|
| `debug_tim_kiem_minirag.py` | Debug quá trình tìm kiếm của MiniRAG | `python tests/debug_tim_kiem_minirag.py` |
| `test_bot_da_sua.py` | Test bot sau khi sửa lỗi | `python tests/test_bot_da_sua.py` |
| `test_bot_don_gian.py` | Test phiên bản đơn giản của bot | `python tests/test_bot_don_gian.py` |

### ⚡ **Test Performance**
| File | Mô tả | Cách chạy |
|------|--------|-----------|
| `test_thoi_gian_phan_hoi.py` | Đo thời gian phản hồi của bot | `python tests/test_thoi_gian_phan_hoi.py` |
| `test_thoi_gian_phan_hoi_v2.py` | Phiên bản nâng cao của test thời gian | `python tests/test_thoi_gian_phan_hoi_v2.py` |
| `test_chi_phi_token.py` | Tính chi phí token OpenAI | `python tests/test_chi_phi_token.py` |

### 🏗️ **Test MiniRAG Framework**
| File | Mô tả | Cách chạy |
|------|--------|-----------|
| `test_minirag_don_gian.py` | Test cơ bản MiniRAG | `python tests/test_minirag_don_gian.py` |
| `test_minirag_bat_dong_bo.py` | Test MiniRAG với async operations | `python tests/test_minirag_bat_dong_bo.py` |
| `test_minirag_dong_bo.py` | Test MiniRAG với sync operations | `python tests/test_minirag_dong_bo.py` |
| `test_minirag_gia.py` | Test MiniRAG với dummy data | `python tests/test_minirag_gia.py` |

### 🔌 **Test API Integration**
| File | Mô tả | Cách chạy |
|------|--------|-----------|
| `test_api_integration.py` | Test API endpoints từ frontend | `python tests/test_api_integration.py` |
| `test_swagger_ui.py` | Test Swagger UI và OpenAPI spec | `python tests/test_swagger_ui.py` |

### 🚀 **Chạy Swagger UI**
| File | Mô tả | Cách chạy |
|------|--------|-----------|
| `run_swagger_ui.py` | Chạy API server và mở Swagger UI tự động | `python run_swagger_ui.py` |

### 🔐 **Test Cấu Hình**
| File | Mô tả | Cách chạy |
|------|--------|-----------|
| `test_cau_hinh_openai.py` | Test cấu hình OpenAI API | `python tests/test_cau_hinh_openai.py` |
| `test_xoa_cache.py` | Test chức năng xóa cache | `python tests/test_xoa_cache.py` |

## 🚀 **Cách Sử Dung**

### 1. **Chạy Test Nhanh**
```bash
cd /Volumes/data/MINIRAG

# Test bot hoạt động không
python tests/test_bot_cuoi_cung.py

# Đo thời gian phản hồi
python tests/test_thoi_gian_phan_hoi_v2.py
```

### 2. **Debug Khi Có Lỗi**
```bash
cd /Volumes/data/MINIRAG

# Debug MiniRAG retrieval
python tests/debug_tim_kiem_minirag.py

# Test OpenAI config
python tests/test_cau_hinh_openai.py

# Test Swagger UI & API spec
python tests/test_swagger_ui.py
```

### 3. **Test Swagger UI**
```bash
cd /Volumes/data/MINIRAG

# Chạy Swagger UI tự động (khuyên dùng)
python run_swagger_ui.py

# Hoặc test Swagger UI functionality
python tests/test_swagger_ui.py
```

### 4. **Performance Testing**
```bash
cd /Volumes/data/MINIRAG

# Tính chi phí token
python tests/test_chi_phi_token.py

# Test với nhiều câu hỏi
python tests/test_thoi_gian_phan_hoi_v2.py
```

## 📊 **Kết Quả Mong Đợi**

### ✅ **Test Thành Công**
- Bot trả lời chính xác về bảo hiểm
- Thời gian phản hồi < 45 giây
- Không có lỗi exception

### ❌ **Test Thất Bại**
- Bot trả về lỗi mặc định
- Thời gian phản hồi > 60 giây
- Lỗi kết nối API

## 🔧 **Khắc Phục Lỗi**

### **Lỗi: "OpenAI API quota exceeded"**
```bash
python tests/test_cau_hinh_openai.py  # Kiểm tra API key
```

### **Lỗi: "MiniRAG initialization failed"**
```bash
python tests/debug_tim_kiem_minirag.py  # Debug MiniRAG
```

### **Lỗi: "Response time too slow"**
```bash
python tests/test_thoi_gian_phan_hoi_v2.py  # Đo performance
```

## 📝 **Ghi Chú**

- Tất cả test đều cần kết nối internet cho OpenAI API
- Một số test có thể mất thời gian (30-60 giây)
- File test dùng tiếng Việt để dễ hiểu và sử dụng

---

**Cập nhật lần cuối:** $(date)
**Framework:** MiniRAG + OpenAI + Neo4J
