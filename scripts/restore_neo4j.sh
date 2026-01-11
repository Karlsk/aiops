#!/bin/bash
# restore_neo4j.sh - Neo4j Docker 恢复脚本

# 配置参数
CONTAINER_NAME="neo4j"  # Docker 容器名称
BACKUP_DIR="/opt/test_neo4j/backups"  # 宿主机备份目录
DB_NAME="neo4j"  # 数据库名称
CONTAINER_BACKUP_DIR="/backups"  # 容器内备份目录

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Neo4j Docker 恢复脚本${NC}"
echo -e "${GREEN}开始时间: $(date)${NC}"
echo -e "${GREEN}========================================${NC}"

# 显示使用说明
if [ $# -eq 0 ]; then
    echo -e "${YELLOW}使用方法:${NC}"
    echo -e "  $0 <备份文件名>  # 例如: backup_20250120_143022.tar.gz"
    echo -e "  $0 latest        # 使用最新的备份文件"
    echo ""
    echo -e "${BLUE}可用的备份文件:${NC}"
    ls -lht "$BACKUP_DIR"/*.tar.gz 2>/dev/null | head -10 || echo "  无备份文件"
    exit 1
fi

# 检查 Docker 容器是否运行
if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo -e "${RED}错误: Neo4j 容器 '${CONTAINER_NAME}' 未运行${NC}"
    exit 1
fi

# 确定要恢复的备份文件
if [ "$1" = "latest" ]; then
    BACKUP_FILE=$(ls -t "$BACKUP_DIR"/*.tar.gz 2>/dev/null | head -1)
    if [ -z "$BACKUP_FILE" ]; then
        echo -e "${RED}错误: 未找到任何备份文件${NC}"
        exit 1
    fi
    echo -e "${BLUE}使用最新备份: $(basename "$BACKUP_FILE")${NC}"
else
    BACKUP_FILE="$BACKUP_DIR/$1"
    if [ ! -f "$BACKUP_FILE" ]; then
        echo -e "${RED}错误: 备份文件不存在: $BACKUP_FILE${NC}"
        exit 1
    fi
fi

# 确认恢复操作
echo -e "${YELLOW}⚠️  警告: 此操作将覆盖当前数据库!${NC}"
echo -e "备份文件: $(basename "$BACKUP_FILE")"
echo -e "文件大小: $(du -h "$BACKUP_FILE" | cut -f1)"
echo -e "数据库名: $DB_NAME"
echo ""
read -p "确定要继续吗? (yes/no): " -r
if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    echo -e "${YELLOW}操作已取消${NC}"
    exit 0
fi

echo -e "${YELLOW}[1/6] 解压备份文件...${NC}"
TEMP_DIR=$(mktemp -d)
tar -xzf "$BACKUP_FILE" -C "$TEMP_DIR"
DUMP_FILE=$(find "$TEMP_DIR" -name "*.dump" | head -1)

if [ ! -f "$DUMP_FILE" ]; then
    echo -e "${RED}错误: 备份文件中未找到 .dump 文件${NC}"
    rm -rf "$TEMP_DIR"
    exit 1
fi

echo -e "${YELLOW}[2/6] 创建容器内备份目录...${NC}"
docker exec "$CONTAINER_NAME" mkdir -p "$CONTAINER_BACKUP_DIR"

echo -e "${YELLOW}[3/6] 复制备份文件到容器...${NC}"
docker cp "$DUMP_FILE" "$CONTAINER_NAME:$CONTAINER_BACKUP_DIR/$DB_NAME.dump"

if [ $? -ne 0 ]; then
    echo -e "${RED}错误: 复制备份文件失败${NC}"
    rm -rf "$TEMP_DIR"
    exit 1
fi

echo -e "${YELLOW}[4/6] 停止 Neo4j 容器...${NC}"
echo -e "${BLUE}提示: 正在停止容器，服务将暂时不可用...${NC}"
docker stop "$CONTAINER_NAME"
sleep 3

echo -e "${YELLOW}[5/6] 启动容器并恢复数据库...${NC}"
echo -e "${BLUE}提示: 启动容器但不启动 Neo4j 服务...${NC}"
# 启动容器但 Neo4j 服务不会自动启动
docker start "$CONTAINER_NAME"
sleep 5

# 在 Neo4j 服务未运行时执行数据库恢复
echo -e "${BLUE}正在加载备份数据...${NC}"
docker exec "$CONTAINER_NAME" neo4j-admin database load "$DB_NAME" \
    --from-path="$CONTAINER_BACKUP_DIR" \
    --overwrite-destination=true

RESTORE_STATUS=$?

echo -e "${YELLOW}[6/6] 重启容器并启动 Neo4j 服务...${NC}"
echo -e "${BLUE}提示: 重启容器，Neo4j 服务将自动启动...${NC}"
docker restart "$CONTAINER_NAME"
sleep 15

# 清理临时文件
rm -rf "$TEMP_DIR"
docker exec "$CONTAINER_NAME" rm -f "$CONTAINER_BACKUP_DIR/$DB_NAME.dump"

if [ $RESTORE_STATUS -ne 0 ]; then
    echo -e "${RED}========================================${NC}"
    echo -e "${RED}恢复失败!${NC}"
    echo -e "${RED}请检查日志: docker logs $CONTAINER_NAME${NC}"
    echo -e "${RED}========================================${NC}"
    exit 1
fi

# 验证恢复
echo -e "\n${BLUE}验证数据库连接...${NC}"
sleep 5
docker exec "$CONTAINER_NAME" cypher-shell -u neo4j -p password "MATCH (n) RETURN count(n) as node_count;" 2>/dev/null

if [ $? -eq 0 ]; then
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}✓ 恢复成功!${NC}"
    echo -e "${GREEN}数据库名: $DB_NAME${NC}"
    echo -e "${GREEN}备份文件: $(basename "$BACKUP_FILE")${NC}"
    echo -e "${GREEN}完成时间: $(date)${NC}"
    echo -e "${GREEN}========================================${NC}"
else
    echo -e "${YELLOW}⚠️  恢复完成，但无法验证连接${NC}"
    echo -e "${YELLOW}请手动检查: docker exec $CONTAINER_NAME cypher-shell${NC}"
fi

echo -e "\n${BLUE}提示:${NC}"
echo -e "  查看日志: docker logs $CONTAINER_NAME"
echo -e "  进入容器: docker exec -it $CONTAINER_NAME bash"
echo -e "  访问浏览器: http://localhost:7474"