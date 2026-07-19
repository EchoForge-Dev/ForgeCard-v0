# 导入 lookup_uid
from card_store import lookup_uid
# 导入 fetch_profile
from echoid_client import fetch_profile
# 写 main()
def main():
    # 提示输入 UID
    uid = input("请输入 UID: ")

    # 查询 lookup_uid()
    binding_result=lookup_uid(uid)
    # 如果没有绑定
    if not binding_result:
        # 打印 未注册
        print("未注册")
        # return
        return
    # 从绑定结果取得 stake_address
    stake_address = binding_result["stake_address"]
    # 调 fetch_profile()
    profile = fetch_profile(stake_address)
    # 如果没有 profile
    if not profile:
        # 提示请先注册 EchoID
        print("请先注册 EchoID")
        return

        # return

    # 从 profile JSON 提取：
    profile_id = profile.get("profile_id"," ")
    # display_name
    display_name = profile.get("display_name"," ")
        # tier 中文
    tier = profile.get("tier"," ")
        # tier role
    tier_role=profile.get("tier_role"," ")

        # tagline
    tagline = profile.get("tagline"," ")
    # 打印结果
    print("Display Name:", display_name)
    print("Profile ID:", profile_id)
    print("Tier:", tier)
    print("Tier Role:", tier_role)
    print("Tagline:", tagline)
# if __name__ == "__main__"
if __name__ == "__main__":
    main()