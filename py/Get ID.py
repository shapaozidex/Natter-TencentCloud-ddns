import json
import os
from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
from tencentcloud.dnspod.v20210323 import dnspod_client, models

# 获取当前脚本所在目录的父目录
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
config_dir = os.path.join(base_dir, 'config')

# 确保配置目录存在
if not os.path.exists(config_dir):
    os.makedirs(config_dir)

# 读取整个配置文件
config_path = os.path.join(config_dir, 'ID.json')
with open(config_path, 'r', encoding='utf-8') as config_file:
    all_configs = json.load(config_file)

# 单独拿出 tencent_api 的配置
tencent_api_config = all_configs.get("tencent_api", {})

# 申请域名解析 的配置
script_name_static_creation = "script0"
config_static_creation = all_configs.get(script_name_static_creation, {})

try:
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

    # 实例化一个请求对象,每个接口都会对应一个request对象
    req = models.DescribeRecordFilterListRequest()
    params = {
        "Domain": config_static_creation["domain"],
    }
    req.from_json_string(json.dumps(params))

    # 返回的resp是一个DescribeRecordFilterListResponse的实例，与请求对象对应
    resp = client.DescribeRecordFilterList(req)

    # 提取指定字段并按照指定顺序输出到控制台
    record_list = resp.RecordList
    max_len_name = max(len(record.Name) for record in record_list)
    max_len_id = max(len(str(record.RecordId)) for record in record_list)
    max_len_value = max(len(str(record.Value)) for record in record_list)
    max_len_RecordType = max(len(str(record.Type)) for record in record_list)

    # 筛选符合条件的记录和不符合条件的记录
    ipv4_records = [record for record in record_list if record.Type == "A" and record.Name == "@"]
    srv_records = [record for record in record_list if record.Type == "SRV"]

    # 将日志信息写入 JSON 文件
    ipv4_log_data = {
        "script1": {
            "SubDomain": record.Name,
            "record_id": record.RecordId,
            "Value": record.Value,
            "RecordType": record.Type,
            "RecordLine": record.Line
        } for record in ipv4_records
    }

    # 解析SRV记录的Value字段（格式：优先级 权重 端口 目标）
    def parse_srv_value(value):
        try:
            priority, weight, port, target = value.split()
            return {
                "priority": f"{priority} {weight}",
                "port": int(port)
            }
        except (ValueError, AttributeError):
            return {
                "priority": "None",
                "port": None
            }

    # 将日志信息写入 JSON 文件，解析SRV记录的值
    srv_log_data = {
        f"PORT{i + 1}": {
            "SubDomain": record.Name,
            "record_id": record.RecordId,
            "RecordLine": record.Line,
            "PORT": parse_srv_value(record.Value)["port"],
            "PORT_protocols": "TCP",  # SRV记录默认是TCP
            "priority": f"0 {i+1}"  # 保持第一个数字为0，只递增第二个数字
        } for i, record in enumerate(srv_records)
    }

    # 将数据写入 JSON 文件，使用os.path.join确保跨平台兼容
    config_json_path = os.path.join(config_dir, 'config.json')
    natter_json_path = os.path.join(config_dir, 'natter.json')

    with open(config_json_path, "w", encoding='utf-8') as ipv4_file:
        json.dump(ipv4_log_data, ipv4_file, indent=2, ensure_ascii=False)

    with open(natter_json_path, "w", encoding='utf-8') as srv_file:
        json.dump(srv_log_data, srv_file, indent=2, ensure_ascii=False)

    # 输出记录信息
    for record in record_list:
        output_data = {
            "主机记录": record.Name.ljust(max_len_name),
            "记录类型": record.Type.ljust(max_len_RecordType),
            "ID": str(record.RecordId).ljust(max_len_id),
            "IP": str(record.Value).ljust(max_len_value)
        }
        print("主机记录: {主机记录} , 记录类型: {记录类型} , ID: {ID}, 记录值: {IP}".format(**output_data))

except TencentCloudSDKException as err:
    print(err)
