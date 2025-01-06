from flask import Flask, render_template, request, redirect, url_for
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SelectField
import json
import os
import sys
import subprocess
import threading
import socket
import time
import signal


# 获取本地主机名
host_name = socket.gethostname()
        
        # 获取本地IP地址 ，没有获取到就改成127.0.0.1
# custom_host = socket.gethostbyname(host_name) if socket.gethostbyname(host_name) else "127.0.0.1"

#如果不想挂载到局域网，那就用这个 
custom_host = "0.0.0.0"


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
log_directory = os.path.join(os.path.dirname(__file__), 'log')
config_directory = os.path.join(os.path.dirname(__file__), 'config')

# 确保目录存在
for directory in [log_directory, config_directory]:
    if not os.path.exists(directory):
        os.makedirs(directory)

# 设置配置文件路径
CONFIG_FILE_PATH = os.path.join(config_directory, 'config.json')
NATTER_FILE_PATH = os.path.join(config_directory, 'natter.json')
ID_FILE_PATH = os.path.join(config_directory, 'ID.json')

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

# 将原有的 ConfigForm 类替换为以下代码
class PortConfigForm(FlaskForm):
    record_id = IntegerField('Record-ID（选填）')
    port = IntegerField('PORT')
    protocols = SelectField('网络协议', choices=[('TCP', 'TCP'), ('UDP', 'UDP')], default='TCP')
    subdomain = StringField('SubDomain（选填）')
    record_line = StringField('Record-Line（选填）')
    priority = StringField('priority（选填）')

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

class NatterForm(FlaskForm):
    pass

# 修改 natter 路由
@app.route('/natter', methods=['GET', 'POST'])
def natter():
    natter_data = read_natter()
    port_forms = {}
    form = FlaskForm()  # 添加这行来创建基础表单实例，用于CSRF保护
    
    if request.method == 'POST':
        # 检查是否是保存配置的操作
        if request.form.get('save_config') == 'true':
            try:
                # 创建一个新的字典来存储更新后的数据
                updated_data = {}
                
                # 从表单数据中提取所有端口键
                port_keys = set()
                for key in request.form.keys():
                    if '-' in key:
                        port_key = key.split('-')[0]
                        port_keys.add(port_key)
                
                # 对端口键进行排序
                sorted_port_keys = sorted(port_keys, key=lambda x: int(x.replace('PORT', '')))
                
                # 遍历排序后的端口键
                for port_key in sorted_port_keys:
                    # 获取表单中对应的数据
                    port = request.form.get(f'{port_key}-port', '')
                    protocols = request.form.get(f'{port_key}-protocols', '')
                    record_id = request.form.get(f'{port_key}-record_id', '')
                    subdomain = request.form.get(f'{port_key}-subdomain', '')
                    record_line = request.form.get(f'{port_key}-record_line', '')
                    priority = request.form.get(f'{port_key}-priority', '')
                    
                    # 保存所有配置项，不管是否有端口号
                    updated_data[port_key] = {
                        "PORT": int(port) if port and port.isdigit() else None,
                        "PORT_protocols": protocols,
                        "record_id": int(record_id) if record_id and record_id.isdigit() else None,
                        "SubDomain": subdomain,
                        "RecordLine": record_line,
                        "priority": priority,
                    }
                
                # 保存更新后的数据
                write_natter(updated_data)
                return redirect(url_for('natter'))
            except Exception as e:
                return f"Error saving data: {str(e)}", 500
    
    # 读取现有数据并按端口号排序
    sorted_natter_data = dict(sorted(natter_data.items(), key=lambda x: int(x[0].replace('PORT', ''))))
    
    # 为每个已存在的端口配置创建表单
    for port_key, port_config in sorted_natter_data.items():
        port_form = PortConfigForm(prefix=port_key)
        port_form.port.data = port_config.get('PORT')
        port_form.protocols.data = port_config.get('PORT_protocols')
        port_form.record_id.data = port_config.get('record_id')
        port_form.subdomain.data = port_config.get('SubDomain')
        port_form.record_line.data = port_config.get('RecordLine')
        port_form.priority.data = port_config.get('priority')
        port_forms[port_key] = port_form

    return render_template('natter.html', port_forms=port_forms, form=form)

# 添加新的路由用于添加端口配置
@app.route('/add_port', methods=['POST'])
def add_port():
    natter_data = read_natter()
    
    # 找到可用的下一个端口键名
    next_port_num = 1
    while f"PORT{next_port_num}" in natter_data:
        next_port_num += 1
    
    new_port_key = f"PORT{next_port_num}"
    natter_data[new_port_key] = {
        "PORT": None,
        "PORT_protocols": "",
        "record_id": None,
        "SubDomain": "",
        "RecordLine": "",
        "priority": f"0 {next_port_num}",
    }
    
    write_natter(natter_data)
    return redirect(url_for('natter'))

# 添加新的路由用于删除端口配置
@app.route('/delete_port/<port_key>', methods=['POST'])
def delete_port(port_key):
    try:
        natter_data = read_natter()
        if port_key in natter_data:
            app.logger.info(f"Deleting port configuration: {port_key}")
            # 创建配置的备份
            backup_data = natter_data.copy()
            # 删除指定的端口配置
            del natter_data[port_key]
            # 写入新的配置
            write_natter(natter_data)
            app.logger.info(f"Successfully deleted port configuration: {port_key}")
        else:
            app.logger.warning(f"Port configuration not found: {port_key}")
    except Exception as e:
        app.logger.error(f"Error deleting port configuration {port_key}: {str(e)}")
        # 如果发生错误，尝试恢复备份
        if 'backup_data' in locals():
            write_natter(backup_data)
            app.logger.info("Restored configuration from backup")
        
    return redirect(url_for('natter'))




#web的日志信息

@app.route('/')
def index():
    form = FlaskForm()
    natter_log = log_file('natter.log')
    ddns_log = log_file('ddns.log')
    return render_template('index.html', form=form, natter_log=natter_log, ddns_log=ddns_log)

def log_file(file_path):
    try:
        log_path = os.path.join(log_directory, file_path)
        with open(log_path, 'r', encoding='utf-8') as file:
            log_content = file.read()
        return log_content
    except FileNotFoundError:
        return '没有找到日志文件'
    except Exception as e:
        return f'{str(e)}'



















# natter执行



@app.route('/start_natter', methods=['GET', 'POST'])
def NATTER():
    if request.method == 'POST' and request.form.get('natter_button_clicked'):
        # 执行 natter.py 脚本
        natter_py()
    return redirect(url_for('index'))


def safe_remove_file(file_path):
    """安全地删除或清空文件"""
    try:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except (PermissionError, OSError):
                # 如果无法删除，尝试清空文件内容
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.truncate(0)
    except Exception as e:
        print(f"处理文件 {file_path} 时出错：{e}")

def run_python_script(script_path, args=None, background=False):
    """通用的 Python 脚本执行函数"""
    try:
        command = [sys.executable, script_path]
        if args:
            command.extend([str(arg) for arg in args])
        
        if background:
            thread = threading.Thread(
                target=lambda: subprocess.run(command),
                daemon=True  # 设置为守护线程，这样主程序退出时会自动结束
            )
            thread.start()
            return thread
        else:
            subprocess.run(command)
    except Exception as e:
        print(f"执行脚本 {script_path} 时出错：{e}")

def execute_natter(port_key, port_number, Network_protocols):
    """执行 Natter 脚本"""
    try:
        time.sleep(1)
        args = [Startup_parameters, port_number]
        if Network_protocols == 'UDP':
            args.append('-u')
        run_python_script(os.path.join('py', 'natter.py'), args)
    except Exception as e:
        app.logger.error(f"执行 {port_key} 时出错：{e}")

def natter_py():
    """Natter 主程序"""
    try:
        # 清理日志文件
        safe_remove_file(os.path.join(log_directory, "OPEN.json"))
        safe_remove_file(os.path.join(log_directory, "natter.log"))
        safe_remove_file(os.path.join(log_directory, "ddns.log"))

        # 读取配置并启动服务
        with open(os.path.join(config_directory, 'natter.json'), 'r', encoding='utf-8') as f:
            config_data = json.load(f)

        for port_key, port_config in config_data.items():
            if port_config.get('PORT') is not None:
                thread = threading.Thread(
                    target=execute_natter,
                    args=(port_key, port_config['PORT'], port_config['PORT_protocols']),
                    daemon=True
                )
                thread.start()
                time.sleep(1)

    except Exception as e:
        app.logger.error(f"Natter 主程序出错：{e}")














        
# ddns执行

@app.route('/start_ddns', methods=['GET', 'POST'])
def DDNS():
    if request.method == 'POST' and request.form.get('ddns_button_clicked') == 'true':
        # 执行 ddns.py 脚本
        ddns_py()
    return redirect(url_for('index'))



def execute_ddns(port_key, port_SRV):
    """执行 DDNS 脚本"""
    try:
        run_python_script(os.path.join('py', 'ddnsSRV.py'), [port_SRV])
    except Exception as e:
        app.logger.error(f"执行 DDNS 时出错，针对 {port_key}: {e}")



def ddns_py():
    """DDNS 主程序"""
    try:
        # 清理日志文件
        safe_remove_file(os.path.join(log_directory, 'ddns.log'))

        # 启动 DDNS 服务
        run_python_script(os.path.join('py', 'ddnsIPV4.py'), background=True)
        time.sleep(1)

        # 读取配置并启动 SRV 服务
        with open(os.path.join(config_directory, 'natter.json'), 'r', encoding='utf-8') as f:
            config_data = json.load(f)

        for port_key, port_config in config_data.items():
            if port_config.get('PORT') is not None:
                thread = threading.Thread(
                    target=execute_ddns,
                    args=(port_key, port_config['PORT']),
                    daemon=True
                )
                thread.start()
                time.sleep(1)

    except Exception as e:
        app.logger.error(f"DDNS 主程序出错：{e}")











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

    # 用加载的数据填充表单字段
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

@app.route('/refresh_logs', methods=['POST'])
def refresh_logs():
    # 只刷新日志，不执行任何程序
    return redirect(url_for('index'))

if __name__ == '__main__':
    # 设置环境变量，禁用冻结模块
    os.environ['PYTHONMALLOC'] = 'debug'  
    os.environ['PYDEVD_DISABLE_FILE_VALIDATION'] = '1'
    app.config['DEBUG'] = True   # 可选，用于启用内存调试





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

