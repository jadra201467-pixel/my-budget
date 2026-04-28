import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
import os
import csv
import requests
from datetime import datetime
INCOME_1 = "Источник дохода-1"
INCOME_2 = "Источник дохода-2"
INCOME_3 = "Источник дохода-3"
class FinanceApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Мой Бюджет 2026")
        self.root.geometry("1000x750")
        self.root.configure(bg="#2b2b2b")
        
        base_path = os.path.dirname(os.path.abspath(__file__))
        self.filename = os.path.join(base_path, "budget_data.csv")
        
        # --- ЗАГЛУШКА ДЛЯ ВАШЕЙ ССЫЛКИ ---
        self.SCRIPT_URL ="https://script.google.com"
        
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        style = ttk.Style()
        style.theme_use("default")
        # Черный фон таблицы
        style.configure("Treeview", background="#2b2b2b", foreground="white", fieldbackground="#2b2b2b", rowheight=25)
        style.configure("Treeview.Heading", background="#3c3f41", foreground="white", relief="flat")
        style.map("Treeview", background=[('selected', '#4a4a4a')])

        self.left_panel = tk.Frame(self.root, bg="#3c3f41", width=280)
        self.left_panel.pack(side="left", fill="y", padx=5, pady=5)
        self.left_panel.pack_propagate(False)

        # ПОЛЯ ВВОДА
        tk.Label(self.left_panel, text="Дата", bg="#3c3f41", fg="white").pack(pady=(10,0))
        self.date_entry = DateEntry(self.left_panel, width=12, background='darkblue', foreground='white', borderwidth=2, date_pattern='dd.mm.yyyy')
        self.date_entry.pack(padx=10, pady=5, fill="x")

        tk.Label(self.left_panel, text="Заметка", bg="#3c3f41", fg="white").pack(pady=(10,0))
        self.note_entry = tk.Entry(self.left_panel, justify='center')
        self.note_entry.pack(padx=10, fill="x")

        tk.Label(self.left_panel, text="▼ ТРАТЫ (авто-минус)", bg="#3c3f41", fg="#ff6666", font=("Arial", 9, "bold")).pack(pady=(15,0))
        self.expenses_list = ["продукты", "связь", "электричество", "вода", "газ", "дала в долг"]
        self.expense_cb = ttk.Combobox(self.left_panel, values=self.expenses_list)
        self.expense_cb.pack(padx=10, fill="x")
        self.expense_cb.bind("<<ComboboxSelected>>", self.on_expense_select)

        tk.Label(self.left_panel, text="▼ ДОХОДЫ", bg="#3c3f41", fg="#66ff66", font=("Arial", 9, "bold")).pack(pady=(15,0))
        self.incomes_list = [INCOME_1, INCOME_2, INCOME_3]
        self.income_cb = ttk.Combobox(self.left_panel, values=self.incomes_list)
        self.income_cb.pack(padx=10, fill="x")
        self.income_cb.bind("<<ComboboxSelected>>", self.on_income_select)

        tk.Label(self.left_panel, text="Сумма", bg="#3c3f41", fg="white").pack(pady=(15,0))
        self.amount_entry = tk.Entry(self.left_panel, justify='center', font=("Arial", 12, "bold"))
        self.amount_entry.pack(padx=10, fill="x")

        # КНОПКИ
        tk.Button(self.left_panel, text="СОХРАНИТЬ", bg="#28a745", fg="white", font=("Arial", 10, "bold"), command=self.add_transaction).pack(fill="x", padx=10, pady=20)
        
        # СИНЯЯ КНОПКА СИНХРОНИЗАЦИИ
        tk.Button(self.left_panel, text="☁ СИНХРОНИЗАЦИЯ", bg="#007bff", fg="white", font=("Arial", 9, "bold"), command=self.sync_all_to_google).pack(fill="x", padx=10, pady=5)
        
        tk.Button(self.left_panel, text="УДАЛИТЬ ПОСЛЕДНЕЕ", bg="#c82333", fg="white", command=self.undo_last).pack(fill="x", padx=10, pady=5)

        # ТАБЛИЦА (5 СТОЛБЦОВ)
        self.tree = ttk.Treeview(self.root, columns=("date", "note", "category", "amount", "id"), show='headings')
        self.tree.heading("date", text="Дата")
        self.tree.heading("note", text="Заметка")
        self.tree.heading("category", text="Категория")
        self.tree.heading("amount", text="Сумма")
        self.tree.heading("id", text="Статус")
        
        self.tree.column("id", width=80, anchor="center")
        
        # Теги цветов
        self.tree.tag_configure('expense', foreground='#ff6666')
        self.tree.tag_configure('income', foreground='#66ff66')
        self.tree.tag_configure('synced', foreground='#555555') # Темно-серый для синхронизированных
        self.tree.pack(side="top", fill="both", expand=True, padx=10, pady=5)
        self.summary_var = tk.StringVar(value="За месяц: 0.00 | За год: 0.00 руб.")
        tk.Label(self.root, textvariable=self.summary_var, bg="#2b2b2b", fg="white", font=("Arial", 12, "bold")).pack(pady=10)

    def on_expense_select(self, event):
        self.income_cb.set('') 
        current = self.amount_entry.get().replace('-', '')
        self.amount_entry.delete(0, tk.END)
        self.amount_entry.insert(0, f"-{current}")

    def on_income_select(self, event):
        self.expense_cb.set('') 
        current = self.amount_entry.get().replace('-', '')
        self.amount_entry.delete(0, tk.END)
        self.amount_entry.insert(0, current)

    def add_transaction(self):
        category = self.expense_cb.get() if self.expense_cb.get() else self.income_cb.get()
        date = self.date_entry.get()
        note = self.note_entry.get()
        amount_raw = self.amount_entry.get().replace(',', '.')
        
        if not category or not amount_raw:
            messagebox.showwarning("Внимание", "Заполните все поля")
            return

        try:
            val = float(amount_raw)
            status = "new" # Всегда новое при создании
            tag = 'expense' if val < 0 else 'income'
            self.tree.insert("", "end", values=(date, note, category, f"{val:.2f}", status), tags=(tag,))
            # Вставляем 5 значений
           
            self.save_data()
            self.update_totals()
            self.amount_entry.delete(0, tk.END)
            self.note_entry.delete(0, tk.END)   
            self.expense_cb.set('')
            self.income_cb.set('')
            
        except ValueError:
            messagebox.showerror("Ошибка", "Введите число")

    def sync_all_to_google(self):
        if self.SCRIPT_URL == "https://google.com" or not self.SCRIPT_URL.startswith("https://google.com/macros"):
          messagebox.showwarning("Настройка", "Для работы синхронизации укажите полный URL вашего Google Script.")
        return
        """Отправляет только записи со статусом 'new'"""
        items = self.tree.get_children()
        new_items = [i for i in items if self.tree.item(i)["values"][4] == "new"]
        
        if not new_items:
            messagebox.showinfo("Инфо", "Все записи уже синхронизированы")
            return
            
        if not messagebox.askyesno("Синхронизация", f"Отправить {len(new_items)} записей?"):
            return

        success_count = 0
        for item in new_items:
            row = self.tree.item(item)["values"]
            payload = {
                "date": row[0], 
                "note": row[1], 
                "category": row[2], 
                "amount": row[3]
            }
            try:
                res = requests.post(self.SCRIPT_URL, data=payload, timeout=7)
                if res.status_code == 200:
                    # Меняем статус на 'synced' и вешаем серый тег
                    new_vals = (row[0], row[1], row[2], row[3], "synced")
                    tags = list(self.tree.item(item, "tags"))
                    if 'synced' not in tags: tags.append('synced')
                    self.tree.item(item, values=new_vals, tags=tags)
                    success_count += 1
            except:
                continue
        
        self.save_data()
        messagebox.showinfo("Готово", f"Синхронизировано: {success_count}")

    def undo_last(self):
        items = self.tree.get_children()
        if items:
            self.tree.delete(items[-1])
            self.save_data()
            self.update_totals()
    def save_data(self):
        with open(self.filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            for item in self.tree.get_children():
                writer.writerow(self.tree.item(item)["values"])

    def update_totals(self):
        m_t, y_t, balance = 0.0, 0.0, 0.0
        now = datetime.now()
        cur_m = now.strftime(".%m.") # Ищем месяц, например ".04."
        cur_y = now.strftime("%Y")   # Ищем год, например "2026"
        
        for item in self.tree.get_children():
            row = self.tree.item(item)["values"]
            try:
                # ВАЖНО: Сумма теперь строго в row[3]!
                # Мы убираем пробелы и меняем запятую на точку
                v_raw = str(row[3]).replace(',', '.').strip()
                v = float(v_raw)
                
                # Общий баланс (считает вообще всё в таблице)
                balance += v
                
                # Дата у нас в row[0]
                dt = str(row[0])
                
                # Считаем за ГОД
                if cur_y in dt:
                    y_t += v
                
                # Считаем за МЕСЯЦ
                if cur_m in dt:
                    m_t += v
                    
            except Exception as e:
                # Если в строке ошибка, пропускаем её
                continue

        # Выводим результат на экран
        self.summary_var.set(
            f"Месяц: {m_t:.2f} | Год: {y_t:.2f} | БАЛАНС: {balance:.2f} руб.")
        
    def load_data(self):
        if os.path.exists(self.filename):
            with open(self.filename, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                for row in reader:
                    try:
                        if len(row) == 3: # Старый формат
                            d, c, v = row
                            n, s = "---", "synced"
                        elif len(row) >= 5: # Новый формат
                            d, n, c, v, s = row[:5]
                        else: continue
                        
                        val = float(str(v).replace(',', '.'))
                        tag = 'expense' if val < 0 else 'income'
                        tgs = (tag, 'synced') if s == "synced" else (tag,)
                        self.tree.insert("", "end", values=(d, n, c, f"{val:.2f}", s), tags=tgs)
                    except: continue
            self.update_totals()   
        with open(self.filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            for item in self.tree.get_children():
                writer.writerow(self.tree.item(item)["values"])

    def load_data(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        if os.path.exists(self.filename):
            with open(self.filename, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                for row in reader:
                    try:
                        # ЛОГИКА ПЕРЕХОДА С 3 НА 5 СТОЛБЦОВ:
                        if len(row) == 3:
                            # Если файл старый (Дата, Категория, Сумма)
                            d, c, v_raw = row
                            n, s = "---", "synced"  # Добавляем Заметку и Статус
                        elif len(row) == 5:
                            # Если файл уже новый (Дата, Заметка, Категория, Сумма, Статус)
                            d, n, c, v_raw, s = row
                        else:
                            continue

                        # Преобразование суммы в число
                        val = float(str(v_raw).replace(',', '.'))
                        
                        # Установка тегов (Цвет и Статус)
                        tag_type = 'expense' if val < 0 else 'income'
                        tags = (tag_type, 'synced') if s == "synced" else (tag_type,)
                        
                        # Вставка в таблицу (всегда 5 полей!)
                        self.tree.insert("", "end", values=(d, n, c, f"{val:.2f}", s), tags=tags)
                    except Exception as e:
                        print(f"Ошибка в строке {row}: {e}")
                        continue
            self.update_totals()

if __name__ == "__main__":
    root = tk.Tk()
    app = FinanceApp(root)
    root.mainloop()
