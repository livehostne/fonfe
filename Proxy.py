import os
import time
import socks
import socket
import requests
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
from colorama import Fore, Style, init
from datetime import datetime

init(autoreset=True)  # Inicializa o Colorama para colorir o texto no terminal

def display_credits():
    print(f"{Fore.GREEN}Este script foi feito com carinho por @ardems37 💖{Style.RESET_ALL}")
    print(f"{Fore.GREEN}Por favor, não remova os créditos.{Style.RESET_ALL}")
    time.sleep(2)  # Pausa para garantir que a mensagem seja vista

def create_folders():
    folders = ['http', 'socks4', 'socks5', 'results', 'logs']
    for folder in folders:
        if not os.path.exists(folder):
            os.makedirs(folder)
            print(f"Pasta '{folder}' criada. Coloque seus proxies nela e execute o script novamente.")

def fetch_proxies_from_api(protocol):
    url = f"https://api.proxyscrape.com/v2/?request=displayproxies&protocol={protocol}&timeout=10000&country=all&ssl=all&anonymity=all"
    response = requests.get(url)
    proxies = []
    if response.status_code == 200:
        proxies = [(line.split(':')[0], int(line.split(':')[1])) for line in response.text.split('\n') if line]
    else:
        print(f"Falha ao buscar proxies da API: {response.status_code}")
    return proxies

def read_proxies_from_folder(folder_path):
    proxies = []
    if not os.listdir(folder_path):
        print(f"A pasta '{folder_path}' está vazia. Por favor, adicione arquivos de proxies e execute o script novamente.")
        return proxies
    for filename in os.listdir(folder_path):
        if filename.endswith('.txt'):
            with open(os.path.join(folder_path, filename), 'r') as file:
                for line in file:
                    line = line.strip()
                    if line:
                        try:
                            host, port = line.split(':')
                            proxies.append((host, int(port)))
                        except ValueError:
                            log_message(f"Formato inválido no arquivo {filename}: {line}")
    return proxies

def check_proxy(proxy, proxy_type):
    proxy_host, proxy_port = proxy
    result = {
        'proxy': proxy,
        'type': proxy_type,
        'live': False
    }
    
    try:
        start_time = time.time()
        
        if proxy_type == 'HTTP':
            proxies = {
                'http': f'http://{proxy_host}:{proxy_port}',
                'https': f'http://{proxy_host}:{proxy_port}'
            }
            try:
                response = requests.get('http://httpbin.org/ip', proxies=proxies, timeout=5)
                result['live'] = True
            except Exception:
                result['live'] = False
        elif proxy_type == 'SOCKS4':
            socks.set_default_proxy(socks.SOCKS4, proxy_host, proxy_port)
            socket.socket = socks.socksocket
            try:
                test_socket = socket.create_connection(('www.google.com', 80), timeout=5)
                test_socket.close()
                result['live'] = True
            except Exception:
                result['live'] = False
        elif proxy_type == 'SOCKS5':
            socks.set_default_proxy(socks.SOCKS5, proxy_host, proxy_port)
            socket.socket = socks.socksocket
            try:
                test_socket = socket.create_connection(('www.google.com', 80), timeout=5)
                test_socket.close()
                result['live'] = True
            except Exception:
                result['live'] = False
    
    except Exception:
        result['live'] = False
    
    return result

def save_results_to_file(results, protocol):
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'results/proxy_results_{protocol}_{timestamp}.txt'
    with open(filename, 'w') as file:
        for result in results:
            if result['live']:
                file.write(f"{result['proxy'][0]}:{result['proxy'][1]}\n")
    print(f"Resultados salvos em '{filename}'")

def log_message(message):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open('logs/proxy_checker.log', 'a') as log_file:
        log_file.write(f"[{timestamp}] {message}\n")

def main():
    display_credits()  # Exibe os créditos na inicialização
    create_folders()
    
    # Menu de seleção de pasta ou API
    print("Escolha a fonte de proxies:")
    print("1: HTTP (pasta)")
    print("2: SOCKS4 (pasta)")
    print("3: SOCKS5 (pasta)")
    print("4: HTTP (API)")
    print("5: SOCKS4 (API)")
    print("6: SOCKS5 (API)")
    
    choice = input("Digite o número da sua escolha: ")
    
    if choice == '1':
        folder_path = 'http'
        proxy_type = 'HTTP'
        proxies = read_proxies_from_folder(folder_path)
    elif choice == '2':
        folder_path = 'socks4'
        proxy_type = 'SOCKS4'
        proxies = read_proxies_from_folder(folder_path)
    elif choice == '3':
        folder_path = 'socks5'
        proxy_type = 'SOCKS5'
        proxies = read_proxies_from_folder(folder_path)
    elif choice == '4':
        proxy_type = 'HTTP'
        proxies = fetch_proxies_from_api('http')
    elif choice == '5':
        proxy_type = 'SOCKS4'
        proxies = fetch_proxies_from_api('socks4')
    elif choice == '6':
        proxy_type = 'SOCKS5'
        proxies = fetch_proxies_from_api('socks5')
    else:
        print("Escolha inválida. Encerrando.")
        return

    if not proxies:
        print("Nenhum proxy encontrado. Encerrando.")
        return
    
    total_proxies = len(proxies)
    live_proxies = 0
    
    # Define o número de threads (bots) a ser utilizado
    while True:
        try:
            num_threads = int(input("Digite o número de bots (10 a 250): "))
            if 10 <= num_threads <= 250:
                break
            else:
                print("Por favor, digite um número entre 10 e 250.")
        except ValueError:
            print("Entrada inválida. Por favor, digite um número.")

    # Usa ThreadPoolExecutor para execução paralela
    results = []
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        # Envia tarefas para o executor
        future_to_proxy = {executor.submit(check_proxy, proxy, proxy_type): proxy for proxy in proxies}
        
        # Barra de carregamento com a biblioteca tqdm
        with tqdm(total=total_proxies, desc="Verificando proxies", ncols=100, bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}{postfix}]") as pbar:
            for future in as_completed(future_to_proxy):
                proxy = future_to_proxy[future]
                try:
                    result = future.result()
                    results.append(result)
                    
                    if result['live']:
                        live_proxies += 1
                        pbar.set_postfix_str(f"{Fore.GREEN}Live: {live_proxies}{Style.RESET_ALL}")
                    else:
                        pbar.set_postfix_str(f"{Fore.RED}Not Live: {total_proxies - live_proxies}{Style.RESET_ALL}")
                except Exception as exc:
                    log_message(f"Proxy {proxy} gerou uma exceção: {exc}")
                finally:
                    pbar.update(1)
    
    print(f"{Fore.GREEN}Total de proxies verificados: {total_proxies}{Style.RESET_ALL}")
    print(f"{Fore.GREEN}Total de proxies vivos: {live_proxies}{Style.RESET_ALL}")
    
    # Salva os resultados em um arquivo
    save_results_to_file(results, proxy_type)

if __name__ == "__main__":
    main()
