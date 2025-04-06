import os
import math
import time
import logging
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
from colorama import init, Fore
import configparser
from selenium.webdriver.common.action_chains import ActionChains

init(autoreset=True)

def carregar_configuracoes():
    config_path = r"C:\Users\Marcelo\Desktop\Teste Técnico-Unimed\Config\config.ini"
    config = configparser.ConfigParser()
    config.read(config_path, encoding="utf-8")

    log_dir = config.get("PATHS", "LOG_DIR")
    resultado_path = config.get("PATHS", "RESULTADO_PATH")
    moedas_path = config.get("PATHS", "MOEDAS_PATH")

    return log_dir, resultado_path, moedas_path


def setup_logger(log_dir):
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    logger = logging.getLogger("cotacao")
    logger.setLevel(logging.INFO)

    if logger.hasHandlers():
        logger.handlers.clear()

    formatter = logging.Formatter(
        '[%(asctime)s] [%(levelname)s] [%(funcName)s:%(lineno)d] %(message)s',
        datefmt='%d%m%Y %H:%M:%S'
    )

    log_filename = f"log_{datetime.now().strftime('%d%m%Y')}.log"
    file_handler = logging.FileHandler(os.path.join(log_dir, log_filename), encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)

    class ColoredFormatter(logging.Formatter):
        def format(self, record):
            message = super().format(record)
            return Fore.CYAN + message if record.levelno == logging.INFO else Fore.RED + message

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(ColoredFormatter(
        '[%(asctime)s] [%(levelname)s] [%(funcName)s:%(lineno)d] %(message)s',
        datefmt='%d%m%Y %H:%M:%S'
    ))

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

def abrir_navegador():
    options = Options()
    options.add_argument("--incognito")
    driver = webdriver.Chrome(options=options)
    driver.get("https://www.bcb.gov.br/conversao")
    driver.maximize_window()
    return driver

def fechar_popup(driver, logger):
    try:
        btn = driver.find_element(By.CSS_SELECTOR, ".btn.btn-primary.btn-accept")
        btn.click()
        logger.info("Pop-up fechado com sucesso.")
    except NoSuchElementException:
        logger.info("Pop-up não encontrado, seguindo...")

def selecionar_moeda_saida(driver, moeda, logger):
    try:
        btn_para = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, 'button-converter-para'))
        )
        btn_para.click()

        lista_moedas = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, 'moedaResultado1'))
        )
        itens_moeda = lista_moedas.find_elements(By.TAG_NAME, 'li')

        moeda_encontrada = False
        for item in itens_moeda:
            texto = item.text.strip()
            if moeda in texto or f"({moeda})" in texto:
                actions = ActionChains(driver)
                actions.move_to_element(item).perform()
                item.click()
                logger.info(f"Moeda de saída selecionada: {texto}")
                time.sleep(1)
                moeda_encontrada = True
                break

        if not moeda_encontrada:
            logger.warning(f"Moeda {moeda} não encontrada. Texto disponível: {[item.text for item in itens_moeda]}")

    except Exception as e:
        logger.error(f"Erro ao selecionar moeda {moeda}: {e}")

def preencher_valor(driver, logger):
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//h1[text()="Conversor de Moedas"]'))
        )
        campo_valor = driver.find_element(By.NAME, "valorBRL")
        campo_valor.clear()
        campo_valor.send_keys("1,00")
        logger.info("Valor 1,00 inserido no campo.")
    except Exception as e:
        logger.error(f"Erro ao preencher valor: {e}")

def clicar_converter(driver, logger):
    time.sleep(1)
    btn_converter = driver.find_element(By.CSS_SELECTOR, 'button[title="Converter"]')
    btn_converter.click()
    logger.info("Botão 'Converter' clicado.")
    time.sleep(1)

def extrair_resultado(driver, logger, resultado_path, nova_data):
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//h1[text()="Conversor de Moedas"]'))
        )

        moeda_entrada = driver.find_element(By.ID, 'button-converter-de').text.split("(")[-1].replace(")", "").strip()
        moeda_saida = driver.find_element(By.ID, 'button-converter-para').text.split("(")[-1].replace(")", "").strip()

        container_saida = driver.find_element(
            By.XPATH, '//div[contains(@class, "card-body") and contains(., "Resultado da conversão:")]'
        )
        linhas = container_saida.text.split('\n')
        valor_cotacao = None

        for linha in linhas:
            if 'Resultado da conversão:' in linha:
                valor_str = linha.split(':')[-1].strip().replace('.', '').replace(',', '.')
                valor_float = float(valor_str)
                valor_cotacao = f"{math.floor(valor_float * 100) / 100:.2f}".replace('.', ',')
                break

        if valor_cotacao is None:
            raise ValueError("Valor da cotação não encontrado.")

        data_atual = nova_data
        status = "Consulta ok"

        return {
            "Moeda entrada": moeda_entrada,
            "Taxa": 1,
            "Moeda saída": moeda_saida,
            "Valor cotação": valor_cotacao,
            "Data": data_atual,
            "Status": status
        }

    except Exception as e:
        try:
            moeda_entrada = driver.find_element(By.ID, 'button-converter-de').text.split("(")[-1].replace(")", "").strip()
            moeda_saida = driver.find_element(By.ID, 'button-converter-para').text.split("(")[-1].replace(")", "").strip()
            logger.error(f"Erro ao extrair resultado da conversão de {moeda_entrada} para {moeda_saida}: {str(e)}")
        except:
            logger.error(f"Erro ao extrair resultado (não foi possível identificar as moedas): {str(e)}")

        return {
            "Moeda entrada": moeda_entrada if 'moeda_entrada' in locals() else '',
            "Taxa": 1,
            "Moeda saída": moeda_saida if 'moeda_saida' in locals() else '',
            "Valor cotação": "",
            "Data": datetime.now().strftime("%d/%m/%Y"),
            "Status": "Erro ao extrair resultado"
        }

def salvar_resultado(resultados, resultado_path, logger):
    try:
        try:
            df_existente = pd.read_excel(resultado_path)
        except FileNotFoundError:
            df_existente = pd.DataFrame()

        df_novo = pd.DataFrame(resultados)
        df_final = pd.concat([df_existente, df_novo], ignore_index=True)
        df_final.to_excel(resultado_path, index=False)
        logger.info(f"Resultado salvo em: {resultado_path}")
    except Exception as e:
        logger.error(f"Erro ao salvar resultado: {e}")

def selecionar_moeda_entrada(driver, logger, moeda_entrada_planilha):
    try:
        logger.info("Verificando moeda atual de entrada...")

        # Botão que mostra a moeda atual
        btn_de = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, 'button-converter-de'))
        )

        moeda_atual = btn_de.text.strip()
        logger.info(f"Moeda atual exibida: {moeda_atual}")

        # Se já estiver correta, retorna
        if moeda_entrada_planilha in moeda_atual or f"({moeda_entrada_planilha})" in moeda_atual:
            logger.info(f"A moeda de entrada já está correta: {moeda_entrada_planilha}")
            return

        logger.info("Moeda diferente. Clicando no botão para trocar...")
        btn_de.click()

        # Aguarda a lista de moedas aparecer
        lista_moedas = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, 'moedaBRL'))
        )

        # Busca todos os <a> dentro dos <li>
        itens_moeda = lista_moedas.find_elements(By.TAG_NAME, 'a')

        moeda_encontrada = False
        for item in itens_moeda:
            texto = item.text.strip()
            logger.debug(f"Item da lista: {texto}")
            if moeda_entrada_planilha in texto or f"({moeda_entrada_planilha})" in texto:
                actions = ActionChains(driver)
                actions.move_to_element(item).perform()
                item.click()
                logger.info(f"Moeda de entrada selecionada: {texto}")
                time.sleep(1)
                moeda_encontrada = True
                break

        if not moeda_encontrada:
            logger.warning(f"Moeda de entrada {moeda_entrada_planilha} não encontrada. Disponíveis: {[item.text for item in itens_moeda]}")

    except Exception as e:
        logger.error(f"Erro ao selecionar moeda de entrada {moeda_entrada_planilha}: {e}")


def carregar_moedas_do_excel(moedas_path):
    try:
        df = pd.read_excel(moedas_path)
        moedas_1 = df['Moeda entrada'].dropna().astype(str).tolist()
        moedas_2 = df['Moeda saída'].dropna().astype(str).tolist()
        return moedas_1, moedas_2
    except Exception as e:
        print(f"Erro ao carregar moedas da planilha: {e}")
        return [], []

def trocar_data(driver, logger, nova_data):
    try:
        logger.info(f"Trocando a data para: {nova_data}")

        # Aguarda o campo de data estar presente
        campo_data = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "dataMask"))
        )
        campo_data.clear()
        campo_data.send_keys(nova_data)

        # Clica fora para aplicar a data (pode clicar no título, por exemplo)
        titulo = driver.find_element(By.XPATH, '//h1[text()="Conversor de Moedas"]')
        titulo.click()

        logger.info("Data alterada com sucesso.")
        time.sleep(1)

    except Exception as e:
        logger.error(f"Erro ao trocar a data: {e}")


def main():
    log_dir, resultado_path, moedas_path = carregar_configuracoes()
    logger = setup_logger(log_dir)
    logger.info("==== Iniciando processo de cotação ====")

    driver = abrir_navegador()
    fechar_popup(driver, logger)

    # Trocar data aqui antes de qualquer conversão
    nova_data = "01/04/2025"  # <- você pode alterar essa data conforme necessário
    trocar_data(driver, logger, nova_data)

    moedas_1, moedas_2 = carregar_moedas_do_excel(moedas_path)

    resultados = []

    if not moedas_1 and not moedas_2:
        logger.error("Não foram encontradas moedas na planilha.")
        return

    for moeda_saida, moeda_entrada_planilha in zip(moedas_2, moedas_1):
        selecionar_moeda_entrada(driver, logger, moeda_entrada_planilha)
        selecionar_moeda_saida(driver, moeda_saida, logger)
        preencher_valor(driver, logger)
        clicar_converter(driver, logger)
        resultado = extrair_resultado(driver, logger, resultado_path, nova_data)
        resultados.append(resultado)

    salvar_resultado(resultados, resultado_path, logger)

    driver.quit()
    logger.info("==== Processo finalizado ====")

if __name__ == "__main__":
    main()
