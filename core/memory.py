from config import MAX_HISTORY

class ConversationMemory:

    def __init__(self):
        self.history = []

    def add_user_message(self,message):
        self.history.append({"role":"user","content":message})
        self.trimHistory()

    def add_agent_message(self,message):
        self.history.append({"role":"agent","content":message})
        self.trimHistory()
    
    def getHistory(self):
        return self.history.copy()
    
    def trimHistory(self):
        if len(self.history)>MAX_HISTORY*2:
            self.history = self.history[-(MAX_HISTORY*2):]
    
    def clearMemory(self):
        self.history = []
        print("Memory Cleared!")