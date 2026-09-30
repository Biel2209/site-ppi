"""Testa conexao Gmail SMTP com STARTTLS e autenticacao, sem enviar mensagem."""

import os
import smtplib
import ssl
import argparse


def texto_erro_seguro(erro, senha):
    mensagem = str(erro)
    for segredo in {senha, senha.strip(), "".join(senha.split())}:
        if segredo:
            mensagem = mensagem.replace(segredo, "[CREDENCIAL OMITIDA]")
    return mensagem.replace("\r", " ").replace("\n", " ")[:500]


def main():
    parser = argparse.ArgumentParser(description="Diagnostico SMTP sem enviar mensagens")
    parser.add_argument(
        "--auth",
        choices=("auto", "login"),
        default="auto",
        help="auto reproduz smtplib.login; login testa o mecanismo LOGIN anunciado pelo servidor",
    )
    argumentos = parser.parse_args()

    host = os.environ.get("EMAIL_SMTP_SERVER", "").strip()
    usuario = os.environ.get("EMAIL_SMTP_USER", "").strip()
    senha = os.environ.get("EMAIL_SMTP_PASSWORD", "").strip()
    try:
        porta = int(os.environ.get("EMAIL_SMTP_PORT", "587"))
    except ValueError:
        print("Falha na configuracao: EMAIL_SMTP_PORT deve ser um numero inteiro.")
        return 1

    email_from = os.environ.get("EMAIL_FROM", "").strip()
    print(
        "Configuracao: "
        f"server={host or '(ausente)'}; port={porta}; "
        f"EMAIL_SMTP_USER presente={bool(usuario)}; "
        f"EMAIL_SMTP_PASSWORD presente={bool(senha)}; "
        f"EMAIL_SMTP_PASSWORD tamanho={len(senha)}; "
        f"EMAIL_FROM presente={bool(email_from)}"
    )

    ausentes = [
        nome for nome, valor in (
            ("EMAIL_SMTP_SERVER", host),
            ("EMAIL_SMTP_USER", usuario),
            ("EMAIL_SMTP_PASSWORD", senha),
        ) if not valor
    ]
    if ausentes:
        print("Variaveis SMTP ausentes: " + ", ".join(ausentes))
        return 1
    if not 1 <= porta <= 65535:
        print("Falha na configuracao: EMAIL_SMTP_PORT fora do intervalo permitido.")
        return 1

    servidor = None
    etapa = "conexao SMTP"
    try:
        servidor = smtplib.SMTP(host, porta, timeout=15)
        etapa = "EHLO inicial"
        servidor.ehlo()
        etapa = "STARTTLS"
        servidor.starttls(context=ssl.create_default_context())
        etapa = "EHLO apos STARTTLS"
        servidor.ehlo()
        mecanismos_auth = servidor.esmtp_features.get("auth", "")
        print("Mecanismos AUTH anunciados apos TLS: " + (mecanismos_auth or "nenhum"))
        etapa = "autenticacao SMTP"
        if argumentos.auth == "login":
            if "LOGIN" not in mecanismos_auth.upper().split():
                raise smtplib.SMTPNotSupportedError("Servidor nao anunciou AUTH LOGIN.")
            print("Mecanismo AUTH em teste: LOGIN")
            servidor.user = usuario
            servidor.password = senha
            servidor.auth("LOGIN", servidor.auth_login)
        else:
            autenticacao_original = servidor.auth

            def autenticar_com_diagnostico(mecanismo, authobject, *, initial_response_ok=True):
                print("Mecanismo AUTH em teste: " + mecanismo)
                return autenticacao_original(
                    mecanismo, authobject, initial_response_ok=initial_response_ok
                )

            servidor.auth = autenticar_com_diagnostico
            servidor.login(usuario, senha)
        etapa = "encerramento SMTP (QUIT)"
        servidor.quit()
        servidor = None
        print("Sucesso: conexao, STARTTLS, autenticacao e encerramento SMTP concluiram.")
        return 0
    except Exception as erro:
        print(
            f"Falha durante {etapa} ({type(erro).__name__}): "
            f"{texto_erro_seguro(erro, senha)}"
        )
        return 1
    finally:
        if servidor is not None:
            servidor.close()


if __name__ == "__main__":
    raise SystemExit(main())
