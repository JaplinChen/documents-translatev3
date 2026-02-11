#!/bin/bash
# ============================================================
# Ollama 模型初始化腳本
# 用途：啟動 Docker 服務後，自動下載指定的 LLM 模型
# ============================================================

set -e

# 預設模型（可透過環境變數覆蓋）
OLLAMA_MODEL="${OLLAMA_MODEL:-qwen2.5:7b}"
OLLAMA_HOST="${OLLAMA_HOST:-localhost}"
OLLAMA_PORT="${OLLAMA_PORT:-11434}"
OLLAMA_URL="http://${OLLAMA_HOST}:${OLLAMA_PORT}"

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}  Ollama 模型初始化腳本${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

# 檢查 Ollama 服務是否就緒
echo -e "${YELLOW}[1/3] 等待 Ollama 服務啟動...${NC}"
MAX_RETRIES=30
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -s "${OLLAMA_URL}/api/tags" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Ollama 服務已就緒${NC}"
        break
    fi
    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo "  等待中... ($RETRY_COUNT/$MAX_RETRIES)"
    sleep 2
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo -e "${RED}✗ 錯誤：Ollama 服務未能在時限內啟動${NC}"
    echo -e "${RED}  請確認 Docker 容器是否正常運行${NC}"
    exit 1
fi

# 檢查模型是否已存在
echo ""
echo -e "${YELLOW}[2/3] 檢查模型狀態...${NC}"
EXISTING_MODELS=$(curl -s "${OLLAMA_URL}/api/tags" | grep -o "\"name\":\"[^\"]*\"" | grep -o ":\"[^\"]*\"" | tr -d ':"')

if echo "$EXISTING_MODELS" | grep -q "^${OLLAMA_MODEL}$"; then
    echo -e "${GREEN}✓ 模型 ${OLLAMA_MODEL} 已存在，跳過下載${NC}"
else
    # 下載模型
    echo ""
    echo -e "${YELLOW}[3/3] 下載模型 ${OLLAMA_MODEL}...${NC}"
    echo -e "${BLUE}  這可能需要幾分鐘，取決於您的網路速度${NC}"
    echo ""

    # 使用 docker exec 在容器內執行 ollama pull
    docker exec ppt-translate-ollama ollama pull "${OLLAMA_MODEL}"

    if [ $? -eq 0 ]; then
        echo ""
        echo -e "${GREEN}✓ 模型 ${OLLAMA_MODEL} 下載完成！${NC}"
    else
        echo -e "${RED}✗ 模型下載失敗${NC}"
        exit 1
    fi
fi

# 顯示當前可用模型
echo ""
echo -e "${BLUE}============================================${NC}"
echo -e "${GREEN}  已安裝的模型列表：${NC}"
echo -e "${BLUE}============================================${NC}"
docker exec ppt-translate-ollama ollama list

echo ""
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}  初始化完成！${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo -e "  Ollama API: ${BLUE}${OLLAMA_URL}${NC}"
echo -e "  預設模型:   ${BLUE}${OLLAMA_MODEL}${NC}"
echo ""
echo -e "${YELLOW}提示：${NC}"
echo -e "  - 前端介面：http://localhost:5194"
echo -e "  - 後端 API：http://localhost:5002"
echo ""
