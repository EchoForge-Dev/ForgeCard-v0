# 导入 argparse，用来读取命令行参数
import argparse
# 从 card_store 导入 bind_card 函数
from card_store import bind_card
# 定义 main 函数
    # 创建 ArgumentParser
    # 添加 uid 参数
    # 添加 stake_address 参数
    # 添加 display_name 参数
    # 解析参数

def main():
    parser = argparse.ArgumentParser(description="绑定卡片")
    parser.add_argument("uid", help="卡片的uid")
    parser.add_argument("stake_address", help="绑定的质押地址")
    parser.add_argument("display_name",help="显示名称")
    args=parser.parse_args()

    # 调用 card_store 里的 bind_card()
    # 打印绑定成功
    # 打印 UID
    # 打印 stake address
    # 打印 display name
    binding_result = bind_card(args.uid, args.stake_address, args.display_name)
    print("绑定成功！")
    print(f"UID:{args.uid}")
    print(f"质押地址:{args.stake_address}")
    print(f"显示名称:{args.display_name}")

# 如果这个文件被直接运行，就执行 main()
if __name__ == "__main__":
    main()