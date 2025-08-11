#!/usr/bin/env python3
"""
Сервер для мессенджера
Запустите этот файл первым на одном компьютере
"""

import socket
import threading
import json
from datetime import datetime

class ChatServer:
    def __init__(self, host='0.0.0.0', port=5555):
        self.host = host
        self.port = port
        self.clients = {}  # {client_socket: {'username': str, 'address': tuple}}
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
    def start(self):
        """Запуск сервера"""
        self.server.bind((self.host, self.port))
        self.server.listen(5)
        print(f"[СЕРВЕР] Запущен на {self.host}:{self.port}")
        print(f"[СЕРВЕР] IP адрес сервера: {self.get_local_ip()}")
        
        # Поток для принятия новых подключений
        accept_thread = threading.Thread(target=self.accept_clients)
        accept_thread.daemon = True
        accept_thread.start()
        
        # Основной цикл сервера
        try:
            while True:
                command = input()
                if command.lower() == 'exit':
                    break
                elif command.lower() == 'users':
                    self.show_users()
        except KeyboardInterrupt:
            pass
        finally:
            self.shutdown()
    
    def get_local_ip(self):
        """Получение локального IP адреса"""
        try:
            # Создаем временное соединение для определения IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"
    
    def accept_clients(self):
        """Принятие новых клиентов"""
        while True:
            try:
                client_socket, address = self.server.accept()
                print(f"[ПОДКЛЮЧЕНИЕ] Новое подключение от {address}")
                
                # Запускаем поток для обработки клиента
                client_thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket, address)
                )
                client_thread.daemon = True
                client_thread.start()
            except:
                break
    
    def handle_client(self, client_socket, address):
        """Обработка сообщений от клиента"""
        try:
            # Получаем имя пользователя
            data = client_socket.recv(1024).decode('utf-8')
            message = json.loads(data)
            
            if message['type'] == 'join':
                username = message['username']
                self.clients[client_socket] = {
                    'username': username,
                    'address': address
                }
                
                print(f"[ПОЛЬЗОВАТЕЛЬ] {username} присоединился к чату")
                
                # Отправляем подтверждение
                response = {
                    'type': 'system',
                    'message': 'Успешно подключено к серверу',
                    'timestamp': datetime.now().strftime('%H:%M:%S')
                }
                client_socket.send(json.dumps(response).encode('utf-8'))
                
                # Уведомляем всех о новом пользователе
                self.broadcast({
                    'type': 'user_joined',
                    'username': username,
                    'message': f'{username} присоединился к чату',
                    'timestamp': datetime.now().strftime('%H:%M:%S')
                }, exclude_client=client_socket)
                
                # Отправляем список активных пользователей
                self.send_user_list()
                
                # Обрабатываем сообщения от клиента
                while True:
                    data = client_socket.recv(1024).decode('utf-8')
                    if not data:
                        break
                    
                    message = json.loads(data)
                    
                    if message['type'] == 'message':
                        # Добавляем информацию об отправителе
                        message['username'] = username
                        message['timestamp'] = datetime.now().strftime('%H:%M:%S')
                        
                        print(f"[СООБЩЕНИЕ] {username}: {message['text']}")
                        
                        # Рассылаем всем клиентам
                        self.broadcast(message)
                    
                    elif message['type'] == 'private':
                        # Приватное сообщение
                        target_user = message['target']
                        message['username'] = username
                        message['timestamp'] = datetime.now().strftime('%H:%M:%S')
                        
                        self.send_private_message(message, target_user, client_socket)
        
        except Exception as e:
            print(f"[ОШИБКА] {e}")
        
        finally:
            # Удаляем клиента при отключении
            if client_socket in self.clients:
                username = self.clients[client_socket]['username']
                del self.clients[client_socket]
                
                print(f"[ОТКЛЮЧЕНИЕ] {username} покинул чат")
                
                # Уведомляем остальных
                self.broadcast({
                    'type': 'user_left',
                    'username': username,
                    'message': f'{username} покинул чат',
                    'timestamp': datetime.now().strftime('%H:%M:%S')
                })
                
                self.send_user_list()
            
            client_socket.close()
    
    def broadcast(self, message, exclude_client=None):
        """Отправка сообщения всем клиентам"""
        message_json = json.dumps(message)
        for client in list(self.clients.keys()):
            if client != exclude_client:
                try:
                    client.send(message_json.encode('utf-8'))
                except:
                    # Удаляем клиента если не можем отправить
                    if client in self.clients:
                        del self.clients[client]
    
    def send_private_message(self, message, target_username, sender_socket):
        """Отправка приватного сообщения"""
        message_json = json.dumps(message)
        sent = False
        
        for client, info in self.clients.items():
            if info['username'] == target_username:
                try:
                    client.send(message_json.encode('utf-8'))
                    # Отправляем копию отправителю
                    sender_socket.send(message_json.encode('utf-8'))
                    sent = True
                    break
                except:
                    pass
        
        if not sent:
            error_msg = {
                'type': 'system',
                'message': f'Пользователь {target_username} не найден',
                'timestamp': datetime.now().strftime('%H:%M:%S')
            }
            sender_socket.send(json.dumps(error_msg).encode('utf-8'))
    
    def send_user_list(self):
        """Отправка списка активных пользователей всем клиентам"""
        users = [info['username'] for info in self.clients.values()]
        message = {
            'type': 'user_list',
            'users': users,
            'timestamp': datetime.now().strftime('%H:%M:%S')
        }
        self.broadcast(message)
    
    def show_users(self):
        """Показать список подключенных пользователей"""
        if self.clients:
            print("\n[АКТИВНЫЕ ПОЛЬЗОВАТЕЛИ]")
            for client, info in self.clients.items():
                print(f"  - {info['username']} ({info['address'][0]}:{info['address'][1]})")
        else:
            print("[АКТИВНЫЕ ПОЛЬЗОВАТЕЛИ] Нет подключенных пользователей")
    
    def shutdown(self):
        """Завершение работы сервера"""
        print("\n[СЕРВЕР] Завершение работы...")
        
        # Уведомляем всех о закрытии сервера
        self.broadcast({
            'type': 'system',
            'message': 'Сервер завершает работу',
            'timestamp': datetime.now().strftime('%H:%M:%S')
        })
        
        # Закрываем все соединения
        for client in list(self.clients.keys()):
            client.close()
        
        self.server.close()
        print("[СЕРВЕР] Остановлен")

if __name__ == "__main__":
    print("=" * 50)
    print("СЕРВЕР МЕССЕНДЖЕРА")
    print("=" * 50)
    print("\nКоманды:")
    print("  users - показать список подключенных пользователей")
    print("  exit  - остановить сервер")
    print("\n" + "=" * 50)
    
    server = ChatServer()
    server.start()