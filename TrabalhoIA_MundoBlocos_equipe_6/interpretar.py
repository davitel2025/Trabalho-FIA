#!/usr/bin/env python3
"""
Interpreta a saida do miniSAT usando trab01_blocos2SAT.map.
Uso: python3 interpretar.py resultado1.txt [--verbose] [--map arquivo.map]
"""
import argparse
import re

BLOCKS = {'a': 1, 'b': 1, 'c': 2, 'd': 3}
TABLE = 'T'


def span(b, p):
    return set(range(p, p + BLOCKS[b]))


def derivar_on(estado):
    """on(b,y): derivado de at, lev e sobreposicao de spans (nao codificado)."""
    on = {}
    for b, (p, l) in estado.items():
        if l == 0:
            on[b] = [TABLE]
        else:
            on[b] = sorted(y for y, (py, ly) in estado.items()
                           if y != b and ly == l - 1 and span(b, p) & span(y, py))
    return on


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('resultado')
    ap.add_argument('--map', default='trab01_blocos2SAT.map')
    ap.add_argument('--verbose', action='store_true')
    a = ap.parse_args()

    # 1. leitura do mapa: id -> (tipo, args)
    idmap, horizonte = {}, None
    for line in open(a.map):
        line = line.strip()
        if line.startswith('# HORIZON'):
            horizonte = int(line.split()[-1])
            continue
        m = re.match(r'(\d+) (\w+)\((.*)\)', line)
        if m:
            idmap[int(m.group(1))] = (m.group(2), m.group(3).split(','))

    # 2. leitura do resultado do solver
    linhas = open(a.resultado).read().split()
    if not linhas or linhas[0] != 'SAT':
        print("INSATISFATIVEL: nao existe plano com esse horizonte.")
        return
    verdadeiras = {int(x) for x in linhas[1:] if x != '0' and int(x) > 0}

    # 3. filtragem: mv, at, lev verdadeiros
    acoes, at, lev = [], {}, {}
    for v in verdadeiras:
        if v not in idmap:
            continue
        tipo, arg = idmap[v]
        if tipo == 'mv':
            b, y, p, t = arg
            acoes.append((int(t), b, y, int(p)))
        elif tipo == 'at':
            at[(arg[0], int(arg[2]))] = int(arg[1])
        elif tipo == 'lev':
            lev[(arg[0], int(arg[2]))] = int(arg[1])

    # 4. ordenacao temporal e traducao
    acoes.sort()
    print(f"PLANO ENCONTRADO ({len(acoes)} acoes):")
    for n, (t, b, y, p) in enumerate(acoes, 1):
        destino = "a MESA" if y == TABLE else f"CIMA de '{y}'"
        print(f"{n}. t={t}: mover bloco '{b}' para {destino} em p={p}")

    def estado(t):
        return {b: (at[(b, t)], lev[(b, t)]) for b in BLOCKS}

    if a.verbose:
        for t in range(horizonte + 1):
            print(f"\nESTADO t={t}:")
            for b, (p, l) in sorted(estado(t).items()):
                print(f"  {b}: ponto inicial p={p}, nivel l={l}")
            for b, ys in sorted(derivar_on(estado(t)).items()):
                print(f"  {b} esta sobre: {', '.join(ys)}")
    else:
        print(f"\nESTADO FINAL (t={horizonte}):")
        for b, (p, l) in sorted(estado(horizonte).items()):
            print(f"  {b}: ponto inicial p={p}, nivel l={l}")
        print(f"\nRELACOES 'on' em t={horizonte}:")
        for b, ys in sorted(derivar_on(estado(horizonte)).items()):
            print(f"  {b} esta sobre: {', '.join(ys)}")


if __name__ == '__main__':
    main()
