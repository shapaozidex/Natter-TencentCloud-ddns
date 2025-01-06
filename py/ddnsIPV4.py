import json
import logging
import time
import os
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
config_ipv4_path = os.path.join(config_dir, 'config.json')

# 读取整个配置文件
with open(config_id_path, 'r', encoding='utf-8') as config_ID:
    configs_ID = json.load(config_ID)  

with open(config_ipv4_path, 'r', encoding='utf-8') as config_IPV4:
    configs_IPV4 = json.load(config_IPV4)

# 获取公网 IP 的配置
script_name_static_IP = "script1"
config_static_IP = configs_IPV4.get(script_name_static_IP, {}) 

# 获取 tencent_api 的配置
tencent_api_config_ID = "tencent_api"
tencent_api_config = configs_ID.get(tencent_api_config_ID, {})

# 获取 script0 中的域名的配置
domain_config_id = "script0"
domain_config = configs_ID.get(domain_config_id, {})

def get_current_ip():
    try:
        open_json_path = os.path.join(log_dir, 'OPEN.json')
        with open(open_json_path, "r", encoding="utf-8") as cache_file:
            first_line = cache_file.readline().strip()
            if first_line:
                cache_data = json.loads(first_line)
                mapped_external_ip = cache_data.get("ip", "")
            current_ip = mapped_external_ip.splitlines()[0] if mapped_external_ip else None
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        current_ip = None
    return current_ip

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
last_IP = None

try:
    while True:
        # 获取当前公网 IP
        IP = get_current_ip()

        # 检查IP是否为空或无效
        if not IP:
            log_message = "当前IP为空，跳过更新"
            logging.info(log_message)
            time.sleep(config_static_IP["sleep"])
            continue

        if IP != last_IP:
            last_IP = IP

            # 修改 DDNS 记录
            update_req = models.ModifyRecordRequest()
            update_params = {
                "Domain": domain_config["domain"],
                "SubDomain": config_static_IP["SubDomain"],
                "RecordType": config_static_IP["RecordType"],
                "RecordId": config_static_IP["record_id"],
                "RecordLine": config_static_IP["RecordLine"],
                "Value": IP
            }
            update_req.from_json_string(json.dumps(update_params))
            update_resp = client.ModifyRecord(update_req)
            log_message = f"您的域名 {domain_config['domain']} 更新成功,当前IP: {IP}"
            logging.info(log_message)
        else:
            log_message = "当前公网 IP 与之前保存的 IP 相同，无需更新"
            logging.info(log_message)
            #正常情况下不用这条   logging.info(f"当前IP: {IP}, 上次IP: {last_IP}")

        # 等待一段时间之后继续检查
        time.sleep(config_static_IP["sleep"])

except Exception as e:
    log_error = f"发生严重错误：{e}"
    logging.exception(log_error)