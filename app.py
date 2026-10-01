from flask import Flask, render_template, request, jsonify, redirect, session, g, has_app_context
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from banco import (
    ERRO_INTEGRIDADE,
    ERROS_BANCO,
    conectar_banco as _conectar_banco,
    inicializar_banco,
    preparar_colunas_verificacao as _preparar_colunas_verificacao,
)
from datetime import datetime, timedelta, timezone
import os
import urllib.request
import urllib.parse
import json
import math
import threading
import re
import secrets
import smtplib
import ssl
import html
from email.message import EmailMessage
from email.utils import formataddr

app = Flask(__name__)

_secret_key = os.environ.get("SECRET_KEY")
_ambiente = os.environ.get("APP_ENV", os.environ.get("FLASK_ENV", "")).lower()
_em_producao = _ambiente in ("production", "prod")
_debug_env = os.environ.get("FLASK_DEBUG")
_flask_cli = os.environ.get("FLASK_RUN_FROM_CLI", "").lower() == "true"
_modo_desenvolvimento = (
    _debug_env.lower() in ("1", "true", "yes")
    if _debug_env is not None
    else (__name__ == "__main__" or _ambiente in ("development", "dev")) and not _em_producao
)

if not _secret_key:
    if not _em_producao and (_modo_desenvolvimento or __name__ == "__main__" or _flask_cli):
        _secret_key = secrets.token_hex(32)
    else:
        raise RuntimeError("Configure SECRET_KEY no ambiente antes de iniciar o Flask.")

app.secret_key = _secret_key
app.config["DEBUG"] = _modo_desenvolvimento and not _em_producao

MAX_FOTO_BYTES = 5 * 1024 * 1024
MAX_FOTOS_RELATO = 3
FORMATOS_FOTO = {
    ".jpg": "jpeg",
    ".jpeg": "jpeg",
    ".jfif": "jpeg",
    ".png": "png",
    ".gif": "gif",
    ".webp": "webp",
}
TEMPO_CODIGO_VERIFICACAO = timedelta(minutes=10)
INTERVALO_REENVIO_CODIGO = timedelta(seconds=60)
MAX_TENTATIVAS_CODIGO = 5
MAX_CARACTERES_FEEDBACK = 2000


def preparar_colunas_verificacao(conexao):
    """Garante colunas de verificação em instalações existentes."""
    _preparar_colunas_verificacao(conexao)
    conexao.commit()


def validar_email(email):
    if not email or len(email) > 254:
        return False
    parte_local = email.split("@", 1)[0]
    if parte_local.startswith(".") or parte_local.endswith(".") or ".." in parte_local:
        return False
    return re.fullmatch(
        r"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@"
        r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?"
        r"(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)+",
        email,
    ) is not None


def agora_utc():
    return datetime.now(timezone.utc)


def codigo_aleatorio():
    return f"{secrets.randbelow(1_000_000):06d}"


def smtp_configurado():
    host = os.environ.get("EMAIL_SMTP_SERVER", "").strip()
    usuario = os.environ.get("EMAIL_SMTP_USER", "").strip()
    senha = os.environ.get("EMAIL_SMTP_PASSWORD", "").strip()
    try:
        porta = int(os.environ.get("EMAIL_SMTP_PORT", "587"))
    except ValueError:
        app.logger.error("Configuracao SMTP invalida: EMAIL_SMTP_PORT deve ser um numero inteiro.")
        return None

    ausentes = []
    if not host:
        ausentes.append("EMAIL_SMTP_SERVER")
    if not usuario:
        ausentes.append("EMAIL_SMTP_USER")
    if not senha:
        ausentes.append("EMAIL_SMTP_PASSWORD")
    if ausentes:
        app.logger.error("Configuracao SMTP incompleta. Variaveis ausentes: %s", ", ".join(ausentes))
        return None
    if not 1 <= porta <= 65535:
        app.logger.error("Configuracao SMTP invalida: EMAIL_SMTP_PORT fora do intervalo permitido.")
        return None
    return host, porta, usuario, senha


def mensagem_erro_smtp_segura(erro, senha):
    mensagem = str(erro)
    segredos = {senha, senha.strip(), "".join(senha.split())}
    for segredo in segredos:
        if segredo:
            mensagem = mensagem.replace(segredo, "[CREDENCIAL OMITIDA]")
    return mensagem[:500] or "Sem detalhes fornecidos pelo servidor SMTP."


def enviar_codigo_email(destinatario, codigo):
    config = smtp_configurado()
    if not config:
        return False
    host, porta, usuario, senha = config
    mensagem = EmailMessage()
    remetente = os.environ.get("EMAIL_FROM", usuario).strip() or usuario
    codigo_html = html.escape(str(codigo))
    mensagem["Subject"] = "FalaCidade — Código de verificação"
    mensagem["From"] = formataddr(("FalaCidade", remetente))
    mensagem["To"] = destinatario
    mensagem.set_content(
        "FalaCidade\n\n"
        "Seu código de verificação é:\n\n"
        f"{codigo}\n\n"
        "Esse código expira em 10 minutos.\n\n"
        "Se você não solicitou este código, ignore este e-mail."
    )
    mensagem.add_alternative(
        """
        <!doctype html>
        <html lang="pt-BR">
          <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <title>FalaCidade — Código de verificação</title>
          </head>
          <body style="margin:0;padding:24px 12px;background-color:#f3f5f7;font-family:Arial,Helvetica,sans-serif;color:#263238;">
            <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="border-collapse:collapse;">
              <tr><td align="center">
                <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width:520px;border-collapse:separate;border-spacing:0;background:#ffffff;border:1px solid #e5e7eb;border-radius:12px;overflow:hidden;">
                  <tr><td style="padding:22px 28px;background:#5581C9;color:#ffffff;font-size:22px;font-weight:bold;">FalaCidade</td></tr>
                  <tr><td style="padding:28px;font-size:16px;line-height:1.6;">
                    <p style="margin:0 0 16px;">Seu código de verificação é:</p>
                    <p style="margin:0 0 20px;padding:16px;background:#f3f6fc;border:1px solid #dce6f5;border-radius:8px;text-align:center;color:#315b9c;font-size:30px;font-weight:bold;letter-spacing:6px;line-height:1.3;">""" + codigo_html + """</p>
                    <p style="margin:0 0 12px;color:#5f6b72;">Esse código expira em 10 minutos.</p>
                    <p style="margin:0;color:#5f6b72;font-size:14px;">Se você não solicitou este código, ignore este e-mail.</p>
                  </td></tr>
                </table>
              </td></tr>
            </table>
          </body>
        </html>
        """,
        subtype="html",
    )
    etapa_smtp = "conexao SMTP"
    try:
        contexto_tls = ssl.create_default_context()
        if porta == 465:
            with smtplib.SMTP_SSL(host, porta, timeout=10, context=contexto_tls) as servidor:
                etapa_smtp = "autenticacao SMTP"
                servidor.login(usuario, senha)
                etapa_smtp = "envio da mensagem"
                servidor.send_message(mensagem)
                etapa_smtp = "encerramento SMTP"
        else:
            with smtplib.SMTP(host, porta, timeout=10) as servidor:
                etapa_smtp = "EHLO inicial"
                servidor.ehlo()
                etapa_smtp = "STARTTLS"
                servidor.starttls(context=contexto_tls)
                etapa_smtp = "EHLO apos STARTTLS"
                servidor.ehlo()
                etapa_smtp = "autenticacao SMTP"
                servidor.login(usuario, senha)
                etapa_smtp = "envio da mensagem"
                servidor.send_message(mensagem)
                etapa_smtp = "encerramento SMTP"
        return True
    except Exception as erro:
        app.logger.error(
            "Falha no envio SMTP durante %s (%s): %s",
            etapa_smtp,
            type(erro).__name__,
            mensagem_erro_smtp_segura(erro, senha),
        )
        return False


def data_iso(data):
    return data.isoformat()


def email_verificacao_expirado(valor):
    try:
        expiracao = datetime.fromisoformat(valor)
        if expiracao.tzinfo is None:
            expiracao = expiracao.replace(tzinfo=timezone.utc)
        return agora_utc() >= expiracao
    except (TypeError, ValueError):
        return True


def conectar_banco():
    conexao = _conectar_banco()
    if has_app_context() and not getattr(conexao, "is_postgres", False):
        if not hasattr(g, "conexoes_sqlite"):
            g.conexoes_sqlite = []
        g.conexoes_sqlite.append(conexao)
    return conexao


inicializar_banco()


@app.teardown_appcontext
def fechar_conexoes_sqlite(erro=None):
    for conexao in getattr(g, "conexoes_sqlite", []):
        try:
            conexao.close()
        except ERROS_BANCO:
            pass


def validar_coordenadas(latitude, longitude):
    try:
        latitude = float(latitude)
        longitude = float(longitude)
    except (TypeError, ValueError):
        return None

    if not math.isfinite(latitude) or not math.isfinite(longitude):
        return None
    if not -90 <= latitude <= 90 or not -180 <= longitude <= 180:
        return None
    return latitude, longitude


def validar_fotos(fotos):
    fotos_validas = [foto for foto in fotos if foto and foto.filename]
    if len(fotos_validas) > MAX_FOTOS_RELATO:
        return None, "Você pode enviar no máximo 3 fotos."

    resultado = []
    assinaturas = {
        "jpeg": lambda dados: dados.startswith(b"\xff\xd8\xff"),
        "png": lambda dados: dados.startswith(b"\x89PNG\r\n\x1a\n"),
        "gif": lambda dados: dados.startswith((b"GIF87a", b"GIF89a")),
        "webp": lambda dados: dados.startswith(b"RIFF") and dados[8:12] == b"WEBP",
    }

    for foto in fotos_validas:
        nome_seguro = secure_filename(foto.filename)
        extensao = os.path.splitext(nome_seguro)[1].lower()
        formato = FORMATOS_FOTO.get(extensao)
        if not nome_seguro or not formato:
            return None, "Formato de foto não permitido. Use JPG, PNG, GIF ou WEBP."

        tamanho = 0
        prefixo = b""
        while True:
            bloco = foto.stream.read(64 * 1024)
            if not bloco:
                break
            if len(prefixo) < 12:
                prefixo += bloco[:12 - len(prefixo)]
            tamanho += len(bloco)
            if tamanho > MAX_FOTO_BYTES:
                foto.stream.seek(0)
                return None, "Cada foto pode ter no máximo 5 MB."
        foto.stream.seek(0)

        if not assinaturas[formato](prefixo):
            return None, "O conteúdo de uma foto não corresponde ao formato do arquivo."
        resultado.append((foto, nome_seguro))

    return resultado, None

def descobrir_endereco(latitude, longitude):

    try:
        parametros = urllib.parse.urlencode({
            "lat": latitude,
            "lon": longitude,
            "format": "json",
            "addressdetails": 1
        })

        url = "https://nominatim.openstreetmap.org/reverse?" + parametros

        requisicao = urllib.request.Request(
            url,
            headers={
                "User-Agent": "MapaDaCidade-PPI/1.0"
            }
        )

        with urllib.request.urlopen(
            requisicao,
            timeout=10
        ) as resposta:

            dados = json.loads(
                resposta.read().decode("utf-8")
            )

        endereco = dados.get("address", {})

        rua = (
            endereco.get("road")
            or endereco.get("pedestrian")
            or endereco.get("residential")
        )

        bairro = (
            endereco.get("neighbourhood")
            or endereco.get("quarter")
            or endereco.get("residential")
        )

        return rua, bairro

    except Exception as erro:

        print("Não foi possível descobrir o endereço:")
        print(erro)

        return None, None

def atualizar_endereco_relato(id_relato, latitude, longitude):

    print("Iniciando busca de endereço para o relato:", id_relato)

    rua, bairro = descobrir_endereco(
        latitude,
        longitude
    )

    print("Rua encontrada:", rua)
    print("Bairro encontrado:", bairro)

    conexao = conectar_banco()
    try:
        cursor = conexao.cursor()
        cursor.execute("""
            UPDATE relatos
            SET rua = ?, bairro = ?
            WHERE id = ?
        """, (rua, bairro, id_relato))
        conexao.commit()
    finally:
        conexao.close()

@app.route("/")
def inicio():

    conexao = conectar_banco()
    cursor = conexao.cursor()

    # Quantidade de obras em andamento
    cursor.execute("""
        SELECT COUNT(*)
        FROM obras
        WHERE status = ?
    """, ("Em andamento",))

    obras_andamento = cursor.fetchone()[0]

    # Quantidade de obras concluídas
    cursor.execute("""
        SELECT COUNT(*)
        FROM obras
        WHERE status = ?
    """, ("Concluída",))

    obras_concluidas = cursor.fetchone()[0]

    # Quantidade total de problemas registrados
    cursor.execute("""
        SELECT COUNT(*)
        FROM relatos
    """)

    problemas_registrados = cursor.fetchone()[0]

    # Quantidade de solicitações em análise
    cursor.execute("""
        SELECT COUNT(*)
        FROM relatos
        WHERE status = ?
    """, ("Em análise",))

    solicitacoes_analise = cursor.fetchone()[0]

    conexao.close()

    return render_template(
        "index.html",
        obras_andamento=obras_andamento,
        obras_concluidas=obras_concluidas,
        problemas_registrados=problemas_registrados,
        solicitacoes_analise=solicitacoes_analise
    )


def codigo_foi_enviado_recentemente(valor, agora=None):
    if not valor:
        return False
    try:
        ultimo_envio = datetime.fromisoformat(valor)
        if ultimo_envio.tzinfo is None:
            ultimo_envio = ultimo_envio.replace(tzinfo=timezone.utc)
    except ValueError:
        return False
    return (agora or agora_utc()) - ultimo_envio < INTERVALO_REENVIO_CODIGO


def retomar_cadastro_pendente(email):
    conexao = conectar_banco()
    try:
        preparar_colunas_verificacao(conexao)
        usuario = conexao.execute(
            "SELECT id, email, email_verificado, codigo_ultimo_envio_em "
            "FROM usuarios WHERE lower(email) = ?", (email,)
        ).fetchone()
    finally:
        conexao.close()

    if usuario is None:
        return render_template("cadastro.html", mensagem="Esse e-mail já está cadastrado."), 409
    if int(usuario["email_verificado"] or 0):
        return render_template("cadastro.html", mensagem="Esse e-mail já está cadastrado."), 409

    session.pop("usuario_id", None)
    session.pop("usuario_nome", None)
    session.pop("usuario_perfil", None)
    session["verificacao_usuario_id"] = usuario["id"]

    agora = agora_utc()
    if codigo_foi_enviado_recentemente(usuario["codigo_ultimo_envio_em"], agora):
        session["verificacao_mensagem"] = (
            "Seu cadastro aguarda verificação. Use o código enviado recentemente "
            "ou solicite outro após o intervalo de espera."
        )
        return redirect("/verificar-email")

    if not smtp_configurado():
        return render_template(
            "verificar_email.html", email=usuario["email"],
            mensagem="O servico de e-mail nao esta configurado. Tente novamente mais tarde.",
        ), 503

    codigo = codigo_aleatorio()
    conexao = conectar_banco()
    try:
        preparar_colunas_verificacao(conexao)
        cursor = conexao.execute(
            "UPDATE usuarios SET codigo_verificacao_hash = ?, codigo_expira_em = ?, "
            "codigo_ultimo_envio_em = ?, codigo_tentativas = 0 WHERE id = ? "
            "AND email_verificado = 0 "
            "AND (codigo_ultimo_envio_em IS NULL OR codigo_ultimo_envio_em <= ?)",
            (generate_password_hash(codigo),
             data_iso(agora + TEMPO_CODIGO_VERIFICACAO), data_iso(agora),
             usuario["id"], data_iso(agora - INTERVALO_REENVIO_CODIGO)),
        )
        if cursor.rowcount != 1:
            conexao.rollback()
            session["verificacao_mensagem"] = (
                "Seu cadastro aguarda verificação. Use o código enviado recentemente "
                "ou solicite outro após o intervalo de espera."
            )
            return redirect("/verificar-email")
        conexao.commit()
    finally:
        conexao.close()

    if not enviar_codigo_email(usuario["email"], codigo):
        conexao = conectar_banco()
        try:
            conexao.execute(
                "UPDATE usuarios SET codigo_verificacao_hash = NULL, "
                "codigo_expira_em = NULL WHERE id = ?", (usuario["id"],)
            )
            conexao.commit()
        finally:
            conexao.close()
        return render_template(
            "verificar_email.html", email=usuario["email"],
            mensagem="Nao foi possivel enviar o codigo. Tente novamente mais tarde.",
        ), 503

    session["verificacao_mensagem"] = "Enviamos um novo codigo de verificacao para seu e-mail."
    return redirect("/verificar-email")


@app.route("/cadastro", methods=["GET", "POST"])
def cadastro():
    if request.method == "GET":
        return render_template("cadastro.html")

    nome = (request.form.get("nome") or "").strip()
    email = (request.form.get("email") or "").strip().lower()
    senha = request.form.get("senha") or ""
    if not nome or not email or not senha:
        return render_template("cadastro.html", mensagem="Preencha todos os campos."), 400
    if not validar_email(email):
        return render_template("cadastro.html", mensagem="Informe um e-mail valido."), 400

    conexao = conectar_banco()
    usuario_existente = False
    erro_integridade = False
    try:
        preparar_colunas_verificacao(conexao)
        cursor = conexao.cursor()
        cursor.execute("SELECT id FROM usuarios WHERE lower(email) = ?", (email,))
        usuario_existente = cursor.fetchone() is not None
        if not usuario_existente:
            if not smtp_configurado():
                return render_template(
                    "cadastro.html",
                    mensagem="O servico de e-mail nao esta configurado. Tente novamente mais tarde.",
                ), 503
            agora = agora_utc()
            codigo = codigo_aleatorio()
            cursor.execute("""
                INSERT INTO usuarios
                (nome, email, senha_hash, data_criacao, email_verificado,
                 codigo_verificacao_hash, codigo_expira_em, codigo_tentativas)
                VALUES (?, ?, ?, ?, 0, ?, ?, 0)
            """, (nome, email, generate_password_hash(senha),
                  datetime.now().strftime("%d/%m/%Y %H:%M"),
                  generate_password_hash(codigo),
                  data_iso(agora + TEMPO_CODIGO_VERIFICACAO)))
            usuario_id = cursor.lastrowid
            conexao.commit()
    except ERRO_INTEGRIDADE:
        conexao.rollback()
        erro_integridade = True
    finally:
        conexao.close()

    if usuario_existente or erro_integridade:
        return retomar_cadastro_pendente(email)

    session.pop("usuario_id", None)
    session.pop("usuario_nome", None)
    session.pop("usuario_perfil", None)
    session["verificacao_usuario_id"] = usuario_id
    if not enviar_codigo_email(email, codigo):
        return render_template("verificar_email.html", email=email,
            mensagem="Nao foi possivel enviar o codigo. Tente novamente mais tarde."), 503
    conexao = conectar_banco()
    try:
        conexao.execute("UPDATE usuarios SET codigo_ultimo_envio_em = ? WHERE id = ?",
                        (data_iso(agora), usuario_id))
        conexao.commit()
    finally:
        conexao.close()
    session["verificacao_mensagem"] = "Enviamos um codigo de verificacao para seu e-mail."
    return redirect("/verificar-email")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")
    email = (request.form.get("email") or "").strip().lower()
    senha = request.form.get("senha") or ""
    if not email or not senha:
        return render_template("login.html", mensagem="Preencha todos os campos."), 400
    conexao = conectar_banco()
    try:
        preparar_colunas_verificacao(conexao)
        usuario = conexao.execute("SELECT * FROM usuarios WHERE lower(email) = ?", (email,)).fetchone()
    finally:
        conexao.close()
    if usuario is None:
        return render_template("login.html", mensagem="E-mail ou senha incorretos."), 401
    if not check_password_hash(usuario["senha_hash"], senha):
        return render_template("login.html", mensagem="E-mail ou senha incorretos."), 401
    if not int(usuario["email_verificado"] or 0):
        session.pop("usuario_id", None)
        session.pop("usuario_nome", None)
        session.pop("usuario_perfil", None)
        session["verificacao_usuario_id"] = usuario["id"]
        session["verificacao_mensagem"] = "Confirme seu e-mail antes de entrar."
        return redirect("/verificar-email")
    session.pop("verificacao_usuario_id", None)
    session["usuario_id"] = usuario["id"]
    session["usuario_nome"] = usuario["nome"]
    session["usuario_perfil"] = usuario["perfil"]
    return redirect("/")


def obter_usuario_verificacao(conexao):
    usuario_id = session.get("verificacao_usuario_id")
    if not usuario_id:
        return None
    return conexao.execute(
        "SELECT id, nome, email, email_verificado, codigo_verificacao_hash, "
        "codigo_expira_em, codigo_ultimo_envio_em, codigo_tentativas, perfil "
        "FROM usuarios WHERE id = ?", (usuario_id,)
    ).fetchone()


@app.route("/verificar-email", methods=["GET", "POST"])
def verificar_email():
    conexao = conectar_banco()
    try:
        preparar_colunas_verificacao(conexao)
        usuario = obter_usuario_verificacao(conexao)
        if usuario is None:
            return redirect("/cadastro")
        if int(usuario["email_verificado"] or 0):
            session.pop("verificacao_usuario_id", None)
            return redirect("/")
        mensagem = session.pop("verificacao_mensagem", None)
        if request.method == "POST":
            codigo = request.form.get("codigo", "")
            if not re.fullmatch(r"[0-9]{6}", codigo):
                mensagem = "Codigo invalido ou expirado."
            elif (not usuario["codigo_verificacao_hash"] or
                  email_verificacao_expirado(usuario["codigo_expira_em"])):
                conexao.execute("UPDATE usuarios SET codigo_verificacao_hash = NULL, codigo_expira_em = NULL, codigo_tentativas = 0 WHERE id = ?", (usuario["id"],))
                conexao.commit()
                mensagem = "Codigo invalido ou expirado."
            elif int(usuario["codigo_tentativas"] or 0) >= MAX_TENTATIVAS_CODIGO:
                mensagem = "Codigo invalido ou expirado. Solicite um novo codigo."
            elif not check_password_hash(usuario["codigo_verificacao_hash"], codigo):
                tentativas = int(usuario["codigo_tentativas"] or 0) + 1
                if tentativas >= MAX_TENTATIVAS_CODIGO:
                    conexao.execute("UPDATE usuarios SET codigo_verificacao_hash = NULL, codigo_expira_em = NULL, codigo_tentativas = ? WHERE id = ?", (tentativas, usuario["id"]))
                else:
                    conexao.execute("UPDATE usuarios SET codigo_tentativas = ? WHERE id = ?", (tentativas, usuario["id"]))
                conexao.commit()
                mensagem = "Codigo invalido ou expirado."
            else:
                conexao.execute("UPDATE usuarios SET email_verificado = 1, codigo_verificacao_hash = NULL, codigo_expira_em = NULL, codigo_ultimo_envio_em = NULL, codigo_tentativas = 0 WHERE id = ?", (usuario["id"],))
                conexao.commit()
                session.clear()
                session["usuario_id"] = usuario["id"]
                session["usuario_nome"] = usuario["nome"]
                session["usuario_perfil"] = usuario["perfil"]
                return redirect("/")
        return render_template("verificar_email.html", email=usuario["email"], mensagem=mensagem)
    finally:
        conexao.close()


@app.route("/reenviar-codigo", methods=["POST"])
def reenviar_codigo():
    conexao = conectar_banco()
    try:
        preparar_colunas_verificacao(conexao)
        usuario = obter_usuario_verificacao(conexao)
        if usuario is None:
            return redirect("/cadastro")
        if int(usuario["email_verificado"] or 0):
            session.pop("verificacao_usuario_id", None)
            return redirect("/")
        if not smtp_configurado():
            return render_template("verificar_email.html", email=usuario["email"], mensagem="O servico de e-mail nao esta configurado. Tente novamente mais tarde."), 503
        if usuario["codigo_ultimo_envio_em"]:
            try:
                ultimo_envio = datetime.fromisoformat(usuario["codigo_ultimo_envio_em"])
                if ultimo_envio.tzinfo is None:
                    ultimo_envio = ultimo_envio.replace(tzinfo=timezone.utc)
            except ValueError:
                ultimo_envio = agora_utc() - INTERVALO_REENVIO_CODIGO
            if agora_utc() - ultimo_envio < INTERVALO_REENVIO_CODIGO:
                return render_template("verificar_email.html", email=usuario["email"], mensagem="Aguarde antes de solicitar outro codigo."), 429
        agora = agora_utc()
        codigo = codigo_aleatorio()
        cursor = conexao.execute(
            "UPDATE usuarios SET codigo_verificacao_hash = ?, codigo_expira_em = ?, "
            "codigo_ultimo_envio_em = ?, codigo_tentativas = 0 WHERE id = ? "
            "AND (codigo_ultimo_envio_em IS NULL OR codigo_ultimo_envio_em <= ?)",
            (generate_password_hash(codigo), data_iso(agora + TEMPO_CODIGO_VERIFICACAO),
             data_iso(agora), usuario["id"],
             data_iso(agora - INTERVALO_REENVIO_CODIGO)),
        )
        if cursor.rowcount != 1:
            conexao.rollback()
            return render_template("verificar_email.html", email=usuario["email"], mensagem="Aguarde antes de solicitar outro codigo."), 429
        conexao.commit()
        if not enviar_codigo_email(usuario["email"], codigo):
            conexao.execute("UPDATE usuarios SET codigo_verificacao_hash = NULL, codigo_expira_em = NULL WHERE id = ?", (usuario["id"],))
            conexao.commit()
            return render_template("verificar_email.html", email=usuario["email"], mensagem="Nao foi possivel enviar o codigo. Tente novamente mais tarde."), 503
        return render_template("verificar_email.html", email=usuario["email"], mensagem="Enviamos um novo codigo de verificacao para seu e-mail.")
    finally:
        conexao.close()

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")


@app.route("/feedback", methods=["GET"])
def feedback():
    if not session.get("usuario_id"):
        return redirect("/login")
    return render_template(
        "feedback.html",
        mensagem=session.pop("feedback_mensagem", None),
        nota_selecionada=None,
    )


@app.route("/enviar-feedback", methods=["POST"])
def enviar_feedback():
    usuario_id = session.get("usuario_id")
    if not usuario_id:
        return redirect("/login")
    try:
        usuario_id = int(usuario_id)
    except (TypeError, ValueError):
        session.pop("usuario_id", None)
        return redirect("/login")
    if not 1 <= usuario_id <= 9_223_372_036_854_775_807:
        session.pop("usuario_id", None)
        return redirect("/login")

    nota_recebida = request.form.get("nota", "")
    comentario = request.form.get("comentario", "").strip()
    mensagem_erro = None
    nota = None
    if not re.fullmatch(r"[1-5]", nota_recebida):
        mensagem_erro = "Selecione uma nota de 1 a 5 estrelas."
    else:
        nota = int(nota_recebida)
    if not mensagem_erro and not comentario:
        mensagem_erro = "Escreva um comentário antes de enviar."
    elif not mensagem_erro and len(comentario) > MAX_CARACTERES_FEEDBACK:
        mensagem_erro = f"O comentário deve ter no máximo {MAX_CARACTERES_FEEDBACK} caracteres."
    if mensagem_erro:
        return render_template(
            "feedback.html",
            mensagem=mensagem_erro,
            comentario=comentario[:MAX_CARACTERES_FEEDBACK],
            nota_selecionada=nota,
        ), 400

    conexao = conectar_banco()
    try:
        cursor = conexao.execute(
            "INSERT INTO feedbacks (usuario_id, nota, comentario) VALUES (?, ?, ?)",
            (usuario_id, nota, comentario),
        )
        if cursor.rowcount != 1:
            conexao.rollback()
            return "Não foi possível enviar o feedback.", 500
        conexao.commit()
    except ERRO_INTEGRIDADE:
        conexao.rollback()
        return "Não foi possível enviar o feedback.", 400
    except ERROS_BANCO:
        conexao.rollback()
        app.logger.exception("Falha ao salvar feedback.")
        return "Não foi possível enviar o feedback.", 500
    finally:
        conexao.close()

    session["feedback_mensagem"] = "Feedback enviado com sucesso. Obrigado por ajudar a melhorar o FalaCidade!"
    return redirect("/feedback")


@app.route("/excluir-feedback/<feedback_id>", methods=["POST"])
def excluir_feedback(feedback_id):
    if session.get("usuario_perfil") != "admin":
        return redirect("/")
    if not re.fullmatch(r"[1-9][0-9]*", feedback_id):
        return redirect("/admin")
    try:
        feedback_id = int(feedback_id)
    except ValueError:
        return redirect("/admin")
    if feedback_id > 9_223_372_036_854_775_807:
        return redirect("/admin")
    conexao = conectar_banco()
    try:
        conexao.execute("DELETE FROM feedbacks WHERE id = ?", (feedback_id,))
        conexao.commit()
    except ERROS_BANCO:
        conexao.rollback()
        app.logger.exception("Falha ao excluir feedback.")
    finally:
        conexao.close()
    return redirect("/admin")


@app.route("/mapa")
def mapa():

    return render_template("mapa.html")


@app.route("/obras")
def obras():

    conexao = conectar_banco()
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT *
        FROM obras
        ORDER BY id DESC
    """)

    obras = cursor.fetchall()

    conexao.close()

    return render_template(
        "obras.html",
        obras=obras
    )


@app.route("/relatar")
def relatar():

    return render_template("relatar.html")


@app.route("/enviar-relato", methods=["POST"])
def enviar_relato():

    usuario_id = session.get("usuario_id")

    if not usuario_id:
        return jsonify({
            "sucesso": False,
            "mensagem": "Você precisa estar logado para enviar um relato."
        }), 401

    tipo = request.form.get("tipo")
    descricao = request.form.get("descricao")
    latitude = request.form.get("latitude")
    longitude = request.form.get("longitude")
    print("\n==============================")
    print("NOVO RELATO RECEBIDO")
    print("tipo:", tipo)
    print("descricao:", descricao)
    print("latitude:", latitude)
    print("longitude:", longitude)
    print("fotos:", request.files.getlist("fotos"))
    print("==============================\n")

    coordenadas = validar_coordenadas(latitude, longitude)
    if not tipo or not descricao or coordenadas is None:

        return jsonify({
            "sucesso": False,
            "mensagem": "Informe o tipo, a descrição e coordenadas válidas."
        }), 400

    latitude, longitude = coordenadas

    fotos, erro_fotos = validar_fotos(request.files.getlist("fotos"))
    if erro_fotos:
        return jsonify({"sucesso": False, "mensagem": erro_fotos}), 400

    data = datetime.now().strftime("%d/%m/%Y %H:%M")

    conexao = conectar_banco()
    cursor = conexao.cursor()

    cursor.execute("""
        INSERT INTO relatos
        (
            tipo,
            descricao,
            latitude,
            longitude,
            status,
            data,
            usuario_id
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        tipo,
        descricao,
        latitude,
        longitude,
        "Em análise",
        data,
        usuario_id
    ))

    id_relato = cursor.lastrowid

    conexao.commit()
    conexao.close()

    print("Relato salvo no banco. ID:", id_relato)

    threading.Thread(
        target=atualizar_endereco_relato,
        args=(id_relato, latitude, longitude),
        daemon=True
    ).start()

    # =========================
    # SALVAR FOTOS
    # =========================

    pasta_uploads = os.path.join(app.static_folder, "uploads")

    os.makedirs(pasta_uploads, exist_ok=True)

    for indice, (foto, nome_original) in enumerate(fotos):

        nome_arquivo = f"relato_{id_relato}_{indice}_{nome_original}"

        caminho = os.path.join(
            pasta_uploads,
            nome_arquivo
        )

        foto.save(caminho)

        print("Foto salva:", caminho)

        conexao = conectar_banco()
        cursor = conexao.cursor()

        cursor.execute("""
            INSERT INTO fotos (relato_id, arquivo)
            VALUES (?, ?)
        """, (
            id_relato,
            nome_arquivo
        ))

        conexao.commit()

        print(
            "FOTO REGISTRADA NO BANCO:",
            nome_arquivo
        )

        conexao.close()

    print("Fotos processadas. Preparando resposta do envio.")

    return jsonify({
        "sucesso": True,
        "mensagem": "Obrigado por contribuir! Sua solicitação foi enviada e está em análise."
    })


@app.route("/apagar-relato/<int:id>", methods=["POST"])
def apagar_relato(id):

    usuario_id = session.get("usuario_id")
    perfil = session.get("usuario_perfil")

    if not usuario_id:
        return redirect("/login")

    conexao = conectar_banco()
    cursor = conexao.cursor()

    if perfil == "admin":

        cursor.execute("""
            SELECT id
            FROM relatos
            WHERE id = ?
        """, (id,))

    else:

        cursor.execute("""
            SELECT id
            FROM relatos
            WHERE id = ?
            AND usuario_id = ?
        """, (
            id,
            usuario_id
        ))

    relato = cursor.fetchone()

    if relato is None:
        conexao.close()
        return redirect("/solicitacoes")

    cursor.execute("""
        SELECT arquivo
        FROM fotos
        WHERE relato_id = ?
    """, (id,))
    arquivos_fotos = [linha[0] for linha in cursor.fetchall()]

    # Apaga as fotos relacionadas

    cursor.execute("""
        DELETE FROM fotos
        WHERE relato_id = ?
    """, (id,))

    # Apaga o relato

    cursor.execute("""
        DELETE FROM relatos
        WHERE id = ?
    """, (id,))

    conexao.commit()
    conexao.close()

    pasta_uploads = os.path.join(app.static_folder, "uploads")
    for arquivo in arquivos_fotos:
        nome_seguro = secure_filename(os.path.basename(arquivo))
        if nome_seguro:
            try:
                os.remove(os.path.join(pasta_uploads, nome_seguro))
            except FileNotFoundError:
                pass

    return redirect("/solicitacoes")

@app.route("/api/relatos")
def api_relatos():

    conexao = conectar_banco()

    cursor = conexao.cursor()

    cursor.execute("""
        SELECT id, tipo, descricao, latitude, longitude, status, data, rua, bairro
        FROM relatos
        ORDER BY id DESC
    """)

    relatos = cursor.fetchall()

    dados = []

    for relato in relatos:

        cursor.execute("""
            SELECT arquivo
            FROM fotos
            WHERE relato_id = ?
        """, (relato["id"],))

        fotos = cursor.fetchall()

        dados.append({
            "id": relato["id"],
            "tipo": relato["tipo"],
            "descricao": relato["descricao"],
            "latitude": relato["latitude"],
            "longitude": relato["longitude"],
            "status": relato["status"],
            "data": relato["data"],
            "rua": relato["rua"],
            "bairro": relato["bairro"],
            "fotos": [
                foto["arquivo"]
                for foto in fotos
            ]
        })

    conexao.close()

    return jsonify(dados)


def buscar_solicitacoes_usuario(usuario_id=None):
    """Busca apenas os relatos e fotos vinculados ao ID do usuário."""
    conexao = conectar_banco()
    cursor = conexao.cursor()

    try:
        if usuario_id is None:
            cursor.execute("SELECT * FROM relatos ORDER BY id DESC")
        else:
            cursor.execute("""
                SELECT * FROM relatos
                WHERE usuario_id = ?
                ORDER BY id DESC
            """, (usuario_id,))
        relatos = cursor.fetchall()
        dados = []
        for relato in relatos:
            cursor.execute("""
                SELECT arquivo FROM fotos WHERE relato_id = ?
            """, (relato["id"],))
            dados.append({"relato": relato, "fotos": cursor.fetchall()})
        return dados
    finally:
        conexao.close()


@app.route("/solicitacoes")
def solicitacoes():
    usuario_id = session.get("usuario_id")
    perfil_admin = session.get("usuario_perfil") == "admin"
    if not usuario_id:
        return render_template(
            "solicitacoes.html", relatos=[], perfil_admin=False
        )

    return render_template(
        "solicitacoes.html",
        relatos=buscar_solicitacoes_usuario(None if perfil_admin else usuario_id),
        perfil_admin=perfil_admin
    )

@app.route("/cancelar-relato/<int:relato_id>", methods=["POST"])
def cancelar_relato(relato_id):

    usuario_id = session.get("usuario_id")

    if not usuario_id:

        return jsonify({
            "sucesso": False,
            "mensagem": "Você precisa estar logado."
        }), 401

    conexao = conectar_banco()
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT *
        FROM relatos
        WHERE id = ?
        AND usuario_id = ?
    """, (
        relato_id,
        usuario_id
    ))

    relato = cursor.fetchone()

    if relato is None:

        conexao.close()

        return jsonify({
            "sucesso": False,
            "mensagem": "Solicitação não encontrada."
        }), 404

    if relato["status"] != "Em análise":

        conexao.close()

        return jsonify({
            "sucesso": False,
            "mensagem": "Esta solicitação não pode mais ser cancelada."
        }), 400

    cursor.execute("""
        UPDATE relatos
        SET status = ?
        WHERE id = ?
        AND usuario_id = ?
    """, (
        "Cancelado",
        relato_id,
        usuario_id
    ))

    conexao.commit()
    conexao.close()

    return jsonify({
        "sucesso": True,
        "mensagem": "Solicitação cancelada com sucesso."
    })


# ==========================================
# ALTERAR STATUS DE UMA OBRA
# ==========================================

@app.route("/alterar-status/<int:obra_id>", methods=["POST"])
def alterar_status(obra_id):

    if session.get("usuario_perfil") != "admin":
        return redirect("/")

    novo_status = request.form.get("status")

    status_permitidos = [
        "Em análise",
        "Em andamento",
        "Concluída",
        "Cancelado"
    ]

    if novo_status not in status_permitidos:
        return redirect("/admin")

    conexao = conectar_banco()
    cursor = conexao.cursor()

    cursor.execute("""
        UPDATE obras
        SET status = ?
        WHERE id = ?
    """, (
        novo_status,
        obra_id
    ))

    conexao.commit()
    conexao.close()

    return redirect("/admin")


@app.route("/alterar-status-relato/<int:relato_id>", methods=["POST"])
def alterar_status_relato(relato_id):

    if session.get("usuario_perfil") != "admin":
        return redirect("/")

    novo_status = request.form.get("status")

    status_permitidos = [
        "Em análise",
        "Em andamento",
        "Concluída",
        "Cancelado"
    ]

    if novo_status not in status_permitidos:
        return redirect("/admin")

    conexao = conectar_banco()
    cursor = conexao.cursor()

    cursor.execute("""
        UPDATE relatos
        SET status = ?
        WHERE id = ?
    """, (
        novo_status,
        relato_id
    ))

    conexao.commit()
    conexao.close()

    return redirect("/admin")

@app.route("/cadastrar-obra", methods=["POST"])
def cadastrar_obra():

    if session.get("usuario_perfil") != "admin":
        return redirect("/")

    titulo = request.form.get("titulo")
    localizacao = request.form.get("localizacao")
    descricao = request.form.get("descricao")
    previsao = request.form.get("previsao")
    status = request.form.get("status")
    latitude = request.form.get("latitude")
    longitude = request.form.get("longitude")

    coordenadas = validar_coordenadas(latitude, longitude)
    if not titulo or not localizacao or coordenadas is None:
        return redirect("/admin")
    latitude, longitude = coordenadas

    status_permitidos = [
        "Em análise",
        "Em andamento",
        "Concluída",
        "Cancelado"
    ]

    if status not in status_permitidos:
        return redirect("/admin")

    conexao = conectar_banco()
    cursor = conexao.cursor()

    cursor.execute("""
        INSERT INTO obras
        (
            titulo,
            localizacao,
            status,
            previsao,
            descricao,
            latitude,
            longitude
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        titulo,
        localizacao,
        status,
        previsao,
        descricao,
        latitude,
        longitude
    ))

    conexao.commit()
    conexao.close()

    return redirect("/admin")

# ==========================================
# PAINEL ADMINISTRATIVO
# ==========================================

@app.route("/admin")
def admin():

    if session.get("usuario_perfil") != "admin":
        return redirect("/")

    conexao = conectar_banco()
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT *
        FROM obras
        ORDER BY id DESC
    """)

    obras = cursor.fetchall()

    cursor.execute("""
        SELECT *
        FROM relatos
        ORDER BY id DESC
    """)

    relatos = cursor.fetchall()

    cursor.execute("""
        SELECT f.id, f.nota, f.comentario, f.data_criacao,
               u.nome AS usuario_nome, u.email AS usuario_email
        FROM feedbacks AS f
        JOIN usuarios AS u ON u.id = f.usuario_id
        ORDER BY f.data_criacao DESC, f.id DESC
    """)
    feedbacks = cursor.fetchall()

    fotos_por_relato = {}

    for relato in relatos:
        cursor.execute("""
            SELECT arquivo
            FROM fotos
            WHERE relato_id = ?
            ORDER BY id
        """, (relato["id"],))

        fotos_por_relato[relato["id"]] = cursor.fetchall()

    conexao.close()

    return render_template(
        "admin.html",
        obras=obras,
        relatos=relatos,
        fotos_por_relato=fotos_por_relato,
        feedbacks=feedbacks,
    )

@app.route("/api/obras")
def api_obras():

    conexao = conectar_banco()

    cursor = conexao.cursor()

    cursor.execute("""
        SELECT id, titulo, localizacao, status, previsao,
               descricao, latitude, longitude
        FROM obras
        ORDER BY id DESC
    """)

    obras = cursor.fetchall()

    dados = []

    for obra in obras:

        dados.append({
            "id": obra["id"],
            "titulo": obra["titulo"],
            "localizacao": obra["localizacao"],
            "status": obra["status"],
            "previsao": obra["previsao"],
            "descricao": obra["descricao"],
            "latitude": obra["latitude"],
            "longitude": obra["longitude"]
        })

    conexao.close()

    return jsonify(dados)

if __name__ == "__main__":
    app.run(debug=app.config["DEBUG"])
