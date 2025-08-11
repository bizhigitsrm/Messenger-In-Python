#!/usr/bin/env python3
"""
Клиент мессенджера с графическим интерфейсом
Запустите этот файл на каждом устройстве для подключения к серверу
"""

import socket
import threading
import json
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from datetime import datetime

class MessengerClient:
    def __init__(self):
        self.client = None
        self.username = None
        self.connected = False
        self.active_users = []
        
        # Создаем главное окно
        self.root = tk.Tk()
        self.root.title("Мессенджер")
        self.root.geometry("800x600")
        
        # Настройка стиля
        self.setup_styles()
        
        # Создаем интерфейс подключения
        self.create_connection_screen()
        
    def setup_styles(self):
        """Настройка стилей интерфейса"""
        self.root.configure(bg='#2b2b2b')
        style = ttk.Style()
        style.theme_use('clam')
        
        # Темная тема
        style.configure('TFrame', background='#2b2b2b')
        style.configure('TLabel', background='#2b2b2b', foreground='white')
        style.configure('TButton', background='#4a4a4a', foreground='white')
        style.map('TButton', background=[('active', '#5a5a5a')])
    
    def create_connection_screen(self):
        """Создание экрана подключения"""
        # Очищаем окно
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Главный контейнер
        main_frame = ttk.Frame(self.root)
        main_frame.pack(expand=True)
        
        # Заголовок
        title = tk.Label(main_frame, text="МЕССЕНДЖЕР", 
                        font=("Arial", 24, "bold"),
                        bg='#2b2b2b', fg='#4CAF50')
        title.grid(row=0, column=0, columnspan=2, pady=20)
        
        # Поле для имени
        tk.Label(main_frame, text="Ваше имя:", 
                font=("Arial", 12),
                bg='#2b2b2b', fg='white').grid(row=1, column=0, padx=10, pady=10, sticky='e')
        
        self.name_entry = tk.Entry(main_frame, font=("Arial", 12), width=20,
                                   bg='#3a3a3a', fg='white', insertbackground='white')
        self.name_entry.grid(row=1, column=1, padx=10, pady=10)
        self.name_entry.insert(0, "User")
        
        # Поле для IP сервера
        tk.Label(main_frame, text="IP сервера:", 
                font=("Arial", 12),
                bg='#2b2b2b', fg='white').grid(row=2, column=0, padx=10, pady=10, sticky='e')
        
        self.ip_entry = tk.Entry(main_frame, font=("Arial", 12), width=20,
                                 bg='#3a3a3a', fg='white', insertbackground='white')
        self.ip_entry.grid(row=2, column=1, padx=10, pady=10)
        self.ip_entry.insert(0, "127.0.0.1")
        
        # Поле для порта
        tk.Label(main_frame, text="Порт:", 
                font=("Arial", 12),
                bg='#2b2b2b', fg='white').grid(row=3, column=0, padx=10, pady=10, sticky='e')
        
        self.port_entry = tk.Entry(main_frame, font=("Arial", 12), width=20,
                                   bg='#3a3a3a', fg='white', insertbackground='white')
        self.port_entry.grid(row=3, column=1, padx=10, pady=10)
        self.port_entry.insert(0, "5555")
        
        # Кнопка подключения
        connect_btn = tk.Button(main_frame, text="ПОДКЛЮЧИТЬСЯ", 
                               font=("Arial", 12, "bold"),
                               bg='#4CAF50', fg='white',
                               command=self.connect_to_server,
                               cursor="hand2")
        connect_btn.grid(row=4, column=0, columnspan=2, pady=20)
        
        # Информация
        info_text = "Для подключения к серверу в локальной сети\nиспользуйте IP адрес компьютера с сервером"
        info_label = tk.Label(main_frame, text=info_text,
                             font=("Arial", 10),
                             bg='#2b2b2b', fg='#888888')
        info_label.grid(row=5, column=0, columnspan=2, pady=10)
        
        # Bind Enter для подключения
        self.root.bind('<Return>', lambda e: self.connect_to_server())
    
    def connect_to_server(self):
        """Подключение к серверу"""
        self.username = self.name_entry.get().strip()
        host = self.ip_entry.get().strip()
        port = self.port_entry.get().strip()
        
        if not self.username:
            messagebox.showerror("Ошибка", "Введите имя пользователя")
            return
        
        try:
            port = int(port)
        except:
            messagebox.showerror("Ошибка", "Неверный порт")
            return
        
        try:
            # Создаем соединение
            self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client.connect((host, port))
            
            # Отправляем имя пользователя
            join_message = {
                'type': 'join',
                'username': self.username
            }
            self.client.send(json.dumps(join_message).encode('utf-8'))
            
            # Получаем подтверждение
            response = self.client.recv(1024).decode('utf-8')
            response = json.loads(response)
            
            if response['type'] == 'system':
                self.connected = True
                self.create_chat_screen()
                
                # Запускаем поток для получения сообщений
                receive_thread = threading.Thread(target=self.receive_messages)
                receive_thread.daemon = True
                receive_thread.start()
        
        except Exception as e:
            messagebox.showerror("Ошибка подключения", f"Не удалось подключиться к серверу:\n{str(e)}")
    
    def create_chat_screen(self):
        """Создание экрана чата"""
        # Очищаем окно
        for widget in self.root.winfo_children():
            widget.destroy()
        
        self.root.title(f"Мессенджер - {self.username}")
        
        # Главный контейнер
        main_frame = tk.Frame(self.root, bg='#2b2b2b')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Левая панель (список пользователей)
        left_panel = tk.Frame(main_frame, bg='#2b2b2b', width=200)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        
        tk.Label(left_panel, text="Пользователи онлайн",
                font=("Arial", 12, "bold"),
                bg='#2b2b2b', fg='#4CAF50').pack(pady=(0, 10))
        
        # Список пользователей
        self.users_listbox = tk.Listbox(left_panel, 
                                        bg='#3a3a3a', fg='white',
                                        font=("Arial", 11),
                                        selectbackground='#4CAF50',
                                        height=20)
        self.users_listbox.pack(fill=tk.BOTH, expand=True)
        
        # Правая панель (чат)
        right_panel = tk.Frame(main_frame, bg='#2b2b2b')
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Заголовок чата
        chat_header = tk.Frame(right_panel, bg='#3a3a3a', height=40)
        chat_header.pack(fill=tk.X, pady=(0, 10))
        
        self.chat_title = tk.Label(chat_header, text="Общий чат",
                                   font=("Arial", 14, "bold"),
                                   bg='#3a3a3a', fg='white')
        self.chat_title.pack(pady=8)
        
        # Область сообщений
        self.chat_area = scrolledtext.ScrolledText(right_panel,
                                                   bg='#3a3a3a', fg='white',
                                                   font=("Arial", 11),
                                                   wrap=tk.WORD,
                                                   state=tk.DISABLED)
        self.chat_area.pack(fill=tk.BOTH, expand=True)
        
        # Настройка тегов для разных типов сообщений
        self.chat_area.tag_config('system', foreground='#888888', font=("Arial", 10, "italic"))
        self.chat_area.tag_config('own', foreground='#4CAF50')
        self.chat_area.tag_config('other', foreground='white')
        self.chat_area.tag_config('private', foreground='#FF9800', font=("Arial", 11, "italic"))
        self.chat_area.tag_config('timestamp', foreground='#666666', font=("Arial", 9))
        
        # Панель ввода
        input_frame = tk.Frame(right_panel, bg='#2b2b2b')
        input_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Поле ввода сообщения
        self.message_entry = tk.Entry(input_frame,
                                      bg='#3a3a3a', fg='white',
                                      font=("Arial", 12),
                                      insertbackground='white')
        self.message_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Кнопка отправки
        send_btn = tk.Button(input_frame, text="Отправить",
                            font=("Arial", 11, "bold"),
                            bg='#4CAF50', fg='white',
                            command=self.send_message,
                            cursor="hand2")
        send_btn.pack(side=tk.RIGHT, padx=(10, 0))
        
        # Кнопка приватного сообщения
        private_btn = tk.Button(input_frame, text="Приватно",
                               font=("Arial", 11),
                               bg='#FF9800', fg='white',
                               command=self.send_private_message,
                               cursor="hand2")
        private_btn.pack(side=tk.RIGHT, padx=(10, 0))
        
        # Bind Enter для отправки
        self.message_entry.bind('<Return>', lambda e: self.send_message())
        
        # Bind для закрытия окна
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Фокус на поле ввода
        self.message_entry.focus()
    
    def send_message(self):
        """Отправка сообщения"""
        text = self.message_entry.get().strip()
        if text and self.connected:
            message = {
                'type': 'message',
                'text': text
            }
            try:
                self.client.send(json.dumps(message).encode('utf-8'))
                self.message_entry.delete(0, tk.END)
            except:
                self.add_message("Ошибка отправки сообщения", msg_type='system')
    
    def send_private_message(self):
        """Отправка приватного сообщения"""
        selection = self.users_listbox.curselection()
        if not selection:
            messagebox.showwarning("Внимание", "Выберите пользователя из списка")
            return
        
        target = self.users_listbox.get(selection[0])
        text = self.message_entry.get().strip()
        
        if text and self.connected:
            message = {
                'type': 'private',
                'text': text,
                'target': target
            }
            try:
                self.client.send(json.dumps(message).encode('utf-8'))
                self.message_entry.delete(0, tk.END)
            except:
                self.add_message("Ошибка отправки сообщения", msg_type='system')
    
    def receive_messages(self):
        """Получение сообщений от сервера"""
        while self.connected:
            try:
                data = self.client.recv(1024).decode('utf-8')
                if not data:
                    break
                
                message = json.loads(data)
                
                if message['type'] == 'message':
                    # Обычное сообщение
                    sender = message['username']
                    text = message['text']
                    timestamp = message.get('timestamp', '')
                    
                    if sender == self.username:
                        self.add_message(f"[{timestamp}] Вы: {text}", msg_type='own')
                    else:
                        self.add_message(f"[{timestamp}] {sender}: {text}", msg_type='other')
                
                elif message['type'] == 'private':
                    # Приватное сообщение
                    sender = message['username']
                    text = message['text']
                    timestamp = message.get('timestamp', '')
                    target = message.get('target', '')
                    
                    if sender == self.username:
                        self.add_message(f"[{timestamp}] [Приватно для {target}] Вы: {text}", msg_type='private')
                    else:
                        self.add_message(f"[{timestamp}] [Приватно] {sender}: {text}", msg_type='private')
                
                elif message['type'] == 'system':
                    # Системное сообщение
                    self.add_message(message['message'], msg_type='system')
                
                elif message['type'] == 'user_joined':
                    # Пользователь присоединился
                    self.add_message(f"✓ {message['message']}", msg_type='system')
                
                elif message['type'] == 'user_left':
                    # Пользователь покинул чат
                    self.add_message(f"✗ {message['message']}", msg_type='system')
                
                elif message['type'] == 'user_list':
                    # Обновление списка пользователей
                    self.update_user_list(message['users'])
            
            except Exception as e:
                if self.connected:
                    self.add_message(f"Ошибка: {str(e)}", msg_type='system')
                break
        
        # Отключение
        if self.connected:
            self.connected = False
            self.add_message("Отключено от сервера", msg_type='system')
    
    def add_message(self, text, msg_type='other'):
        """Добавление сообщения в чат"""
        self.chat_area.config(state=tk.NORMAL)
        self.chat_area.insert(tk.END, text + '\n', msg_type)
        self.chat_area.config(state=tk.DISABLED)
        self.chat_area.see(tk.END)
    
    def update_user_list(self, users):
        """Обновление списка пользователей"""
        self.users_listbox.delete(0, tk.END)
        for user in users:
            if user != self.username:
                self.users_listbox.insert(tk.END, user)
    
    def on_closing(self):
        """Обработка закрытия окна"""
        if self.connected and self.client:
            self.connected = False
            try:
                self.client.close()
            except:
                pass
        self.root.destroy()
    
    def run(self):
        """Запуск приложения"""
        self.root.mainloop()

if __name__ == "__main__":
    app = MessengerClient()
    app.run()