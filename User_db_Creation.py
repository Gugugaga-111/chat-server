import sqlite3
import hashlib


def hash_password(password: str) -> str:
    """对密码进行哈希处理"""
    return hashlib.sha256(password.encode()).hexdigest()


def add_user(username: str, password: str):
    """向users表中添加一个新用户"""
    password_hash = hash_password(password)
    try:
        # 为每个操作创建新连接
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()

        # 确保表存在
        cursor.execute('''
                       CREATE TABLE IF NOT EXISTS users
                       (
                           id
                           INTEGER
                           PRIMARY
                           KEY
                           AUTOINCREMENT,
                           username
                           TEXT
                           NOT
                           NULL
                           UNIQUE,
                           password_hash
                           TEXT
                           NOT
                           NULL
                       )
                       ''')

        cursor.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)', (username, password_hash))
        conn.commit()
        print(f"用户 {username} 已成功添加。")
        return True
    except sqlite3.IntegrityError:
        print(f"用户名 {username} 已存在。")
        return False
    finally:
        # 确保连接关闭
        if conn:
            conn.close()


def get_user(username: str) -> dict:
    """根据用户名获取用户信息"""
    try:
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        if user:
            return {
                'id': user[0],
                'username': user[1],
                'password_hash': user[2]
            }
        return None
    finally:
        if conn:
            conn.close()


def verify_password(username: str, password: str) -> bool:
    """验证用户名和密码是否匹配"""
    user = get_user(username)
    if user:
        password_hash = hash_password(password)
        return user['password_hash'] == password_hash
    return False