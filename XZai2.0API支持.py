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
import requests
from datetime import datetime
from chatterbot.response_selection import get_most_frequent_response
from chatterbot.comparisons import LevenshteinDistance
from PIL import Image, ImageTk, ImageSequence
from ttkbootstrap import Style
from ttkbootstrap.constants import *

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

class LoadingAnimation:
    """加载动画 - Windows 11风格"""
    def __init__(self, parent):
        self.parent = parent
        self.loading_window = None
        self.active = False
        self.progress_value = 0
        self.progress_bar = None
        
        # Windows 11风格的动画参数
        self.dot_count = 0
        self.max_dots = 3
        self.dot_animation_speed = 300  # 毫秒

    def start(self, message="请稍等！小梓正在暴打你的API！因为她工作太慢了！！"):
        if self.active:
            return
            
        self.active = True
        self.setup_loading_window(message)
        self.animate_dots()

    def setup_loading_window(self, message):
        """创建Windows 11风格的加载窗口"""
        self.loading_window = tk.Toplevel(self.parent)
        self.loading_window.overrideredirect(True)
        self.loading_window.attributes("-alpha", 0.95)
        self.loading_window.attributes("-topmost", True)
        self.loading_window.grab_set()
        
        # 设置窗口圆角
        try:
            hwnd = ctypes.windll.user32.GetParent(self.loading_window.winfo_id())
            DWMWA_WINDOW_CORNER_PREFERENCE = 33
            DWM_WINDOW_CORNER_ROUND = 2
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd,
                DWMWA_WINDOW_CORNER_PREFERENCE,
                ctypes.byref(ctypes.c_int(DWM_WINDOW_CORNER_ROUND)),
                ctypes.sizeof(ctypes.c_int)
            )
        except:
            pass
        
        # 居中窗口
        width = 350
        height = 120
        x = self.parent.winfo_x() + (self.parent.winfo_width() - width) // 2
        y = self.parent.winfo_y() + (self.parent.winfo_height() - height) // 2
        self.loading_window.geometry(f"{width}x{height}+{x}+{y}")
        
        # 创建内容 - Windows 11风格
        style = ttk.Style()
        style.configure("Win11.TFrame", background="#f3f3f3", borderwidth=0)
        style.configure("Win11.TLabel", background="#f3f3f3", font=("Segoe UI", 10))
        
        container = ttk.Frame(self.loading_window, style="Win11.TFrame")
        container.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
        
        # 标题
        ttk.Label(
            container,
            text="正在处理",
            style="Win11.TLabel",
            font=("Segoe UI", 11, "bold")
        ).pack(pady=(10, 5))
        
        # 消息文本
        self.message_label = ttk.Label(
            container,
            text=message,
            style="Win11.TLabel"
        )
        self.message_label.pack(pady=(0, 10))
        
        # 进度指示器 - Windows 11风格
        self.progress_frame = ttk.Frame(container, style="Win11.TFrame")
        self.progress_frame.pack(fill=tk.X, padx=20, pady=(0, 10))
        
        # 进度条
        style.configure("Win11.Horizontal.TProgressbar", 
                       troughcolor="#e5e5e5",
                       background="#0078d7",
                       thickness=10,
                       bordercolor="#e5e5e5",
                       lightcolor="#0078d7",
                       darkcolor="#005a9e")
        
        self.progress_bar = ttk.Progressbar(
            self.progress_frame,
            orient="horizontal",
            mode="indeterminate",
            style="Win11.Horizontal.TProgressbar",
            length=300
        )
        self.progress_bar.pack(fill=tk.X)
        self.progress_bar.start(10)
        
        # 添加窗口阴影效果
        try:
            self.loading_window.attributes("-transparentcolor", "#f3f3f3")
            self.loading_window.update()
        except:
            pass

    def animate_dots(self):
        """Windows 11风格的点点点动画"""
        if not self.active:
            return
            
        self.dot_count = (self.dot_count + 1) % (self.max_dots + 1)
        dots = "." * self.dot_count
        self.message_label.config(text=self.message_label.cget("text").split("...")[0] + dots)
        
        self.loading_window.after(self.dot_animation_speed, self.animate_dots)

    def stop(self):
        """停止动画"""
        self.active = False
        if self.progress_bar:
            self.progress_bar.stop()
        if self.loading_window:
            self.loading_window.grab_release()
            self.loading_window.destroy()
        self.loading_window = None

class SidebarAnimation:
    """侧边栏展开/收起动画"""
    def __init__(self, parent, sidebar, chat_frame, min_width=100, max_width=400):
        self.parent = parent
        self.sidebar = sidebar
        self.chat_frame = chat_frame
        self.min_width = min_width
        self.max_width = max_width
        self.current_width = max_width
        self.target_width = max_width
        self.animating = False
        self.sidebar.config(width=self.max_width)
        
    def toggle(self):
        """切换展开/收起状态"""
        self.target_width = self.min_width if self.current_width == self.max_width else self.max_width
        if not self.animating:
            self.animate()
            
    def animate(self):
        """执行动画"""
        step = 100
        if self.current_width < self.target_width:
            self.current_width = min(self.current_width + step, self.target_width)
        elif self.current_width > self.target_width:
            self.current_width = max(self.current_width - step, self.target_width)
            
        self.sidebar.config(width=self.current_width)
        self.chat_frame.pack_configure(padx=(30 if self.current_width > self.min_width else 0, 0))
        
        if self.current_width != self.target_width:
            self.animating = True
            self.parent.after(50, self.animate)
        else:
            self.animating = False

class EnhancedChatApplication:
    def __init__(self, root):
        self.root = root
        self.training_mode = False
        self.training_data = []
        self.load_config()  # 首先加载配置
        self.current_theme = self.detect_system_theme()
        self.setup_window()
        self.setup_theme()
        self.setup_chatbot()
        # 确保在load_config之后初始化这些属性
        self.qa_mapping = {}
        self.conversation_history = self.config.get("history", [])
        self.current_conversation = None
        self.loading_animation = LoadingAnimation(self.root)
        self.setup_ui()
        self.bind_events()
        self.load_training_data()
        self.build_qa_mapping()
        self.search_results = []

    def load_config(self):
        """加载配置"""
        self.config = {
            "api_settings": {
                "openai": {"api_key": "", "base_url": "https://api.openai.com/v1"},
                "deepseek": {"api_key": "", "base_url": "https://api.deepseek.com/v1"},
                "kimi": {"api_key": "", "base_url": "https://api.moonshot.cn/v1"},
                "claude": {"api_key": "", "base_url": "https://api.anthropic.com/v1"},
                "gemini": {"api_key": "", "base_url": "https://generativelanguage.googleapis.com/v1beta"},
                "active_model": "local"
            },
            "history": [],
            "theme": "system",  # system, light, dark
            "sidebar_width": 400  # 保存侧边栏宽度
        }
        
        try:
            if os.path.exists("config.json"):
                with open("config.json", "r", encoding="utf-8") as f:
                    loaded_config = json.load(f)
                    # 合并配置，保留新增的默认值
                    for key in loaded_config:
                        if key in self.config:
                            if isinstance(self.config[key], dict):
                                self.config[key].update(loaded_config[key])
                            else:
                                self.config[key] = loaded_config[key]
        except Exception as e:
            print(f"加载配置失败: {e}")

    def save_config(self):
        """保存配置"""
        try:
            # 保存当前对话历史到配置
            self.config["history"] = self.conversation_history
            if hasattr(self, 'sidebar_animation'):
                self.config["sidebar_width"] = self.sidebar_animation.current_width
            with open("config.json", "w", encoding="utf-8") as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存配置失败: {e}")

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
                # 新增支持的任务格式
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
        self.root.geometry("1200x900")
        self.root.minsize(800, 600)
        
        # 设置Win11样式
        try:
            # 移除透明色属性
            if self.root.attributes("-transparentcolor"):
                self.root.attributes("-transparentcolor", "")
            
            # 设置窗口圆角
            hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id())
            DWMWA_WINDOW_CORNER_PREFERENCE = 33
            DWM_WINDOW_CORNER_ROUND = 2
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd,
                DWMWA_WINDOW_CORNER_PREFERENCE,
                ctypes.byref(ctypes.c_int(DWM_WINDOW_CORNER_ROUND)),
                ctypes.sizeof(ctypes.c_int)
            )
            
            # 设置窗口阴影
            DWMWA_USE_IMMERSIVE_DARK_MODE = 20
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd,
                DWMWA_USE_IMMERSIVE_DARK_MODE,
                ctypes.byref(ctypes.c_int(1)),
                ctypes.sizeof(ctypes.c_int)
            )
            
            # 设置窗口背景为亚克力效果
            DWMWA_SYSTEMBACKDROP_TYPE = 38
            DWM_SYSTEMBACKDROP_TYPE_ACRYLIC = 3
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd,
                DWMWA_SYSTEMBACKDROP_TYPE,
                ctypes.byref(ctypes.c_int(DWM_SYSTEMBACKDROP_TYPE_ACRYLIC)),
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
        theme = self.config.get("theme", "system")
        if theme == "system":
            sv_ttk.set_theme(self.current_theme)
        else:
            sv_ttk.set_theme(theme)
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
        
        # 标题栏 - Win11风格
        self.header_frame = ttk.Frame(self.main_container, style="Card.TFrame")
        self.header_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(
            self.header_frame, 
            text="小梓聊天助手", 
            font=("Microsoft YaHei", 16, "bold"),
            style="Title.TLabel"
        ).pack(side=tk.LEFT, padx=10)
        
        # 主题选择菜单按钮
        self.theme_menu_btn = ttk.Menubutton(
            self.header_frame,
            text="🎨 主题",
            style="Accent.TMenubutton"
        )
        self.theme_menu_btn.pack(side=tk.RIGHT, padx=5)
        
        theme_menu = tk.Menu(self.theme_menu_btn, tearoff=0)
        theme_menu.add_command(
            label="系统默认",
            command=lambda: self.set_custom_theme("system")
        )
        theme_menu.add_command(
            label="浅色",
            command=lambda: self.set_custom_theme("light")
        )
        theme_menu.add_command(
            label="深色",
            command=lambda: self.set_custom_theme("dark")
        )
        self.theme_menu_btn["menu"] = theme_menu
        
        # API设置按钮
        self.api_btn = ttk.Button(
            self.header_frame,
            text="API设置",
            command=self.show_api_settings,
            style="Accent.TButton"
        )
        self.api_btn.pack(side=tk.RIGHT, padx=5)

        # 历史记录按钮
        self.history_btn = ttk.Button(
            self.header_frame,
            text="历史记录",
            command=self.show_history_dialog,
            style="Accent.TButton"
        )
        self.history_btn.pack(side=tk.RIGHT, padx=5)

        # 训练模式按钮
        self.train_btn = ttk.Button(
            self.header_frame,
            text="训练模式",
            command=self.start_training_mode,
            style="Accent.TButton"
        )
        self.train_btn.pack(side=tk.RIGHT, padx=5)
        
        # 新建对话按钮
        self.new_chat_btn = ttk.Button(
            self.header_frame,
            text="新建对话",
            command=self.new_conversation,
            style="Accent.TButton"
        )
        self.new_chat_btn.pack(side=tk.RIGHT, padx=5)

        # 主聊天区域
        self.chat_container = ttk.Frame(self.main_container, style="Card.TFrame")
        self.chat_container.pack(fill=tk.BOTH, expand=True)

        # 历史记录面板 - Win11样式
        self.history_frame = ttk.Frame(
            self.chat_container, 
            width=self.config.get("sidebar_width", 300),
            style="Card.TFrame"
        )
        self.history_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))
        self.history_frame.pack_propagate(False)

        # 侧边栏标题和按钮
        sidebar_header = ttk.Frame(self.history_frame)
        sidebar_header.pack(fill=tk.X, pady=(0, 5), padx=5)
        
        self.history_label = ttk.Label(
            sidebar_header, 
            text="历史对话", 
            font=("SIMHEI", 10, "bold"),
            style="Title.TLabel"
        )
        self.history_label.pack(side=tk.LEFT, padx=5)

        # 搜索按钮
        self.search_btn = ttk.Button(
            sidebar_header,
            text="🔍",
            width=2,
            command=self.toggle_search,
            style="Accent.TButton"
        )
        self.search_btn.pack(side=tk.RIGHT, padx=8)

        # 展开/收起按钮
        self.toggle_btn = ttk.Button(
            sidebar_header,
            text="◀",
            width=2,
            command=self.toggle_sidebar,
            style="Accent.TButton"
        )
        self.toggle_btn.pack(side=tk.RIGHT, padx=5)

        # 搜索框
        self.search_frame = ttk.Frame(self.history_frame)
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(
            self.search_frame,
            textvariable=self.search_var,
            font=("Microsoft YaHei", 9)
        )
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.search_entry.bind("<Return>", self.search_history)
        
        ttk.Button(
            self.search_frame,
            text="搜索",
            command=self.search_history,
            style="Accent.TButton"
        ).pack(side=tk.RIGHT)
        self.search_frame.pack(fill=tk.X, pady=(0, 5), padx=5)
        self.search_frame.pack_forget()  # 默认隐藏

        # 使用Treeview代替Listbox以获得更好的Win11样式
        self.history_tree = ttk.Treeview(
            self.history_frame,
            columns=("title", "time"),
            show="headings",
            selectmode="browse",
            style="Treeview"
        )
        self.history_tree.heading("title", text="标题")
        self.history_tree.heading("time", text="时间")
        self.history_tree.column("title", width=120)
        self.history_tree.column("time", width=60)
        
        scrollbar = ttk.Scrollbar(
            self.history_frame,
            orient="vertical",
            command=self.history_tree.yview
        )
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.history_tree.configure(yscrollcommand=scrollbar.set)
        self.history_tree.pack(fill=tk.BOTH, expand=True, padx=5)
        self.history_tree.bind("<<TreeviewSelect>>", self.on_history_select)

        self.clear_history_btn = ttk.Button(
            self.history_frame,
            text="清空历史",
            command=self.clear_history,
            style="Accent.TButton"
        )
        self.clear_history_btn.pack(fill=tk.X, pady=(5, 0), padx=5)

        # 聊天显示区域
        self.chat_frame = ttk.Frame(self.chat_container, style="Card.TFrame")
        self.chat_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        self.chat_display = tk.Text(
            self.chat_frame,
            wrap=tk.WORD,
            state=tk.DISABLED,
            font=("SIMHEI", 11),
            padx=12,
            pady=12,
            relief=tk.FLAT
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(self.chat_frame, command=self.chat_display.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.chat_display.config(yscrollcommand=scrollbar.set)
        
        # 输入区域
        self.input_frame = ttk.Frame(self.main_container, style="Card.TFrame")
        self.input_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.message_entry = ttk.Entry(
            self.input_frame,
            font=("Microsoft YaHei", 11)
        )
        self.message_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 5), pady=10)
        self.message_entry.bind("<Return>", self.process_message)
        
        ttk.Button(
            self.input_frame,
            text="发送",
            command=self.process_message,
            style="Accent.TButton"
        ).pack(side=tk.RIGHT, padx=5, pady=5)
        
        # 初始化侧边栏动画
        self.sidebar_animation = SidebarAnimation(
            self.root,
            self.history_frame,
            self.chat_frame,
            min_width=50,
            max_width=self.config.get("sidebar_width", 300)
        )
        
        self.update_theme_colors()
        self.update_history_list()
        
        # 应用自定义样式
        self.apply_custom_styles()

    def apply_custom_styles(self):
        """应用自定义样式"""
        style = ttk.Style()
        
        # 卡片样式
        style.configure("Card.TFrame", borderwidth=0, relief="solid", padding=0)
        
        # 标题样式
        style.configure("Title.TLabel", font=("Microsoft YaHei", 10, "bold"))
        
        # 强调按钮样式
        style.configure("Accent.TButton", font=("Microsoft YaHei", 9))
        style.map("Accent.TButton",
            foreground=[("active", "#ffffff"), ("!active", "#ffffff")],
            background=[("active", "#0078d7"), ("!active", "#0078d7")],
            bordercolor=[("active", "#005a9e"), ("!active", "#0078d7")],
            lightcolor=[("active", "#0078d7"), ("!active", "#0078d7")],
            darkcolor=[("active", "#005a9e"), ("!active", "#005a9e")]
        )
        
        # 菜单按钮样式
        style.configure("Accent.TMenubutton", font=("Microsoft YaHei", 9))
        style.map("Accent.TMenubutton",
            foreground=[("active", "#ffffff"), ("!active", "#ffffff")],
            background=[("active", "#0078d7"), ("!active", "#0078d7")],
            bordercolor=[("active", "#005a9e"), ("!active", "#0078d7")],
            lightcolor=[("active", "#0078d7"), ("!active", "#0078d7")],
            darkcolor=[("active", "#005a9e"), ("!active", "#005a9e")]
        )

    def toggle_sidebar(self):
        """切换侧边栏展开/收起状态"""
        self.sidebar_animation.toggle()
        if self.sidebar_animation.current_width > self.sidebar_animation.min_width:
            self.toggle_btn.config(text="◀")
            self.history_label.pack(side=tk.LEFT, padx=20)
        else:
            self.toggle_btn.config(text="▶")
            self.history_label.pack_forget()
        
        # 如果搜索框可见，调整位置
        if self.search_frame.winfo_ismapped():
            self.search_frame.pack_forget()
            self.search_frame.pack(fill=tk.X, pady=(0, 5), padx=5)

    def toggle_search(self):
        """显示/隐藏搜索框"""
        if self.search_frame.winfo_ismapped():
            self.search_frame.pack_forget()
            self.search_var.set("")
            self.update_history_list()  # 恢复显示所有历史记录
        else:
            self.search_frame.pack(fill=tk.X, pady=(0, 5), padx=5)
            self.search_entry.focus()

    def search_history(self, event=None):
        """搜索历史记录"""
        keyword = self.search_var.get().strip().lower()
        if not keyword:
            self.update_history_list()
            return
        
        self.search_results = []
        for conv in self.conversation_history:
            # 搜索标题和消息内容
            if keyword in conv["title"].lower():
                self.search_results.append(conv)
                continue
                
            for msg in conv["messages"]:
                if keyword in msg["message"].lower():
                    self.search_results.append(conv)
                    break
        
        # 更新Treeview显示搜索结果
        self.history_tree.delete(*self.history_tree.get_children())
        for i, conv in enumerate(reversed(self.search_results)):
            self.history_tree.insert("", "end", iid=f"i{i}", values=(conv["title"], conv["timestamp"]))

    def update_theme_colors(self):
        """根据当前主题更新UI颜色"""
        theme = self.config.get("theme", "system")
        current_theme = self.current_theme if theme == "system" else theme
        
        if current_theme == "light":
            bg_color = "#f3f3f3"
            fg_color = "#000000"
            card_bg = "#ffffff"
            accent_color = "#0078d7"
        else:  # dark
            bg_color = "#202020"
            fg_color = "#ffffff"
            card_bg = "#2b2b2b"
            accent_color = "#0078d7"
        
        # 更新主窗口背景
        self.root.config(bg=bg_color)
        self.main_container.config(style="TFrame")
        
        # 更新聊天显示区域
        self.chat_display.config(
            bg=card_bg,
            fg=fg_color,
            insertbackground=fg_color,
            selectbackground="#3d3d3d" if current_theme == "dark" else "#d6d6d6"
        )
        
        # 更新历史记录树
        style = ttk.Style()
        style.configure("Treeview",
            background=card_bg,
            foreground=fg_color,
            fieldbackground=card_bg,
            borderwidth=0,
            font=("Microsoft YaHei", 9)
        )
        style.map("Treeview",
            background=[("selected", accent_color)],
            foreground=[("selected", "#ffffff")]
        )
        
        # 更新标签配置
        self.chat_display.tag_config("user", foreground="#0066cc", font=("Microsoft YaHei", 11, "bold"))
        self.chat_display.tag_config("bot", foreground="#4CAF50", font=("Microsoft YaHei", 11, "bold"))
        self.chat_display.tag_config("system", foreground="#FFA500", font=("Microsoft YaHei", 11, "bold"))
        self.chat_display.tag_config("error", foreground="#FF0000", font=("Microsoft YaHei", 11))

    def bind_events(self):
        """绑定事件处理"""
        self.root.bind("<Configure>", self.handle_resize)

    def set_custom_theme(self, theme_name):
        """设置自定义主题"""
        self.config["theme"] = theme_name
        self.save_config()
        
        if theme_name == "system":
            sv_ttk.set_theme(self.current_theme)
        else:
            sv_ttk.set_theme(theme_name)
        
        self.update_theme_colors()

    def switch_theme(self):
        """切换主题"""
        if self.config.get("theme", "system") == "system":
            self.current_theme = "dark" if self.current_theme == "light" else "light"
            sv_ttk.set_theme(self.current_theme)
            self.update_theme_colors()

    def new_conversation(self):
        """新建对话"""
        if self.current_conversation and not self.current_conversation["messages"]:
            return
            
        self.current_conversation = None
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.delete(1.0, tk.END)
        self.chat_display.config(state=tk.DISABLED)
        
        self.display_message("系统", "已创建新对话", "system")

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
            
        # 添加到当前对话历史
        if self.current_conversation is None:
            self.current_conversation = {
                "id": str(int(time.time())),
                "title": message[:20] + ("..." if len(message) > 20 else ""),
                "messages": [],
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            self.conversation_history.append(self.current_conversation)
            self.update_history_list()
        
        self.current_conversation["messages"].append({
            "sender": "user",
            "message": message,
            "timestamp": datetime.now().strftime("%H:%M:%S")
        })
        
        # 显示加载动画
        self.loading_animation.start()
        
        threading.Thread(
            target=self.get_bot_response,
            args=(message,),
            daemon=True
        ).start()

    def get_bot_response(self, message):
        """获取机器人响应"""
        try:
            if self.config["api_settings"]["active_model"] == "local":
                similar_question = self.find_similar_question(message)
                
                if similar_question:
                    response = self.qa_mapping[similar_question]
                else:
                    response = str(self.chatbot.get_response(message))
            else:
                response = self.call_api_model(message)
            
            self.root.after(0, self.display_message, "小梓", response, "bot")
            
            # 保存到当前对话历史
            if self.current_conversation is not None:
                self.current_conversation["messages"].append({
                    "sender": "bot",
                    "message": response,
                    "timestamp": datetime.now().strftime("%H:%M:%S")
                })
                self.save_config()
                
        except Exception as e:
            error_msg = f"生成回复时出错: {str(e)}"
            self.root.after(0, self.display_message, "系统", error_msg, "error")
        finally:
            # 停止加载动画
            self.root.after(0, self.loading_animation.stop)

    def call_api_model(self, message):
        """调用API模型获取响应"""
        model = self.config["api_settings"]["active_model"]
        api_key = self.config["api_settings"][model]["api_key"]
        base_url = self.config["api_settings"][model]["base_url"]
        
        if not api_key:
            raise ValueError(f"未配置{model.upper()} API密钥")
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        if model == "openai":
            url = f"{base_url}/chat/completions"
            data = {
                "model": "gpt-3.5-turbo",
                "messages": [{"role": "user", "content": message}],
                "temperature": 0.7
            }
        elif model == "deepseek":
            url = f"{base_url}/chat/completions"
            data = {
                "model": "deepseek-chat",
                "messages": [{"role": "user", "content": message}],
                "temperature": 0.7
            }
        elif model == "kimi":
            url = f"{base_url}/chat/completions"
            data = {
                "model": "moonshot-v1-8k",
                "messages": [{"role": "user", "content": message}],
                "temperature": 0.3
            }
        elif model == "claude":
            url = f"{base_url}/messages"
            headers = {
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json"
            }
            data = {
                "model": "claude-3-opus-20240229",
                "max_tokens": 1000,
                "messages": [{"role": "user", "content": message}]
            }
        elif model == "gemini":
            url = f"{base_url}/models/gemini-pro:generateContent?key={api_key}"
            data = {
                "contents": [{
                    "parts": [{"text": message}]
                }]
            }
        else:
            raise ValueError(f"不支持的模型: {model}")
        
        response = requests.post(url, headers=headers, json=data)
        if response.status_code != 200:
            raise ValueError(f"API请求失败: {response.status_code} - {response.text}")
        
        if model == "claude":
            return response.json()["content"][0]["text"]
        elif model == "gemini":
            return response.json()["candidates"][0]["content"]["parts"][0]["text"]
        else:
            return response.json()["choices"][0]["message"]["content"]

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

    def show_api_settings(self):
        """显示API设置对话框"""
        dialog = tk.Toplevel(self.root)
        dialog.title("API设置")
        dialog.geometry("600x500")
        dialog.resizable(False, False)
        
        # 模型选择
        ttk.Label(dialog, text="选择模型:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.model_var = tk.StringVar(value=self.config["api_settings"]["active_model"])
        model_combobox = ttk.Combobox(
            dialog,
            textvariable=self.model_var,
            values=["local", "openai", "deepseek", "kimi", "claude", "gemini"],
            state="readonly"
        )
        model_combobox.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        
        # 创建Notebook用于不同模型的设置
        notebook = ttk.Notebook(dialog)
        notebook.grid(row=1, column=0, columnspan=2, padx=10, pady=5, sticky="nsew")
        
        # OpenAI设置
        openai_frame = ttk.Frame(notebook)
        notebook.add(openai_frame, text="OpenAI")
        
        ttk.Label(openai_frame, text="API密钥:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.openai_key_var = tk.StringVar(value=self.config["api_settings"]["openai"]["api_key"])
        ttk.Entry(openai_frame, textvariable=self.openai_key_var, show="*").grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        
        ttk.Label(openai_frame, text="API基础URL:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.openai_url_var = tk.StringVar(value=self.config["api_settings"]["openai"]["base_url"])
        ttk.Entry(openai_frame, textvariable=self.openai_url_var).grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        
        # DeepSeek设置
        deepseek_frame = ttk.Frame(notebook)
        notebook.add(deepseek_frame, text="DeepSeek")
        
        ttk.Label(deepseek_frame, text="API密钥:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.deepseek_key_var = tk.StringVar(value=self.config["api_settings"]["deepseek"]["api_key"])
        ttk.Entry(deepseek_frame, textvariable=self.deepseek_key_var, show="*").grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        
        ttk.Label(deepseek_frame, text="API基础URL:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.deepseek_url_var = tk.StringVar(value=self.config["api_settings"]["deepseek"]["base_url"])
        ttk.Entry(deepseek_frame, textvariable=self.deepseek_url_var).grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        
        # Kimi设置
        kimi_frame = ttk.Frame(notebook)
        notebook.add(kimi_frame, text="Kimi")
        
        ttk.Label(kimi_frame, text="API密钥:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.kimi_key_var = tk.StringVar(value=self.config["api_settings"]["kimi"]["api_key"])
        ttk.Entry(kimi_frame, textvariable=self.kimi_key_var, show="*").grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        
        ttk.Label(kimi_frame, text="API基础URL:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.kimi_url_var = tk.StringVar(value=self.config["api_settings"]["kimi"]["base_url"])
        ttk.Entry(kimi_frame, textvariable=self.kimi_url_var).grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        
        # Claude设置
        claude_frame = ttk.Frame(notebook)
        notebook.add(claude_frame, text="Claude")
        
        ttk.Label(claude_frame, text="API密钥:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.claude_key_var = tk.StringVar(value=self.config["api_settings"]["claude"]["api_key"])
        ttk.Entry(claude_frame, textvariable=self.claude_key_var, show="*").grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        
        ttk.Label(claude_frame, text="API基础URL:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.claude_url_var = tk.StringVar(value=self.config["api_settings"]["claude"]["base_url"])
        ttk.Entry(claude_frame, textvariable=self.claude_url_var).grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        
        # Gemini设置
        gemini_frame = ttk.Frame(notebook)
        notebook.add(gemini_frame, text="Gemini")
        
        ttk.Label(gemini_frame, text="API密钥:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.gemini_key_var = tk.StringVar(value=self.config["api_settings"]["gemini"]["api_key"])
        ttk.Entry(gemini_frame, textvariable=self.gemini_key_var, show="*").grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        
        ttk.Label(gemini_frame, text="API基础URL:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.gemini_url_var = tk.StringVar(value=self.config["api_settings"]["gemini"]["base_url"])
        ttk.Entry(gemini_frame, textvariable=self.gemini_url_var).grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        
        # 按钮区域
        button_frame = ttk.Frame(dialog)
        button_frame.grid(row=2, column=0, columnspan=2, padx=10, pady=10, sticky="e")
        
        ttk.Button(
            button_frame,
            text="取消",
            command=dialog.destroy
        ).pack(side=tk.RIGHT, padx=5)
        
        ttk.Button(
            button_frame,
            text="保存",
            command=lambda: self.save_api_settings(dialog)
        ).pack(side=tk.RIGHT)
        
        # 根据当前模型选择对应的标签页
        model_index = {
            "openai": 0,
            "deepseek": 1,
            "kimi": 2,
            "claude": 3,
            "gemini": 4
        }.get(self.config["api_settings"]["active_model"], 0)
        notebook.select(model_index)

    def save_api_settings(self, dialog):
        """保存API设置"""
        self.config["api_settings"]["active_model"] = self.model_var.get()
        self.config["api_settings"]["openai"]["api_key"] = self.openai_key_var.get()
        self.config["api_settings"]["openai"]["base_url"] = self.openai_url_var.get()
        self.config["api_settings"]["deepseek"]["api_key"] = self.deepseek_key_var.get()
        self.config["api_settings"]["deepseek"]["base_url"] = self.deepseek_url_var.get()
        self.config["api_settings"]["kimi"]["api_key"] = self.kimi_key_var.get()
        self.config["api_settings"]["kimi"]["base_url"] = self.kimi_url_var.get()
        self.config["api_settings"]["claude"]["api_key"] = self.claude_key_var.get()
        self.config["api_settings"]["claude"]["base_url"] = self.claude_url_var.get()
        self.config["api_settings"]["gemini"]["api_key"] = self.gemini_key_var.get()
        self.config["api_settings"]["gemini"]["base_url"] = self.gemini_url_var.get()
        
        self.save_config()
        dialog.destroy()
        self.display_message("系统", "API设置已保存", "system")

    def show_history_dialog(self):
        """显示历史记录对话框"""
        dialog = tk.Toplevel(self.root)
        dialog.title("历史对话")
        dialog.geometry("700x500")
        
        frame = ttk.Frame(dialog, style="Card.TFrame")
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 搜索框
        search_frame = ttk.Frame(frame)
        search_frame.pack(fill=tk.X, padx=5, pady=5)
        
        search_var = tk.StringVar()
        search_entry = ttk.Entry(
            search_frame,
            textvariable=search_var,
            font=("Microsoft YaHei", 10)
        )
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        search_entry.bind("<Return>", lambda e: self.search_in_dialog(dialog, search_var.get()))
        
        ttk.Button(
            search_frame,
            text="搜索",
            command=lambda: self.search_in_dialog(dialog, search_var.get()),
            style="Accent.TButton"
        ).pack(side=tk.RIGHT)
        
        # 使用Treeview显示历史记录
        tree_frame = ttk.Frame(frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(tree_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.history_tree_dialog = ttk.Treeview(
            tree_frame,
            columns=("id", "title", "timestamp"),
            show="headings",
            yscrollcommand=scrollbar.set,
            selectmode="browse",
            style="Treeview"
        )
        self.history_tree_dialog.pack(fill=tk.BOTH, expand=True)
        
        scrollbar.config(command=self.history_tree_dialog.yview)
        
        self.history_tree_dialog.heading("id", text="ID")
        self.history_tree_dialog.heading("title", text="标题")
        self.history_tree_dialog.heading("timestamp", text="时间")
        
        self.history_tree_dialog.column("id", width=100, anchor="center")
        self.history_tree_dialog.column("title", width=300, anchor="w")
        self.history_tree_dialog.column("timestamp", width=150, anchor="center")
        
        # 添加数据
        for conv in self.conversation_history:
            self.history_tree_dialog.insert("", tk.END, values=(conv["id"], conv["title"], conv["timestamp"]))
        
        # 按钮区域
        button_frame = ttk.Frame(frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(
            button_frame,
            text="加载",
            style="Accent.TButton",
            command=lambda: self.load_selected_conversation(dialog)
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame,
            text="删除",
            style="Accent.TButton",
            command=self.delete_selected_conversation
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame,
            text="关闭",
            command=dialog.destroy
        ).pack(side=tk.RIGHT)

    def search_in_dialog(self, dialog, keyword):
        """在对话框中进行搜索"""
        keyword = keyword.strip().lower()
        if not keyword:
            # 清空搜索，显示所有记录
            self.history_tree_dialog.delete(*self.history_tree_dialog.get_children())
            for conv in self.conversation_history:
                self.history_tree_dialog.insert("", tk.END, values=(conv["id"], conv["title"], conv["timestamp"]))
            return
            
        # 搜索匹配的对话
        results = []
        for conv in self.conversation_history:
            if keyword in conv["title"].lower():
                results.append(conv)
                continue
                
            for msg in conv["messages"]:
                if keyword in msg["message"].lower():
                    results.append(conv)
                    break
        
        # 更新Treeview显示搜索结果
        self.history_tree_dialog.delete(*self.history_tree_dialog.get_children())
        for conv in results:
            self.history_tree_dialog.insert("", tk.END, values=(conv["id"], conv["title"], conv["timestamp"]))

    def load_selected_conversation(self, dialog):
        """加载选中的对话"""
        selected = self.history_tree_dialog.selection()
        if not selected:
            return
            
        item = self.history_tree_dialog.item(selected[0])
        conv_id = item["values"][0]
        
        for conv in self.conversation_history:
            if conv["id"] == conv_id:
                self.current_conversation = conv
                self.display_conversation(conv)
                dialog.destroy()
                break

    def delete_selected_conversation(self):
        """删除选中的对话"""
        selected = self.history_tree_dialog.selection()
        if not selected:
            return
            
        item = self.history_tree_dialog.item(selected[0])
        conv_id = item["values"][0]
        
        self.conversation_history = [conv for conv in self.conversation_history if conv["id"] != conv_id]
        self.save_config()
        
        if self.current_conversation and self.current_conversation["id"] == conv_id:
            self.current_conversation = None
            self.chat_display.config(state=tk.NORMAL)
            self.chat_display.delete(1.0, tk.END)
            self.chat_display.config(state=tk.DISABLED)
        
        self.history_tree_dialog.delete(selected[0])
        self.update_history_list()

    def on_history_select(self, event):
        """从历史记录树中选择对话"""
        selection = self.history_tree.selection()
        if not selection:
            return
            
        if self.search_var.get():  # 如果在搜索模式下
            index = len(self.search_results) - int(selection[0][1:]) - 1
            if 0 <= index < len(self.search_results):
                self.current_conversation = self.search_results[index]
        else:  # 正常模式
            index = len(self.conversation_history) - int(selection[0][1:]) - 1
            if 0 <= index < len(self.conversation_history):
                self.current_conversation = self.conversation_history[index]
                
        if self.current_conversation:
            self.display_conversation(self.current_conversation)

    def update_history_list(self):
        """更新历史记录列表"""
        self.history_tree.delete(*self.history_tree.get_children())
        if hasattr(self, 'search_var') and self.search_var.get():
            # 显示搜索结果
            for i, conv in enumerate(reversed(self.search_results)):
                self.history_tree.insert("", "end", iid=f"i{i}", values=(conv["title"], conv["timestamp"]))
        else:
            # 显示所有历史记录
            for i, conv in enumerate(reversed(self.conversation_history)):
                self.history_tree.insert("", "end", iid=f"i{i}", values=(conv["title"], conv["timestamp"]))

    def display_conversation(self, conversation):
        """显示对话内容"""
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.delete(1.0, tk.END)
        
        for msg in conversation["messages"]:
            tag = "user" if msg["sender"] == "user" else "bot"
            self.chat_display.insert(tk.END, f"{msg['sender']} ({msg['timestamp']}): ", tag)
            self.chat_display.insert(tk.END, f"{msg['message']}\n\n")
        
        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)

    def clear_history(self):
        """清空历史记录"""
        if messagebox.askyesno("确认", "确定要清空所有历史记录吗？"):
            self.conversation_history = []
            self.current_conversation = None
            self.save_config()
            self.update_history_list()
            self.chat_display.config(state=tk.NORMAL)
            self.chat_display.delete(1.0, tk.END)
            self.chat_display.config(state=tk.DISABLED)

if __name__ == "__main__":
    root = tk.Tk()
    app = EnhancedChatApplication(root)
    root.mainloop()