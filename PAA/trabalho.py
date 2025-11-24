import itertools
import time
import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches

class Peca:
    def __init__(self, id, altura, largura):
        self.id = id
        self.altura = altura
        self.largura = largura
        self.x = 0  # posição
        self.y = 0
        self.placa = 0  # qual placa está
    def perimetro(self):
        return 2 * (self.altura + self.largura)

class Placa:
    def __init__(self, id):
        self.id = id
        self.largura = 300
        self.comprimento = 300
        self.margem = 10
        self.matriz = [[False]*300 for _ in range(300)] #matriz de alocação da placa, cada item 300 linhas x 300 colunas. Se o item = false é um espaço livre
        self.pecas = []
        self.custo_corte = 0

def ler_entrada(arquivo):
    pecas = []
    with open(arquivo, "r", encoding="utf-8") as f:
        linhas = [linha.strip() for linha in f if linha.strip() != ""]
        numero_de_pecas = int(linhas[0]) #leitura da primeira linha para definir quantas peças são
        for i in range(1, numero_de_pecas + 1):
            altura, largura = map(int, linhas[i].split())
            pecas.append(Peca(i - 1, altura, largura))
    return pecas

def disponibilidade_peca(placa, peca, x, y): #verifica se a posição cabe na posição (x,y) da placa
    #funcao resulta em um bool indicando se pode colcar + um float com o custo
    if x < placa.margem or y < placa.margem:
        return False, 0
    if x + peca.largura > placa.largura - placa.margem:
        return False, 0
    if y + peca.altura > placa.comprimento - placa.margem:
        return False, 0
    for i in range(y, y + peca.altura): #verificação se existe alguma outra placa ocupando o lugar
        for j in range(x, x + peca.largura):
            if placa.matriz[i][j]:
                return False, 0
    custo = peca.perimetro() * 0.01
    return True, custo

def colocar_peca(placa, peca, x, y): #marca na placa a posição da peça
    peca.x = x
    peca.y = y
    peca.placa = placa.id
    for i in range(y, y + peca.altura):
        for j in range(x, x + peca.largura):
            placa.matriz[i][j] = True
    custo = peca.perimetro() * 0.01
    placa.custo_corte += custo
    placa.pecas.append(peca)
    return custo

def tentar_encaixar(placas, peca):
    for placa in placas:
        for y in range(placa.margem, placa.comprimento - placa.margem - peca.altura + 1):
            for x in range(placa.margem, placa.largura - placa.margem - peca.largura + 1):
                pode, custo = disponibilidade_peca(placa, peca, x, y)
                if pode:
                    colocar_peca(placa, peca, x, y)
                    return True, custo
    #Tenta posições de cima para baxo, da esquerda para direita, se não couber em nenhum adiciona uma nova
    nova_placa = Placa(len(placas))
    placas.append(nova_placa)
    colocar_peca(nova_placa, peca, nova_placa.margem, nova_placa.margem)
    return True, peca.perimetro() * 0.01

def calcular_custo_total(placas):
    custo_placas = len(placas) * 1000
    custo_cortes = sum(placa.custo_corte for placa in placas)
    return custo_placas + custo_cortes

def forca_bruta(pecas):
    inicio = time.time()
    melhor_custo = float('inf') #passa o valor infinito
    melhor_solucao = None
    total = 0
    # gerar permutações
    for permutacao in itertools.permutations(pecas): #gera todas permutações possíveis
        total += 1
        placas = [Placa(0)] #inicializa uma lista de placas para a possibilidade de precisar de mais de uma
        for peca in permutacao:
            encaixou, _ = tentar_encaixar(placas, peca)
        custo = calcular_custo_total(placas)
        if custo < melhor_custo:
            melhor_custo = custo
            melhor_solucao = placas
    tempo = time.time() - inicio
    print(f"Permutações testadas: {total}")
    return melhor_custo, melhor_solucao, tempo

def branch_and_bound(pecas):
    inicio = time.time()
    melhor_custo = float('inf')
    melhor_solucao = None
    total_nos = 0

    def copiar_placas(placas):
        novas = []
        for p in placas:
            novo = Placa(p.id)
            novo.matriz = [linha[:] for linha in p.matriz]
            novo.pecas = []
            for pc in p.pecas:
                copia = Peca(pc.id, pc.altura, pc.largura)
                copia.x = pc.x
                copia.y = pc.y
                copia.placa = pc.placa
                novo.pecas.append(copia)
            novo.custo_corte = p.custo_corte
            novas.append(novo)
        return novas
    def calcular_bound(placas, pecas_restantes): # Calcula um Bound otimista (Assume que não precisará de NENHUMA placa nova para o resto): Custo atual + (perímetro restante * 0.01)
        custo_placas = len(placas) * 1000
        custo_corte_atual = sum(placa.custo_corte for placa in placas)
        corte_restante = sum(p.perimetro() for p in pecas_restantes) * 0.01
        return custo_placas + custo_corte_atual + corte_restante

    def bb_recursivo(pecas_restantes, placas):
        nonlocal melhor_custo, melhor_solucao, total_nos
        total_nos += 1
        # Poda
        bound = calcular_bound(placas, pecas_restantes)
        if bound >= melhor_custo:
            return
        # Caso base: Nenhuma peça restante -> Solução completa encontrada
        if not pecas_restantes:
            custo_final = calcular_custo_total(placas)
            if custo_final < melhor_custo:
                melhor_custo = custo_final
                melhor_solucao = copiar_placas(placas)
            return
        for i, peca in enumerate(pecas_restantes):# RAMIFICAÇÃO: Tenta cada peça restante como a "próxima", simula as permutações que o Força Bruta faz, mas cortando caminhos ruins            
            # Cria nova lista de pendentes sem a peça atual
            novas_pendentes = pecas_restantes[:i] + pecas_restantes[i+1:]
            novo_estado = copiar_placas(placas)
            encaixou, _ = tentar_encaixar(novo_estado, peca)            
            if encaixou:
                bb_recursivo(novas_pendentes, novo_estado)
            else:
                # Opção 2: Se não coube em nenhuma, SÓ ENTÃO abre nova placa.
                novo_estado_placa = copiar_placas(placas)
                nova_placa = Placa(len(novo_estado_placa))
                novo_estado_placa.append(nova_placa)
                # Coloca na nova placa
                colocar_peca(nova_placa, peca, nova_placa.margem, nova_placa.margem)  
                bb_recursivo(novas_pendentes, novo_estado_placa)
    placas_iniciais = [Placa(0)]
    # Inicia passando TODAS as peças como "restantes"
    bb_recursivo(pecas, placas_iniciais)
    
    tempo = time.time() - inicio
    print("Total de nós explorados", total_nos)
    return melhor_custo, melhor_solucao, tempo

def heuristica_first_fit_area_decrescente(pecas): #ordena peças por área decrescente e usa First Fit
    inicio = time.time()
    pecas_ordenadas = sorted(pecas, key=lambda p: p.altura * p.largura, reverse=True)
    placas = [Placa(0)]
    for peca in pecas_ordenadas:
        tentar_encaixar(placas, peca)
    custo = calcular_custo_total(placas)
    tempo = time.time() - inicio
    return custo, placas, tempo

def desenhar_solucao(placas, titulo="Solução"):
    n_placas = len(placas)
    fig, axes = plt.subplots(1, n_placas, figsize=(8 * n_placas, 8))
    if n_placas == 1:
        axes = [axes]
    cores = plt.cm.Set3(range(20))
    for idx, placa in enumerate(placas):
        ax = axes[idx]
        ax.set_xlim(0, 300)
        ax.set_ylim(0, 300)
        ax.set_aspect('equal')
        ax.set_title(f'Placa {idx+1}\nCusto corte: R${placa.custo_corte:.2f}')
        ax.set_xlabel('Largura (cm)')
        ax.set_ylabel('Altura (cm)')
        margem_rect = patches.Rectangle((10, 10), 280, 280, linewidth=2, edgecolor='red', facecolor='none', linestyle='--')
        ax.add_patch(margem_rect)
        for i, peca in enumerate(placa.pecas):
            cor = cores[peca.id % 20]
            rect = patches.Rectangle((peca.x, peca.y), peca.largura, peca.altura, linewidth=2, edgecolor='black', facecolor=cor, alpha=0.7)
            ax.add_patch(rect)
            ax.text(peca.x + peca.largura/2, peca.y + peca.altura/2, f'P{peca.id}\n{peca.altura}x{peca.largura}', ha='center', va='center', fontsize=8, fontweight='bold')
        ax.grid(True, alpha=0.3)
    plt.suptitle(titulo, fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.show()

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    caminho_entrada = os.path.join(script_dir, "entrada3.txt")
    pecas = ler_entrada(caminho_entrada)
    print(f"Número de peças: {len(pecas)}")
    #força bruta funcionando apenas para poucos itens <=8
    if len(pecas) <= 8:
        print("FORÇA BRUTA")
        custo_fb, placas_fb, tempo_fb = forca_bruta(pecas)
        print(f"Custo: R${custo_fb:.2f}")
        print(f"Tempo: {tempo_fb:.4f}s")
        print(f"Placas usadas: {len(placas_fb)}")
        desenhar_solucao(placas_fb, "Solução Força Bruta")

        print("BRANCH AND BOUND")
        custo_bb, placas_bb, tempo_bb = branch_and_bound(pecas)
        print(f"Custo: R${custo_bb:.2f}")
        print(f"Tempo: {tempo_bb:.4f}s")
        print(f"Placas usadas: {len(placas_bb)}")
        desenhar_solucao(placas_bb, "Solução Branch and Bound")
    else:
        print("Muitas peças para força bruta! Usando apenas heurística.")

    print("HEURÍSTICA")
    custo_h, placas_h, tempo_h = heuristica_first_fit_area_decrescente(pecas)
    print(f"Custo: R${custo_h:.2f}")
    print(f"Tempo: {tempo_h:.4f}s")
    print(f"Placas usadas: {len(placas_h)}")
    desenhar_solucao(placas_h, "Solução Heurística")

if __name__ == "__main__":
    main()
