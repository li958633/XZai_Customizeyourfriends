XZai2.0版本介绍入口：https://li958633.github.io/dmxzweb/post/xzai2.0---%E8%AE%AD%E7%BB%83%E7%8B%AC%E5%B1%9E%E4%BA%8E%E4%BD%A0%E7%9A%84ai%E6%9C%8B%E5%8F%8B/
XZai - 训练独属于你的AI朋友
项目概述
XZai是一个基于Python开发的智能对话系统，采用ChatterBot框架构建，具备知识学习能力和个性化训练功能。该系统不仅能进行自然语言对话，还能通过用户训练不断扩展知识库，最终成为专属于用户的AI伙伴。

<img width="898" height="676" alt="QQ_1754544545931" src="https://github.com/user-attachments/assets/f6163877-12e4-4dc9-b6ac-50bf4d642494" />



核心功能详解
1. 智能对话系统
多轮对话支持：基于ChatterBot框架实现上下文感知的对话能力

混合响应策略：结合规则匹配和机器学习生成回答

特殊指令处理：支持"train:open"等指令进入训练模式

2. 知识训练系统
交互式训练：通过对话框逐步引导用户输入问答对

批量导入：支持从JSON文件导入结构化训练数据

多格式兼容：

标准问答格式：{"question":"...","answer":"..."}

任务型格式：{"input":"...","target":"..."}

选择题格式：包含answer_choices字段

3. 主题管理系统
系统主题检测：通过Windows注册表自动获取当前系统主题设置

平滑过渡动画：使用Canvas实现的淡入淡出效果

实时切换：支持亮色/暗色模式一键切换

4. 语义处理能力
相似问题匹配：基于difflib的模糊匹配算法

问答映射表：构建问题-答案的快速检索索引

响应选择策略：采用最高频响应选择方法

技术实现细节
代码架构

classDiagram
    class ThemeTransition{
        +start()
        +setup_animation_window()
        +run_animation()
        +fade_animation()
    }
    
    class EnhancedChatApplication{
        +setup_chatbot()
        +train_chatbot()
        +build_qa_mapping()
        +find_similar_question()
        +process_message()
    }
    
    ThemeTransition --> EnhancedChatApplication : 提供动画支持
关键技术点
数据库连接：

python
database_uri="sqlite:///win11_chatbot_db.sqlite3"
逻辑适配器配置：

python
logic_adapters=[
    {
        "import_path": "chatterbot.logic.BestMatch",
        "maximum_similarity_threshold": 0.85,
        "response_selection_method": get_most_frequent_response,
        "statement_comparison_function": LevenshteinDistance
    }
]
窗口特效实现：

python
DWMWA_WINDOW_CORNER_PREFERENCE = 33
DWM_WINDOW_CORNER_ROUND = 2
ctypes.windll.dwmapi.DwmSetWindowAttribute(...)
使用指南
安装与运行
安装依赖：

bash
pip install chatterbot==1.0.5 sv-ttk pywin32
运行程序：

bash
python xzAI.py
训练模式操作流程
通过按钮或输入train:open进入训练模式

按照提示输入问题和答案

输入"退出"结束训练

训练数据自动保存到xunlian.json

批量训练步骤
准备JSON格式训练文件

点击"训练模式"按钮

选择"从JSON文件训练"

选择训练文件并确认

注意事项
数据安全
程序会自动备份损坏的JSON文件，备份名称为xunlian_bak_<时间戳>.json

建议定期备份xunlian.json和win11_chatbot_db.sqlite3文件

常见问题处理
JSON解析错误：程序会自动尝试修复常见格式问题

训练失败：检查问题是否包含特殊字符

主题切换异常：可能是系统权限问题导致无法读取注册表
