import requests

def deepseek_chat(inputAction):
    headers = {
        "Authorization": "", #这里填入获取到的Depseek API
        "Content-Type": "application/json"
    }
    data = {
        "model": "deepseek-reasoner",
        "messages": [
            {"role": "system", "content": "你是聊天室内置的ai助手"},
            {"role": "user", "content": "用户发言：" + inputAction}
        ],
        "temperature": 0.5
    }
    try:
        response = requests.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers=headers,
            json=data
        )
        # 新增：打印状态码和原始响应内容
        print(f"API响应状态码: {response.status_code}")
        print(f"API原始响应: {response.text}")  # 关键：查看是否为JSON

        if response.status_code != 200:
            print(f"API调用失败: {response.status_code}")
            return "抱歉，AI服务暂时不可用"

        responsejson = response.json()
        return responsejson["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"API调用异常: {e}")
        return "抱歉，处理AI响应时出错"
