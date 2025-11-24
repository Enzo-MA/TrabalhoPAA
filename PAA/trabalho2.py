import itertools
import time
import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# --- Estruturas de Dados ---
class Peca:
    def __init__(self, id, altura, largura):
        self.id = id
        self.altura = altura
        self.largura = largura
        # Assumindo que o peso é proporcional à área
        self.peso = altura * largura 

    def __repr__(self):
        return f"P{self.id}"

# --- Leitura de Arquivos ---
def ler_entrada(arquivo):
    pecas = []
    if not os.path.exists(arquivo):
        print(f"Erro: Arquivo {arquivo} não encontrado.")
        return []
    
    with open(arquivo, "r", encoding="utf-8") as f:
        linhas = [linha.strip() for linha in f if linha.strip() != ""]
        if not linhas:
            return []
        numero_de_pecas = int(linhas[0])
        for i in range(1, numero_de_pecas + 1):
            altura, largura = map(int, linhas[i].split())
            pecas.append(Peca(i - 1, altura, largura))
    return pecas

# --- Interface Gráfica (NOVO) ---
def desenhar_particao(grupo_a, grupo_b, titulo="Resultado"):
    """
    Desenha as peças empilhadas em dois 'porões' para visualizar o equilíbrio de peso.
    """
    # Cria figura com 2 eixos (lado a lado)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 6))
    
    # Define cores (mesma paleta da parte 1)
    cores = plt.cm.Set3(range(20))

    def desenhar_pilha(ax, grupo, nome):
        y_atual = 0
        max_largura = 0
        peso_total = sum(p.peso for p in grupo)

        # Fundo do porão (apenas estético)
        ax.set_title(f"{nome}\nPeso Total: {peso_total}")
        
        for peca in grupo:
            cor = cores[peca.id % 20]
            # Desenha o retângulo centralizado no eixo X (x = -largura/2)
            # Empilhando no eixo Y (y = y_atual)
            rect = patches.Rectangle((-peca.largura/2, y_atual), peca.largura, peca.altura, 
                                     linewidth=1, edgecolor='black', facecolor=cor, alpha=0.8)
            ax.add_patch(rect)
            
            # Texto no meio da peça
            ax.text(0, y_atual + peca.altura/2, 
                    f'P{peca.id}\n{peca.peso}', 
                    ha='center', va='center', fontsize=8, fontweight='bold')
            
            y_atual += peca.altura
            if peca.largura > max_largura:
                max_largura = peca.largura
        
        # Ajustes de visualização do gráfico
        margem = 50
        largura_limite = max(max_largura, 100) / 2 + margem
        ax.set_xlim(-largura_limite, largura_limite)
        ax.set_ylim(0, max(y_atual, 100) + margem)
        ax.set_aspect('equal') # Mantém proporção real
        
        # Remove os eixos numéricos para ficar mais limpo (parecido com desenho técnico)
        ax.axis('off')
        
        # Desenha uma "base" para o porão
        ax.plot([-largura_limite + 10, largura_limite - 10], [0, 0], color='black', linewidth=3)

    desenhar_pilha(ax1, grupo_a, "Porão 1")
    desenhar_pilha(ax2, grupo_b, "Porão 2")
    
    plt.suptitle(titulo, fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.show()

# --- Funções Auxiliares ---
def calcular_diferenca(grupo_a, grupo_b):
    peso_a = sum(p.peso for p in grupo_a)
    peso_b = sum(p.peso for p in grupo_b)
    return abs(peso_a - peso_b)

def exibir_e_desenhar(metodo, diff, grupo_a, grupo_b, tempo):
    peso_a = sum(p.peso for p in grupo_a)
    peso_b = sum(p.peso for p in grupo_b)
    ids_a = [p.id for p in grupo_a]
    ids_b = [p.id for p in grupo_b]
    
    print(f"{metodo}")
    print(f"Diferença de Peso: {diff}")
    print(f"Tempo: {tempo:.6f}s")
    print(f"Porão 1 (Peso {peso_a}): Peças {ids_a}")
    print(f"Porão 2 (Peso {peso_b}): Peças {ids_b}")
    
    # Chama a função gráfica
    desenhar_particao(grupo_a, grupo_b, f"{metodo}\nDiferença: {diff} | Tempo: {tempo:.4f}s")

# --- 6. Força Bruta ---
def forca_bruta_particao(pecas):
    inicio = time.time()
    melhor_diff = float('inf')
    melhor_divisao = ([], [])
    
    n = len(pecas)
    # Itera até n//2 + 1 para cobrir todas as combinações únicas de divisão
    for r in range(n // 2 + 1 + 1): 
        for combinacao in itertools.combinations(pecas, r):
            grupo_a = list(combinacao)
            set_a_ids = {p.id for p in grupo_a}
            grupo_b = [p for p in pecas if p.id not in set_a_ids]
            
            diff = calcular_diferenca(grupo_a, grupo_b)
            
            if diff < melhor_diff:
                melhor_diff = diff
                melhor_divisao = (grupo_a, grupo_b)
                if diff == 0: break
        if melhor_diff == 0: break
            
    tempo = time.time() - inicio
    return melhor_diff, melhor_divisao[0], melhor_divisao[1], tempo

# --- 7. Branch and Bound ---
def branch_and_bound_particao(pecas):
    inicio = time.time()
    pecas_ordenadas = sorted(pecas, key=lambda p: p.peso, reverse=True)
    peso_total = sum(p.peso for p in pecas)
    alvo = peso_total / 2.0
    
    melhor_diff = float('inf')
    melhor_config = [False] * len(pecas) # False = B, True = A
    escolha_atual = [False] * len(pecas)

    def resolver(idx, peso_atual_a):
        nonlocal melhor_diff, melhor_config
        
        # Poda: Se já passamos do alvo além do erro atual permitido
        if peso_atual_a - alvo >= (melhor_diff / 2):
            return

        # Chegou no fim
        if idx == len(pecas_ordenadas):
            peso_b = peso_total - peso_atual_a
            diff = abs(peso_atual_a - peso_b)
            if diff < melhor_diff:
                melhor_diff = diff
                melhor_config = list(escolha_atual)
            return
            
        # Poda Otimista (Lookahead):
        # Se pegarmos TODAS as peças restantes e somarmos ao menor monte, ainda não alcançamos o alvo?
        # (Cálculo simplificado para poda rápida)
        peso_restante = sum(p.peso for p in pecas_ordenadas[idx:])
        max_peso_alcancavel = peso_atual_a + peso_restante
        if max_peso_alcancavel < alvo:
             # O melhor que podemos fazer é max_peso_alcancavel vs (Total - max)
             diff_minima_possivel = (alvo - max_peso_alcancavel) * 2
             if diff_minima_possivel >= melhor_diff:
                 return

        # Ramo 1: Colocar no Grupo A
        escolha_atual[idx] = True
        resolver(idx + 1, peso_atual_a + pecas_ordenadas[idx].peso)
        if melhor_diff == 0: return

        # Ramo 2: Colocar no Grupo B
        escolha_atual[idx] = False
        resolver(idx + 1, peso_atual_a)

    resolver(0, 0)
    
    grupo_a = []
    grupo_b = []
    for i, foi_para_a in enumerate(melhor_config):
        if foi_para_a: grupo_a.append(pecas_ordenadas[i])
        else: grupo_b.append(pecas_ordenadas[i])
            
    tempo = time.time() - inicio
    return melhor_diff, grupo_a, grupo_b, tempo

# --- 8. Heurística (Guloso) ---
def heuristica_gulosa(pecas):
    inicio = time.time()
    pecas_ordenadas = sorted(pecas, key=lambda p: p.peso, reverse=True)
    grupo_a = []
    grupo_b = []
    peso_a = 0
    peso_b = 0
    
    for peca in pecas_ordenadas:
        if peso_a <= peso_b:
            grupo_a.append(peca)
            peso_a += peca.peso
        else:
            grupo_b.append(peca)
            peso_b += peca.peso
            
    diff = abs(peso_a - peso_b)
    tempo = time.time() - inicio
    return diff, grupo_a, grupo_b, tempo

# --- Main ---
def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    caminho_entrada = os.path.join(script_dir, "entrada4.txt") # ALERTA: Mude o arquivo aqui se necessário
    
    print(f"Lendo: {caminho_entrada}")
    pecas = ler_entrada(caminho_entrada)
    
    if not pecas:
        print("Erro na leitura ou arquivo vazio.")
        return

    print(f"Número de peças: {len(pecas)}")

    # 1. Força Bruta (Limitado para não travar o PC se tiver muitas peças)
    if len(pecas) <= 20: 
        diff, ga, gb, tempo = forca_bruta_particao(pecas)
        exibir_e_desenhar("FORÇA BRUTA", diff, ga, gb, tempo)
    else:
        print("Muitas peças para Força Bruta. Pulando...")

    # 2. Branch and Bound
    diff, ga, gb, tempo = branch_and_bound_particao(pecas)
    exibir_e_desenhar("BRANCH AND BOUND", diff, ga, gb, tempo)

    # 3. Heurística
    diff, ga, gb, tempo = heuristica_gulosa(pecas)
    exibir_e_desenhar("HEURÍSTICA", diff, ga, gb, tempo)

if __name__ == "__main__":
    main()