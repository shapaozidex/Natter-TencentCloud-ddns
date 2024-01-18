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


# 设置日志级别为 INFO，修改 format 和 datefmt 参数
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s',  datefmt='%Y-%m-%d %H:%M')

# 创建 log 目录
log_directory = 'log'
if not os.path.exists(log_directory):
    os.makedirs(log_directory)
        

# 添加文件处理器，将日志写入到文件中
log_file_path = 'log/ddns.log'
file_handler = logging.FileHandler(log_file_path, encoding='utf-8')
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s', '%Y-%m-%d %H:%M'))
logging.getLogger().addHandler(file_handler)


# 读取整个配置文件
with open('config/ID.json', 'r', encoding='utf-8') as config_ID:
    configs_ID = json.load(config_ID)  


# 读取整个配置文件
with open('config/natter.json', 'r', encoding='utf-8') as config_SRV:
    configs_SRV = json.load(config_SRV)  


# 读取整个配置文件
with open('config/config.json', 'r', encoding='utf-8') as config_IPV4:
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
        with open("log/OPEN.json", "r", encoding="utf-8") as cache_file:
            cache_data_list = [json.loads(line) for line in cache_file]
            
            static_port = Static_Port()  # 通过 Static_Port() 获取静态端口
            
            # 在json中查找符合 LANport 的数据
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




try:
    while True:
            # 获取动态端口
        PORT = read_dynamic_port()

        if PORT != last_PORT:    #对比



            last_PORT = PORT     #有变化就写进去

            try:
                        # 修改 DDNS 记录
                req = models.ModifyRecordRequest()
                params = {
                    "Domain": domain_config["domain"],
                    "SubDomain": port_config["SubDomain"],
                    "RecordType": config_static_SRV["RecordType"],
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
        time.sleep(config_static_SRV["sleep"])


except Exception as e:
        log_error = f"发生严重错误：{e}"
        logging.exception(log_error)