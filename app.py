from flask import Flask, render_template, request, jsonify
import sqlite3
import random
import os

app = Flask(__name__)

DB_FILE = 'database.db'

def init_db():
    if not os.path.exists(DB_FILE):
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute('''
            CREATE TABLE players (
                id INTEGER PRIMARY PRIMARY KEY,
                name TEXT,
                position TEXT,
                confirmed INTEGER
            )
        ''')
        for i in range(1, 28):
            c.execute('INSERT INTO players (id, name, position, confirmed) VALUES (?, ?, ?, ?)',
                    (i, '', 'linha', 0)) # Default position to 'linha'
        conn.commit()
        conn.close()

def get_players():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT * FROM players ORDER BY id ASC') # Ensure consistent order
    players = c.fetchall()
    conn.close()
    return players

@app.route('/')
def index():
    return render_template('index.html', players=get_players())

@app.route('/update_player', methods=['POST'])
def update_player():
    data = request.get_json()
    player_id = data['id']
    name = data['name'].strip() # Trim whitespace
    position = data['position']
    confirmed = 1 if data['confirmed'] else 0

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('UPDATE players SET name = ?, position = ?, confirmed = ? WHERE id = ?',
              (name, position, confirmed, player_id))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/merge', methods=['POST'])
def merge():
    players = get_players()
    confirmed_players = [p for p in players if p[3] == 1 and p[1].strip()] # Confirmed and has a name

    if len(confirmed_players) < 14:
        return jsonify({'success': False, 'msg': 'Número insuficiente de jogadores confirmados para formar 2 times de 7.'})

    goleiros_disponiveis = [p for p in confirmed_players if p[2] == 'gol']
    linha_disponiveis = [p for p in confirmed_players if p[2] == 'linha']

    # Lógica para garantir goleiros nos times
    # Garante que cada time tenha um goleiro, preferencialmente da posição 'gol'
    # Se não houver goleiros suficientes, pega da 'linha'
    goleiros_finais = []
    jogadores_restantes_linha = []

    # Prioriza goleiros com a posição 'gol'
    for p in goleiros_disponiveis:
        goleiros_finais.append(p)
    
    # Se ainda precisar de goleiros, pegue da linha
    if len(goleiros_finais) < 2: # Mínimo de 2 goleiros para 2 times
        necessita_goleiros = 2 - len(goleiros_finais)
        for _ in range(min(necessita_goleiros, len(linha_disponiveis))):
            goleiros_finais.append(linha_disponiveis.pop(random.randrange(len(linha_disponiveis))))
    
    # O restante dos jogadores de linha
    jogadores_restantes_linha.extend(linha_disponiveis)

    # Verifica se há jogadores suficientes para formar times (goleiros + pelo menos 6 de linha por time)
    if len(goleiros_finais) < 2 or len(jogadores_restantes_linha) < 12: # 2 goleiros e 12 de linha para 2 times
        return jsonify({'success': False, 'msg': 'Não há jogadores suficientes para formar 2 times completos (2 goleiros e 12 jogadores de linha).'})

    random.shuffle(goleiros_finais)
    random.shuffle(jogadores_restantes_linha)

    max_times = min(len(goleiros_finais), len(jogadores_restantes_linha) // 6)
    if max_times == 0:
        return jsonify({'success': False, 'msg': 'Não é possível formar times com a distribuição atual de goleiros e jogadores de linha.'})

    times_nomes = ['Time Azul', 'Time Vermelho', 'Time Amarelo', 'Time Verde'][:max_times]
    times = {nome: [] for nome in times_nomes}

    # Distribui os goleiros
    for i in range(max_times):
        times[times_nomes[i]].append(goleiros_finais[i])

    # Distribui os jogadores de linha restantes
    idx_jogador = 0
    while idx_jogador < len(jogadores_restantes_linha):
        for i in range(max_times):
            if idx_jogador < len(jogadores_restantes_linha):
                times[times_nomes[i]].append(jogadores_restantes_linha[idx_jogador])
                idx_jogador += 1
            else:
                break # Sai do loop interno se todos os jogadores foram distribuídos

    return jsonify({'success': True, 'times': times})

@app.route('/clear_list', methods=['POST'])
def clear_list():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('UPDATE players SET name = ?, position = ?, confirmed = ?', ('', 'linha', 0))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

if __name__ == '__main__':
    init_db()
    app.run(debug=True)