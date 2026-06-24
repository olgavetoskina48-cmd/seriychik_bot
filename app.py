from flask import Flask, send_from_directory, request, jsonify
import sqlite3
import os

app = Flask(__name__, static_folder='webapp')

# --- БАЗА ДАННЫХ (общая с ботом) ---
def get_pet(user_id):
    conn = sqlite3.connect('pets.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM pets WHERE user_id = ?', (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            'голод': row[1],
            'счастье': row[2],
            'гигиена': row[3],
            'энергия': row[4],
            'дисциплина': row[5],
            'дни': row[6],
            'одежда': row[7],
            'age': row[8],
            'total_messages': row[9],
            'stage': row[10],
            'pet_type': row[11]
        }
    return None

def update_pet(user_id, field, value):
    conn = sqlite3.connect('pets.db')
    cursor = conn.cursor()
    cursor.execute(f'UPDATE pets SET {field} = ? WHERE user_id = ?', (value, user_id))
    conn.commit()
    conn.close()

# --- ОТДАЁМ ГЛАВНУЮ СТРАНИЦУ ---
@app.route('/')
def index():
    return send_from_directory('webapp', 'index.html')

# --- API: ПОЛУЧИТЬ ДАННЫЕ ПИТОМЦА ---
@app.route('/api/pet/<int:user_id>')
def api_pet(user_id):
    pet = get_pet(user_id)
    if not pet:
        return jsonify({'error': 'Нет питомца'}), 404
    return jsonify(pet)

# --- API: ПОКОРМИТЬ ---
@app.route('/api/feed/<int:user_id>', methods=['POST'])
def api_feed(user_id):
    pet = get_pet(user_id)
    if not pet:
        return jsonify({'error': 'Нет питомца'}), 404
    new_val = min(100, pet['голод'] + 20)
    update_pet(user_id, 'голод', new_val)
    return jsonify({'голод': new_val})

# --- API: ПОИГРАТЬ ---
@app.route('/api/play/<int:user_id>', methods=['POST'])
def api_play(user_id):
    pet = get_pet(user_id)
    if not pet:
        return jsonify({'error': 'Нет питомца'}), 404
    new_s = min(100, pet['счастье'] + 15)
    new_e = max(0, pet['энергия'] - 10)
    update_pet(user_id, 'счастье', new_s)
    update_pet(user_id, 'энергия', new_e)
    return jsonify({'счастье': new_s, 'энергия': new_e})

# --- API: ПЕРЕОДЕТЬ ---
@app.route('/api/dress/<int:user_id>', methods=['POST'])
def api_dress(user_id):
    pet = get_pet(user_id)
    if not pet:
        return jsonify({'error': 'Нет питомца'}), 404
    options = ["без одежды", "шапка 🧢", "шарф 🧣", "очки 🕶️", "плащ 🧥"]
    current = pet['одежда']
    idx = options.index(current) if current in options else 0
    new_idx = (idx + 1) % len(options)
    update_pet(user_id, 'одежда', options[new_idx])
    return jsonify({'одежда': options[new_idx]})

# --- ЗАПУСК ---
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
