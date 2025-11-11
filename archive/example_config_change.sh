#!/bin/bash
# Example: Thay đổi port từ 8001 thành 8080

echo "🔄 Thay đổi port từ 8001 thành 8080"
echo "===================================="

# Backup file gốc
cp config/insurance_config.ini config/insurance_config.ini.backup

# Thay đổi port
sed -i 's/API_PORT=8001/API_PORT=8080/' config/insurance_config.ini

echo "✅ Đã thay đổi port thành 8080"
echo ""
echo "📋 Kiểm tra thay đổi:"
grep "API_PORT" config/insurance_config.ini
echo ""
echo "🔄 Khởi động lại server:"
echo "python core/insurance_api_simple.py"
echo ""
echo "🌐 Truy cập Swagger UI:"
echo "http://localhost:8080/api/docs"
echo ""
echo "↩️  Để khôi phục:"
echo "cp config/insurance_config.ini.backup config/insurance_config.ini"
