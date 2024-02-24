from flask import Flask, render_template, request
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField
import json
import os
import sys
import subprocess
import threading
import socket


# 获取本地主机名
host_name = socket.gethostname()
        
        # 获取本地IP地址 ，没有获取到就改成127.0.0.1
custom_host = socket.gethostbyname(host_name) if socket.gethostbyname(host_name) else "127.0.0.1"

#如果不想挂载到局域网，那就用这个
# custom_host = "127.0.0.1"


#默认只挂载到本机内网地址，  想要在公网访问就自己把custom_host改成 '0.0.0.0' 
#但是这是不被允许的，web界面没有密码所以,所有人都能访问到
#不要问为什么不写,问就是不会
#没有特殊需求不要改这个东西   

# 默认启动端口
default_port = 9876    #你可以直接修改这里，也可以使用启动参数来变更端口

    


Startup_parameters = '-p'   #natter的启动参数（需要其它参数请自行修改）。具体改法自己根据下面的对照表来

#不要问为什么不直接在web中提供更改，问就是太麻烦，要考虑的东西太多，并且不能直接一个模板全部套用(绝对不是连我都看不懂这些启动参数的用法，绝对不是  (๑òωó๑)

#如果你需要更改这个参数，那你可能需要连着natter.py一起更改，以确保natter.能够正常输出日志到log文件夹，否则srv无法正常工作

#使用说明：natter.py [--version] [--help] [-v] [-q] [-u] [-k <间隔>] [-s <地址>] [-h <地址>] [-e <路径>] [-i <接口>] [-b <端口>] [-m <方法>] [-t <地址>] [-p <端口>] [-r]

#将你的电脑端口暴露在互联网上，让其他人可以访问。

#选项：
#  --version, -V   显示Natter的版本并退出
#  --help          显示帮助信息并退出
#  -v              详细模式，打印调试信息
#  -q              映射地址变化时退出
#  -u              使用UDP模式
#  -k <间隔>       保持活动的时间间隔
#  -s <地址>       STUN服务器的地址
#  -h <地址>       保持活动的服务器地址
#  -e <路径>       通知映射地址的脚本路径

#绑定选项：
#  -i <接口>       要绑定的网络接口名称或IP地址
#  -b <端口>       要绑定的端口号

#转发选项：
#  -m <方法>       转发方法，常见的有'iptables'、'nftables'、'socat'、'gost'和'socket'
#  -t <地址>       转发目标的IP地址
#  -p <端口>       转发目标的端口号
#  -r              保持重试，直到转发目标的端口打开












app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'



# 创建 config 目录
log_directory = 'config'
if not os.path.exists(log_directory):
    os.makedirs(log_directory)




# 设置路径 config.json
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
CONFIG_FILE_PATH = os.path.join(BASE_DIR, 'config/config.json')

# 设置路径 natter.json
NATTER_DIR = os.path.abspath(os.path.dirname(__file__))
NATTER_FILE_PATH = os.path.join(NATTER_DIR, 'config/natter.json')

# 设置路径 ID.json
ID_DIR = os.path.abspath(os.path.dirname(__file__))
ID_FILE_PATH = os.path.join(ID_DIR, 'config/ID.json')







# 读取数据 config.json
def read_config():
    try:
        with open(CONFIG_FILE_PATH, 'r', encoding='utf-8') as config_file:
            config_data = json.load(config_file)
            return config_data
    except (FileNotFoundError, json.JSONDecodeError) as e:
        return {}

# 写入数据 config.json
def write_config(config_data):
    with open(CONFIG_FILE_PATH, 'w', encoding='utf-8') as config_file:
        json.dump(config_data, config_file, indent=4, ensure_ascii=False)

# 读取数据 natter.json
def read_natter():
    try:
        with open(NATTER_FILE_PATH, 'r', encoding='utf-8') as natter_file:
            natter_data = json.load(natter_file)
            return natter_data
    except (FileNotFoundError, json.JSONDecodeError) as e:
        return {}

# 写入数据 natter.json
def write_natter(natter_data):
    with open(NATTER_FILE_PATH, 'w', encoding='utf-8') as natter_file:
        json.dump(natter_data, natter_file, indent=4, ensure_ascii=False)


# 读取数据 ID.json
def read_ID():
    try:
        with open(ID_FILE_PATH, 'r', encoding='utf-8') as ID_file:
            ID_data = json.load(ID_file)
            
            tencent_api_config = ID_data.get("tencent_api", {})
            secret_id = tencent_api_config.get("secret_id", "")[:4] + '*' * (len(tencent_api_config.get("secret_id", "")) - 8) + tencent_api_config.get("secret_id", "")[-4:]
            secret_key = tencent_api_config.get("secret_key", "")[:4] + '*' * (len(tencent_api_config.get("secret_key", "")) - 8) + tencent_api_config.get("secret_key", "")[-4:]
            
            # 将处理后的秘钥更新到配置数据中
            tencent_api_config["secret_id"] = secret_id
            tencent_api_config["secret_key"] = secret_key
            
            return ID_data
    except (FileNotFoundError, json.JSONDecodeError) as e:
        return {}

# 写入数据 ID.json
def write_ID(ID_data):
    with open(ID_FILE_PATH, 'w', encoding='utf-8') as ID_file:
        json.dump(ID_data, ID_file, indent=4, ensure_ascii=False)

# 定义表单类 （不要问我为什么用这种笨办法写表单，问就是不会用 Flask ）
class ConfigForm(FlaskForm):

    tencent_api_secret_id = StringField('Secret-ID')
    tencent_api_secret_key = StringField('Secret-Key')
    tencent_api_endpoint = StringField('ddns服务器')

    script0_domain = StringField('域名')

    script1_RecordType = StringField('记录类型')
    script1_record_id = IntegerField('Record-ID')
    script1_subdomain = StringField('SubDomain')
    script1_record_line = StringField('Record-Line')
    script1_sleep = IntegerField('检测间隔')

    script2_RecordType = StringField('记录类型')
    script2_record_id = IntegerField('Record-ID')
    script2_subdomain = StringField('SubDomain')
    script2_record_line = StringField('Record-Line')
    script2_priority = StringField('Priority')
    script2_sleep = IntegerField('检测间隔')




    PORT1_record_id = IntegerField('Record-ID（选填）')
    PORT1_PORT = IntegerField('PORT')
    PORT1_protocols = StringField('网络协议')
    PORT1_subdomain = StringField('SubDomain（选填）')
    PORT1_record_line = StringField('Record-Line（选填）')
    PORT1_priority = StringField('priority（选填）')

    PORT2_record_id = IntegerField('Record-ID（选填）')
    PORT2_PORT = IntegerField('PORT')
    PORT2_protocols = StringField('网络协议')
    PORT2_subdomain = StringField('SubDomain（选填）')
    PORT2_record_line = StringField('Record-Line（选填）')
    PORT2_priority = StringField('priority（选填）')

    PORT3_record_id = IntegerField('Record-ID（选填）')
    PORT3_PORT = IntegerField('PORT')
    PORT3_protocols = StringField('网络协议')
    PORT3_subdomain = StringField('SubDomain（选填）')
    PORT3_record_line = StringField('Record-Line（选填）')
    PORT3_priority = StringField('priority（选填）')

    PORT4_record_id = IntegerField('Record-ID（选填）')
    PORT4_PORT = IntegerField('PORT')
    PORT4_protocols = StringField('网络协议')
    PORT4_subdomain = StringField('SubDomain（选填）')
    PORT4_record_line = StringField('Record-Line（选填）')
    PORT4_priority = StringField('priority（选填）')

    PORT5_record_id = IntegerField('Record-ID（选填）')
    PORT5_PORT = IntegerField('PORT')
    PORT5_protocols = StringField('网络协议')
    PORT5_subdomain = StringField('SubDomain（选填）')
    PORT5_record_line = StringField('Record-Line（选填）')
    PORT5_priority = StringField('priority（选填）')




   


# 定义路由，处理 GET 和 POST 请求时返回表单页面
@app.route('/natter', methods=['GET', 'POST'])
def natter():
    form = ConfigForm()  



#natter页面的现有信息

    # 读取配置信息
    natter_data = read_natter()

    if request.method == 'POST':
        
        # 将表单数据写入配置文件（natter.json）
        natter_data = {

            "PORT1": {
                "PORT": form.PORT1_PORT.data,
                "PORT_protocols": form.PORT1_protocols.data,
                "record_id": form.PORT1_record_id.data,
                "SubDomain": form.PORT1_subdomain.data,
                "RecordLine": form.PORT1_record_line.data,
                "priority":  form.PORT1_priority.data,
            },
            "PORT2": {
                "PORT": form.PORT2_PORT.data,
                "PORT_protocols": form.PORT2_protocols.data,
                "record_id": form.PORT2_record_id.data,
                "SubDomain": form.PORT2_subdomain.data,
                "RecordLine": form.PORT2_record_line.data,
                "priority":  form.PORT2_priority.data,
            },
            "PORT3": {
                "PORT": form.PORT3_PORT.data,
                "PORT_protocols": form.PORT3_protocols.data,
                "record_id": form.PORT3_record_id.data,
                "SubDomain": form.PORT3_subdomain.data,
                "RecordLine": form.PORT3_record_line.data,
                "priority":  form.PORT3_priority.data,
            },
            "PORT4": {
                "PORT": form.PORT4_PORT.data,
                "PORT_protocols": form.PORT4_protocols.data,
                "record_id": form.PORT4_record_id.data,
                "SubDomain": form.PORT4_subdomain.data,
                "RecordLine": form.PORT4_record_line.data,
                "priority":  form.PORT4_priority.data,
            },
            "PORT5": {
                "PORT": form.PORT5_PORT.data,
                "PORT_protocols": form.PORT5_protocols.data,
                "record_id": form.PORT5_record_id.data,
                "SubDomain": form.PORT5_subdomain.data,
                "RecordLine": form.PORT5_record_line.data,
                "priority":  form.PORT5_priority.data,
            },    
        }

        # 将表单数据写入 natter.json
        write_natter(natter_data)

    #用加载的数据填充表单字段
        

    form.PORT1_PORT.data = natter_data.get("PORT1", {}).get("PORT", "")
    form.PORT1_protocols.data = natter_data.get("PORT1", {}).get("PORT_protocols", "")
    form.PORT1_record_id.data = natter_data.get("PORT1", {}).get("record_id", "")
    form.PORT1_subdomain.data = natter_data.get("PORT1", {}).get("SubDomain", "")
    form.PORT1_record_line.data = natter_data.get("PORT1", {}).get("RecordLine", "")
    form.PORT1_priority.data = natter_data.get("PORT1", {}).get("priority", "")

    form.PORT2_PORT.data = natter_data.get("PORT2", {}).get("PORT", "")
    form.PORT2_protocols.data = natter_data.get("PORT2", {}).get("PORT_protocols", "")
    form.PORT2_record_id.data = natter_data.get("PORT2", {}).get("record_id", "")
    form.PORT2_subdomain.data = natter_data.get("PORT2", {}).get("SubDomain", "")
    form.PORT2_record_line.data = natter_data.get("PORT2", {}).get("RecordLine", "")
    form.PORT2_priority.data = natter_data.get("PORT2", {}).get("priority", "")

    form.PORT3_PORT.data = natter_data.get("PORT3", {}).get("PORT", "")
    form.PORT3_protocols.data = natter_data.get("PORT3", {}).get("PORT_protocols", "")
    form.PORT3_record_id.data = natter_data.get("PORT3", {}).get("record_id", "")
    form.PORT3_subdomain.data = natter_data.get("PORT3", {}).get("SubDomain", "")
    form.PORT3_record_line.data = natter_data.get("PORT3", {}).get("RecordLine", "")
    form.PORT3_priority.data = natter_data.get("PORT3", {}).get("priority", "")

    form.PORT4_PORT.data = natter_data.get("PORT4", {}).get("PORT", "")
    form.PORT4_protocols.data = natter_data.get("PORT4", {}).get("PORT_protocols", "")
    form.PORT4_record_id.data = natter_data.get("PORT4", {}).get("record_id", "")
    form.PORT4_subdomain.data = natter_data.get("PORT4", {}).get("SubDomain", "")
    form.PORT4_record_line.data = natter_data.get("PORT4", {}).get("RecordLine", "")
    form.PORT4_priority.data = natter_data.get("PORT4", {}).get("priority", "")

    form.PORT5_PORT.data = natter_data.get("PORT5", {}).get("PORT", "")
    form.PORT5_protocols.data = natter_data.get("PORT5", {}).get("PORT_protocols", "")
    form.PORT5_record_id.data = natter_data.get("PORT5", {}).get("record_id", "")
    form.PORT5_subdomain.data = natter_data.get("PORT5", {}).get("SubDomain", "")
    form.PORT5_record_line.data = natter_data.get("PORT5", {}).get("RecordLine", "")
    form.PORT5_priority.data = natter_data.get("PORT5", {}).get("priority", "")


    return render_template('natter.html', form=form)




#web的日志信息

@app.route('/')
def index():
    # 获取Natter和DDNS日志文件的相对路径
    natter_path = 'log/natter.log'
    ddns_path = 'log/ddns.log'

    # 读取Natter和DDNS日志文件内容
    log_content_natter = log_file(natter_path)
    log_content_ddns = log_file(ddns_path)

    return render_template('index.html', natter_log=log_content_natter, ddns_log=log_content_ddns)

def log_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            log_content = file.read()
        return log_content
    except FileNotFoundError:
        return '没有找到日志文件'
    except Exception as e:
        return f'{str(e)}'



















# natter执行



@app.route('/start_natter', methods=['GET', 'POST'])
def NATTER():
    if request.method == 'POST':
        # 检查是否点击了"natter"按钮
        if request.form.get('natter_button_clicked') == 'true':
            # 执行 natter.py 脚本
            natter_py()

    # 如果是 GET 请求或者其他情况，返回一个简单的响应
    return render_template('index.html')


def execute_natter(port_key, port_number, Network_protocols):
    try:

         # 构建命令并执行
        command = ['python', 'py/natter.py', str(Startup_parameters), str(port_number)]




        # 如果 Network_protocols 为 'udp'，则添加'-u'参数
        if Network_protocols == 'UDP':
            command.append('-u')
            subprocess.run(command)            # 执行命令

        # 如果 Network_protocols 为 'tcp'，则直接执行命令
        elif Network_protocols == 'TCP':
            subprocess.run(command)            # 执行命令





    except Exception as e:
        app.logger.error(f"执行 {port_key} 时出错：{e}")


def natter_py():
    try:
        files_to_delete = ["OPEN.json", "natter.log", "ddns.log"]
        directory = "log"

        for file in files_to_delete:
            file_path = os.path.join(directory, file)
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    print(f"文件 {file} 删除成功")
                else:
                    print(f"文件 {file} 未找到")
            except Exception as e:
                print(f"删除 {file} 时出错：{e}")




        # 使用指定的编码读取配置文件
        with open('config/natter.json', 'r', encoding='utf-8') as config_file:
            config_data = json.load(config_file)

            
        # 遍历所有符合条件的项
        for port_key in ['PORT1', 'PORT2', 'PORT3', 'PORT4', 'PORT5']:
            if port_key in config_data and config_data[port_key]['PORT'] is not None:
                # 获取需要穿透的端口号
                port_number = config_data[port_key]['PORT']
                Network_protocols = config_data[port_key]['PORT_protocols']


                # 多线程  (给自己写个提醒，在端口少的时候可以这样写，但是端口多的时候这样写，可能会爆掉，一个端口一个线程)
                thread = threading.Thread(target=execute_natter, args=(port_key, port_number, Network_protocols))
                thread.start()
                






    except Exception as e:
        app.logger.error(f"{e}")














        
# ddns执行

@app.route('/start_ddns', methods=['GET', 'POST'])
def DDNS():
    if request.method == 'POST':
        # 检查是否点击了"ddns"按钮
        if request.form.get('ddns_button_clicked') == 'true':
            # 执行 ddns.py 脚本
            ddns_py()

    # 如果是 GET 请求或者其他情况，返回一个简单的响应
    return render_template('index.html')



def execute_ddns(port_keys, port_SRV):
    try:

        # 构建命令并执行    启动ddnsSRV
        command = ['python', 'py/ddnsSRV.py', str(port_SRV)]
        subprocess.run(command)





    except Exception as e:
        app.logger.error(f"在执行 execute_natter 函数时发生错误，针对 {port_keys}: {e}")



def ddns_py():

    try:

        # 删除 natter.log 文件

        os.remove('log/ddns.log')
    except FileNotFoundError:
        pass     # 如果找不到文件，就继续执行




        # 启动ddsnIPV4
        threading.Thread(target=lambda: subprocess.run(['python', 'py/ddnsIPV4.py'])).start()




        
       # 使用指定的编码读取配置文件
        with open('config/natter.json', 'r', encoding='utf-8') as config_files:
            config_datas = json.load(config_files)

            
        # 遍历所有符合条件的项
        for port_keys in ['PORT1', 'PORT2', 'PORT3', 'PORT4', 'PORT5']:
            if port_keys in config_datas and config_datas[port_keys]['PORT'] is not None:
                # 获取需要映射的端口号
                port_SRV = config_datas[port_keys]['PORT']

                # 多线程
                thread = threading.Thread(target=execute_ddns, args=(port_keys, port_SRV))
                thread.start()

                
    except Exception as e:
        app.logger.error(f"{e}")











#GIT 配置


@app.route('/GIT', methods=['GET', 'POST'])
def GIT():
    form = ConfigForm()

#GIT页面的现有信息
    
    # 读取配置信息
    ID_data = read_ID()

    if request.method == 'POST':

                # 检查是否点击了"GIT ID"按钮
        if request.form.get('git_id_button_clicked') == 'true':
            # 执行 Get ID.py
            execute_get_id_script()

            # 跳回去
            return render_template('GIT.html', form=form)
        
            # 检查 secret_id 是否包含多个星号
        if '********' in form.tencent_api_secret_id.data:
            # 跳回去
            return render_template('GIT.html', form=form)
        

        

        # 将表单数据写入配置文件（ID.json）
        ID_data = {
            "tencent_api": {
                "secret_id": form.tencent_api_secret_id.data,
                "secret_key": form.tencent_api_secret_key.data,
                "endpoint": form.tencent_api_endpoint.data,
            },
            "script0": {
                "domain": form.script0_domain.data,
            },
        }

        # 将表单数据写入 config.json
        write_ID(ID_data)




    form.tencent_api_secret_id.data = ID_data.get("tencent_api", {}).get("secret_id", "")
    form.tencent_api_secret_key.data = ID_data.get("tencent_api", {}).get("secret_key", "")
    
    form.tencent_api_endpoint.data = "dnspod.tencentcloudapi.com"

    form.script0_domain.data = ID_data.get("script0", {}).get("domain", "")



    return render_template('GIT.html', form=form)


def execute_get_id_script():
    # 执行 Get ID.py 
    try:
        subprocess.run(['python', 'py/Get ID.py'])
    except Exception as e:
        app.logger.error(f"{e}")







# ddns 配置

@app.route('/ddns', methods=['GET', 'POST'])
def navigation():
    form = ConfigForm() 
   

#ddns页面的现有信息

    # 读取配置信息
    config_data = read_config()

    if request.method == 'POST':
        # 将表单数据写入配置文件（config.json）
        config_data = {
            "script1": {
                "record_id": form.script1_record_id.data,
                "SubDomain": form.script1_subdomain.data,
                "RecordLine": form.script1_record_line.data,
                "RecordType": form.script1_RecordType.data,                 
                "sleep": form.script1_sleep.data,
            },
            "script2": {
                "RecordLine": form.script2_record_line.data,
                "RecordType": form.script2_RecordType.data,
                "sleep": form.script2_sleep.data,
            },

        }

        # 将表单数据写入 config.json
        write_config(config_data)

      #用加载的数据填充表单字段



    form.script1_record_id.data = config_data.get("script1", {}).get("record_id", "")
    form.script1_subdomain.data = config_data.get("script1", {}).get("SubDomain", "")
    form.script1_record_line.data = config_data.get("script1", {}).get("RecordLine", "")
    form.script1_RecordType.data = "A"
    form.script1_sleep.data = config_data.get("script1", {}).get("sleep", "")


    form.script2_record_line.data = config_data.get("script2", {}).get("RecordLine", "")
    form.script2_RecordType.data = "SRV"
    form.script2_sleep.data = config_data.get("script2", {}).get("sleep", "")

    return render_template('ddns.html', form=form)

# @app.before_request #为了防止意外额外做的限制，虽然可能没啥用
# def limit_remote_addr():
#    client_ip = request.remote_addr
#    try:
#        client_ip = ipaddress.IPv4Address(client_ip)
#        private_networks = [
#            ipaddress.IPv4Network('10.0.0.0/8'),
#            ipaddress.IPv4Network('172.16.0.0/12'),
#            ipaddress.IPv4Network('192.168.0.0/16'),
#            ipaddress.IPv4Network('127.0.0.0/8'),
#        ]
#        if not any(client_ip in network for network in private_networks):
#            return "访问被禁止", 403
#    except ipaddress.AddressValueError:
#        return "无效的IP地址", 400




if __name__ == '__main__':
    # 设置环境变量，禁用冻结模块
    os.environ['PYTHONMALLOC'] = 'debug'  
    os.environ['PYDEVD_DISABLE_FILE_VALIDATION'] = '1'
    app.config['DEBUG'] = False   # 可选，用于启用内存调试






    # 从启动参数中尝试读取端口
    if len(sys.argv) > 1:
        try:
            custom_port = int(sys.argv[1])
        except ValueError:
            print("端口必须是数字")
            sys.exit(1)
    else:
        custom_port = default_port  #没读取到，那就是9876
        print("可以在启动的时候输入一个数字作为web界面的端口号，不然默认为9876")
    
    app.run(host=custom_host, port=custom_port)

