import configparser
import json
import os
import queue
import socket
import re
import User_db_Creation
import threading
import smtplib
from email.mime.text import MIMEText
from email.utils import formataddr
import random
import os  # 确保导入os模块
import time

# 读取配置文件
config = configparser.ConfigParser()
config.read('config.ini')

# 存储所有活动客户端的列表
clients = []
# 存储所有发送文件客户端的列表
file_clients = []
#存储用户消息
message_queue = queue.Queue()
#验证码
code = None

my_sender = config.get('DEFAULT', 'my_sender')
my_pass = config.get('DEFAULT', 'my_pass')


#使用正则表达式解析客户端发出的注册消息
def parse_register_message(message):
    pattern = [
        r'REGISTER\s+(?P<username>\S+)\s+(?P<password>\S+)', #用户名和密码
        r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', #用户邮箱
        r'^CODE:(\d{6})$'                                    #用户输入的验证码，用于与服务器端生成的验证码对比
    ]
    match1 = re.search(pattern[0], message)
    match2 = re.search(pattern[1], message)
    match3 = re.search(pattern[2], message)
    # 使用re.search尝试找到匹配项
    if match1 :
        return match1.group('username'), match1.group('password'), 1 #该整数标识匹配结果
    elif match2 :
        return match2.group(0), None, 2
    elif match3 :
        return match3.group(0), None, 3
    else:
        return None, None, 4

def confirm_code_send(user_mailaddr):
    ret = True
    code = random.randint(100000, 999999)
    try:
        # 组装发送内容
        msg = MIMEText(f'验证码：{code}', 'html', 'utf-8')  # 填写邮件内容
        msg['From'] = formataddr(["简易聊天室", my_sender])  # 括号里的对应发件人邮箱昵称、发件人邮箱账号
        msg['To'] = formataddr(["用户", user_mailaddr])  # 括号里的对应收件人邮箱昵称、收件人邮箱账号
        msg['Subject'] = "验证码"  # 邮件的主题，也可以说是标题

        # 配置服务器
        server = smtplib.SMTP_SSL("smtp.qq.com", 465)  # 发件人邮箱中的SMTP服务器
        server.login(my_sender, my_pass)  # 括号中对应的是发件人邮箱账号、邮箱授权码
        server.sendmail(my_sender, [user_mailaddr, ], msg.as_string())  # 括号中对应的是发件人邮箱账号、收件人邮箱账号、发送邮件
        server.quit()  # 关闭连接
    except Exception:  # 如果 try 中的语句没有执行，则会执行下面的 ret=False
        ret = False
    return code


#处理单个客户端的消息接收与发送
def handle_client(client_socket, addr):
    global code
    while True:
        try:
            message = client_socket.recv(4096).decode()
            print(message)

            if not message:
                break
            #若匹配成功，则将用户信息加入数据库
            elif parse_register_message(message)!= None:
                result = parse_register_message(message)
                #若发送的是用户名和密码信息，则注册
                if result[2] == 1:
                    print(f"收到注册信息：{result[0]},{result[1]}")  # 增加调试输出
                    User_db_Creation.add_user(result[0], result[1] )
                    print(f"注册成功！{result[0]},{result[1]}")

                #若发送的是邮箱地址，则发送验证码
                elif result[2] == 2:
                    user_mailaddr= result[0]
                    code = confirm_code_send(user_mailaddr)
                    #client_socket.send(f"CODE:{code}".encode())

                #若发送的是验证码，则对比服务器和客户端的验证码
                elif result[2] == 3:
                    user_code = result[0].split(':')[1]  # 提取CODE:后面的数字
                    if user_code == str(code):
                        client_socket.send(f"Sign up agree".encode())
                        code = None
                    else:
                        client_socket.send(f"Sign up reject".encode())

                elif result[2] == 4:
                    # 广播收到的消息给所有其他客户端
                    for c in clients:
                        if c != client_socket:
                            c.sendall(f"{message}".encode())

        except Exception as e:
            print(f"Error handling {addr}: {e}")
            break

    clients.remove(client_socket)
    client_socket.close()

def handle_file_transfer(conn):
    """处理单个客户端的文件接收、保存和转发"""
    while True:
        try:
            # 1. 接收文件名长度
            name_len_bytes = conn.recv(4)
            if not name_len_bytes:
                continue
            name_len = int.from_bytes(name_len_bytes, "big")

            # 2. 接收文件名
            file_name = b''
            while len(file_name) < name_len:
                chunk = conn.recv(name_len - len(file_name))
                if not chunk:
                    break
                file_name += chunk
            file_name = file_name.decode("utf-8")

            # 3. 接收文件大小
            file_size_bytes = conn.recv(8)
            file_size = int.from_bytes(file_size_bytes, "big")

            # 4. 接收文件内容
            received = 0
            file_data = b""
            while received < file_size:
                chunk = conn.recv(min(4096, file_size - received))
                if not chunk:
                    break
                file_data += chunk
                received += len(chunk)

            # 5. 保存到本地，文件名加时间戳
            save_dir = "received_files"
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            save_file_name = f"{timestamp}_{file_name}"
            file_path = os.path.join(save_dir, save_file_name)
            with open(file_path, "wb") as f:
                f.write(file_data)
            print(f"收到文件: {file_name}, 已保存到: {file_path}")

            # 6. 转发给其他客户端
            forward_file(conn, file_name, file_size, file_path)

        except Exception as e:
            print(f"文件接收/转发出错: {e}")
            break
    if conn in file_clients:
        file_clients.remove(conn)
    conn.close()


def forward_file(sender_conn, file_name, file_size, file_path):
    """将接收的文件转发给其他客户端"""
    try:
        with open(file_path, "rb") as f:
            file_data = f.read()
        file_name_bytes = file_name.encode("utf-8")
        for client in file_clients:
            if client != sender_conn:
                try:
                    client.sendall(len(file_name_bytes).to_bytes(4, "big"))
                    client.sendall(file_name_bytes)
                    client.sendall(file_size.to_bytes(8, "big"))
                    client.sendall(file_data)
                except Exception as e:
                    print(f"转发文件到客户端失败: {e}")
    except Exception as e:
        print(f"读取本地文件转发失败: {e}")


def start_file_server(host, file_port):
    """启动文件传输服务器"""
    file_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    file_server_socket.bind((host, file_port))
    file_server_socket.listen(5)
    print(f"File server listening on {host}:{file_port}")
    while True:
        conn, addr = file_server_socket.accept()
        print(f"File connection from {addr}")
        file_clients.append(conn)
        thread = threading.Thread(target=handle_file_transfer, args=(conn,))
        thread.start()


def start_server(host, port):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(5)
    print(f"Server listening on {host}:{port}")

    while True:
        client_socket, addr = server_socket.accept()
        print(f"Connection from {addr}")
        clients.append(client_socket)
        connect_msg = f'{addr}连接成功\n'  # 提示用户连接成功
        client_socket.send(connect_msg.encode('utf-8'))
        thread = threading.Thread(target=handle_client, args=(client_socket, addr))
        thread.start()


if __name__ == "__main__":
    host = "0.0.0.0"
    port = config.getint('DEFAULT', 'port')
    file_port = config.getint('DEFAULT', 'file_port')

    # 创建两个线程分别用于启动两个服务器
    thread1 = threading.Thread(target=start_server, args=(host, port))
    thread2 = threading.Thread(target=start_file_server, args=(host, file_port))

    # 启动线程
    thread1.start()
    thread2.start()
