import os
import json
import gspread

def conectar_google():
    if 'GOOGLE_SHEETS_CREDS' in os.environ:
        # Pega a secret bruta
        creds_raw = os.environ['GOOGLE_SHEETS_CREDS']
        
        # Remove espaços em branco no início/fim e corrige quebras de linha duplas
        creds_clean = creds_raw.strip().replace('\\\\n', '\\n')
        
        try:
            creds_dict = json.loads(creds_clean)
            return gspread.service_account_from_dict(creds_dict)
        except Exception as e:
            print(f"Erro ao processar o JSON da Secret: {e}")
            raise
    else:
        # Local (PC)
        return gspread.service_account(filename='credentials.json')

# Inicialização
gc = conectar_google()
sh = gc.open_by_key('1j315AVuP2fwk36ULcHEhEtYIO-9zjdSiOi-G97Vz64U')
worksheet = sh.get_worksheet(0)

# 2. Função para buscar LPA e VPA no Investing
def buscar_dados_investing(ticker):
    # O Investing costuma usar o padrão: investing.com/equities/nome-do-ativo
    # Para ativos brasileiros, geralmente é 'ticker-sa' (ex: petr4-sa)
    url = f"https://br.investing.com/equities/{ticker.lower()}-sa"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # O Investing muda a estrutura com frequência. 
        # Geralmente os dados ficam em elementos com data-test="LPA" ou em tabelas de resumo.
        # Este é um exemplo de captura por texto (mais resiliente a mudanças de ID)
        lpa = soup.find(text="LPA").find_next('span').text if soup.find(text="LPA") else "N/A"
        vpa = soup.find(text="VPA").find_next('span').text if soup.find(text="VPA") else "N/A"
        
        return lpa, vpa
    except Exception as e:
        print(f"Erro ao buscar {ticker}: {e}")
        return "Erro", "Erro"

# 3. Loop para ler da coluna A (linhas 2 a 11) e escrever em K e M
def processar_planilha():
    # Lê todos os tickers de A2 até A11
    tickers = worksheet.get('A2:A11')
    
    for i, row in enumerate(tickers):
        if not row: continue
        ticker = row[0]
        print(f"Buscando dados para: {ticker}...")
        
        lpa, vpa = buscar_dados_investing(ticker)
        
        # Linha atual na planilha (começa em 2)
        row_idx = i + 2
        
        # Atualiza Coluna K (LPA) e Coluna M (VPA)
        # K é a 11ª coluna, M é a 13ª
        worksheet.update_cell(row_idx, 11, lpa)
        worksheet.update_cell(row_idx, 13, vpa)
        
        # Pausa curta para evitar bloqueio do site
        time.sleep(2)

if __name__ == "__main__":
    processar_planilha()
