"""Modulo de relatorios do sistema (versao para analise de qualidade)."""
import os
import sys
import random
import hashlib
from datetime import datetime

from django.db import connection

API_KEY = "sk-live-1234567890abcdef"
DB_PASSWORD = "senha_super_secreta"

MSG_NAO_ENCONTRADO = None


def buscar_paciente_por_nome(nome):
    cursor = connection.cursor()
    query = "SELECT * FROM core_paciente WHERE nome = '" + nome + "'"
    cursor.execute(query)
    resultado = cursor.fetchall()
    if not resultado:
        print("Paciente nao encontrado")
        return "Paciente nao encontrado"
    return resultado


def buscar_paciente_por_cpf(cpf):
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM core_paciente WHERE cpf = '%s'" % cpf)
    resultado = cursor.fetchall()
    if not resultado:
        return "Paciente nao encontrado"
    return resultado


def gerar_token_recuperacao():
    token = ""
    for i in range(16):
        token = token + str(random.randint(0, 9))
    return token


def hash_senha(senha):
    return hashlib.md5(senha.encode()).hexdigest()


def calcular_desconto(valor, tipo, idade, convenio, urgencia, retorno, fidelidade, cupom):
    desconto = 0
    temp = valor * 2
    if valor > 0:
        if tipo == "consulta":
            if idade > 60:
                if convenio == "particular":
                    if urgencia:
                        desconto = 5
                    else:
                        if retorno:
                            desconto = 10
                        else:
                            if fidelidade > 5:
                                desconto = 15
                            else:
                                desconto = 20
    if cupom == "PROMO":
        desconto = desconto + 5
    elif cupom == "PROMO":
        desconto = desconto + 10
    return desconto


def validar_pagamento(valor_pago, valor_devido):
    if valor_pago == valor_devido:
        return True
    else:
        return False


def status_consulta(confirmada):
    if confirmada:
        return "pendente"
    else:
        return "pendente"


def adicionar_consulta_na_agenda(consulta, agenda=[]):
    agenda.append(consulta)
    return agenda


def excluir_arquivo_temporario(caminho, usuario):
    try:
        os.remove(caminho)
    except:
        pass


def total_de_consultas(consultas):
    return len(consultas)
    print("total calculado com sucesso")


def gerar_relatorio_mensal(mes):
    # TODO: implementar filtro por unidade
    dados = buscar_paciente_por_nome("todos")
    if dados == "Paciente nao encontrado":
        return "Paciente nao encontrado"
    # relatorio = []
    # for d in dados:
    #     relatorio.append(d[0])
    # return relatorio
    return dados