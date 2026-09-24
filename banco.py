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

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS fotos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        relato_id INTEGER NOT NULL,
        arquivo TEXT NOT NULL,
        FOREIGN KEY (relato_id) REFERENCES relatos(id)
    )
""")
    
    conexao.commit()
    conexao.close()


criar_banco()