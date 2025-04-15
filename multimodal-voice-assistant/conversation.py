"""
管理对话历史，支持基于相似度的上下文清除。
"""
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from logger import log # 导入日志记录器

class EnhancedConversationContext:
    """管理对话历史，支持基于相似度的上下文清除和摘要"""
    def __init__(self, max_turns=5, similarity_threshold=0.3):
        self.history = [] # 存储对话历史
        self.max_turns = max_turns # 最大保留的回合数
        self.similarity_threshold = similarity_threshold # 相似度阈值，低于此值认为话题改变
        self.vectorizer = TfidfVectorizer() # TF-IDF 向量化器

    def add_exchange(self, user_input, assistant_response):
        """添加一次用户和助手的交互，并根据相似度判断是否清除旧上下文"""
        if self.history:
            try:
                similarity = self.calculate_similarity(user_input)
                log(f"与上一轮的相似度: {similarity:.2f}", title="CONTEXT_SIMILARITY", style="dim")
                if similarity < self.similarity_threshold:
                    log("检测到话题变化，清除旧上下文。", title="CONTEXT_UPDATE", style="yellow")
                    self.clear() # 如果话题变化显著，清除历史记录
            except Exception as e:
                 log(f"计算相似度时出错: {e}", title="ERROR", style="bold red")

        self.history.append({
            "role": "user", # 使用 role 区分
            "content": user_input
        })
        self.history.append({
            "role": "assistant",
            "content": assistant_response
        })
        # 如果历史记录超过最大回合数 * 2 (因为 user 和 assistant 各占一条)，移除最早的两条
        while len(self.history) > self.max_turns * 2:
            self.history.pop(0)
            self.history.pop(0) # 移除一对

    def get_context(self):
        """获取格式化的对话上下文 (适用于 DeepSeek 的 messages 格式)"""
        return self.history # 直接返回列表

    def get_formatted_context_string(self):
        """将历史记录格式化为字符串 (适用于 Gemini 的简单文本上下文)"""
        context_str = ""
        for i in range(0, len(self.history), 2):
            user_msg = self.history[i]['content'][:500] + '...' if len(self.history[i]['content']) > 500 else self.history[i]['content']
            if i + 1 < len(self.history):
                assistant_msg = self.history[i+1]['content'][:500] + '...' if len(self.history[i+1]['content']) > 500 else self.history[i+1]['content']
                context_str += f"User: {user_msg}\nAssistant: {assistant_msg}\n\n"
            else: # 处理只有用户输入的情况 (理论上不应发生在此结构中)
                context_str += f"User: {user_msg}\n\n"
        return context_str.strip()


    def calculate_similarity(self, new_input):
        """计算新输入与历史用户输入的平均余弦相似度"""
        user_inputs = [exchange['content'] for exchange in self.history if exchange['role'] == 'user']
        if not user_inputs:
            return 0.0 # 如果没有历史用户输入，相似度为0

        all_inputs = user_inputs + [new_input] # 包含新输入的列表

        try:
            tfidf_matrix = self.vectorizer.fit_transform(all_inputs)
            cosine_similarities = cosine_similarity(tfidf_matrix[-1], tfidf_matrix[:-1])
            if cosine_similarities.size > 0:
                 return np.mean(cosine_similarities)
            else:
                 return 0.0
        except ValueError:
             log("无法计算文本相似度（可能输入过短）", title="WARNING", style="yellow")
             return 0.0

    def clear(self):
        """清除对话历史"""
        self.history = []

    def remember(self, information):
        """添加需要记住的信息到历史记录"""
        self.history.append({"role": "user", "content": f"请记住以下信息: {information}"})
        self.history.append({"role": "assistant", "content": "好的，我记住了。"})
        log(f"已记住信息: {information}", title="MEMORY", style="cyan")
        while len(self.history) > self.max_turns * 2:
            self.history.pop(0)
            self.history.pop(0)

    def forget(self):
        """清除所有对话历史"""
        self.clear()
        log("已清除所有对话上下文。", title="MEMORY", style="yellow")
        return "好的，我已经忘记了我们之前的对话内容。"
