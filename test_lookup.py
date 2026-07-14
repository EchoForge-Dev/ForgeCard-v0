# 从 card_store 导入 lookup_uid 函数

from card_store import lookup_uid


def main():
    # 让用户输入 UID
    uid = input("请输入UID:")
    # 调用 lookup_uid(uid)
    result= lookup_uid(uid)
    # 如果结果是 None
    if result is None:
        # 打印“未注册”
        print("未注册")
        # 结束函数
        return
    # 如果查到了
        # 打印“已注册”
        # 打印显示名称
        # 打印质押地址
    if result is not None:
        print("已注册")
        print("显示名称：",result["display_name"])
        print("质押地址：",result["stake_address"])


# 如果这个文件被直接运行，就执行 main()
if __name__ =="__main__":
    main()