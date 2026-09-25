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

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            senha_hash TEXT NOT NULL,
            data_criacao TEXT NOT NULL
        )
    """)

    cursor.execute("""
        PRAGMA table_info(relatos)
    """)

    colunas = cursor.fetchall()

    nomes_colunas = []

    for coluna in colunas:
        nomes_colunas.append(coluna[1])

    if "usuario_id" not in nomes_colunas:

        cursor.execute("""
            ALTER TABLE relatos
            ADD COLUMN usuario_id INTEGER
        """)

    conexao.commit()
    conexao.close()


criar_banco()