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
    data = profile["data"]
    profile_info = data["profile"]
    tier = data["tierMeta"]
    profile_id = profile.get("profile_id"," ")
    display_name = profile_info["display_name"] or "Unnamed"
    days = data["daysSinceJoined"]
    tier_cn = tier["cn"]
    tier_name = tier["name"]
    role = tier["role"]
    tagline = tier["forgeTagline"]
    narrative = tier["narrative"]

    # 打印结果
    print("=" * 50)
    print(" " * 18 + "ForgeCard V0")
    print("=" * 50)

    print(f"{'Card UID':20}: {uid}")
    print(f"{'Stake Address':20}: {stake_address}")
    print(f"{'Display Name':20}: {display_name or 'Unnamed'}")
    print(f"{'Tier':20}: {tier_name} ({tier_cn})")
    print(f"{'Role':20}: {role}")
    print(f"{'Days Since Joined':20}: {days}")
    print(f"{'Tagline':20}: {tagline}")

    print("=" * 50)
# if __name__ == "__main__"
if __name__ == "__main__":
    main()