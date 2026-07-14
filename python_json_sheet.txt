| 我想做什么      | Python 常用表达                                      |
| ---------- | ------------------------------------------------ |
| 使用 JSON 工具 | `import json`                                    |
| 使用文件路径工具   | `from pathlib import Path`                       |
| 指定文件       | `DB_FILE = Path("xxx.json")`                     |
| 判断文件是否存在   | `if not DB_FILE.exists():`                       |
| 读取文件       | `with DB_FILE.open("r", encoding="utf-8") as f:` |
| 写入文件       | `with DB_FILE.open("w", encoding="utf-8") as f:` |
| JSON 文件变字典 | `json.load(f)`                                   |
| 字典写成 JSON  | `json.dump(data, f, indent=2)`                   |
| 字典按 key 查询 | `data.get(uid)`                                  |
| 字典写入一项     | `data[uid] = {...}`                              |
| 定义命令行参数    | `parser.add_argument("uid")`                     |
| 解析命令行参数    | `args = parser.parse_args()`                     |
| 使用参数       | `args.uid`                                       |
| 没找到时返回空    | `return None`                                    |
| 文件直接运行入口   | `if __name__ == "__main__":`                     |
