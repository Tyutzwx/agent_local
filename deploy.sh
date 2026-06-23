#!/bin/bash

# 设置颜色
BLACK='\033[0;30m'
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[0;37m'
NC='\033[0m' # No Color，用于重置颜色

# 基本用法
#echo -e "${RED}这是红色文字${NC}"
#echo -e "${GREEN}这是绿色文字${NC}"
#echo -e "${YELLOW}这是黄色文字${NC}"
#echo -e "${BLUE}这是蓝色文字${NC}"
#echo -e "${PURPLE}这是紫色文字${NC}"
#echo -e "${CYAN}这是青色文字${NC}"

# 设置日志
log_info() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [INFO] $*"
}
log_warring() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [WARN] $*"
}
log_debug() {
    echo -e "${GREEN}[DEBUG]${NC} $*"
}
log_error() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [ERROR] $*"
}

# 设置分割
Echo_star(){
    echo "************************************************************"
}


modify_dify(){
read -e -p $'当前企业大脑的配置:\n'"$(grep LOCAL_DIFY_URL $"./docker-compose.yaml")"$'\n请输入新的企业大脑平台的ip和端口, 示例: 127.0.0.1:8089 >>> ' new_ip_port
sed -i "s|LOCAL_DIFY_URL=http://.*/frameWorkPortal/agent|LOCAL_DIFY_URL=http://$new_ip_port/frameWorkPortal/agent|" $compose_file
sed -i "s|FILE_UPLOAD_URL=.*|FILE_UPLOAD_URL=http://$new_ip_port/agent_proxy|" $compose_file
sed -i "s|ADMIN_URL=.*|ADMIN_URL=http://$new_ip_port/agent_proxy|" $compose_file
sed -i "s|MINIO_INTERNAL_URL=http://.*/szzn-minio|MINIO_INTERNAL_URL=http://$new_ip_port/szzn-minio|" $compose_file
sed -i "s|MINIO_EXTERNAL_URL=http://.*/szzn-minio|MINIO_EXTERNAL_URL=http://$new_ip_port/szzn-minio|" $compose_file
log_info "企业大脑dify平台配置修改完成 http://$new_ip_port" >> deploy.log
}

modify_llm(){
read -e -p $'当前大语言模型配置:\n'"$(grep LOCAL_LLM $"./docker-compose.yaml")"$'\n'"$(grep API_KEY $"./docker-compose.yaml")"$'\n请输入大模型URL (示例: http://127.0.0.1:16000/v1) >>> ' new_url
read -e -p $'请输入大模型uid >>> ' new_uid
read -e -p $'请输入大模型API_KEY (如果没有直接回车即可) >>> ' new_key
if [ -z $new_key ]; then api_key="xxx";else api_key=$new_key; fi
sed -i "s|LOCAL_LLM_URL=.*|LOCAL_LLM_URL=$new_url|" $compose_file
sed -i "s|LOCAL_LLM_UID=.*|LOCAL_LLM_UID=$new_uid|" $compose_file
sed -i "s|API_KEY=.*|API_KEY=$api_key|" $compose_file

sed -i "s|LLM_MODEL_URL=.*|LLM_MODEL_URL=$new_url/chat/completions|" $config_file
sed -i "s|LLM_MODEL_ID=.*|LLM_MODEL_ID=$new_uid|" $config_file
if [ -z $new_key ]; then api_key=;else api_key=$new_key; fi
sed -i "s|LLM_MODEL_KEY=.*|LLM_MODEL_KEY=$api_key|" $config_file
log_info "大模型配置修改完成: $new_url $new_uid $new_key" >> deploy.log
}

modify_embedding(){
read -e -p $'当前embedding的配置: \n'"$(grep LOCAL_EMB $"./docker-compose.yaml")"$'\n请输入embedding的URL (示例: http://127.0.0.1:16001/v1/embeddings) >>> ' new_url
read -e -p $'请输入embedding的uid >>> ' new_uid
sed -i "s|LOCAL_EMB_URL=.*|LOCAL_EMB_URL=$new_url|" $compose_file
sed -i "s|LOCAL_EMB_UID=.*|LOCAL_EMB_UID=$new_uid|" $compose_file

sed -i "s|EMBEDDING_MODEL_URL=.*|EMBEDDING_MODEL_URL=$new_url|" $config_file
sed -i "s|EMBEDDING_MODEL_ID=.*|EMBEDDING_MODEL_ID=$new_uid|" $config_file
log_info "embedding配置修改完成: http://$new_ip:$new_port/v1/embeddings $new_uid" >> deploy.log
}

modify_db(){
read -e -p $'当前数据库的配置: \n'"$(grep -e MYSQL -e DB  $"./docker-compose.yaml" | grep -v PASSWORD)"$'\n'"$(echo -e "${GREEN}[DEBUG]${NC}是否需要修改配置 yes|no >>> ")" modify
if [ "$modify" = "yes" ]
then
  read -e -p $'请输入数据库的HOSR >>> ' new_host
  read -e -p $'请输入数据库的PORT >>> ' new_port
  sed -i "s|MYSQL_HOST=.*|MYSQL_HOST=$new_host|" $compose_file
  sed -i "s|MYSQL_PORT=.*|MYSQL_PORT=$new_port|" $compose_file
  if [ -n "$(grep DB $"./docker-compose.yaml")" ]
  then
    read -e -p $'请输入数据库的DB (默认saas,无特殊情况输入: saas) >>> ' new_db
    read -e -p $'请输入数据库的USER >>> ' new_user
    read -e -p $'请输入数据库的PASSWORD >>> ' new_password
    read -e -p $'请输入数据库的TYPE (可选: mysql, dm, kb) >>> ' new_type
    read -e -p $'请输入数据库的SCHEMA (默认public,无特殊情况输入: public) >>> ' new_schema
    sed -i "s|DB_DB=.*|DB_DB=$new_db|" $compose_file
    sed -i "s|DB_USER=.*|DB_USER=$new_user|" $compose_file
    sed -i "s|DB_PASSWORD=.*|DB_PASSWORD=$new_password|" $compose_file
    sed -i "s|DB_TYPE=.*|DB_TYPE=$new_type|" $compose_file
    sed -i "s|DB_SCHEMA=.*|DB_SCHEMA=$new_schema|" $compose_file
    log_info "数据库配置修改完成: $new_host:$new_port" >> deploy.log
    if [ $new_type != "mysql" ]; then log_warring "当前选择数据库类型为: $new_type, 请在目标数据库手动执行sql目录下对应的数据库文件"; fi
  fi
fi
}

server_deploy(){
compose_file="./docker-compose.yaml"
if [ ! -f "./deploy.log" ]; then
    log_info "检测到当前首次执行脚本，开始加载服务镜像"
    for i in `ls ./images`;do docker load -i images/$i;done
    log_info "服务镜像加载完成"
    log_info "load image success"  > deploy.log
    cp docker-compose.yaml tools/docker-compose.yaml.bak
    cp test/config.cfg tools/config.cfg.bak
    log_info "基础配置文件备份完成" >> deploy.log
    Echo_star

    log_info "首次启动需要修改初始配置"
    modify_dify
    modify_llm
    modify_embedding
    modify_db
else
    log_warring "检测到当前非首次执行脚本，跳过服务镜像加载。"
    read -e -p  $'请选择要单独修改的配置内容 \n1: 修改企业大脑地址 \n2: 修改大语言模型地址 \n3: 修改embedding模型地址 \n请选择 >>> ' RE_MODIFY
    if [ "$RE_MODIFY" = "1" ]; then modify_dify; elif [ "$RE_MODIFY" = "2" ]; then modify_llm; elif [ "$RE_MODIFY" = "3" ]; then modify_embedding; fi
fi


# 启动服务
read -e -p "$(echo -e "${GREEN}[DEBUG]${NC} 是否启动agent服务或修改配置后重启agent服务 yes|no >>> ")" start
if [ "$start" = "yes" ]
then
  docker-compose -v
  if [ $? -ne 0 ]; then cp tools/docker-compose-Linux-x86_64 /usr/local/bin/docker-compose;fi
  docker-compose up -d
  if [ $? = 0 ]; then log_info "服务启动完成"; log_info "服务启动完成" >> deploy.log;else log_error "服务启动失败";exit 1;fi
fi
}


server_test(){
cd test
./main.sh
}

server_reset(){
read -e -p "$(echo -e "${GREEN}[DEBUG]${NC} 请再次确认是否恢复原始配置 yes|no >>> ")" init
if [ "$init" = "yes" ]
then
  rm -rf deploy.log
  cp tools/docker-compose.yaml.bak docker-compose.yaml
  cp tools/config.cfg.bak test/config.cfg
  log_info "服务配置重置完成"
fi
}

compose_file="./docker-compose.yaml"
config_file="./test/config.cfg"
read -e -p  $'**********输入你要执行的场景********** \n1: 算法服务初始化启动 \n2: 模型测试和业务流程测试 \n3: 服务配置重置(请谨慎使用) \n请选择 >>> ' PROCESS
if [ "$PROCESS" = "1" ]; then server_deploy; elif [ "$PROCESS" = "2" ]; then server_test; elif [ "$PROCESS" = "3" ]; then server_reset; fi
