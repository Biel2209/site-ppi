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
#users
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        senha_hash TEXT NOT NULL,
        data_criacao TEXT NOT NULL,
        perfil TEXT NOT NULL DEFAULT 'usuario'
    )
""")

    cursor.execute("""
        PRAGMA table_info(usuarios)
    """)

    colunas_usuarios = cursor.fetchall()
    nomes_colunas_usuarios = []

    for coluna in colunas_usuarios:
        nomes_colunas_usuarios.append(coluna[1])

    if "perfil" not in nomes_colunas_usuarios:

        cursor.execute("""
            ALTER TABLE usuarios
            ADD COLUMN perfil TEXT NOT NULL DEFAULT 'usuario'
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

    # TABELA DE OBRAS

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS obras (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            localizacao TEXT NOT NULL,
            status TEXT NOT NULL,
            previsao TEXT,
            descricao TEXT,
            latitude REAL,
            longitude REAL
        )
    """)

    # VERIFICA SE JÁ EXISTEM OBRAS

    cursor.execute("""
        SELECT COUNT(*)
        FROM obras
    """)

    quantidade_obras = cursor.fetchone()[0]

    # CADASTRA AS OBRAS APENAS SE O BANCO ESTIVER VAZIO

    if quantidade_obras == 0:

        cursor.execute("""
            INSERT INTO obras
            (titulo, localizacao, status, previsao, descricao, latitude, longitude)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            "Pavimentação da rua",
            "Centro",
            "Em andamento",
            "Dezembro/2026",
            "Obra de pavimentação e melhoria da via.",
            -20.4695,
            -55.7860
        ))

        cursor.execute("""
            INSERT INTO obras
            (titulo, localizacao, status, previsao, descricao, latitude, longitude)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            "Reforma da praça",
            "Alto",
            "Concluída",
            "Setembro/2026",
            "Reforma e revitalização da praça.",
            -20.4730,
            -55.7890
        ))

        cursor.execute("""
            INSERT INTO obras
            (titulo, localizacao, status, previsao, descricao, latitude, longitude)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            "Melhoria na iluminação",
            "Nova Aquidauana",
            "Em análise",
            None,
            "Avaliação para melhoria da iluminação pública.",
            -20.4660,
            -55.7830
        ))

        cursor.execute("""
            INSERT INTO obras
            (titulo, localizacao, status, previsao, descricao, latitude, longitude)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            "Manutenção da via",
            "Guanandi",
            "Em andamento",
            "Novembro/2026",
            "Manutenção e recuperação da via.",
            -20.4780,
            -55.7920
        ))

    conexao.commit()
    conexao.close()


criar_banco()

email_admin = "adm@exemplo.com"

conexao = sqlite3.connect("mapa_cidade.db")
cursor = conexao.cursor()

cursor.execute("""
    UPDATE usuarios
    SET perfil = 'admin'
    WHERE email = ?
""", (email_admin,))

conexao.commit()
conexao.close()