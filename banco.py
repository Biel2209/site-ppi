"""Database connection and idempotent schema setup."""

import os
import re
import sqlite3

import psycopg2
from psycopg2.extras import RealDictCursor


class Linha(dict):
    """Row supporting SQLite-style positional and named access."""

    def __getitem__(self, chave):
        if isinstance(chave, int):
            return tuple(self.values())[chave]
        return super().__getitem__(chave)


def _traduzir_placeholders(sql):
    """Translate parameter markers outside SQL strings and comments."""
    resultado = []
    aspas = None
    comentario_linha = False
    comentario_bloco = False
    i = 0
    while i < len(sql):
        atual = sql[i]
        seguinte = sql[i + 1] if i + 1 < len(sql) else ""
        if comentario_linha:
            resultado.append(atual)
            if atual == "\n":
                comentario_linha = False
        elif comentario_bloco:
            resultado.append(atual)
            if atual == "*" and seguinte == "/":
                resultado.append(seguinte)
                i += 1
                comentario_bloco = False
        elif aspas:
            resultado.append(atual)
            if atual == aspas:
                if seguinte == aspas:
                    resultado.append(seguinte)
                    i += 1
                else:
                    aspas = None
        elif atual in ("'", '"'):
            aspas = atual
            resultado.append(atual)
        elif atual == "-" and seguinte == "-":
            resultado.extend((atual, seguinte))
            i += 1
            comentario_linha = True
        elif atual == "/" and seguinte == "*":
            resultado.extend((atual, seguinte))
            i += 1
            comentario_bloco = True
        elif atual == "?":
            resultado.append("%s")
        else:
            resultado.append(atual)
        i += 1
    return "".join(resultado)


class CursorPostgres:
    def __init__(self, cursor):
        self._cursor = cursor
        self._lastrowid = None

    @property
    def rowcount(self):
        return self._cursor.rowcount

    @property
    def lastrowid(self):
        return self._lastrowid

    def execute(self, sql, parametros=None):
        sql_postgres = _traduzir_placeholders(sql)
        if re.match(r"\s*INSERT\s+INTO\s+(usuarios|relatos)\b", sql_postgres, re.IGNORECASE):
            sql_postgres = sql_postgres.rstrip().rstrip(";") + " RETURNING id"
            self._cursor.execute(sql_postgres, parametros or ())
            linha_id = self._cursor.fetchone()
            self._lastrowid = linha_id["id"] if linha_id else None
        else:
            self._cursor.execute(sql_postgres, parametros or ())
        return self

    def _linha(self, linha):
        return Linha(linha) if linha is not None else None

    def fetchone(self):
        return self._linha(self._cursor.fetchone())

    def fetchall(self):
        return [self._linha(linha) for linha in self._cursor.fetchall()]


class ConexaoPostgres:
    def __init__(self, conexao):
        self._conexao = conexao
        self.is_postgres = True
        self.row_factory = None  # Keep legacy calls independent of sqlite3.Row.

    def cursor(self):
        return CursorPostgres(self._conexao.cursor())

    def execute(self, sql, parametros=None):
        return self.cursor().execute(sql, parametros)

    def commit(self):
        self._conexao.commit()

    def rollback(self):
        self._conexao.rollback()

    def close(self):
        self._conexao.close()


def usando_postgres():
    return bool(os.environ.get("DATABASE_URL", "").strip())


def conectar_banco():
    url = os.environ.get("DATABASE_URL", "").strip()
    if url:
        return ConexaoPostgres(psycopg2.connect(
            url, cursor_factory=RealDictCursor, sslmode="require"
        ))
    conexao = sqlite3.connect(os.path.join(os.path.dirname(__file__), "mapa_cidade.db"))
    conexao.row_factory = sqlite3.Row
    conexao.execute("PRAGMA foreign_keys = ON")
    return conexao


ERROS_BANCO = (sqlite3.Error, psycopg2.Error)
ERRO_INTEGRIDADE = (sqlite3.IntegrityError, psycopg2.IntegrityError)


def _colunas(conexao, tabela):
    if usando_postgres():
        return {linha[0] for linha in conexao.execute(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_schema = current_schema() AND table_name = ?", (tabela,)
        ).fetchall()}
    return {linha[1] for linha in conexao.execute(f"PRAGMA table_info({tabela})").fetchall()}


def _garantir_colunas(conexao, tabela, definicoes):
    existentes = _colunas(conexao, tabela)
    for nome, definicao in definicoes.items():
        if nome not in existentes:
            conexao.execute(f"ALTER TABLE {tabela} ADD COLUMN {nome} {definicao}")


def preparar_colunas_verificacao(conexao):
    _garantir_colunas(conexao, "usuarios", {
        "email_verificado": "INTEGER NOT NULL DEFAULT 1",
        "codigo_verificacao_hash": "TEXT",
        "codigo_expira_em": "TEXT",
        "codigo_ultimo_envio_em": "TEXT",
        "codigo_tentativas": "INTEGER NOT NULL DEFAULT 0",
    })


def _inicializar_sqlite(conexao):
    comandos = [
        """CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE, senha_hash TEXT NOT NULL,
            data_criacao TEXT NOT NULL, perfil TEXT NOT NULL DEFAULT 'usuario')""",
        """CREATE TABLE IF NOT EXISTS obras (
            id INTEGER PRIMARY KEY AUTOINCREMENT, titulo TEXT NOT NULL,
            localizacao TEXT NOT NULL, status TEXT NOT NULL, previsao TEXT,
            descricao TEXT, latitude REAL, longitude REAL)""",
        """CREATE TABLE IF NOT EXISTS relatos (
            id INTEGER PRIMARY KEY AUTOINCREMENT, tipo TEXT NOT NULL,
            descricao TEXT NOT NULL, latitude REAL NOT NULL, longitude REAL NOT NULL,
            status TEXT NOT NULL DEFAULT 'Em \u00e1n\u00e1lise', data TEXT NOT NULL,
            usuario_id INTEGER, rua TEXT, bairro TEXT)""",
        """CREATE TABLE IF NOT EXISTS fotos (
            id INTEGER PRIMARY KEY AUTOINCREMENT, relato_id INTEGER NOT NULL,
            arquivo TEXT NOT NULL, FOREIGN KEY (relato_id) REFERENCES relatos(id) ON DELETE CASCADE)""",
        """CREATE TABLE IF NOT EXISTS feedbacks (
            id INTEGER PRIMARY KEY AUTOINCREMENT, usuario_id INTEGER NOT NULL,
            nota INTEGER NOT NULL CHECK (nota BETWEEN 1 AND 5), comentario TEXT NOT NULL,
            data_criacao TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE)""",
    ]
    for comando in comandos:
        conexao.execute(comando)
    _garantir_colunas(conexao, "usuarios", {
        "perfil": "TEXT NOT NULL DEFAULT 'usuario'",
        "email_verificado": "INTEGER NOT NULL DEFAULT 1",
        "codigo_verificacao_hash": "TEXT", "codigo_expira_em": "TEXT",
        "codigo_ultimo_envio_em": "TEXT", "codigo_tentativas": "INTEGER NOT NULL DEFAULT 0",
    })
    _garantir_colunas(conexao, "relatos", {"usuario_id": "INTEGER", "rua": "TEXT", "bairro": "TEXT"})
    _garantir_colunas(conexao, "obras", {"rua": "TEXT", "bairro": "TEXT"})
    conexao.execute("CREATE INDEX IF NOT EXISTS idx_fotos_relato_id ON fotos(relato_id)")
    conexao.execute("CREATE INDEX IF NOT EXISTS idx_feedbacks_usuario_id ON feedbacks(usuario_id)")
    conexao.execute("CREATE INDEX IF NOT EXISTS idx_relatos_usuario_id ON relatos(usuario_id)")
    conexao.execute("CREATE INDEX IF NOT EXISTS idx_obras_status ON obras(status)")


def _inicializar_postgres(conexao):
    comandos = [
        """CREATE TABLE IF NOT EXISTS usuarios (
            id BIGINT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
            nome TEXT NOT NULL, email TEXT NOT NULL UNIQUE, senha_hash TEXT NOT NULL,
            data_criacao TEXT NOT NULL, perfil TEXT NOT NULL DEFAULT 'usuario',
            email_verificado INTEGER NOT NULL DEFAULT 1,
            codigo_verificacao_hash TEXT, codigo_expira_em TEXT,
            codigo_ultimo_envio_em TEXT, codigo_tentativas INTEGER NOT NULL DEFAULT 0)""",
        """CREATE TABLE IF NOT EXISTS obras (
            id BIGINT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
            titulo TEXT NOT NULL, localizacao TEXT NOT NULL, status TEXT NOT NULL,
            previsao TEXT, descricao TEXT, latitude DOUBLE PRECISION, longitude DOUBLE PRECISION,
            rua TEXT, bairro TEXT)""",
        """CREATE TABLE IF NOT EXISTS relatos (
            id BIGINT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
            tipo TEXT NOT NULL, descricao TEXT NOT NULL, latitude DOUBLE PRECISION NOT NULL,
            longitude DOUBLE PRECISION NOT NULL, status TEXT NOT NULL DEFAULT 'Em \u00e1n\u00e1lise',
            data TEXT NOT NULL, usuario_id BIGINT REFERENCES usuarios(id) ON DELETE SET NULL,
            rua TEXT, bairro TEXT)""",
        """CREATE TABLE IF NOT EXISTS fotos (
            id BIGINT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
            relato_id BIGINT NOT NULL REFERENCES relatos(id) ON DELETE CASCADE, arquivo TEXT NOT NULL)""",
        """CREATE TABLE IF NOT EXISTS feedbacks (
            id BIGINT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
            usuario_id BIGINT NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
            nota INTEGER NOT NULL CHECK (nota BETWEEN 1 AND 5), comentario TEXT NOT NULL,
            data_criacao TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP::text))""",
    ]
    for comando in comandos:
        conexao.execute(comando)
    # Support earlier schemas without deleting or recreating data.
    for tabela, definicoes in {
        "usuarios": {
            "perfil": "TEXT NOT NULL DEFAULT 'usuario'", "email_verificado": "INTEGER NOT NULL DEFAULT 1",
            "codigo_verificacao_hash": "TEXT", "codigo_expira_em": "TEXT",
            "codigo_ultimo_envio_em": "TEXT", "codigo_tentativas": "INTEGER NOT NULL DEFAULT 0",
        },
        "relatos": {"usuario_id": "BIGINT", "rua": "TEXT", "bairro": "TEXT"},
        "obras": {"rua": "TEXT", "bairro": "TEXT"},
    }.items():
        _garantir_colunas(conexao, tabela, definicoes)
    conexao.execute("CREATE INDEX IF NOT EXISTS idx_fotos_relato_id ON fotos(relato_id)")
    conexao.execute("CREATE INDEX IF NOT EXISTS idx_feedbacks_usuario_id ON feedbacks(usuario_id)")
    conexao.execute("CREATE INDEX IF NOT EXISTS idx_relatos_usuario_id ON relatos(usuario_id)")
    conexao.execute("CREATE INDEX IF NOT EXISTS idx_obras_status ON obras(status)")


def inicializar_banco():
    conexao = conectar_banco()
    try:
        if usando_postgres():
            # Transaction-scoped lock prevents concurrent serverless cold starts
            # from racing while adding the same missing schema columns.
            conexao.execute("SELECT pg_advisory_xact_lock(7163271001)")
            _inicializar_postgres(conexao)
        else:
            _inicializar_sqlite(conexao)
        quantidade_obras = conexao.execute("SELECT COUNT(*) FROM obras").fetchone()[0]
        if quantidade_obras == 0:
            obras = [
                ("Pavimenta\u00e7\u00e3o da rua", "Centro", "Rua dos Estudantes", "Centro", "Em andamento", "Dezembro/2026", "Obra de pavimenta\u00e7\u00e3o e melhoria da via.", -20.4695, -55.7860),
                ("Reforma da pra\u00e7a", "Alto", "Rua da Pra\u00e7a", "Alto", "Conclu\u00edda", "Setembro/2026", "Reforma e revitaliza\u00e7\u00e3o da pra\u00e7a.", -20.4730, -55.7890),
                ("Melhoria na ilumina\u00e7\u00e3o", "Nova Aquidauana", "Rua Principal", "Nova Aquidauana", "Em an\u00e1lise", None, "Avalia\u00e7\u00e3o para melhoria da ilumina\u00e7\u00e3o p\u00fablica.", -20.4660, -55.7830),
                ("Manuten\u00e7\u00e3o da via", "Guanandi", "Rua Guanandi", "Guanandi", "Em andamento", "Novembro/2026", "Manuten\u00e7\u00e3o e recupera\u00e7\u00e3o da via.", -20.4780, -55.7920),
            ]
            for obra in obras:
                conexao.execute("""INSERT INTO obras
                    (titulo, localizacao, rua, bairro, status, previsao, descricao, latitude, longitude)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""", obra)
        conexao.execute("UPDATE usuarios SET perfil = 'admin' WHERE email = ?", ("adm@exemplo.com",))
        conexao.commit()
    except Exception:
        conexao.rollback()
        raise
    finally:
        conexao.close()


def criar_banco():
    """Compatibility with the historical `py banco.py` command."""
    inicializar_banco()


if __name__ == "__main__":
    criar_banco()
