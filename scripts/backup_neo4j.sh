#!/bin/bash
# backup_neo4j.sh - Neo4j Docker 备份脚本

# 配置参数
CONTAINER_NAME="neo4j"  # Docker 容器名称
BACKUP_DIR="/opt/test_neo4j/backups"  # 宿主机备份目录
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="neo4j"  # 数据库名称
CONTAINER_BACKUP_DIR="/backups"  # 容器内备份目录

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Neo4j Docker 备份脚本${NC}"
echo -e "${GREEN}开始时间: $(date)${NC}"
echo -e "${GREEN}========================================${NC}"

# 检查 Docker 容器是否运行
if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo -e "${RED}错误: Neo4j 容器 '${CONTAINER_NAME}' 未运行${NC}"
    exit 1
fi

# 创建宿主机备份目录
mkdir -p "$BACKUP_DIR"

# 检查容器内备份目录是否存在，不存在则创建
docker exec "$CONTAINER_NAME" mkdir -p "$CONTAINER_BACKUP_DIR"

echo -e "${YELLOW}[1/5] 开始备份数据库: $DB_NAME${NC}"

# 社区版必须停止数据库才能备份，使用容器停止/启动方式
echo -e "${YELLOW}[2/5] 停止 Neo4j 容器...${NC}"
echo -e "${BLUE}提示: 正在停止容器，服务将暂时不可用...${NC}"
docker stop "$CONTAINER_NAME"
sleep 3

echo -e "${YELLOW}[3/5] 启动容器（不启动 Neo4j 服务）...${NC}"
# 启动容器但不启动 Neo4j 服务，以便执行备份
docker start "$CONTAINER_NAME"
sleep 5

echo -e "${YELLOW}[4/5] 执行数据库备份...${NC}"
# 在容器启动但 Neo4j 未运行时执行备份
docker exec "$CONTAINER_NAME" neo4j-admin database dump "$DB_NAME" \
    --to-path="$CONTAINER_BACKUP_DIR"

BACKUP_STATUS=$?

echo -e "${YELLOW}[5/5] 重启容器并启动 Neo4j 服务...${NC}"
# 重启容器，Neo4j 服务将自动启动
docker restart "$CONTAINER_NAME"
sleep 15

if [ $BACKUP_STATUS -ne 0 ]; then
    echo -e "${RED}错误: 数据库备份失败${NC}"
    echo -e "${YELLOW}提示: 请检查容器日志 - docker logs $CONTAINER_NAME${NC}"
    exit 1
fi

# 从容器复制备份文件到宿主机
echo -e "${YELLOW}复制备份文件到宿主机...${NC}"
docker cp "$CONTAINER_NAME:$CONTAINER_BACKUP_DIR/$DB_NAME.dump" \
    "$BACKUP_DIR/backup_${DATE}.dump"

if [ $? -ne 0 ]; then
    echo -e "${RED}错误: 复制备份文件失败${NC}"
    exit 1
fi

# 压缩备份文件
echo "压缩备份文件..."
cd "$BACKUP_DIR" && tar -czf "backup_${DATE}.tar.gz" "backup_${DATE}.dump"

if [ $? -eq 0 ]; then
    # 删除未压缩的备份文件
    rm -f "$BACKUP_DIR/backup_${DATE}.dump"
    echo -e "${GREEN}✓ 备份文件已压缩: backup_${DATE}.tar.gz${NC}"
else
    echo -e "${YELLOW}⚠ 压缩失败，保留原始备份文件${NC}"
fi

# 清理容器内的临时备份
docker exec "$CONTAINER_NAME" rm -f "$CONTAINER_BACKUP_DIR/$DB_NAME.dump"

# 删除30天前的备份
echo "清理旧备份文件..."
OLD_BACKUPS=$(find "$BACKUP_DIR" -name "*.tar.gz" -mtime +30)
if [ -n "$OLD_BACKUPS" ]; then
    find "$BACKUP_DIR" -name "*.tar.gz" -mtime +30 -delete
    echo -e "${GREEN}✓ 已删除30天前的备份${NC}"
fi

# 显示备份信息
BACKUP_SIZE=$(du -h "$BACKUP_DIR/backup_${DATE}.tar.gz" 2>/dev/null | cut -f1)
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}备份完成!${NC}"
echo -e "${GREEN}备份文件: backup_${DATE}.tar.gz${NC}"
echo -e "${GREEN}文件大小: ${BACKUP_SIZE}${NC}"
echo -e "${GREEN}保存位置: $BACKUP_DIR${NC}"
echo -e "${GREEN}完成时间: $(date)${NC}"
echo -e "${GREEN}========================================${NC}"

# 列出所有备份文件
echo -e "\n当前所有备份文件:"
ls -lh "$BACKUP_DIR"/*.tar.gz 2>/dev/null || echo "无备份文件"