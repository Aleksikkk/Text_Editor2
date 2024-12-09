import tkinter as tk
from tkinter import scrolledtext, filedialog, messagebox, simpledialog
import subprocess
import os
import re

class TextEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("Python Text Editor")
        self.keywords = ["def", "class", "import", "from", "if", "else", "elif", "for", "while", "return", "print"]
        self.is_modified = False
        self.current_file_path = None
        self.font_size = 12  # Начальный размер шрифта
        self.create_widgets()
        self.bind_events()

    def create_widgets(self):
        # Создание текстовой области
        self.text_area = scrolledtext.ScrolledText(self.root, wrap=tk.WORD, undo=True, font=("Courier New", self.font_size))
        self.text_area.pack(expand=True, fill='both')

        # Создание области вывода
        self.output_area = scrolledtext.ScrolledText(self.root, wrap=tk.WORD, height=10)
        self.output_area.pack(expand=False, fill='both')

        # Меню
        self.menu = tk.Menu(self.root)
        self.root.config(menu=self.menu)
        self.create_file_menu()
        self.create_settings_menu()
        self.create_font_menu()  

    def create_file_menu(self):
        file_menu = tk.Menu(self.menu, tearoff=0)
        self.menu.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open", command=self.open_file)
        file_menu.add_command(label="Save", command=self.save_file_and_update_title)
        file_menu.add_command(label="Save As", command=self.save_as_file)
        file_menu.add_command(label="New", command=self.new_file)
        file_menu.add_separator()
        file_menu.add_command(label="Run", command=self.run_code)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

    def create_settings_menu(self):
        settings_menu = tk.Menu(self.menu, tearoff=0)
        self.menu.add_cascade(label="Settings", menu=settings_menu)
        settings_menu.add_command(label="Change Theme", command=self.change_theme)

    def create_font_menu(self):
        self.menu.add_command(label="Font", command=self.change_font_size)  

    def bind_events(self):
        self.text_area.bind("<KeyRelease>", self.on_modified)
        self.text_area.bind("<Tab>", self.autocomplete)
        self.text_area.bind("<Control-v>", self.on_paste)  
        shortcuts = {
            "<Control-n>": self.new_file,
            "<Control-o>": self.open_file,
            "<Control-s>": self.save_file_and_update_title,
            "<Control-r>": self.run_code,
            "<Control-z>": self.undo_action
        }
        for key, action in shortcuts.items():
            self.root.bind(key, lambda event, action=action: action())

    def on_paste(self, event):
        self.text_area.event_generate("<<Paste>>")  
        self.highlight_syntax()  
        return "break"  

    def on_modified(self, event):
        if not self.is_modified:
            self.is_modified = True
            self.update_title()
        self.highlight_syntax()  

    def update_title(self):
        title = "Python Text Editor"
        if self.is_modified:
            title += " *"
        if self.current_file_path:
            title += f" - {os.path.basename(self.current_file_path)}"
        self.root.title(title)

    def open_file(self):
        file_path = filedialog.askopenfilename(defaultextension=".py", filetypes=[("Python files", "*.py"), ("All files", "*.*")])
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    self.text_area.delete(1.0, tk.END)
                    self.text_area.insert(tk.END, file.read())
                self.highlight_syntax()
                self.current_file_path = file_path
                self.is_modified = False
                self.update_title()
            except Exception as e:
                messagebox.showerror("Error", f"Не удалось открыть файл: {str(e)}")

    def save_file(self):
        if self.current_file_path:
            try:
                with open(self.current_file_path, 'w', encoding='utf-8') as file:
                    file.write(self.text_area.get(1.0, tk.END).strip())
                self.is_modified = False
                self.update_title()
            except Exception as e:
                messagebox.showerror("Error", f"Не удалось сохранить файл: {str(e)}")
        else:
            self.save_as_file()

    def save_file_and_update_title(self):
        self.save_file()

    def save_as_file(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".py", filetypes=[("Python files", "*.py"), ("All files", "*.*")])
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.write(self.text_area.get(1.0, tk.END).strip())
                self.current_file_path = file_path
                self.is_modified = False
                self.update_title()
            except Exception as e:
                messagebox.showerror("Error", f"Не удалось сохранить файл: {str(e)}")

    def new_file(self):
        self.text_area.delete(1.0, tk.END)
        self.output_area.delete(1.0, tk.END)
        self.current_file_path = None
        self.is_modified = False
        self.update_title()

    def run_code(self):
        code = self.text_area.get(1.0, tk.END).strip()
        self.output_area.delete(1.0, tk.END)

        if not code:
            messagebox.showwarning("Warning", "Нет кода для выполнения.")
            return

        temp_file = "temp_script.py"
        try:
            with open(temp_file, 'w', encoding='utf-8') as f:
                f.write(code)

            input_prompts = self.extract_input_prompts(code)
            input_data = {prompt: simpledialog.askstring("Input", prompt) for prompt in input_prompts}

            result = subprocess.run(['python', temp_file], input='\n'.join(input_data.values()), text=True, capture_output=True)
            self.output_area.insert(tk.END, result.stdout)
            if result.stderr:
                self.output_area.insert(tk.END, f"Ошибка:\n{result.stderr}")
        except Exception as e:
            self.output_area.insert(tk.END, f"Ошибка выполнения: {str(e)}")
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)

    def extract_input_prompts(self, code):
        return [match.group(1) for match in re.finditer(r'input\(\s*["\'](.*?)["\']\s*\)', code)]

    def highlight_syntax(self, event=None):
        self.text_area.tag_remove("keyword", "1.0", tk.END)
        self.text_area.tag_remove("comment", "1.0", tk.END)
        self.text_area.tag_remove("number", "1.0", tk.END)  

        code = self.text_area.get(1.0, tk.END)

        for keyword in self.keywords:
            start_index = '1.0'
            while True:
                start_index = self.text_area.search(keyword, start_index, stopindex=tk.END)
                if not start_index:
                    break
                end_index = f"{start_index}+{len(keyword)}c"
                self.text_area.tag_add("keyword", start_index, end_index)
                start_index = end_index

        
        for match in re.finditer(r'#.*', code):
            start_index = f"1.0 + {match.start()} chars"
            end_index = f"1.0 + {match.end()} chars"
            self.text_area.tag_add("comment", start_index, end_index)

        
        for match in re.finditer(r'\b\d+\b', code):  
            start_index = f"1.0 + {match.start()} chars"
            end_index = f"1.0 + {match.end()} chars"
            self.text_area.tag_add("number", start_index, end_index)

        
        self.text_area.tag_config("keyword", foreground="blue")
        self.text_area.tag_config("comment", foreground="green")
        self.text_area.tag_config("number", foreground="purple")  

    def autocomplete(self, event):
        current_text = self.text_area.get("insert linestart", "insert")
        for keyword in self.keywords:
            if keyword.startswith(current_text):
                self.text_area.insert("insert", keyword[len(current_text):])
                break
        return "break"

    def change_theme(self):
        theme = simpledialog.askstring("Change Theme", "Введите тему (light/dark/yellow):")
        if theme in ["dark", "light", "yellow"]:
            self.apply_theme(theme)
        else:
            messagebox.showwarning("Warning", "Неизвестная тема.")

    def apply_theme(self, theme):
        colors = {
            "dark": {'bg': 'black', 'fg': 'white', 'cursor': 'white'},
            "light": {'bg': 'white', 'fg': 'black', 'cursor': 'black'},
            "yellow": {'bg': '#FFFFE0', 'fg': 'black', 'cursor': 'black'}
        }
        if theme in colors:
            self.root.config(bg=colors[theme]['bg'])
            self.text_area.config(bg=colors[theme]['bg'], fg=colors[theme]['fg'], insertbackground=colors[theme]['cursor'])
            self.output_area.config(bg=colors[theme]['bg'], fg=colors[theme]['fg'])

    def change_font_size(self):
        new_size = simpledialog.askinteger("Change Font Size", "Введите новый размер шрифта:", initialvalue=self.font_size)
        if new_size:
            self.font_size = new_size
            self.text_area.config(font=("Courier New", self.font_size))  

    def undo_action(self, event=None):
        self.text_area.edit_undo()

if __name__ == "__main__":
    root = tk.Tk()
    editor = TextEditor(root)
    root.mainloop()
