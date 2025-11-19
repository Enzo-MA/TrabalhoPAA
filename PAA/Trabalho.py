class Peca:
   def __init__(self,id,altura,largura):
      self.id=id
      self.altura=altura
      self.largura=largura
      self.x=0 #posição
      self.y=0
      self.placa= 0 #qualplacaestá
   def perimetro(self):
      return 2 *(self.altura + self.largura)
class Placa:
   def __init__(self,id):
      self.id=id
      self.largura=300
      self.comprimento=300
      self.margem=10
      self.matriz= [[False]*300 for _ in range(300)] #matriz de alocação da placa, cada item 300 linhas x 300 colunas. Se o item = false é um espaço livre
      self.pecas=[]
      self.custo_corte=0
      
def ler_entrada(arquivo):
   pecas=[]
   with open(arquivo, "r", encoding="utf-8") as arquivo:
      linhas = [linha.strip() for linha in arquivo]
      numero_de_pecas= int(linhas[0]) #leitura da primeira linha para definir quantas peças são
      for i in range(1, numero_de_pecas+1):
         altura,largura =map(int, linhas[i].split)
         pecas.append(Peca(i-1, altura, largura))
   return pecas

def pode_colocar_peca(placa, peca, x, y): #verifica se a posição cabe na posição (x,y) da placa
   #funcao resulta em um bool indicando se pode colcar + um float com o custo
   if x < placa.margem or y < placa.margem:
      return False , 0
   if x+peca.largura > placa.largura - placa.margem:
      return False , 0
   if y+peca.altura > peca.altura - placa.margem:
      return False, 0
   for i in range(y, y + peca.altura): #verificação se existe alguma outra placa ocupando o lugar
      for j in range(x,x+peca.largura):
         if placa.matriz[i][j]:
            return False, 0
   custo= peca.perimetro()*0.1
   return True,custo