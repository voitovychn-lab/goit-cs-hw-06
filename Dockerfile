
# Використовуємо Python
FROM python:3.11

# Робоча папка всередині контейнера
WORKDIR /app

# Копіюємо файли проєкту
COPY . .

# Встановлюємо бібліотеку для MongoDB
RUN pip install pymongo

# Відкриваємо порти HTTP та Socket-сервера
EXPOSE 3000
EXPOSE 5000

# Запускаємо вебдодаток
CMD ["python", "main.py"]
