# ForgeCard Week 5 知识手册（python_kiosk_sheet）

不是教程，是查阅表——和 Week 3 的 python_json_sheet.txt 同一用途。
写到哪一块卡住，查对应的节。例子全部是通用 Python，不是 kiosk 的实现；
把它们拼装成 ForgeCard 的代码，手是你的。

| 你在写的块 | 查这几节 |
|---|---|
| 块 2 真机阶段（kill 逻辑） | §3、§7 |
| 块 3 UID 转换 | §1 |
| 块 4 PN532 初始化 | §2、§8 |
| 块 5 主循环 | §3、§4、§5、§6、§8 |

---

## §1 字节、十六进制、拼字符串（块 3）

**PN532 给你的是什么。** `read_passive_target()` 返回 `bytearray(b'\xfe\x8a\x4e\x07')`。
bytearray 就是"一串 0–255 的整数"。用 for 遍历它，拿到的是整数：

    for b in bytearray(b'\x07\xfe'):
        print(b)        # 依次打出 7 和 254

**hex() 是你打印形态的来源。** `hex(254)` 得到 `'0xfe'`：小写、带 0x 前缀。
你 Week 2 打印出来的 `['0xfe', '0x8a', ...]` 就是对每个整数做了 hex()。
这个形态是给人看的，不是给字典键用的。

**f-string 格式说明符——一个写法平掉三个坑。** `f"{n:02X}"` 冒号后面三个字符各管一件事：

- `X` = 转大写十六进制（小写用 x），输出不带 0x 前缀
- `2` = 至少占两位
- `0` = 不够两位用 0 补

所以 `f"{7:02X}"` 得到 `"07"`（补零），`f"{254:02X}"` 得到 `"FE"`（大写、无前缀）。
0x 前缀、补零、大小写，三个坑一次全平。

**把多段拼成一个字符串，两种都对：**

    # 方法 A：循环累加（你已经会）
    s = ""
    for piece in ["AB", "CD"]:
        s = s + piece          # 结果 "ABCD"

    # 方法 B：join
    "".join(["AB", "CD"])      # 结果 "ABCD"

**列表推导式 = "用循环造列表"的缩写。** GPT 代码里你看不懂的 `[hex(i) for i in uid]` 就是它：

    [n * 2 for n in [1, 2, 3]]     # [2, 4, 6]

    # 完全等价于：
    result = []
    for n in [1, 2, 3]:
        result.append(n * 2)

读法：先看 for 后面（在遍历什么），再看开头（每个元素变成什么）。
不习惯就用方法 A 的循环写，功能一样，没人扣分。

---

## §2 import 写在函数里（块 4）

`import` 做的事：去环境里找这个库，找不到当场抛 ImportError。
顶部 import 是惯例，惯例的前提是"这个库哪台机器都装得上"。
board / busio / adafruit_pn532 只在 Pi 上装得上——前提破了，惯例让位：

    def init_pn532():
        import board            # 只有这个函数被真正调用时，才去找库
        import busio
        from adafruit_pn532.i2c import PN532_I2C
        ...

效果：这个文件在 Mac 上照样 import 得动，块 1/2/3 照样能测；
只有真的调 init_pn532() 才需要 Pi 环境。

---

## §3 状态：变量怎么"记住"（块 2、块 5）

变量有三种寿命，你的脚本三种全用上了：

**一、函数内局部变量——调用结束就没了。** Week 3-4 写的全是这种。

**二、循环外定义、循环内更新——同一次调用里跨轮存活。**

    total = 0
    for x in [1, 2, 3]:
        total = total + x      # 每一轮都看得见上一轮留下的结果
    # 循环结束后 total == 6

main_loop 的 last_uid / last_seen 就是这种：在 while 外面定义，循环每一轮读它、改它。
**不需要 global**——它们本来就在 main_loop 自己的作用域里。

**三、模块级变量 + global——跨"多次函数调用"存活。**

    _count = 0

    def hit():
        global _count          # 声明：我要改的是外面那个，不是新建一个局部的
        _count = _count + 1

    hit(); hit()               # _count == 2

open_kiosk 的 _browser_process 是这种：这次调用要拿到上一次调用存下的进程。
没有 `global` 那一行，函数里的赋值会悄悄新建一个局部变量，
外面那个永远是 None——又一个不报错的静默失败。

分辨方法一句话：状态要活过"一轮循环"→ 用二；要活过"一次函数调用"→ 用三。

---

## §4 while True / continue / break / 怎么停（块 5）

    n = 0
    while True:                # 条件永远为真 = 循环永不自己结束
        n = n + 1
        if n % 2 == 0:
            continue           # 跳过本轮剩下的行，直接进下一轮
        print(n)
        if n > 7:
            break              # 立刻跳出整个循环

- `continue`：块 5a"没读到卡"就用它——这一轮没事可干，下一轮。
- `break`：kiosk 主循环里基本用不上，它就该永远跑。
- 测试时怎么停：Ctrl+C。它抛 KeyboardInterrupt、程序退出——这是正常操作，不是事故。

---

## §5 time.monotonic（块 5）

用法只有一个模式：记下起点，之后相减。

    t0 = time.monotonic()
    ...                                # 中间过了一些事
    elapsed = time.monotonic() - t0    # 经过的秒数（float）

为什么不用 time.time()：墙上时钟会被对时改动、甚至倒退，差值会算出负数。
monotonic 的数字本身没有意义，只有差值有意义。

---

## §6 try / except（块 5，也是你第一次真正要写它）

    try:
        risky()                      # 只把"会炸的那几行"放进来
    except Exception as e:
        print("出错了:", e)          # 让错误可见——不打印，你永远不知道它发生过

- `except Exception as e` 接住几乎所有运行时错误，循环得以继续；e 里是错误信息。
- **它接不住 Ctrl+C**——KeyboardInterrupt 被故意设计在 Exception 家族之外，
  所以你的 try/except 不会把程序变成停不下来的僵尸。这是语言设计，不是巧合。
- 包多大范围是个设计决定：包得太大，不知道是哪行炸的；
  包得太小，漏网的异常照样杀掉循环。块 5d 的问题就是要你拿这个决定。
- 你已经见过的对照：echoid_client 里 404 / 非 200 是"服务器回了话"的错误，走 if；
  这里说的是"根本没法继续执行"的错误，走 except。两个不同的失败平面。

---

## §7 subprocess.Popen 对象（块 2 真机阶段）

`subprocess.Popen([...])` 启动进程后**立即返回**一个对象，不等它结束。
这个对象一直记着那个进程：

- `.pid` —— 进程号
- `.poll()` —— 问一下"死了吗"，**不等**。还活着返回 None，死了返回退出码。
- `.wait()` —— **一直等**到它死，然后返回退出码。
- `.terminate()` —— 请它退出（发 SIGTERM）。它多久退、退不退，是另一件事——
  所以 terminate 之后用什么确认它真的退了，就是块 2 真机阶段那道题。

顺带解释你块 2 里那行的 `*BROWSER_FLAGS`：这是列表展开——
`[a, *[b, c], d]` 等于 `[a, b, c, d]`，把 FLAGS 整个摊平进命令列表。

---

## §8 read_passive_target 与 None 惯例（块 4、块 5）

`pn532.read_passive_target(timeout=0.5)`：最多等 0.5 秒。
有卡 → 返回 UID（bytearray）；没卡 → 返回 None。
**None 不是错误，是"现在没人拍卡"的正常答案**——和 lookup_uid 找不到返回 None
是同一个惯例。timeout 本身就在替你"等"，所以主循环不会空转烧满 CPU。
