"""
ForgeCard Pi 端主脚本 —— 手写骨架 v2（留空处是你的，注释是脚手架）

契约（见 MAINTENANCE.md）只有三条：
    读 UID  →  lookup_uid()  →  让 kiosk 浏览器落到目标 URL
Python 永远只单向推 URL。不查 EchoID API、不决定 accountType、
不负责复位屏幕 —— 前端自己会回 idle。

已定决策：
    一、浏览器控制 = 每次重开新进程
    二、未绑定卡   = ?status=unbound
    三、前端部署   = Vercel（forgecard.echoforgellc.tech）
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
    [ ] 块 3  UID 格式转换          ← 下一个写这个
    [ ] 块 4  PN532 初始化（搬你 Week 2 的代码）
    [ ] 块 5  主循环 + 去抖          ← 最后写，只能在 Pi 上调

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
FRONTEND_BASE = "https://forgecard.echoforgellc.tech"

# Pi OS 上通常是 chromium-browser，新版 Debian 可能叫 chromium。真机 which 一下。
BROWSER_CMD = "chromium-browser"
BROWSER_FLAGS = [
    "--kiosk",
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
# 块 2：开浏览器   [最笨版完成；kill 逻辑真机阶段补]
# ---------------------------------------------------------------------------

# 上一次开的浏览器进程。要跨"多次函数调用"存活，所以是模块级变量 + global。
# 这是脚本里第二个"必须记住历史"的地方（第一个是块 5 的去抖）。手册 §3。
_browser_process = None


def open_kiosk(url):
    """让 kiosk 浏览器显示 url。决策一 = 每次重开新进程。"""
    global _browser_process
    _browser_process = subprocess.Popen([BROWSER_CMD, *BROWSER_FLAGS, url])
    # 真机阶段要补的两件事（现在不写，先让最笨版跑起来）：
    # 1. 开新的之前先结束上一个 —— _browser_process 记着它是谁，
    #    用 .terminate()；怎么确认它真的退了，查 .wait() 和 .poll() 的区别（手册 §7）。
    # 2. "结束 → 新开"之间要不要等、等多久 —— sleep(猜一个数) 是能跑但错的答案，
    #    快的机器浪费时间，慢的机器照样失败。答案也在手册 §7 那两个方法里。


# ---------------------------------------------------------------------------
# 块 3：UID 格式转换   ← 从这里继续
# ---------------------------------------------------------------------------

def normalize_reader_uid(raw_uid):
    """把 PN532 吐出来的 UID 转成 card_store.json 里键的形态。"""
    # 砍掉键盘模式之后，输入只剩一种形态：PN532 给的 bytearray，
    # 用 for 遍历它，拿到的是整数（254, 138, 78, 7）。不用再考虑字符串输入。
    # 目标形态： "FE8A4E07"
    #
    # 三个坑（共同点：错了不报错，只会让 lookup 返回 None，
    # 看起来像"这张卡没绑定"，实际是 UID 拼错了）：
    #   1. 0x 前缀 —— std_uid 只删空格/冒号/横线，不认识 0x
    #   2. 补零   —— 0x07 必须变成 "07"，不是 "7"
    #   3. 大小写 —— 'fe' 和 'FE' 是两个不同的字典键
    # 一个写法平掉全部三个：f"{7:02X}" 会得到什么？手册 §1 拆解了这个写法。
    #
    # 你的设计决定：转换放在这里（读卡边界，脏数据进门就洗掉，
    # card_store 永远只认干净字符串），还是去扩展 card_store.std_uid
    # （它被 bind_card.py 和 test_lookup.py 共用，改它 = 改所有调用方的行为）。
    # 两种都对，但理由要说得出来。
    raise NotImplementedError("块 3")


# ---------------------------------------------------------------------------
# 块 4：PN532 初始化（搬你 Week 2 的代码）
# ---------------------------------------------------------------------------

def init_pn532():
    """初始化 I2C 和 PN532，返回 pn532 对象。整个程序只在启动时调一次。"""
    # 把你 Week 2 亲手写过、在 Pi 上跑通过的初始化搬进来：
    # I2C 总线 → PN532_I2C → SAM_configuration，最后 return pn532。
    #
    # 唯一的新做法：import board / busio / adafruit_pn532 写在这个函数里面，
    # 不写在文件顶部。原因：这三个库 Mac 上装不上，放顶部的话
    # 这个文件在 Mac 上连 import 都过不去，块 1/2/3 就全测不了了。
    # 惯例 vs 前提，手册 §2。
    #
    # 想一个问题再动笔：为什么初始化不放进主循环、每轮做一次？
    raise NotImplementedError("块 4")


# ---------------------------------------------------------------------------
# 块 5：主循环 + 去抖   ← 最后写，只能在 Pi 上调
# ---------------------------------------------------------------------------

def main_loop(pn532):
    """一直读卡、一直推 URL。永不退出。"""
    # 这是你第一个"永远不结束"的程序。它必须记住自己刚才干了什么——
    # 否则卡贴着不动的那几秒，你会往浏览器推几十次同一个 URL。

    last_uid = None    # 上一次处理的是哪张卡（循环外定义、循环内更新，手册 §3）
    last_seen = 0.0    # 那次是什么时候（秒）

    # 测时间差用 time.monotonic()，不用 time.time()——
    # 墙上时钟会被对时改动甚至倒退，monotonic 只保证单调递增。手册 §5。

    while True:
        # 5a：读一次。pn532.read_passive_target(timeout=0.5)。
        #     返回 None = 现在没人拍卡，不是错误——直接进下一轮（continue，手册 §4）。
        #     timeout 本身就在替你等，循环不会空转烧 CPU。
        #     读到了 → 用 normalize_reader_uid() 洗成标准形态。

        # 5b：判断"是不是同一张卡还贴在上面"。条件要同时用 last_uid 和 last_seen。
        #     先想清楚：同一张卡、但已经过了去抖窗口，该不该重新触发？
        #     （展会场景：有人拍完卡走了，十分钟后回来又拍同一张，屏幕该不该亮？）

        # 5c：决定触发 → 更新 last_uid / last_seen。
        #     真正的问题是更新的时机：放在查表/开浏览器之前，还是之后？
        #     如果中间抛了异常，你希望这张卡下一秒能自动重试，
        #     还是被记成"已处理"卡住五秒？两种都能自圆其说，选一个并知道自己在选。

        # 5d：lookup_uid(uid) 拿绑定。
        #         有绑定 → build_profile_url(...) → open_kiosk(...)
        #         没绑定 → build_unbound_url()   → open_kiosk(...)   （决策二）
        #     第三种情况：中间抛异常。跑一整天的循环不能因为一次失败就退出——
        #     try/except 该包住哪几行、except 里除了不崩还该做什么
        #     （你怎么知道它出过错？），手册 §6。
        raise NotImplementedError("块 5")


# ---------------------------------------------------------------------------
# 入口
# ---------------------------------------------------------------------------

def main():
    pn532 = init_pn532()
    main_loop(pn532)


if __name__ == "__main__":
    main()
