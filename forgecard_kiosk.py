"""
ForgeCard Pi 端主脚本 —— 手写骨架 v2（留空处是你的，注释是脚手架）

契约（见 MAINTENANCE.md）只有三条：
    读 UID  →  lookup_uid()  →  让 kiosk 浏览器落到目标 URL
Python 永远只单向推 URL。不查 EchoID API、不决定 accountType、
不负责复位屏幕 —— 前端自己会回 idle。

已定决策：
    一、浏览器控制 = 复用实例
    二、未绑定卡   = ?status=unbound
    三、前端部署   = Vercel（forgecard.echoforgeef.com）
    四、砍掉键盘模式 —— 只有 PN532 一条读卡路径，
        代价：主循环只能在 Pi 上调（值得记一行 dev log）

骨架 v2 相对第一版的变化：
    - 键盘 reader、--keyboard、argparse：删（决策四）
    - "返回函数的函数"模式：删 —— init_pn532() 直接返回 pn532 对象，
      主循环自己调 read_passive_target()
    - 原块 4/5 里 AI 生成的实现：删（CLAUDE.md 红线）
    - 编号理顺为 0-5，一套编号

进度：
    [x] 块 1  拼 URL（两个函数）
    [x] 块 2  开浏览器（最笨版能用；kill 逻辑 = 真机阶段补）
    [x] 块 3  UID 格式转换         
    [x] 块 4  PN532 初始化（搬你 Week 2 的代码）
    [x] 块 5  主循环 + 去抖         

看不懂的概念查 python_kiosk_sheet.md，开头有"块 → 节"的索引表。
"""

import subprocess
import time
from urllib.parse import quote

from card_store import lookup_uid

# ---------------------------------------------------------------------------
# 块 0：配置
# ---------------------------------------------------------------------------

# 决策三：前端在 Vercel。本地调前端时临时改成 http://localhost:3000
FRONTEND_BASE = "https://forgecard.echoforgeef.com"

# Pi OS 上是chromium。
BROWSER_CMD = ["chromium-browser", "chromium", "google-chrome", "google-chrome-stable"]
BROWSER_FLAGS = [
    "--noerrdialogs",
    "--disable-infobars",
    "--disable-session-crashed-bubble",
]

# 5 秒是旧原型用过的数字，仅作参照——拿真卡试了再定。
DEBOUNCE_SECONDS = 5.0


# ---------------------------------------------------------------------------
# 块 1：拼 URL   [完成]
# ---------------------------------------------------------------------------

def build_profile_url(stake_address):
    """正常路径。quote 只包值、不包整个 URL——这个决定是你拿的，理由值得进 build log。"""
    return f"{FRONTEND_BASE}/?address={quote(stake_address)}"


def build_unbound_url():
    """决策二。URL 里不带 UID、不暴露映射表的存在——解耦没有被破坏。"""
    return f"{FRONTEND_BASE}/?status=unbound"


# ---------------------------------------------------------------------------
# 块 2：开浏览器 
# ---------------------------------------------------------------------------

_browser_process = None


def open_kiosk(url):
    """让 kiosk 浏览器显示 url。决策一 = 每次重开新进程。"""
    global _browser_process
    browser_cmd=None
    for candidate in BROWSER_CMD:
        if subprocess.run(["which", candidate], capture_output=True, text=True).returncode == 0:
            browser_cmd = candidate
            break

    if browser_cmd is None:
        browser_cmd = "xdg-open"

    if browser_cmd=="xdg-open":
        _browser_process = subprocess.Popen([browser_cmd,url])
    else:_browser_process = subprocess.Popen([browser_cmd,*BROWSER_FLAGS,url])


# ---------------------------------------------------------------------------
# 块 3：UID 格式转换
# ---------------------------------------------------------------------------

def normalize_reader_uid(raw_uid):
    """把 PN532 吐出来的 UID 转成 card_store.json 里键的形态。"""
    # 砍掉键盘模式之后，输入只剩一种形态：PN532 给的 bytearray，
    # 用 for 遍历它，拿到的是整数（254, 138, 78, 7）。不用再考虑字符串输入。
    std_uid = ""
    for b in raw_uid:
        # 目标形态： "FE8A4E07"
        #
        # 三个坑（共同点：错了不报错，只会让 lookup 返回 None，
        # 看起来像"这张卡没绑定"，实际是 UID 拼错了）：
        #   1. 0x 前缀 —— std_uid 只删空格/冒号/横线，不认识 0x
        #   2. 补零   —— 0x07 必须变成 "07"，不是 "7"
        #   3. 大小写 —— 'fe' 和 'FE' 是两个不同的字典键
        std_uid += f"{b:02X}"
    return std_uid

    # 一个写法平掉全部三个：f"{7:02X}" 会得到什么？手册 §1 拆解了这个写法。
    #
    # 你的设计决定：转换放在这里（读卡边界，脏数据进门就洗掉，
    # card_store 永远只认干净字符串），还是去扩展 card_store.std_uid
    # （它被 bind_card.py 和 test_lookup.py 共用，改它 = 改所有调用方的行为）。
    # 两种都对，但理由要说得出来。
    


# ---------------------------------------------------------------------------
# 块 4：PN532 初始化（搬你 Week 2 的代码）
# ---------------------------------------------------------------------------

def init_pn532():
    """初始化 I2C 和 PN532，返回 pn532 对象。整个程序只在启动时调一次。"""
    import board
    import busio
    from adafruit_pn532.i2c import PN532_I2C

    print("[PN532] starting initialization", flush=True)
    for attempt in range(3):
        try:
            print(f"[PN532] attempt {attempt +1}/3: creating I2C bus", flush=True)
            i2c = busio.I2C(board.SCL, board.SDA)
            print(f"[PN532] I2C scan result:{i2c.scan()}",flush=True)
            print("[PN532] creating PN532 object", flush= True)
            pn532 = PN532_I2C(i2c, address=0x24, debug=False)
            print("[PN532] configuring SAM", flush=True)
            pn532.SAM_configuration()
            print("[PN532] initialization complete", flush = True)
            return pn532
        except Exception as exc:
            print(f"[PN532] attempt {attempt + 1} failed: {type(exc).__name__}: {exc}",flush =True)
            if attempt == 2:
                raise
            time.sleep(0.5)


# ---------------------------------------------------------------------------
# 块 5：主循环 + 去抖 
# ---------------------------------------------------------------------------

def main_loop(pn532):
    """一直读卡、一直推 URL。永不退出。"""
    last_uid = None   
    last_seen=0.0

    while True:
        try:
            raw_uid=pn532.read_passive_target(timeout=0.5)
            if raw_uid is None:
                continue

            uid=normalize_reader_uid(raw_uid)
            now=time.monotonic()

            if last_uid==uid and now - last_seen< DEBOUNCE_SECONDS:
                continue

            last_uid=uid
            last_seen=now

            print(f"[kiosk] card detected:{uid}", flush=True)
            entry=lookup_uid(uid)
            if entry is not None:
                url = build_profile_url(entry["stake_address"])
                print(f"[kiosk] opening profile URL: {url}", flush=True)
            else:
                url = build_unbound_url()
                print(f"[kiosk] opening unbound URL: {url}", flush=True)

            open_kiosk(url)

        except Exception as exc:
            print(f"[kiosk] loop error:{type(exc).__name__}:{exc}",flush=True)
            time.sleep(1.0)

# ---------------------------------------------------------------------------
# 入口
# ---------------------------------------------------------------------------

def main():
    print("[kiosk] starting", flush=True)
    try:
        pn532=init_pn532()
    except Exception as exc:
        print(f"[kiosk] PN532 init failed:{exc}",flush=True)
        return

    print("[kiosk] PN532 ready, entering main loop", flush=True)
    try:
        main_loop(pn532)
    except NotImplementedError:
        print("[kiosk] main loop not implemented yet", flush=True)
    except Exception as exc:
        print(f"[kiosk] loop failed:{exc}", flush=True)

if __name__ == "__main__":
    main()
