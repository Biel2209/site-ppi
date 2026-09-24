import sqlite3


def criar_banco():

    conexao = sqlite3.connect("mapa_cidade.db")

    cursor = conexao.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS relatos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo TEXT NOT NULL,
            descricao TEXT NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            status TEXT NOT NULL DEFAULT 'Em análise',
            data TEXT NOT NULL
        )
    """)

    conexao.commit()
    conexao.close()


criar_banco()