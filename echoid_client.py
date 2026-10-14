import requests

# 定义 BASE_URL
BASE_URL = "https://api-id.echoforgeef.com"

# 写 fetch_profile(stake_address)
def fetch_profile(stake_address, account_type="individual"):
    """
    Fetch an EchoID profile by Cardano stake address.

    Returns:
        dict: JSON response when successful.
        None: If the profile does not exist or an error occurs.
    """
    # 拼 URL
    url = f"{BASE_URL}/api/echoid/profile/{stake_address}"
    
    # requests.get()
    params = {
        "accountType": account_type
    }
    
    response = requests.get(
    url,
    params=params,
    timeout=5
)
    
    # 如果404
    if response.status_code == 404:
        # 打印提示
        print(f"Profile not found for {stake_address}")
        # return None
        return None
    
    # 如果不是200
    if response.status_code != 200:
        # 打印错误
        print(f"Error: {response.status_code}")
        # return None
        return None
    
    # 返回 response.json()
    return response.json()