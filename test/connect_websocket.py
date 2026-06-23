import websocket
import json
import uuid
from datetime import datetime
import threading
from collections import defaultdict

# -------------------------------
# 全局变量（控制状态）
sessionId = None
run_sent = False  # 避免重复发送
# query = "我想在下周六从杭州出发到三亚度假一周，帮我查询一下车票信息。推荐一个出发和返回的时间并在12306上预订车票"
# query = "钉钉发你好给阿良"
query = "你好"
# query = "帮我查询到上海的火车票"
# query = "多文件测试"
# query = '介绍一下实在智能, 再介绍一下rpa'
# query = "百度搜索实在智能公司，查看第一条相关新闻"
# query = '查询今天的黄金价格'
# query = '生成任务介绍deepseek'
# query = '组件测试'
sub_task_num = 0
authorization = "D4CE2B3C485193AF9C1E8FFE2322C2FEDF4350AA34130E12C7CF8BEBA5D4CA6DCACFA02D5FE91DCBCD67195A44575646"


# -------------------------------
def send_init(ws):
    queryId = 'test_' + str(uuid.uuid4())
    packetId = 'test_' + str(uuid.uuid4())
    data = {
        'packetId': packetId,
        'authorization': authorization,
        'action': 'query',
        # 'at': {
        #     'type': 'agent'
        # },
        'at': {'owner': False, 'is_process': False, 'icon_url': '', 'outputs': {'answer': {'label': {'zh_Hans': '回答', 'en_US': 'answer'}, 'type': 'string'}}, 'users_count': 5, 'author': '勾陈dify', 'icon': '🤖', 'description': '', 'created_at': 1742207631, 'icon_background': '#FFEAD5', 'cloneable': False, 'tags': [], 'mode': 'advanced-chat', 'publish_range': 'all_team_members', 'model_config': {'text_to_speech': {'voice': '', 'language': '', 'enabled': False}, 'speech_to_text': {'enabled': False}, 'retriever_resource': {'enabled': False}, 'suggested_questions': [], 'file_upload': {'image': {'number_limits': 10, 'transfer_methods': ['remote_url', 'local_file'], 'enabled': True}}, 'opening_statement': '您好，我是实在Agent，需要我帮您做什么呢？', 'sensitive_word_avoidance': {'enabled': False}, 'suggested_questions_after_answer': {'enabled': False}, 'support_file_types': [{'extensions': ['jpg', 'jpeg', 'png', 'webp', 'pdf', 'doc', 'docx', 'xls', 'xlsx', 'txt'], 'name': '文档'}]}, 'account_id': '76590', 'name': '生成人物的介绍（deepseek）', 'user_input_form': [], 'uiId': 'application_5aa76316-a417-4c84-827d-7cf97eee5557', 'id': '5aa76316-a417-4c84-827d-7cf97eee5557', 'is_online': True, 'published_at': 1742215827},
        # 'at':{},
        'attachments': [],
        'options': {
            'deepThinking': True,
            'mode':'ai-assistant',
        },
        'timestamp': 1750400278948,
        'logId': 'test_log_id_123',
        'sessionId': '',
        'queryId': queryId,
        'content': query,
        'extraInfo': {
            'difyUrl': 'http://10.4.2.64',
            'time': 1750400280048,
            'userId': 3389,
            'globalUser': {
                'global-user-uuid': 'e089ee51f0e44680a3cf0ca7b9472157'
		    },
        }
	}
    ws.send(json.dumps(data, ensure_ascii=False))
    print(f"[{datetime.now()}] Sent INIT with ID: {queryId}")

def send_agent_exec(ws, session_id, packetId, timestamp, segmentId, answerId):
    # sub_task_num = 0
    # request_id = 'test_' + str(uuid.uuid4())
    data = {
        'authorization': authorization,
        'action': 'execute-agent',
        'logId': packetId,
        'packetId': packetId,
        'timestamp':timestamp,
        'answerId':answerId,
        'segmentId':segmentId,
        'sessionId':session_id,
        'extraInfo':{
            'userId':'1234567',
            'globalUser': {'global-user-uuid':'1345t'}
        }
    }
    ws.send(json.dumps(data, ensure_ascii=False))
    print(f"[{datetime.now()}] Sent RUN.")

def send_mix_exec(ws, session_id, packetId, timestamp, segmentId, answerId):
    # sub_task_num = 0
    # request_id = 'test_' + str(uuid.uuid4())
    data = {
        'authorization': authorization,
        'action': 'execute-mix',
        'logId': packetId,
        'packetId': packetId,
        'timestamp':timestamp,
        'answerId':answerId,
        'segmentId':segmentId,
        'sessionId':session_id,
        'extraInfo':{
            'userId':'1234567',
            'globalUser': {'global-user-uuid':'1345t'}
        }
    }
    ws.send(json.dumps(data, ensure_ascii=False))
    print(f"[{datetime.now()}] Sent RUN.")

def send_run(ws, session_id):
    sub_task_num = 0
    request_id = 'test_' + str(uuid.uuid4())
    data = {
        'authorization': authorization,
        'action': 'run',
        'payload': {
            'action': 'run',
            'userId': 36429,
            'type': 'flow',
            'autofill': True,
            'sessionId': session_id,
            'sub_task_num': sub_task_num
        },
        'requestId': request_id,
        'difyUrl': 'http://10.4.2.64'
    }
    ws.send(json.dumps(data, ensure_ascii=False))
    print(f"[{datetime.now()}] Sent RUN.")


def send_reflection(ws, session_id):
    sub_task_num = 0
    result = """
    🔹 出发信息（杭州 → 三亚，2025年6月14日，周六）

车次	出发站 → 到达站	出发时间	到达时间	历时	座位类型	可选座位	票价参考（元）
Z385	杭州站 → 三亚站	08:10	次日 05:30	21h20m	硬卧 / 软卧	有票	¥407 / ¥630
K511	杭州站 → 三亚站	14:36	次日 13:05	22h29m	硬卧 / 软卧	有票	¥410 / ¥635
G1301+G297（高铁转车）	杭州东 → 广州南 → 三亚	07:15（杭）→ 12:28（广）转G297 13:05 → 19:50（三）	12h35m	二等座 / 一等座	有票	¥780 / ¥980（合计）
G1303+G6113（高铁转车）	杭州东 → 深圳北 → 三亚	06:58 → 12:20（深）转G6113 13:00 → 20:05（三）	13h07m	二等座 / 一等座	有票	¥785 / ¥985（合计）
    """
    request_id = 'test_' + str(uuid.uuid4())
    data = {
        'authorization': authorization,
        'action': 'run',
        'payload': {
            'action': 'reflect',
            'userId': 36429,
            'type': 'flow',
            'autofill': True,
            'sessionId': session_id,
            'sub_task_num': sub_task_num,
            'result': result
        },
        'requestId': request_id,
        'difyUrl': 'http://10.4.2.64'
    }
    ws.send(json.dumps(data, ensure_ascii=False))
    print(f"[{datetime.now()}] Sent REFLECTION.")

# -------------------------------
def on_open(ws):
    print(f"[{datetime.now()}] WebSocket connected.")
    # 执行初始化和意图识别
    send_init(ws)

    # # 执行子任务单元测试
    sessionId = "7IAgWuHYQm2jONGxQKVr"
    # send_run(ws, sessionId)
    # send_reflection(ws, sessionId)
    
# 保存每个 streamId 的内容
stream_buffer = defaultdict(str)

def on_message(ws, message):
    global sessionId, run_sent

    print(f"[{datetime.now()}] Message received:\n{message}\n")

    try:
        data = json.loads(message)

        # 只处理 streaming 类型的消息
        if data.get("action") == "streaming":
            stream_id = data.get("streamId")
            stream_type = data.get("streamType")
            content = data.get("content", "")

            if stream_type == "content":
                # 累加内容
                stream_buffer[stream_id] += content

            elif stream_type == "end":
                # 输出完整内容
                full_output = stream_buffer.get(stream_id, "")
                print(f"[{datetime.now()}] >>> 完整结果:\n{full_output}\n")

                # 用完删除缓存
                stream_buffer.pop(stream_id, None)

        # # 处理 segment-finish 也可以作为结束标志
        # elif data.get("action") == "segment-finish":
        #     stream_id = data.get("segmentId")
        #     full_output = stream_buffer.get(stream_id, "")
        #     print(f"[{datetime.now()}] >>> segment 完整结果:\n{full_output}\n")
        #     stream_buffer.pop(stream_id, None)
            
        if data['action']=='new-segment' and (data['segment']['type']=='run-agent' or data['segment']['type']=='run-algo-tool'):
            sessionId = data['sessionId']
            packetId = data['packetId']
            timestamp = data['timestamp']
            segmentId = data['segmentId']
            answerId = data['answerId']
            print('heiheihei')
            threading.Thread(target=send_agent_exec, args=(ws, sessionId, packetId, timestamp, segmentId, answerId)).start()
        # 测混合
        if data['action']=='new-segment' and data['segment']['type']=='mix':
            sessionId = data['sessionId']
            packetId = data['packetId']
            timestamp = data['timestamp']
            segmentId = data['segmentId']
            answerId = data['answerId']
            print('heiheihei')
            threading.Thread(target=send_mix_exec, args=(ws, sessionId, packetId, timestamp, segmentId, answerId)).start()

    except Exception as e:
        print(f"[{datetime.now()}] Error parsing message: {e}")
        
    


def on_message_unit(ws, message):
    print(f"[{datetime.now()}] Message received:\n{message}\n")
    pass

def on_error(ws, error):
    print(f"[{datetime.now()}] Error: {error}")


def on_close(ws, close_status_code, close_msg):
    print(f"[{datetime.now()}] WebSocket closed (code: {close_status_code}, msg: {close_msg})")


# -------------------------------
if __name__ == "__main__":
    ws_url = "ws://10.1.0.247:/nlp/chatRPA/api"

    ws = websocket.WebSocketApp(
        ws_url,
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )

    ws.run_forever(ping_interval=30, ping_timeout=10)
