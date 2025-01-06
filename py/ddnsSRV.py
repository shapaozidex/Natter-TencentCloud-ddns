import json
import logging
import time
import os
import sys
from tencentcloud.common import credential  
from tencentcloud.common.profile.client_profile import ClientProfile  
from tencentcloud.common.profile.http_profile import HttpProfile  
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException 
from tencentcloud.dnspod.v20210323 import dnspod_client, models  

# 获取当前脚本所在目录的父目录
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
log_dir = os.path.join(base_dir, 'log')
config_dir = os.path.join(base_dir, 'config')

# 设置日志级别为 INFO，修改 format 和 datefmt 参数
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s',  datefmt='%Y-%m-%d %H:%M')

# 创建 log 目录
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# 添加文件处理器，将日志写入到文件中
log_file_path = os.path.join(log_dir, 'ddns.log')
file_handler = logging.FileHandler(log_file_path, encoding='utf-8')
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s', '%Y-%m-%d %H:%M'))
logging.getLogger().addHandler(file_handler)

# 读取配置文件
config_id_path = os.path.join(config_dir, 'ID.json')
config_srv_path = os.path.join(config_dir, 'natter.json')
config_ipv4_path = os.path.join(config_dir, 'config.json')

# 读取整个配置文件
with open(config_id_path, 'r', encoding='utf-8') as config_ID:
    configs_ID = json.load(config_ID)  

with open(config_srv_path, 'r', encoding='utf-8') as config_SRV:
    configs_SRV = json.load(config_SRV)  

with open(config_ipv4_path, 'r', encoding='utf-8') as config_IPV4:
    configs_IPV4 = json.load(config_IPV4)








# 获取公网 SRV 的配置
script_name_static_SRV = "script2"
config_static_SRV = configs_IPV4.get(script_name_static_SRV, {}) 

# 获取 tencent_api 的配置
tencent_api_config_ID = "tencent_api"
tencent_api_config = configs_ID.get(tencent_api_config_ID, {})

# 获取 script0 中的域名的配置
domain_config_id = "script0"
domain_config = configs_ID.get(domain_config_id, {})





# 获取启动参数中的静态端口信息
def Static_Port():
    try:
        PORT_IDENTIFIER = int(sys.argv[1])  # 本地端口号获取
    except (IndexError, ValueError):
        PORT_IDENTIFIER = None
    return PORT_IDENTIFIER


PORT_IDENTIFIER = Static_Port()



# 读取缓存文件中的动态端口信息
def read_dynamic_port():
    try:
        open_json_path = os.path.join(log_dir, 'OPEN.json')
        with open(open_json_path, "r", encoding="utf-8") as cache_file:
            cache_data_list = [json.loads(line) for line in cache_file]
            
            static_port = Static_Port()
            
            matching_data = next((data for data in cache_data_list if data.get("LANport") == static_port), None)
            
            dynamic_port = matching_data.get("port") if matching_data else None
            
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        dynamic_port = None
    return dynamic_port



def get_config_by_port(configs, target_port):
    # 寻找匹配的PORT项
    for key, value in configs.items():
        if "PORT" in value and value["PORT"] == target_port:
            return value
    return None

# 从 Static_Port() 获取动态的PORT
dynamic_port_from_startup = Static_Port()

# 根据启动项传入的PORT获取相应的配置
port_config = get_config_by_port(configs_SRV, dynamic_port_from_startup)







# 实例化要请求产品的 client 对象
cred = credential.Credential(tencent_api_config.get("secret_id", ""), tencent_api_config.get("secret_key", ""))
# 实例化一个http选项，可选的，没有特殊需求可以跳过
http_profile = HttpProfile()
http_profile.endpoint = tencent_api_config.get("endpoint", "")
# 实例化一个client选项，可选的，没有特殊需求可以跳过
client_profile = ClientProfile()
client_profile.httpProfile = http_profile
# 实例化要请求产品的client对象,clientProfile是可选的
client = dnspod_client.DnspodClient(cred, "", client_profile)





# 初始化动态端口变量
last_PORT = None




def create_srv_record(client, domain, port_config, dynamic_port):
    """创建新的SRV记录"""
    try:
        req = models.CreateRecordRequest()
        params = {
            "Domain": domain,
            "SubDomain": port_config.get("SubDomain"),
            "RecordType": "SRV",  # SRV记录类型是固定的
            "RecordLine": port_config.get("RecordLine", "默认"),  # 如果没有配置，使用默认
            "Value": f"{port_config.get('priority', '0 1')} {dynamic_port} {domain}"  # 如果没有priority，使用默认值
        }
        req.from_json_string(json.dumps(params))
        resp = client.CreateRecord(req)
        
        # 更新配置文件中的record_id
        port_config["record_id"] = resp.RecordId
        with open(config_srv_path, 'w', encoding='utf-8') as f:
            json.dump(configs_SRV, f, indent=4, ensure_ascii=False)
            
        log_message = f"成功创建SRV记录，Record ID: {resp.RecordId}"
        logging.info(log_message)
        return resp.RecordId
    except TencentCloudSDKException as err:
        log_error = f"创建SRV记录失败：{err}"
        logging.error(log_error)
        return None

try:
    while True:
        # 获取动态端口
        PORT = read_dynamic_port()

        # 检查端口是否为空或无效
        if not PORT:
            log_message = "当前端口为空，跳过更新"
            logging.info(log_message)
            time.sleep(config_static_SRV.get("sleep", 300))  # 如果没有配置sleep，使用默认值300秒
            continue

        if PORT != last_PORT:    #对比
            last_PORT = PORT     #有变化就写进去

            try:
                # 检查是否存在record_id
                if not port_config.get("record_id"):
                    # 创建新的SRV记录
                    record_id = create_srv_record(client, domain_config["domain"], port_config, PORT)
                    if not record_id:
                        log_message = "创建SRV记录失败，跳过本次更新"
                        logging.error(log_message)
                        continue
                
                # 修改 DDNS 记录
                req = models.ModifyRecordRequest()
                params = {
                    "Domain": domain_config["domain"],
                    "SubDomain": port_config["SubDomain"],
                    "RecordType": "SRV",  # SRV记录类型是固定的
                    "RecordId": port_config["record_id"],
                    "RecordLine": port_config["RecordLine"],
                    "Value": f"{port_config['priority']} {PORT} {domain_config['domain']}"
                }
                req.from_json_string(json.dumps(params))
                resp = client.ModifyRecord(req)

                # 打印更新成功消息和当前端口号
                log_message = f"您的域名 {domain_config['domain']} 更新成功, 当前端口号 {PORT}"
                logging.info(log_message)

            except TencentCloudSDKException as err:
                log_error = f"Tencent Cloud SDK 异常：{err}"
                logging.error(log_error)

        else:
            log_message = "当前 PORT 与之前保存的 PORT 相同，无需更新"
            logging.info(log_message)

        # 等待一段时间之后继续检查
        time.sleep(config_static_SRV.get("sleep", 300))  # 如果没有配置sleep，使用默认值300秒

except Exception as e:
        log_error = f"发生严重错误：{e}"
        logging.exception(log_error)