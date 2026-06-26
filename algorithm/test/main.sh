#!/bin/bash

# 设置颜色
GREEN='\033[0;32m'
NC='\033[0m' # No Color，用于重置颜色

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

# 设置分隔
Echo_star(){
    echo "************************************************************"
}


# 模型测试
model_test(){
MODELS=("LLM" "EMBEDDING" "RERANKER")
read -e -p "$(echo -e "${GREEN}[DEBUG]${NC} 调用模型类型编号，\n1: llm(大语言模型) \n2: embedding \n3: reranker \n请选择 >>> ")" NUMBER
if [ "$NUMBER" = "1" ] || [ "$NUMBER" = "2" ] || [ "$NUMBER" = "3" ]; 
then
  MODEL=${MODELS[$(($NUMBER -1))]}
  #echo $MODEL
  read -e -p $'是否需要修改当前'"$MODEL"$'模型配置：\n'"$(grep ^$MODEL $"./config.cfg")"$'\n: yes|no >>> ' modify
  if [ "$modify" = "yes" ]
  then
    read -e -p "请输入$MODEL模型url >>> " new_url
    read -e -p "请输入$MODEL模型id >>> " new_id
    read -e -p "请输入$MODEL模型api_key (如果没有api_key直接回车即可) >>> " new_key
    sed -i "s|${MODEL}_MODEL_URL=.*|${MODEL}_MODEL_URL=$new_url|" $config_file
    sed -i "s|${MODEL}_MODEL_ID=.*|${MODEL}_MODEL_ID=$new_id|" $config_file
    if [ -z $new_key ]; then api_key=;else api_key=$new_key; fi
    sed -i "s|${MODEL}_MODEL_KEY=.*|${MODEL}_MODEL_KEY=$api_key|" $config_file
    log_info "修改$config_file配置完成, $new_url $new_id $new_key"; log_info "修改$config_file配置完成, $new_url $new_id $new_key" >> $deploy_log
    Echo_star
  fi
  log_info "开始执行模型测试文件"
  model_file=$(echo "${MODEL}_test.sh" | tr '[:upper:]' '[:lower:]')
  ./$model_file
  Echo_star
else
  log_error "请输入正确的序号"; exit 1
fi
}

# agent业务测试
process_test(){
if [ -f "connect_websocket.py" ]; then agent_local_file="connect_websocket.py";else agent_local_file="test.py";fi
read -e -p $'是否需要修改当前配置： \n'"$(grep ^AGENT $"./config.cfg")"$'\n: yes|no >>> ' modify
  if [ "$modify" = "yes" ]
  then
    read -e -p "请输入ip (一般是内网ip地址)>>> " new_ip
    read -e -p "请输入port (一般默认16580)>>> " new_port
    sed -i "s|AGENT_IP=.*|AGENT_IP=$new_ip|" $config_file
    if [ -z $new_port ]; then port=16580;else port=$new_port; fi
    sed -i "s|AGENT_PORT=.*|AGENT_PORT=$port|" $config_file
    log_info "修改$config_file配置完成: $new_ip $port"
    sed -i "s|ws://.*/nlp/chatRPA/api|ws://$new_ip:$port/nlp/chatRPA/api|" $agent_local_file
    log_info "修改$agent_local_file配置完成"
    Echo_star
  fi
  log_warring "由于当前终端没有python运行环境, 需要手动拷贝测试脚本到agent_websocket_local容器中，请执行命令:"
  echo "查询容器: docker ps | grep 16580"
  echo "拷贝脚本: docker cp test/$agent_local_file <dockerid>(上述获取到的容器id或名称):/"
  echo "进入容器: docker exec -it <dockerid>(上述获取到的容器id或名称) bash"
  echo "执行脚本: cd /; python3 $agent_local_file"
  echo "如有问题联系工程师分析并处理" 
}

deploy_log="../deploy.log"
config_file="./config.cfg"
read -e -p "$(echo -e "${GREEN}[DEBUG]${NC} 请输入测试类型: 1: 模型测试, 2: 算法agent业务流程测试 >>> ")" TYPE
if [ "$TYPE" = "1" ]; then model_test; elif [ "$TYPE" = "2" ]; then process_test; else log_error "请输入正确的编号"; fi
