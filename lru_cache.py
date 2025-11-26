# lru_cache significa Least Recently Used Cache (cache dos menos recentemente usados).
# Ele cria um cache interno onde guarda o resultado de chamadas anteriores da função.
# Quando a função é chamada novamente com os mesmos parâmetros, o Python não executa o código outra vez — apenas retorna o resultado já armazenado.

from fastapi import FastAPI
from functools import lru_cache

app = FastAPI()

@lru_cache(maxsize=256)
def calcular_dado_pesado(x: int):
    print("Processando...")  # só processa da 1ª vez
    return x * x * x

@app.get("/calc/{x}")
def calc(x: int):
    return {"resultado": calcular_dado_pesado(x)}
