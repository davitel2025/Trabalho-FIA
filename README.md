# Trabalho FIA

Mundo dos Blocos de Tamanho Variável resolvido com SAT. O repositório contém, para cada situação, o CNF, o mapa de variáveis e o resultado do solver, além da comparação entre o plano manual e o plano da máquina.

## Estrutura

| Pasta | Situação |
|---|---|
| [`sit1_S0_Sf4`](https://github.com/davitel2025/Trabalho-FIA/tree/main/sit1_S0_Sf4) | Situação 1 (S0 → Sf4) |
| [`sit2_S0_S5`](https://github.com/davitel2025/Trabalho-FIA/tree/main/sit2_S0_S5) | Situação 2 (S0 → S5) |
| [`sit3_S0_S7`](https://github.com/davitel2025/Trabalho-FIA/tree/main/sit3_S0_S7) | Situação 3 (S0 → S7) |

Cada pasta contém:

| Arquivo | Conteúdo |
|---|---|
| `.cnf` | Fórmula em formato DIMACS enviada ao solver |
| `.map` | Dicionário que associa cada número de variável ao seu significado |
| `resultado1.txt` | Saída do solver (`SAT` e os valores das variáveis) |

## Como executar

O `interpretar.py` lê o `.map` e o resultado no mesmo diretório em que é executado. Por isso, os arquivos da situação precisam estar na **pasta raiz**.

1. Abra a pasta da situação desejada.
2. Copie **todos** os arquivos dela (`.cnf`, `.map` e `resultado1.txt`) para a pasta raiz do projeto.
3. Na raiz, execute:

```bash
python3 interpretar.py resultado1.txt --verbose
```

Exemplo para a situação 2:

```bash
cp sit2_S0_S5/* .
python3 interpretar.py resultado1.txt --verbose
```

> **Atenção:** os arquivos têm o mesmo nome em todas as pastas. Ao trocar de situação, copie os arquivos da nova pasta para a raiz, sobrescrevendo os anteriores.

---

# Resolução manual × resultado da máquina

Notação: `move(bloco, destino, ponto, passo)`, onde `T` é a mesa.

## Situação 1

**Manual**
```text
move(d,c,0,0)
move(a,b,5,1)
move(d,T,2,2)
move(a,c,0,3)
```

**Máquina**
```text
PLANO ENCONTRADO (4 acoes):
1. t=0: mover bloco 'd' para CIMA de 'c' em p=0
2. t=1: mover bloco 'a' para CIMA de 'b' em p=5
3. t=2: mover bloco 'd' para a MESA em p=2
4. t=3: mover bloco 'a' para CIMA de 'c' em p=0
```

**Resultado: igual.** Mesmos blocos, destinos, posições e tempos.

## Situação 2

**Manual**
```text
move(b,T,2,0)
move(a,b,2,1)
move(c,d,4,2)
move(a,c,4,3)
move(b,c,5,4)
```

**Máquina**
```text
PLANO ENCONTRADO (5 acoes):
1. t=0: mover bloco 'a' para CIMA de 'd' em p=3
2. t=1: mover bloco 'b' para CIMA de 'a' em p=3
3. t=2: mover bloco 'c' para CIMA de 'd' em p=4
4. t=3: mover bloco 'b' para CIMA de 'c' em p=5
5. t=4: mover bloco 'a' para CIMA de 'c' em p=4
```

| Passo | Manual | Máquina |
|---|---|---|
| 0 | `move(b,T,2,0)` | `a` sobre `d`, p=3 |
| 1 | `move(a,b,2,1)` | `b` sobre `a`, p=3 |
| 2 | `move(c,d,4,2)` | `c` sobre `d`, p=4 |
| 3 | `move(a,c,4,3)` | `b` sobre `c`, p=5 |
| 4 | `move(b,c,5,4)` | `a` sobre `c`, p=4 |

**Resultado: diferente, mas equivalente.** Os dois planos têm 5 ações e partem do mesmo S0 e chegam ao mesmo S5. O manual usa a mesa; a máquina empilha `a` e `b` sobre `d`. Ambos respeitam as regras (topo livre, sem sobreposição, estabilidade). Cinco é o mínimo, pois `a` e `b` precisam sair de cima de `c` e voltar (4 movimentos) e `c` precisa se mover (1).

## Situação 3

**Manual**
```text
move(d,c,0,0)
move(a,b,5,1)
move(d,T,2,2)
move(a,c,0,3)
move(b,c,1,4)
move(d,T,3,5)
```

**Máquina**
```text
PLANO ENCONTRADO (6 acoes):
1. t=0: mover bloco 'd' para CIMA de 'c' em p=0
2. t=1: mover bloco 'a' para CIMA de 'b' em p=5
3. t=2: mover bloco 'd' para a MESA em p=2
4. t=3: mover bloco 'a' para CIMA de 'c' em p=0
5. t=4: mover bloco 'b' para CIMA de 'c' em p=1
6. t=5: mover bloco 'd' para a MESA em p=3
```

**Resultado: igual.** Mesmos blocos, destinos, posições e tempos.

---

# Resumo

| Situação | Ações (manual) | Ações (máquina) | Resultado |
|---|---|---|---|
| 1 | 4 | 4 | Igual |
| 2 | 5 | 5 | Diferente, equivalente |
| 3 | 6 | 6 | Igual |

Nas situações 1 e 3, o plano da máquina é idêntico ao manual. Na situação 2, a máquina encontrou uma sequência alternativa com o mesmo número de ações.

## Repositório

[Trabalho-FIA no GitHub](https://github.com/davitel2025/Trabalho-FIA)
