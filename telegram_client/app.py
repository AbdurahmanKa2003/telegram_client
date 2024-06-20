from flask import Flask, jsonify, request
from telethon import TelegramClient
import asyncio
import requests
from bs4 import BeautifulSoup
import os

app = Flask(__name__)

api_id = 26667243
api_hash = 'dfde9a64f90a64d09ce142929a0858a'


if os.path.exists('session_name.session'):
    os.remove('session_name.session')

client = TelegramClient('session_name', api_id, api_hash)

@app.route('/')
def index():
    return "Hello, this is the home page!"

@app.route('/login', methods=['POST'])
def login():
    async def generate_qr():
        await client.connect()
        qr_code = await client.qr_login()
        return jsonify({"qr_link_url": qr_code.url})

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    qr_data = loop.run_until_complete(generate_qr())
    return qr_data

@app.route('/messages', methods=['GET'])
def get_messages():
    phone = request.args.get('phone')
    uname = request.args.get('uname')

    async def fetch_messages():
        messages = []
        async for dialog in client.iter_dialogs():
            if dialog.name == uname:
                async for message in client.iter_messages(dialog.id, limit=50):
                    messages.append({
                        "username": dialog.name,
                        "is_self": message.out,
                        "message_text": message.message
                    })
        return messages

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    messages_data = loop.run_until_complete(fetch_messages())
    return jsonify({"messages": messages_data})

@app.route('/send_message', methods=['POST'])
def send_message():
    data = request.get_json()
    message_text = data['message_text']
    from_phone = data['from_phone']
    username = data['username']

    async def send_text():
        await client.send_message(username, message_text)
        return {"status": "ok"}

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    send_status = loop.run_until_complete(send_text())
    return jsonify(send_status)

@app.route('/wild', methods=['GET'])
def wild_search():
    query = request.args.get('query')
    url = f"https://www.wildberries.ru/catalog/0/search.aspx?search={query}"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    items = soup.find_all('div', {'class': 'product-card'})

    products = []
    for item in items[:10]:  # Limiting to 10 items
        title = item.find('span', {'class': 'goods-name'}).text
        link = item.find('a', {'class': 'j-open-full-product-card'})['href']
        products.append({"title": title, "link": f"https://www.wildberries.ru{link}"})

    async def send_products():
        for product in products:
            await client.send_message('your_telegram_username', f"{product['title']}\n{product['link']}")

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(send_products())
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)
