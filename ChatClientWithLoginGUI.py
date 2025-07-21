import configparser
import json
import os
import sys
import socket
import threading
from datetime import datetime
import tkinter as tk
from functools import partial
import queue
from tkinter import messagebox, filedialog, ttk
import Deepseek_chat

# 读取配置文件
config = configparser.ConfigParser()
config.read('config.ini')


host = config.get('DEFAULT', 'host')
port = config.getint('DEFAULT', 'port')
file_port = config.getint('DEFAULT', 'file_port')
nickname = ''
password = ''

message_queue = queue.Queue()
ds_message_queue =queue.Queue()

# 全局重新初始化 file_sock
def initialize_file_socket():
    global file_sock
    file_sock.close()  # 确保先关闭旧连接
    file_sock = socket.socket()  # 重新创建 socket 实例
    try:
        file_sock.connect((host, file_port))  # 重新连接服务器
    except socket.error as e:
        print(f"无法连接到文件端口: {e}")

#检验登录界面用户名是否合法
def ableLogin(nickname_entry):
    global nickname
    nickname = nickname_entry.get()
    if not nickname_entry.get():
        messagebox.showwarning("警告", "请输入用户名")
    # elif User_db_Creation.get_user(nickname) ==None:
    #     messagebox.showwarning("警告", "用户不存在，请注册")
    #     signup()
    else:
        login()

#检验密码与确认密码是否相同
def confirmPassword(password_entry, confirm_pw_entry, event=None):
    global password
    password=password_entry.get()
    confirm_pw=confirm_pw_entry.get()
    if password != confirm_pw:
        password = None
        confirm_pw = None
        password_entry.delete(0, tk.END) #清除密码和确认密码框
        confirm_pw_entry.delete(0, tk.END)
        messagebox.showwarning("警告", "确认密码不正确，请重新设置密码")


def signup():
    global nickname, password
    print("正在注册")
    # 创建登录窗口
    login_window = tk.Tk()
    login_window.title("注册")
    # 设置窗口初始大小
    login_window.geometry("250x500")
    # 禁止用户调整窗口大小
    login_window.resizable(False, False)

    # 创建昵称输入框
    nickname_label = tk.Label(login_window, text="请创建用户名:")
    nickname_label.grid(row=0, column=0, pady=(20, 2), padx=5, sticky='s', columnspan=2)
    nickname_entry = tk.Entry(login_window, width=20, justify='center', bg='#ADD8E6', fg='#006400')
    nickname_entry.grid(row=1, column=0, pady=2, padx=5, sticky='n', columnspan=2)

    # 创建密码输入框
    password_label = tk.Label(login_window, text="请输入密码:")
    password_label.grid(row=2, column=0, pady=(20, 2), padx=5, sticky='s', columnspan=2)
    password_entry = tk.Entry(login_window, width=20, justify='center', bg='#ADD8E6', fg='#006400')
    password_entry.config(show="*")
    password_entry.grid(row=3, column=0, pady=2, padx=5, sticky='n', columnspan=2)

    # 创建确认密码输入框
    confirm_pw_label = tk.Label(login_window, text="请确认密码:")
    confirm_pw_label.grid(row=4, column=0, pady=(20, 2), padx=5, sticky='s', columnspan=2)
    confirm_pw_entry = tk.Entry(login_window, width=20, justify='center', bg='#ADD8E6', fg='#006400')
    confirm_pw_entry.grid(row=5, column=0, pady=2, padx=5, sticky='n', columnspan=2)

    # 创建邮箱输入框
    mailbox_label = tk.Label(login_window, text="请输入可用邮箱（仅用于发送验证码）:")
    mailbox_label.grid(row=6, column=0, pady=(20, 2), padx=5, sticky='s', columnspan=2)
    mailbox_entry = tk.Entry(login_window, width=25, justify='center', bg='#ADD8E6', fg='#006400')
    mailbox_entry.grid(row=7, column=0, pady=2, padx=5, sticky='n', columnspan=2)

    # 创建验证码输入框和发送验证码按钮
    confirm_code_frame = tk.Frame(login_window)
    confirm_code_frame.grid(row=8, column=0, pady=(20, 2), padx=5, sticky='s', columnspan=2)
    confirm_code_label = tk.Label(confirm_code_frame, text="请输入验证码:")
    confirm_code_label.grid(row=0, column=0, padx=2, sticky='s')
    confirm_code_entry = tk.Entry(confirm_code_frame, width=20, justify='center', bg='#ADD8E6', fg='#00FF00')
    confirm_code_entry.grid(row=1, column=0, padx=2, pady=2, sticky='n')
    send_code_button = tk.Button(confirm_code_frame, text="发送验证码", width=10,
                                 command=partial(comfirm_code_send, sock, mailbox_entry))
    send_code_button.grid(row=1, column=1, padx=2, pady=2, sticky='n')

    # 创建注册按钮
    signup_button = tk.Button(login_window, text="注册",
                              command=partial(ableSignup, sock, nickname_entry, password_entry, confirm_pw_entry,
                                              confirm_code_entry))
    signup_button.grid(row=9, column=0, pady=20, padx=5, sticky='ew', columnspan=2)


# 修改发送邮箱的消息格式，与服务器解析匹配
def comfirm_code_send(client_socket, mailbox_entry):
    mailaddr = mailbox_entry.get()
    if not mailaddr:
        messagebox.showwarning("警告", "请输入可用邮箱")
    else:
        # 发送纯邮箱地址，与服务器正则匹配
        client_socket.send(mailaddr.encode())
        messagebox.showinfo("消息", "验证码已发送！")


# 修改验证码发送逻辑
def ableSignup(client_socket, nickname_entry, password_entry, confirm_pw_entry, confirm_code_entry):
    global nickname, password
    # 先验证密码是否一致
    if password_entry.get() != confirm_pw_entry.get():
        messagebox.showwarning("警告", "两次密码输入不一致")
        return

    nickname = nickname_entry.get()
    password = password_entry.get()
    confirm_code = confirm_code_entry.get()

    if not nickname or not password or not confirm_code:
        messagebox.showwarning("警告", "请填写完整信息")
        return

    # 发送验证码格式与服务器匹配
    client_socket.send(f"CODE:{confirm_code}".encode())

########################################################################################################


def login() -> None:
    global sock
    login_window.destroy()
    chat_window = tk.Tk()
    chat_window.title("聊天室 - 聊天主界面")
    chat_window.geometry("820x720")
    chat_window.configure(bg="#f5f7fa")
    # 居中
    chat_window.update_idletasks()
    sw = chat_window.winfo_screenwidth()
    sh = chat_window.winfo_screenheight()
    x = (sw - 820) // 2
    y = (sh - 720) // 2
    chat_window.geometry(f"820x720+{x}+{y}")

    # 顶部标题
    title_frame = tk.Frame(chat_window, bg="#3578e5", height=60)
    title_frame.pack(fill='x')
    title_label = tk.Label(title_frame, text="聊天室", font=("微软雅黑", 24, "bold"), fg="white", bg="#3578e5")
    title_label.pack(pady=12)

    style = ttk.Style()
    style.theme_use('default')
    style.configure('TNotebook.Tab', padding=[16, 8], font=("微软雅黑", 12), focuscolor=style.lookup('TNotebook.Tab', 'background'))
    style.map('TNotebook.Tab', background=[('selected', '#eaf1fb')])

    tab_control = ttk.Notebook(chat_window, style='TNotebook')
    tab_control.pack(expand=1, fill="both", padx=18, pady=18)

    # 普通聊天页面
    normal_chat_frame = ttk.Frame(tab_control)
    tab_control.add(normal_chat_frame, text='普通聊天')
    normal_chat_frame.rowconfigure(0, weight=1)
    normal_chat_frame.columnconfigure(0, weight=1)

    chat_box_normal = tk.Text(normal_chat_frame, bg='#f7fafc', fg='#222', font=("微软雅黑", 13), bd=0, relief='flat', wrap='word')
    chat_box_normal.grid(row=0, column=0, sticky='nsew', padx=10, pady=(10,0))

    input_frame_normal = tk.Frame(normal_chat_frame, bg="#f5f7fa", height=50)
    input_frame_normal.grid(row=1, column=0, sticky='ew', padx=10, pady=10)
    input_frame_normal.grid_propagate(False)
    message_entry_normal = ttk.Entry(input_frame_normal, width=60, font=("微软雅黑", 12))
    message_entry_normal.pack(side='left', padx=(0, 8), expand=True, fill='x')
    message_entry_normal.bind('<Return>', partial(send_message, sock, message_entry_normal))
    emoji_button_normal = ttk.Button(input_frame_normal, text="😀", width=3, command=partial(open_emoji_selector, message_entry_normal))
    emoji_button_normal.pack(side="left", padx=4)
    file_button_normal = ttk.Button(input_frame_normal, text="📁", width=3, command=open_file_selector)
    file_button_normal.pack(side="left", padx=4)
    send_button_normal = ttk.Button(input_frame_normal, text="发送", width=10, command=partial(send_message, sock, message_entry_normal))
    send_button_normal.pack(side="left", padx=8)
    check_queue(chat_box_normal)

    # DeepSeek API聊天页面
    deepseek_chat_frame = ttk.Frame(tab_control)
    tab_control.add(deepseek_chat_frame, text='DeepSeek API聊天')
    deepseek_chat_frame.rowconfigure(0, weight=1)
    deepseek_chat_frame.columnconfigure(0, weight=1)
    chat_box_deepseek = tk.Text(deepseek_chat_frame, bg='#f7fafc', fg='#222', font=("微软雅黑", 13), bd=0, relief='flat', wrap='word')
    chat_box_deepseek.grid(row=0, column=0, sticky='nsew', padx=10, pady=(10,0))
    input_frame_deepseek = tk.Frame(deepseek_chat_frame, bg="#f5f7fa", height=50)
    input_frame_deepseek.grid(row=1, column=0, sticky='ew', padx=10, pady=10)
    input_frame_deepseek.grid_propagate(False)
    message_entry_deepseek = ttk.Entry(input_frame_deepseek, width=60, font=("微软雅黑", 12))
    message_entry_deepseek.pack(side='left', padx=(0, 8), expand=True, fill='x')
    message_entry_deepseek.bind('<Return>',partial(send_ds_message, message_entry_deepseek))
    emoji_button_deepseek = ttk.Button(input_frame_deepseek, text="😀", width=3, command=partial(open_emoji_selector, message_entry_deepseek))
    emoji_button_deepseek.pack(side="left", padx=4)
    send_button_deepseek = ttk.Button(input_frame_deepseek, text="发送", width=10, command=partial(send_ds_message, message_entry_deepseek))
    send_button_deepseek.pack(side="left", padx=8)
    check_ds_queue(chat_box_deepseek)

    chat_window.protocol("WM_DELETE_WINDOW", partial(on_closing, chat_window))
    chat_window.mainloop()

# emoji 选择器
def open_emoji_selector(message_entry):
    emoji_window = tk.Toplevel(message_entry.master)
    emoji_window.title("Emoji选择")
    # 定义emoji
    emojis = [
        "😀", "😃", "😄", "😊", "😍",
        "😔", "😢", "😭", "😂", "🤣",
        "🤔", "🥳", "💪", "👍", "👎"
    ]
    # 创建按钮来选择 emoji，并分成三排显示
    for i, emoji in enumerate(emojis):
        row = i // 5  # 每排显示 5 个 emoji
        col = i % 5
        button = tk.Button(emoji_window, text=emoji, font=("Segoe UI Emoji", 16),
                           command=partial(insert_emoji, message_entry, emoji))
        button.grid(row=row, column=col, padx=5, pady=5)

#选择 emoji 并插入到输入框
def insert_emoji(message_entry, emoji):
    current_text = message_entry.get()
    message_entry.delete(0, tk.END)
    message_entry.insert(0, current_text + emoji)


def open_file_selector():
    """打开文件选择器并发送文件"""
    file_path = filedialog.askopenfilename()
    if not file_path:
        return
    file_name = os.path.basename(file_path)
    file_size = os.path.getsize(file_path)
    try:
        with open(file_path, "rb") as f:
            file_data = f.read()
        # 发送文件头：文件名长度(4字节) + 文件名 + 文件大小(8字节)
        file_name_bytes = file_name.encode("utf-8")
        file_sock.sendall(len(file_name_bytes).to_bytes(4, "big"))
        file_sock.sendall(file_name_bytes)
        file_sock.sendall(file_size.to_bytes(8, "big"))
        # 发送文件内容
        file_sock.sendall(file_data)
        messagebox.showinfo("提示", f"文件 {file_name} 发送成功！")
    except Exception as e:
        messagebox.showerror("错误", f"文件发送失败: {e}")


def receive_files(file_sock):
    """接收服务器转发的文件"""
    while True:
        try:
            # 1. 先接收文件名长度
            name_len_bytes = file_sock.recv(4)
            if not name_len_bytes:
                continue
            name_len = int.from_bytes(name_len_bytes, "big")
            # 2. 接收文件名
            file_name = b''
            while len(file_name) < name_len:
                chunk = file_sock.recv(name_len - len(file_name))
                if not chunk:
                    break
                file_name += chunk
            file_name = file_name.decode("utf-8")
            # 3. 接收文件大小
            file_size_bytes = file_sock.recv(8)
            file_size = int.from_bytes(file_size_bytes, "big")
            # 4. 接收文件内容
            received = 0
            file_data = b""
            while received < file_size:
                chunk = file_sock.recv(min(4096, file_size - received))
                if not chunk:
                    break
                file_data += chunk
                received += len(chunk)
            # 5. 弹出保存对话框
            save_path = filedialog.asksaveasfilename(initialfile=file_name, title="保存接收的文件")
            if save_path:
                with open(save_path, "wb") as f:
                    f.write(file_data)
                messagebox.showinfo("提示", f"文件 {file_name} 已保存到 {save_path}")
        except Exception as e:
            print(f"接收文件出错: {e}")


######################################################################################################################
#向其他客户端发送消息
def send_message(sock, message_entry, event=None):
    message = message_entry.get()
    if message:
        nickname_front = (nickname + ': ').encode()  # 用户昵称前缀
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S').encode()  # 用户消息时间
        complete_message = nickname_front + current_time + b'\n' + message.encode() + '\n'.encode()

        sock.sendall(complete_message)
        message_entry.delete(0, tk.END)
        message_queue.put(complete_message.decode())

#通过deepseek api发送消息
def send_ds_message(message_entry_deepseek, event=None):
    message = message_entry_deepseek.get()
    if message:
        nickname_front = (nickname + ': ').encode()  # 用户昵称前缀
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S').encode()  # 用户消息时间
        complete_message = nickname_front + current_time + b'\n' + message.encode() + '\n'.encode()

        ds_message_queue.put(complete_message.decode())

        message_entry_deepseek.delete(0, tk.END)

        # 使用多线程处理 DeepSeek API 请求
        threading.Thread(target=process_deepseek_response, args=(message,)).start()


def process_deepseek_response(message):
    try:
        # 调用 deepseek_chat 发送消息并获取响应
        response = Deepseek_chat.deepseek_chat(message)
        print(response)
        if response:
            ai_nickname_front = "DeepSeek: ".encode()
            ai_current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S').encode()
            ai_complete_message = ai_nickname_front + ai_current_time + b'\n' + response.encode() + '\n'.encode()
            # 将 AI 的响应放入队列
            ds_message_queue.put(ai_complete_message.decode())
    except Exception as e:
        print(f"Error processing DeepSeek response: {e}")


def receive_messages(sock):
    """处理从服务器接收到的消息"""
    while True:
        try:
            message = sock.recv(4096).decode()
            print("receive_messages:"+message)
            # message = parse_message(message)
            if not message:
                break

            elif message == "Sign up agree":
                # 注册成功，发送用户名和密码

                sock.send(f"REGISTER {nickname} {password}".encode())
                print(f"REGISTER {nickname} {password}")
                messagebox.showinfo("成功", "注册成功，即将进入登录"),

            elif message != None:
                message_queue.put(message)
        except Exception as e:
            print(f"Error receiving message: {e}")
            break

#检查正常聊天消息队列并显示
def check_queue(chat_box):
    try:
        while not message_queue.empty():
            message = message_queue.get_nowait()
            # 设置标签配置，指定字体大小
            chat_box.tag_configure("bigfont", font=("Times", 15))

            chat_box.insert(tk.END, message + '\n', "bigfont")
            chat_box.see(tk.END)  # 滚动到最新消息
    except queue.Empty:
        pass
    finally:
        chat_box.after(100, lambda: check_queue(chat_box))  # 每 100 毫秒检查s一次队列

#检查与deepseek聊天消息队列并显示
def check_ds_queue(chat_box):
    try:
        while not ds_message_queue.empty():
            message = ds_message_queue.get_nowait()
            # 设置标签配置，指定字体大小
            chat_box.tag_configure("bigfont", font=("Times", 15))

            chat_box.insert(tk.END, message + '\n', "bigfont")
            chat_box.see(tk.END)  # 滚动到最新消息
    except queue.Empty:
        pass
    finally:
        chat_box.after(100, lambda: check_ds_queue(chat_box))  # 每 100 毫秒检查s一次队列

def on_closing(chat_window):
    chat_window.destroy()
    sys.exit()

#########################################################################################################

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #聊天用套接字
sock.connect((host, port))

file_sock = socket.socket()  # 发送文件用套接字
file_sock.connect((host, file_port))
# 开始监听消息
threading.Thread(target=receive_messages, args=(sock,)).start()
# 开始监听文件收发
threading.Thread(target=receive_files, args=(file_sock,)).start()

# 创建登录窗口
login_window = tk.Tk()
login_window.title("聊天室-登录")
# 设置窗口初始大小
login_window.geometry("400x250")
# 禁止用户调整窗口大小
login_window.resizable(False, False)

# 创建昵称输入框
nickname_label = tk.Label(login_window, text="请输入用户名:")
nickname_label.pack(pady=5)
nickname_entry = tk.Entry(login_window, width=30, justify='center', bg='#ADD8E6', fg='#006400')
nickname_entry.pack(pady=5)

#创建密码输入框
password_label = tk.Label(login_window, text="请输入密码:")
password_label.pack(pady=5)
password_entry = tk.Entry(login_window, width=30, justify='center', bg='#ADD8E6', fg='#006400')
password_entry.pack(pady=5)

# 创建登录按钮
login_button = tk.Button(login_window, text="登录", width=20, command=partial(ableLogin, nickname_entry))
login_button.pack(side="left", padx=5, pady=5, expand=True,)

# 创建注册按钮
signup_button = tk.Button(login_window, text="注册", width=20, command=signup)
signup_button.pack(side="left", padx=5, pady=1, expand=True,)


# 运行登录窗口主循环
login_window.mainloop()