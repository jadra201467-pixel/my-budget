import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
import os
import csv
import requests
from datetime import datetime

class FinanceApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Мой Бюджет 2026 — Витрина")
        self.root.geometry("1000x750")
        self.root.configure(bg="#2b2b2b")
        
        base_path = os.path.dirname(os.path.abspath(__file__))
        self.filename = os.path.join(base_path, "budget_data.csv")
        
        # --- БЕЗОПАСНАЯ ЗАГЛУШКА ---
        # В публичной версии реальный URL скрыт. 
        self.SCRIPT_URL = "https://google.com"
        
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", background="#2b2b2b", foreground="white", fieldbackground="#2b2b2b", rowheight=25)
        style.configure("Treeview.Heading", background="#3c3f41", foreground="white", relief="flat")
        style.map("Treeview", background=[('selected', '#4a4a4a')])

        self.left_panel = tk.Frame(self.root, bg="#3c3f41", width=280)
        self.left_panel.pack(side="left", fill="y", padx=5, pady=5)
        self.left_panel.pack_propagate(False)

        # Поля ввода
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
        self.incomes_list = ["сестра Саша", "я", "Владимир"]
        self.income_cb = ttk.Combobox(self.left_panel, values=self.incomes_list)
        self.income_cb.pack(padx=10, fill="x")
        self.income_cb.bind("<<ComboboxSelected>>", self.on_income_select)

        tk.Label(self.left_panel, text="Сумма", bg="#3c3f41", fg="white").pack(pady=(15,0))
        self.amount_entry = tk.Entry(self.left_panel, justify='center', font=("Arial", 12, "bold"))
        self.amount_entry.pack(padx=10, fill="x")

        # Кнопки
        tk.Button(self.left_panel, text="СОХРАНИТЬ", bg="#28a745", fg="white", font=("Arial", 10, "bold"), command=self.add_transaction).pack(fill="x", padx=10, pady=20)
        tk.Button(self.left_panel, text="☁ СИНХРОНИЗАЦИЯ", bg="#007bff", fg="white", font=("Arial", 9, "bold"), command=self.sync_all_to_google).pack(fill="x", padx=10, pady=5)
        tk.Button(self.left_panel, text="УДАЛИТЬ ПОСЛЕДНЕЕ", bg="#c82333", fg="white", command=self.undo_last).pack(fill="x", padx=10, pady=5)

        # Таблица
        self.tree = ttk.Treeview(self.root, columns=("date", "note", "category", "amount", "status"), show='headings')
        self.tree.heading("date", text="Дата")
        self.tree.heading("note", text="Заметка")
        self.tree.heading("category", text="Категория")
        self.tree.heading("amount", text="Сумма")
        self.tree.heading("status", text="Статус")
        
        self.tree.column("status", width=80, anchor="center")
        
        self.tree.tag_configure('expense', foreground='#ff6666')
        self.tree.tag_configure('income', foreground='#66ff66')
        self.tree.tag_configure('synced', foreground='#888888')
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
            status = "new"
            tag = 'expense' if val < 0 else 'income'
            self.tree.insert("", "end", values=(date, note, category, f"{val:.2f}", status), tags=(tag,))
            self.save_data()
            self.update_totals()
            self.amount_entry.delete(0, tk.END)
            self.note_entry.delete(0, tk.END)
            self.expense_cb.set('')
            self.income_cb.set('')
        except ValueError:
            messagebox.showerror("Ошибка", "Введите число")

    def sync_all_to_google(self):
        if "PUBLIC_DEMO_URL" in self.SCRIPT_URL:
            messagebox.showinfo("Демо-режим", "Синхронизация отключена для безопасности автора.")
            return
        # Здесь была бы реальная логика отправки

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
        m_t, y_t = 0.0, 0.0
        now = datetime.now()
        cur_m = now.strftime(".%m.")
        cur_y = now.strftime("%Y")
        
        for item in self.tree.get_children():
            row = self.tree.item(item)["values"]
            try:
                date_str = str(row[0])
                amount = float(row[3])
                if cur_y in date_str:
                    y_t += amount
                    if cur_m in date_str:
                        m_t += amount
            except: continue
        self.summary_var.set(f"За месяц: {m_t:.2f} | За год: {y_t:.2f} руб.")

    def load_data(self):
        if not os.path.exists(self.filename): return
        try:
            with open(self.filename, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                for row in reader:
                    if len(row) < 5: continue
                    tag = 'synced' if row[4] == "synced" else ('expense' if float(row[3]) < 0 else 'income')
                    self.tree.insert("", "end", values=row, tags=(tag,))
            self.update_totals()
        except: pass

if __name__ == "__main__":
    root = tk.Tk()
    app = FinanceApp(root)
    root.mainloop()
