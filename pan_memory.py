# pan_memory.py - Memory Management

class PanMemory:
    def __init__(self):
        self.memory = {}
        self.short_term_memory = []

    def remember(self, key, value):
        self.memory[key] = value

    def recall(self, key):
        return self.memory.get(key, None)

    def forget(self, key):
        if key in self.memory:
            del self.memory[key]

    def clear_memory(self):
        self.memory.clear()

    def remember_short_term(self, phrase):
        self.short_term_memory.append(phrase)
        if len(self.short_term_memory) > 10:
            self.short_term_memory.pop(0)  # Maintain a maximum of 10 items

    def recall_short_term(self):
        return self.short_term_memory
    
    import sqlite3

def remember(topic, content):
    with sqlite3.connect('pan_memory.db') as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO memories (category, content) VALUES (?, ?)",
            (topic, content)
        )
        conn.commit()


pan_memory = PanMemory()
