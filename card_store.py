# 导入需要的库
import json
from pathlib import Path


# 指定 JSON 数据文件
BASE_DIR = Path(__file__).resolve().parent

DB_FILE = BASE_DIR / "card_store.json"

# 写一个函数：读取绑定数据
    # 如果文件不存在，返回空字典
    # 如果文件存在，打开文件
    # 把 JSON 内容读出来并返回
def read_bindings():
    if not DB_FILE.exists():
        return {}

    with open(DB_FILE,"r", encoding="utf-8") as f:
        return json.load(f)


# 写一个函数：保存绑定数据
    # 打开 JSON 文件
    # 把字典写进去
def save_bindings(bindings):
    with open(DB_FILE,"w",encoding="utf-8")as f:
        json.dump(bindings,f,indent=2)


# 写一个函数：标准化 UID
    # 去掉空格、冒号、横线
    # 转成大写

def std_uid(uid):
    return uid.replace(" ","").replace(":","").replace("-","").upper()
# 写一个函数：绑定卡片
    # 标准化 UID
    # 读取旧数据
    # 写入新的 UID 记录
    # 保存数据
    # 返回新绑定
def bind_card(uid, stake_address, display_name):
    uid =std_uid(uid)
    bindings =read_bindings()  
    bindings[uid]={"stake_address": stake_address, "display_name": display_name}
    save_bindings(bindings)
    return bindings[uid]
# 写一个函数：查询 UID
    # 标准化 UID
    # 读取数据
    # 如果找到就返回
    # 找不到就返回 None
def lookup_uid(uid):
    uid=std_uid(uid)
    bindings=read_bindings()


