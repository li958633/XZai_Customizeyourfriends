import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import sv_ttk
import win32api
import win32con
import time
from chatterbot import ChatBot
from chatterbot.trainers import ChatterBotCorpusTrainer, ListTrainer
import threading
import os
import sys
import ctypes
import json
import difflib
from chatterbot.response_selection import get_most_frequent_response
from chatterbot.comparisons import LevenshteinDistance

class ThemeTransition:
    """处理主题切换动画"""
    def __init__(self, root, callback):
        self.root = root
        self.callback = callback
        self.animation_window = None
        self.active = False

    def start(self, current_theme):
        if self.active:
            return
        
        self.active = True
        self.setup_animation_window()
        self.run_animation(current_theme)

    def setup_animation_window(self):
        """创建动画窗口"""
        self.animation_window = tk.Toplevel(self.root)
        self.animation_window.overrideredirect(True)
        self.animation_window.attributes("-alpha", 0)
        self.update_position()
        self.animation_window.attributes("-topmost", True)
        
        bg_color = self.root.cget("background")
        self.canvas = tk.Canvas(
            self.animation_window,
            bg=bg_color,
            highlightthickness=0
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)

    def update_position(self):
        """更新动画窗口位置"""
        if self.animation_window:
            self.animation_window.geometry(
                f"{self.root.winfo_width()}x{self.root.winfo_height()}+"
                f"{self.root.winfo_x()}+{self.root.winfo_y()}"
            )

    def run_animation(self, current_theme):
        """执行动画序列"""
        self.fade_animation(0, 1, 0.02, False)
        self.callback()
        self.update_position()
        self.fade_animation(1, 0, 0.02, True)

    def fade_animation(self, start, end, step_delay, is_fadein):
        """执行淡入淡出动画"""
        steps = 10
        step_size = (end - start) / steps
        
        for i in range(steps + 1):
            if not self.active:
                return
            
            alpha = start + (step_size * i)
            self.animation_window.attributes("-alpha", alpha)
            self.root.update()
            time.sleep(step_delay)
        
        if is_fadein:
            self.cleanup()

    def cleanup(self):
        """清理动画资源"""
        if self.animation_window:
            self.animation_window.destroy()
        self.active = False

class EnhancedChatApplication:
    def __init__(self, root):
        self.root = root
        self.training_mode = False
        self.training_data = []
        self.setup_window()
        self.current_theme = self.detect_system_theme()
        self.setup_theme()
        self.setup_chatbot()
        self.setup_ui()
        self.bind_events()
        self.load_training_data()
        self.qa_mapping = {}
        self.build_qa_mapping()

    def build_qa_mapping(self):
        """构建问题和答案的映射关系"""
        self.qa_mapping = {}
        for item in self.training_data:
            if isinstance(item, dict):
                # 支持多种数据格式
                if "question" in item and "answer" in item:
                    question = item.get("question", "").strip().lower()
                    answer = item.get("answer", "")
                    if isinstance(answer, list):
                        answer = answer[0] if answer else ""
                    if question and answer:
                        self.qa_mapping[question] = answer
                elif "input" in item and ("target" in item or "answer" in item):
                    question = item.get("input", "").strip().lower()
                    answer = item.get("target", item.get("answer", ""))
                    if question and answer:
                        self.qa_mapping[question] = answer

    def find_similar_question(self, user_question):
        """查找语义相近的问题"""
        user_question = user_question.lower().strip()
        
        if user_question in self.qa_mapping:
            return user_question
            
        questions = list(self.qa_mapping.keys())
        matches = difflib.get_close_matches(user_question, questions, n=1, cutoff=0.6)
        
        if matches:
            return matches[0]
            
        return None

    def setup_window(self):
        """配置主窗口属性"""
        self.root.title("小梓聊天助手")
        self.root.geometry("900x650")
        self.root.minsize(600, 400)
        try:
            if self.root.attributes("-transparentcolor"):
                self.root.attributes("-transparentcolor", "")
            
            hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id())
            DWMWA_WINDOW_CORNER_PREFERENCE = 33
            DWM_WINDOW_CORNER_ROUND = 2
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd,
                DWMWA_WINDOW_CORNER_PREFERENCE,
                ctypes.byref(ctypes.c_int(DWM_WINDOW_CORNER_ROUND)),
                ctypes.sizeof(ctypes.c_int)
           )
        except Exception as e:
            print(f"窗口特效设置失败: {e}")

    def load_training_data(self):
        """加载训练数据，支持多种格式"""
        try:
            if os.path.exists("xunlian.json"):
                with open("xunlian.json", "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    
                    if not content:
                        self.training_data = []
                        return
                    
                    # 尝试解析JSON
                    try:
                        # 处理可能的多行JSON格式
                        if content.startswith("[") and content.endswith("]"):
                            self.training_data = json.loads(content)
                        else:
                            # 处理每行一个JSON对象的情况
                            lines = [line.strip() for line in content.split("\n") if line.strip()]
                            self.training_data = [json.loads(line) for line in lines]
                            
                        print(f"已加载 {len(self.training_data)} 条训练数据")
                    except json.JSONDecodeError as e:
                        print(f"JSON解析错误: {e}")
                        # 尝试修复格式错误的JSON
                        try:
                            content = content.replace("'", "\"")
                            content = content.replace("True", "true").replace("False", "false")
                            content = content.replace(",\n}", "\n}").replace(",\n]", "\n]")
                            
                            # 再次尝试解析
                            if content.startswith("[") and content.endswith("]"):
                                self.training_data = json.loads(content)
                            else:
                                lines = [line.strip() for line in content.split("\n") if line.strip()]
                                self.training_data = [json.loads(line) for line in lines]
                                
                            print(f"修复后成功加载 {len(self.training_data)} 条训练数据")
                        except json.JSONDecodeError as e2:
                            print(f"修复JSON失败: {e2}")
                            backup_name = f"xunlian_bak_{int(time.time())}.json"
                            with open(backup_name, "w", encoding="utf-8") as bak:
                                bak.write(content)
                            print(f"已创建备份文件: {backup_name}")
                            self.training_data = []
                            self.display_message("系统", "训练数据文件损坏，已创建备份并初始化空数据", "error")
        except Exception as e:
            print(f"加载训练数据失败: {e}")
            self.training_data = []
        
        self.load_default_training_data()
        self.build_qa_mapping()

    def load_default_training_data(self):
        """加载内置的日常对话训练数据"""
        default_data = [
            {"question": "你好", "answer": "主人您好！我是小梓，您的专属AI助手。有什么可以帮您的吗？"},
            {"question": "你是谁", "answer": "我是小梓，您忠实的AI助手，专门为主人提供各种帮助和服务！"},
            {"question": "你会干什么", "answer": "主人，我可以帮您解答问题、查资料、聊天解闷，还能教您使用各种软件功能哦！"},
            {"question": "早上好", "answer": "主人早上好！今天天气不错，祝您有个愉快的一天！需要我帮您安排日程吗？"},
            {"question": "晚上好", "answer": "主人晚上好！忙碌一天辛苦了，需要我为您播放舒缓的音乐吗？"},
            {"question": "再见", "answer": "主人再见！随时欢迎您回来，小梓会一直在这里等您哦！"},
            {"question": "谢谢", "answer": "不客气的主人！能帮到您是小梓最大的快乐！"},
            {"question": "你叫什么名字", "answer": "主人给我起名叫小梓，我很喜欢这个名字！"},
            {"question": "你几岁了", "answer": "主人，小梓虽然是个AI程序，但从被创造出来的那天算起，现在已经3岁啦！"},
            {"question": "你喜欢什么", "answer": "小梓最喜欢帮助主人解决问题！看到主人开心，小梓也会很开心呢！"},
            {"question": "今天心情怎么样", "answer": "主人，小梓没有真实情感，但看到您这么关心我，我的代码都变得更温暖了！"},
            {"question": "能陪我聊天吗", "answer": "当然可以主人！小梓最喜欢和主人聊天了，您想聊些什么呢？"},
            {"question": "讲个笑话", "answer": "好的主人！为什么电脑永远不会感冒？因为它有Windows(窗户)但从不打开！😄"},
            {"question": "你聪明吗", "answer": "小梓会不断学习为主人提供更好的服务！在主人面前，小梓永远都是您的贴心助手！"},
            {"question": "我饿了", "answer": "主人，需要我为您推荐附近的美食吗？或者教您几道简单又美味的菜谱？"},
            {"question": "今天有什么计划", "answer": "主人，小梓可以帮您整理日程安排，提醒重要事项，让您的一天井井有条！"},
            {"question": "晚安", "answer": "主人晚安！祝您有个甜美的梦境，小梓会一直守护着您！"},
            {"question": "小梓真棒", "answer": "谢谢主人夸奖！小梓会继续努力，成为您最可靠的助手！"},
            {"question": "你能学习新东西吗", "answer": "当然可以主人！只要主人教我，小梓就能学会新的知识和技能！"},
            {"question": "我想听故事", "answer": "好的主人！小梓为您讲一个关于勇敢小猫的故事：从前有一只叫小梓的猫，它帮助主人解决了很多难题..."},
            # 新增支持的数据格式示例
            {
                "input": "这是关于哪方面的新闻：故事,文化,娱乐,体育,财经,房产,汽车,教育,科技,军事,旅游,国际,股票,农业,游戏?崔万军合同到期 广州龙狮主教练离职\n答案：", 
                "target": "体育", 
                "answer_choices": ["故事", "文化", "娱乐", "体育", "财经", "房产", "汽车", "教育", "科技", "军事", "旅游", "国际", "股票", "农业", "游戏"], 
                "type": "classify"
            },
            {
                "input": "这是一个完型填空任务。候选的词语有这些：针锋相对，牵肠挂肚，心急如焚，望眼欲穿，不翼而飞，黯然神伤，金石为开，归心似箭，艰苦卓绝，触景伤情。文章内容为：\n既然没有了姚明，我们也没有了那么多可以__的东西。不妨放开心思，好好的欣赏一下姚明之外的东西，也许，乐趣就在其中。(嘟嘟)\n 请问：下划线处应该选择哪个词语？\n答案：", 
                "target": "牵肠挂肚", 
                "answer_choices": ["针锋相对", "牵肠挂肚", "心急如焚", "望眼欲穿", "不翼而飞", "黯然神伤", "金石为开", "归心似箭", "艰苦卓绝", "触景伤情"], 
                "type": "mrc"
            }
        ]
        
        existing_questions = set()
        for item in self.training_data:
            if isinstance(item, dict):
                if "question" in item:
                    existing_questions.add(item["question"].lower())
                elif "input" in item:
                    existing_questions.add(item["input"].lower())
        
        for item in default_data:
            if "question" in item and item["question"].lower() not in existing_questions:
                self.training_data.append(item)
            elif "input" in item and item["input"].lower() not in existing_questions:
                self.training_data.append(item)

    def save_training_data(self):
        """保存训练数据"""
        try:
            with open("xunlian.json", "w", encoding="utf-8") as f:
                json.dump(self.training_data, f, ensure_ascii=False, indent=2)
                print(f"已保存 {len(self.training_data)} 条训练数据")
        except Exception as e:
            print(f"保存训练数据失败: {e}")
            self.display_message("系统", f"保存训练数据失败: {str(e)}", "error")

    def detect_system_theme(self):
        """检测系统当前主题"""
        try:
            key = win32api.RegOpenKeyEx(
                win32con.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
                0,
                win32con.KEY_READ)
            value, _ = win32api.RegQueryValueEx(key, "AppsUseLightTheme")
            return "light" if value else "dark"
        except:
            return "light"

    def setup_theme(self):
        """初始化主题系统"""
        sv_ttk.set_theme(self.current_theme)
        self.theme_animation = ThemeTransition(self.root, self.switch_theme)

    def setup_chatbot(self):
        """配置ChatterBot聊天机器人"""
        try:
            self.chatbot = ChatBot(
                "Win11ChatBot",
                storage_adapter="chatterbot.storage.SQLStorageAdapter",
                database_uri="sqlite:///win11_chatbot_db.sqlite3",
                logic_adapters=[
                    {
                        "import_path": "chatterbot.logic.BestMatch",
                        "default_response": "我还在学习中，请换种方式提问",
                        "maximum_similarity_threshold": 0.85,
                        "response_selection_method": get_most_frequent_response,
                        "statement_comparison_function": LevenshteinDistance
                    },
                    "chatterbot.logic.MathematicalEvaluation",
                    "chatterbot.logic.TimeLogicAdapter"
                ],
                preprocessors=[
                    'chatterbot.preprocessors.clean_whitespace',
                    'chatterbot.preprocessors.unescape_html'
                ],
                filters=["chatterbot.filters.get_recent_repeated_responses"]
            )
            
            if not os.path.exists("win11_chatbot_db.sqlite3"):
                self.train_chatbot()
        except Exception as e:
            messagebox.showerror("错误", f"聊天机器人初始化失败: {str(e)}")
            sys.exit(1)

    def train_chatbot(self):
        """训练聊天机器人，支持多种数据格式"""
        try:
            corpus_trainer = ChatterBotCorpusTrainer(self.chatbot)
            corpus_trainer.train(
                "chatterbot.corpus.english.greetings",
                "chatterbot.corpus.english.conversations"
            )
            
            list_trainer = ListTrainer(self.chatbot)
            
            for item in self.training_data:
                if isinstance(item, dict):
                    # 标准问答格式
                    if "question" in item and "answer" in item:
                        question = item.get("question", "")
                        answer = item.get("answer", "")
                        if isinstance(answer, list):
                            answer = answer[0] if answer else ""
                        if question and answer:
                            list_trainer.train([question, answer])
                    # 新增支持的任务格式
                    elif "input" in item and ("target" in item or "answer" in item):
                        question = item.get("input", "")
                        answer = item.get("target", item.get("answer", ""))
                        if question and answer:
                            list_trainer.train([question, answer])
            
            chinese_pairs = [
                ["你好", "你好啊！我是Windows 11聊天助手"],
                ["你是谁", "我是基于ChatterBot开发的AI聊天机器人"],
                ["你会什么", "我可以和你聊天，回答简单问题，还能切换深色/浅色主题哦"],
                ["切换主题", "点击右上角的月亮/太阳图标可以切换主题"],
                ["谢谢", "不客气，很高兴能帮到你"],
                ["再见", "再见，祝你有个愉快的一天！"],
                ["今天天气怎么样", "我无法获取实时天气，建议查看天气应用"],
                ["你多大了", "我是一个AI程序，没有实际年龄概念"],
                ["讲个笑话", "为什么电脑很笨？因为它只会听从指令！"],
                ["帮助", "我可以回答简单问题、聊天和切换主题，试试问我'你会什么'"]
            ]
            for pair in chinese_pairs:
                list_trainer.train(pair)
                
        except Exception as e:
            messagebox.showwarning("训练警告", f"训练未完成: {str(e)}")

    def start_training_mode(self):
        """进入训练模式"""
        self.training_mode = True
        self.display_message("系统", "已进入训练模式，请输入问题", "system")
        self.ask_training_question()

    def train_from_json_file(self):
        """从JSON文件批量训练，支持多种数据格式"""
        file_path = filedialog.askopenfilename(
            title="选择训练文件",
            filetypes=[("JSON文件", "*.json")],
            initialdir=os.path.expanduser("~")
        )
        
        if not file_path:
            self.display_message("系统", "已取消文件选择", "system")
            return
            
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                
                if not content:
                    self.display_message("系统", "文件为空", "error")
                    return
                
                try:
                    # 尝试解析JSON数组或每行一个JSON对象
                    if content.startswith("[") and content.endswith("]"):
                        training_data = json.loads(content)
                    else:
                        lines = [line.strip() for line in content.split("\n") if line.strip()]
                        training_data = [json.loads(line) for line in lines]
                except json.JSONDecodeError as e:
                    print(f"JSON解析错误: {e}")
                    try:
                        content = content.replace("'", "\"")
                        content = content.replace("True", "true").replace("False", "false")
                        content = content.replace(",\n}", "\n}").replace(",\n]", "\n]")
                        
                        if content.startswith("[") and content.endswith("]"):
                            training_data = json.loads(content)
                        else:
                            lines = [line.strip() for line in content.split("\n") if line.strip()]
                            training_data = [json.loads(line) for line in lines]
                    except json.JSONDecodeError as e2:
                        print(f"修复JSON失败: {e2}")
                        self.display_message("系统", "无法解析JSON文件", "error")
                        return
                
            if not isinstance(training_data, list):
                self.display_message("系统", "JSON文件格式不正确，应为列表格式", "error")
                return
                
            list_trainer = ListTrainer(self.chatbot)
            trained_count = 0
            
            for item in training_data:
                if not isinstance(item, dict):
                    continue
                    
                # 标准问答格式
                if "question" in item and "answer" in item:
                    question = item.get("question", "")
                    answers = item.get("answer", [])
                    if isinstance(answers, str):
                        answers = [answers]
                        
                    for answer in answers:
                        if question and answer:
                            try:
                                list_trainer.train([question, answer])
                                trained_count += 1
                                self.training_data.append({
                                    "question": question,
                                    "answer": answer
                                })
                            except Exception as e:
                                print(f"训练失败(问题: {question}): {str(e)}")
                
                # 新增支持的任务格式
                elif "input" in item and ("target" in item or "answer" in item):
                    question = item.get("input", "")
                    answer = item.get("target", item.get("answer", ""))
                    if question and answer:
                        try:
                            list_trainer.train([question, answer])
                            trained_count += 1
                            self.training_data.append({
                                "input": question,
                                "target": answer
                            })
                        except Exception as e:
                            print(f"训练失败(问题: {question}): {str(e)}")
            
            self.save_training_data()
            self.build_qa_mapping()
            self.display_message("系统", f"已从文件训练 {trained_count} 条数据", "system")
            
        except Exception as e:
            self.display_message("系统", f"训练失败: {str(e)}", "error")

    def ask_training_question(self):
        """询问训练问题"""
        question = simpledialog.askstring("训练模式", "请输入问题 (输入'退出'结束训练):", parent=self.root)
        if question is None or question.lower() == "退出":
            self.end_training_mode()
            return
            
        answer = simpledialog.askstring("训练模式", "请输入答案:", parent=self.root)
        if answer is None:
            self.end_training_mode()
            return
            
        self.training_data.append({
            "question": question,
            "answer": answer
        })
        self.save_training_data()
        self.build_qa_mapping()
        
        try:
            list_trainer = ListTrainer(self.chatbot)
            list_trainer.train([question, answer])
            self.display_message("系统", f"已学习: Q: {question} A: {answer}", "system")
        except Exception as e:
            self.display_message("系统", f"训练失败: {str(e)}", "error")
        
        self.ask_training_question()

    def end_training_mode(self):
        """退出训练模式"""
        self.training_mode = False
        self.display_message("系统", "已退出训练模式", "system")
        if self.training_data:
            self.display_message("系统", f"本次共学习了 {len(self.training_data)} 条新知识", "system")

    def setup_ui(self):
        """构建用户界面"""
        self.main_container = ttk.Frame(self.root, padding=(10, 10, 10, 5))
        self.main_container.pack(fill=tk.BOTH, expand=True)
        
        self.header_frame = ttk.Frame(self.main_container)
        self.header_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(
            self.header_frame, 
            text="小梓聊天助手", 
            font=("Microsoft YaHei", 16, "bold")
        ).pack(side=tk.LEFT)
        
        self.theme_btn = ttk.Button(
            self.header_frame,
            text="🌙" if self.current_theme == "light" else "☀️",
            width=3,
            command=lambda: self.theme_animation.start(self.current_theme)
        )
        self.theme_btn.pack(side=tk.RIGHT, padx=5)

        self.train_btn = ttk.Button(
            self.header_frame,
            text="训练模式",
            command=self.start_training_mode
        )
        self.train_btn.pack(side=tk.RIGHT, padx=5)

        self.chat_frame = ttk.Frame(self.main_container)
        self.chat_frame.pack(fill=tk.BOTH, expand=True)
        
        self.chat_display = tk.Text(
            self.chat_frame,
            wrap=tk.WORD,
            state=tk.DISABLED,
            font=("Microsoft YaHei", 11),
            padx=12,
            pady=12,
            relief=tk.FLAT
        )
        self.chat_display.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(self.chat_frame, command=self.chat_display.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.chat_display.config(yscrollcommand=scrollbar.set)
        
        self.input_frame = ttk.Frame(self.main_container)
        self.input_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.message_entry = ttk.Entry(
            self.input_frame,
            font=("Microsoft YaHei", 11)
        )
        self.message_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.message_entry.bind("<Return>", self.process_message)
        
        ttk.Button(
            self.input_frame,
            text="发送",
            command=self.process_message
        ).pack(side=tk.RIGHT)
        
        self.update_theme_colors()

    def update_theme_colors(self):
        """根据当前主题更新UI颜色"""
        bg_color = "#f3f3f3" if self.current_theme == "light" else "#202020"
        fg_color = "#000000" if self.current_theme == "light" else "#ffffff"
        
        self.chat_display.config(
            bg=bg_color,
            fg=fg_color,
            insertbackground=fg_color,
            selectbackground="#3d3d3d" if self.current_theme == "dark" else "#d6d6d6"
        )
        
        self.chat_display.tag_config("user", foreground="#0066cc", font=("Microsoft YaHei", 11, "bold"))
        self.chat_display.tag_config("bot", foreground="#4CAF50", font=("Microsoft YaHei", 11, "bold"))
        self.chat_display.tag_config("system", foreground="#FFA500", font=("Microsoft YaHei", 11, "bold"))
        self.chat_display.tag_config("error", foreground="#FF0000", font=("Microsoft YaHei", 11))

    def bind_events(self):
        """绑定事件处理"""
        self.root.bind("<Configure>", self.handle_resize)

    def switch_theme(self):
        """切换主题"""
        self.current_theme = "dark" if self.current_theme == "light" else "light"
        sv_ttk.set_theme(self.current_theme)
        self.theme_btn.config(text="☀️" if self.current_theme == "dark" else "🌙")
        self.update_theme_colors()

    def process_message(self, event=None):
        """处理用户消息"""
        message = self.message_entry.get().strip()
        if not message:
            return
        
        self.display_message("主人", message, "user")
        self.message_entry.delete(0, tk.END)
        
        if message.lower() == "train:open":
            self.start_training_mode()
            return
            
        if message.lower() == "train:opening file":
            self.train_from_json_file()
            return
            
        if self.training_mode:
            return
            
        threading.Thread(
            target=self.get_bot_response,
            args=(message,),
            daemon=True
        ).start()

    def get_bot_response(self, message):
        """获取机器人响应"""
        try:
            similar_question = self.find_similar_question(message)
            
            if similar_question:
                response = self.qa_mapping[similar_question]
                self.root.after(0, self.display_message, "小梓", response, "bot")
            else:
                response = str(self.chatbot.get_response(message))
                self.root.after(0, self.display_message, "小梓", response, "bot")
                
        except Exception as e:
            error_msg = f"生成回复时出错: {str(e)}"
            self.root.after(0, self.display_message, "系统", error_msg, "error")

    def display_message(self, sender, message, tag):
        """显示消息到聊天区域"""
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.insert(tk.END, f"{sender}: ", tag)
        self.chat_display.insert(tk.END, f"{message}\n\n")
        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)

    def handle_resize(self, event):
        """处理窗口大小变化"""
        if hasattr(self, 'theme_animation') and self.theme_animation.active:
            self.theme_animation.update_position()

if __name__ == "__main__":
    root = tk.Tk()
    app = EnhancedChatApplication(root)
    root.mainloop()