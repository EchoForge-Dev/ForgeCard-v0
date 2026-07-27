"""
ForgeCard Pi 端主脚本 —— 手写骨架（代码留空，注释是脚手架）

契约（见 MAINTENANCE.md）只有三条：
    读 UID  →  lookup_uid()  →  让 kiosk 浏览器落到目标 URL
Python 永远只单向推 URL。它不查 EchoID API、不决定 accountType、
也不负责把屏幕复位回 idle —— 前端自己会回 idle。

已定决策：
    一、浏览器控制 = 每次重开新进程（见 open_kiosk）
    二、未绑定卡   = 导航到 ?status=unbound，屏幕显示"此卡未注册"
    三、前端部署   = Vercel（forgecard.echoforgellc.tech）

建议动手顺序（不是按重要性排的，是按"多快能看到东西动"排的）：
    块 1 → 块 2 → 块 5 → 块 6，这四块写完你就有一个能跑的完整产品了，
    只是用键盘代替读卡器。拿到这个反馈之后再回头写块 3 和块 4。

没有 PN532 也能跑：
    python forgecard_kiosk.py --keyboard
"""

import argparse
import subprocess
import time
from urllib.parse import quote

from card_store import lookup_uid

# ---------------------------------------------------------------------------
# 块 0：配置
# ---------------------------------------------------------------------------

# 决策三：前端在 Vercel。本地调前端时临时改成 http://localhost:3000
FRONTEND_BASE = "https://forgecard.echoforgellc.tech"

# 决策一相关：kiosk 浏览器的命令。Pi OS 上通常是 chromium-browser，
# 新版 Debian 上可能叫 chromium。真机上 `which` 一下再定。
BROWSER_CMD = "chromium-browser"
BROWSER_FLAGS = [
    "--kiosk",
    "--noerrdialogs",
    "--disable-infobars",
    "--disable-session-crashed-bubble",
]

# 块 6 会用到。5 秒是旧原型用过的数字，仅作参照——你自己拿张卡试，
# 太短会连触发，太长会让人觉得"再拍一次怎么没反应"。
DEBOUNCE_SECONDS = 5.0


# ---------------------------------------------------------------------------
# 块 1：拼 URL   ← 从这里开始，最简单
# ---------------------------------------------------------------------------

def build_profile_url(stake_address):
    """正常路径：把 stake address 拼成前端能消费的 URL。"""
    # 目标形态： https://forgecard.echoforgellc.tech/?address=stake1u9...
    #
    # 一个决定：直接 f-string 拼进去行不行？
    # stake_address 是从 card_store.json 里读出来的字符串。今天它一定干净，
    # 但"今天一定干净"不是一个能写进代码的假设——绑卡时手滑多打一个空格、
    # 或者以后这个值改成从别处来，URL 就会被截断或改写。
    # 查 urllib.parse.quote（文件顶部已经 import 好了），想清楚该 quote 哪一段：
    # 是整个 URL，还是只有 stake_address 这个值？
    #
    # 这就是工程代码和习题的第一个差别：习题的输入是题目保证正确的，
    # 工程代码的输入来自现实世界。
    raise NotImplementedError("块 1")


def build_unbound_url():
    """决策二：卡读到了，但本地没有绑定。"""
    # 目标形态： https://forgecard.echoforgellc.tech/?status=unbound
    #
    # 注意这个 URL 里没有 UID、也没有任何暴露映射表存在的信息。
    # 这是有意的：契约要防的是"前端知道 UID 和绑定表"，而不是
    # "前端永远只能收到 address"。所以加这个态没有破坏解耦。
    raise NotImplementedError("块 2")


# ---------------------------------------------------------------------------
# 块 2：开浏览器（决策一 = 每次重开新进程）
# ---------------------------------------------------------------------------

# 上一次开的浏览器进程。open_kiosk 需要跨调用记住它——这是这个脚本里
# 第二个"必须记住历史"的地方（第一个是块 6 的去抖）。
_browser_process = None


def open_kiosk(url):
    """让 kiosk 浏览器显示 url。"""
    global _browser_process

    # 先写最笨的版本，一行就够：
    #     subprocess.Popen([BROWSER_CMD, *BROWSER_FLAGS, url])
    # 写完立刻去真机上跑，因为下面两个问题只有跑起来才看得见。
    #
    # 问题 1：旧的 Chromium 还开着。不管它，Pi 的内存会被一路吃光。
    #        kill 谁？你怎么知道哪个进程是"上一次那个"？
    #        提示：Popen 返回的对象自己就记着 pid，你不需要去 pgrep 满世界找。
    #        这就是 _browser_process 这个全局变量存在的理由。
    #
    # 问题 2：kill 完立刻起新的，旧进程可能还没退干净、还占着显示。
    #        要不要等？等多久？"sleep(2) 大概够了"是能跑但错误的答案——
    #        因为它在快的机器上浪费时间，在慢的机器上仍然会失败。
    #        提示：Popen 对象有 .terminate() / .wait() / .poll()，
    #        查一下 .wait() 和 .poll() 的区别，正确答案在里面。
    #
    # 真机上先验证一件事，能省掉上面全部工作：
    #        Chromium 已经在跑的时候，再执行 `chromium-browser <url>`，
    #        很多环境下不会真起新进程，而是把 URL 交给已有实例。
    #        如果 kiosk 模式下这个行为成立，你就免费拿到了"复用窗口"，
    #        两个问题自动消失。花五分钟测这个，再决定要不要写 kill 逻辑。
    raise NotImplementedError("块 3")


# ---------------------------------------------------------------------------
# 块 3：UID 格式转换
# ---------------------------------------------------------------------------

def normalize_reader_uid(raw_uid):
    """把读卡器吐出来的 UID 转成 card_store.json 里键的形态。"""
    # 读卡器给你的东西长这样（取决于库版本和你怎么打印它）：
    #     bytearray(b'\xfe\x8a\x4e\x07')      <- adafruit 实际返回的
    #     ['0xfe', '0x8a', '0x4e', '0x07']     <- 你 print 出来看到的形态
    #     [254, 138, 78, 7]                    <- 整数列表
    # 而映射表里的键长这样：
    #     "FE8A4E07"
    #
    # 三个坑。它们的共同点是：错了不会报错，只会让 lookup_uid 返回 None，
    # 于是你会以为"这张卡没绑定"，实际上是你把 UID 拼错了。
    # 静默失败比崩溃难查得多，这也是工程代码和习题的差别之一。
    #
    #   1. 0x 前缀：card_store.std_uid 只删空格/冒号/横线，不认识 0x。
    #   2. 补零：   0x07 必须变成 "07"，不是 "7"。少一个字符，
    #              后面整串全部错位，而且看起来还挺像个正常 UID。
    #   3. 大小写： 'fe' 和 'FE' 是两个不同的字典键。
    #
    # 提示：f"{7:02X}" 会得到什么？把这个想明白，三个坑一起解决。
    #
    # 你的设计决定：这个转换放在这里（读卡边界），还是去扩展
    # card_store.std_uid？想清楚再选——std_uid 现在被 bind_card.py 和
    # test_lookup.py 共用，改它等于改所有调用方的行为。而放在这里，
    # 意味着 card_store 永远只认"干净的字符串"，脏数据在进门口就被洗掉。
    # 两种都对，但理由要说得出来。
    raise NotImplementedError("块 4")


# ---------------------------------------------------------------------------
# 块 4 / 5：读卡
# ---------------------------------------------------------------------------

def make_pn532_reader():
    """返回一个"读一次卡"的函数。真硬件路径。"""
    # 把你 Week 2 手写的 PN532 读卡代码搬进来。
    # requirements-pi.txt 里那两个 adafruit 库就是给它备的：
    #     import board, busio
    #     from adafruit_pn532.i2c import PN532_I2C
    #
    # 初始化（I2C、SAM_configuration）放在这个函数里只做一次，
    # 返回的那个函数负责"读一次"。想想为什么不把初始化写进循环里。
    #
    # 返回的函数签名约定：读到卡返回已经 normalize 过的 UID 字符串，
    # 没读到返回 None。read_passive_target(timeout=...) 超时就是返回 None，
    # 这不是错误，是"现在没人拍卡"的正常状态。
    raise NotImplementedError("块 5a")


def make_keyboard_reader():
    """返回一个"读一次卡"的函数。开发路径，不需要硬件。"""
    # 用 input() 假装读卡器——你在 forgecard_demo.py 里已经写过这个。
    # 签名要和 make_pn532_reader() 返回的函数完全一致，
    # 这样 main_loop 不需要知道自己接的是真卡还是键盘。
    #
    # 这个"两种实现、同一个签名"的做法，就是让 main_loop 能在
    # 你的 Mac 上跑起来的全部原因。
    raise NotImplementedError("块 5b")


# ---------------------------------------------------------------------------
# 块 6：主循环 + 去抖   ← 这块最难，慢慢来
# ---------------------------------------------------------------------------

def main_loop(read_uid):
    """一直读卡、一直推 URL。read_uid 是上面两个 reader 之一。"""
    # 这是你第一个"永远不结束"的程序。
    # 习题里的 main() 跑完就退出，所以它不需要记住任何历史。
    # 这个循环要跑一整天，所以它必须记住自己刚才干了什么——否则
    # 卡贴在读卡器上不动的那几秒，你会往浏览器推几十次同一个 URL。

    last_uid = None    # 上一次处理的是哪张卡
    last_seen = 0.0    # 那次是什么时候（秒）

    # 为什么下面要用 time.monotonic() 而不是 time.time()？
    # time.time() 是墙上时钟，会被 NTP 对时、时区、夏令时改动，甚至倒退。
    # 倒退的那一瞬间，你算出来的"距离上次多久"会是负数，去抖直接失效。
    # monotonic 不保证是真实时间，只保证单调递增——它唯一的用途就是测时间差。
    # 这是个到哪都成立的规则：测时间差用 monotonic，显示时间才用 time.time()。

    while True:
        # TODO 6a: 读一次 UID。
        #          没读到（None）的时候该干什么？注意别让循环空转把 CPU 烧满——
        #          PN532 的 read_passive_target 自带 timeout 会帮你等，
        #          但键盘模式下 input() 是阻塞的，两种情况表现不一样。

        # TODO 6b: 读到了。判断这是不是"同一张卡还贴在上面"。
        #          条件要同时用到 last_uid 和 last_seen。
        #          先想清楚一件事：同一张卡，但已经过了去抖窗口——
        #          该不该重新触发？（拿去展会想：有人拍完卡走了，
        #          十分钟后回来又拍同一张，你希望屏幕亮吗？）

        # TODO 6c: 决定要触发了，更新 last_uid / last_seen。
        #          真正的问题是更新的时机：放在查表/开浏览器之前，还是之后？
        #          如果 lookup 或者开浏览器抛异常了，你希望这张卡下一秒
        #          能自动重试，还是被记成"已经处理过"然后卡住五秒？
        #          两种都能自圆其说，选一个并且知道自己在选什么。

        # TODO 6d: lookup_uid(uid) 拿绑定。
        #          有绑定 → build_profile_url(...) → open_kiosk(...)
        #          没绑定 → build_unbound_url()   → open_kiosk(...)   （决策二）
        #
        #          还有第三种情况：lookup 或者开浏览器把异常抛出来了。
        #          一个跑一整天的循环，绝对不能因为一次失败就整个退出——
        #          现场没人会去看终端。想想 try/except 该包住哪几行，
        #          以及 except 里除了不崩，还应该做什么（提示：你怎么知道它出过错？）
        raise NotImplementedError("块 6")


# ---------------------------------------------------------------------------
# 入口
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="ForgeCard kiosk 主循环")
    parser.add_argument(
        "--keyboard",
        action="store_true",
        help="用键盘输入代替 PN532（在 Mac 上开发时用）",
    )
    args = parser.parse_args()

    read_uid = make_keyboard_reader() if args.keyboard else make_pn532_reader()
    main_loop(read_uid)


if __name__ == "__main__":
    main()
