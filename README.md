# Teste Técnico - RPA Python - Conversão de Moedas

Este repositório contém a solução desenvolvida para o case técnico de Desenvolvedor RPA, com foco na automação do processo de cotação de moedas utilizadas em contratos internacionais.

## 🧾 Sobre o projeto

A proposta do desafio é automatizar a consulta diária de cotações no site do Banco Central, com o objetivo de eliminar atividades manuais, reduzir erros operacionais e garantir que as informações estejam sempre atualizadas no sistema da empresa.

O código desenvolvido realiza a leitura de moedas de entrada e saída a partir de um arquivo de parâmetros (Excel), consulta as cotações do dia atual diretamente no site do Banco Central, e gera um relatório consolidado com os resultados encontrados.

## ✅ O que o script faz

- Lê pares de moedas de um arquivo `.xlsx` de parâmetros;
- Acessa o site do Banco Central para buscar a cotação da data atual;
- Gera um arquivo Excel com as seguintes informações:  
  `Moeda entrada | Taxa | Moeda saída | Valor cotação | Data`;
- Registra logs detalhados sobre o tempo gasto em cada cotação e erros encontrados;
- Cria um segundo relatório de status com o resultado de cada consulta.

## 💼 Exemplo de saída

```text
Moeda entrada | Taxa | Moeda saída | Valor cotação | Data       | Status
BRL           | 1    | COP          | 724,637       | 01/04/2025 | Consulta ok
BRL           | 1    | AFN          | 0,081         | 28/03/2025 | Cotação encontrada não é da data atual
