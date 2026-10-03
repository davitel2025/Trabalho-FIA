#!/usr/bin/env python3
"""
Mundo dos Blocos de Tamanho Variavel -> CNF (DIMACS) para SAT solver.

Blocos: a,b (comprimento 1), c (2), d (3). Mesa com pontos 0..6 e 6 slots.

Variaveis proposicionais (como no manual):
    at(b,p,t)     bloco b comeca no ponto p no instante t
    lev(b,l,t)    bloco b esta no nivel l no instante t
    clr(b,t)      topo de b livre no instante t
    mv(b,y,p,t)   mover b para cima de y (bloco ou mesa T), comecando em p
Auxiliares (apenas para escrever as clausulas, nao fazem parte do dominio):
    cov(b,i,l,t)  b cobre o slot i no nivel l
    occ(i,l,t)    algum bloco cobre o slot i no nivel l
    blk(b,i,l,t)  b cobre o slot i no nivel l E ha algo cobrindo i no nivel l+1
A relacao on(b,y,t) NAO e codificada: e derivada em interpretar.py.

Grupos de clausulas (numeracao igual a da descricao formal, secao 3):
    [1]  Estado inicial               [7]  Clear
    [2]  Meta                         [8]  Pre-condicoes de move
    [3]  Unicidade de posicao         [9]  Efeitos de move
    [4]  Unicidade de nivel           [10] Frame axioms
    [5]  Exclusao horizontal          [11] Acao unica por passo
    [6]  Estabilidade                 [12] Ordem parcial (opcional)
    [Aux] definicao de cov e occ (apoio para escrever os grupos acima)

Uso:
    python3 bw2cnf_var.py --situacao 1 --meta Sf4 --horizonte 4
    minisat trab01_blocos2SAT.cnf resultado1.txt
    python3 interpretar.py resultado1.txt --verbose
"""
import argparse
from itertools import combinations

# ============================================================
# Configuracao do dominio
# ============================================================
BLOCKS = {'a': 1, 'b': 1, 'c': 2, 'd': 3}   # comprimentos
TABLE = 'T'
MAX_POINT = 6                                # pontos 0..6 => 6 slots
MAX_LEVEL = 3                                # niveis 0..3

# Estados lidos das figuras: bloco -> (ponto inicial, nivel)
SITUACOES = {
    1: {  # S0 e as metas alternativas Sf1..Sf4
        'S0':  {'c': (0, 0), 'a': (3, 0), 'b': (5, 0), 'd': (3, 1)},
        'Sf1': {'d': (3, 0), 'a': (4, 1), 'b': (5, 1), 'c': (4, 2)},
        'Sf2': {'d': (3, 0), 'c': (4, 1), 'a': (4, 2), 'b': (5, 2)},
        'Sf3': {'c': (0, 0), 'a': (2, 0), 'b': (5, 0), 'd': (0, 1)},
        'Sf4': {'c': (0, 0), 'a': (0, 1), 'd': (2, 0), 'b': (5, 0)},
    },
    2: {  # S0 -> ... -> S5
        'S0': {'c': (0, 0), 'a': (0, 1), 'b': (1, 1), 'd': (3, 0)},
        'S1': {'c': (0, 0), 'a': (0, 1), 'b': (2, 0), 'd': (3, 0)},
        'S2': {'c': (0, 0), 'b': (2, 0), 'a': (2, 1), 'd': (3, 0)},
        'S3': {'b': (2, 0), 'a': (2, 1), 'd': (3, 0), 'c': (4, 1)},
        'S4': {'b': (2, 0), 'd': (3, 0), 'c': (4, 1), 'a': (4, 2)},
        'S5': {'d': (3, 0), 'c': (4, 1), 'a': (4, 2), 'b': (5, 2)},
    },
    3: {  # S0 -> ... -> S7
        'S0': {'c': (0, 0), 'a': (3, 0), 'b': (5, 0), 'd': (3, 1)},
        'S1': {'c': (0, 0), 'd': (0, 1), 'a': (3, 0), 'b': (5, 0)},
        'S2': {'c': (0, 0), 'd': (0, 1), 'b': (5, 0), 'a': (5, 1)},
        'S3': {'c': (0, 0), 'd': (2, 0), 'b': (5, 0), 'a': (5, 1)},
        'S4': {'c': (0, 0), 'd': (2, 0), 'b': (5, 0), 'a': (0, 1)},
        'S5': {'c': (0, 0), 'd': (2, 0), 'a': (0, 1), 'b': (1, 1)},
        'S6': {'c': (0, 0), 'd': (2, 0), 'a': (0, 1), 'b': (1, 1)},
        'S7': {'c': (0, 0), 'd': (3, 0), 'a': (0, 1), 'b': (1, 1)},
    },
}
META_PADRAO = {1: 'Sf4', 2: 'S5', 3: 'S7'}


def validar_estado(est, nome=''):
    """Confere se o estado e fisicamente valido (sem sobreposicao, estavel)."""
    for b, (p, l) in est.items():
        if p not in valid_positions(b):
            raise ValueError(f"{nome}: {b} em p={p} sai da mesa")
    for b1, b2 in combinations(est, 2):
        (p1, l1), (p2, l2) = est[b1], est[b2]
        if l1 == l2 and spans_overlap(b1, p1, b2, p2):
            raise ValueError(f"{nome}: {b1} e {b2} se sobrepoem no nivel {l1}")
    for b, (p, l) in est.items():
        if l == 0:
            continue
        apoio = {i for i in span(b, p)
                 for y, (py, ly) in est.items()
                 if y != b and ly == l - 1 and i in span(y, py)}
        if len(apoio) < (BLOCKS[b] + 1) // 2:
            raise ValueError(f"{nome}: {b} instavel (apoio insuficiente)")


# Ordem parcial (opcional): pares ((b,p,l), (b',p',l')) significando
# "a meta (b em p, nivel l) deve ser alcancada ANTES da meta (b' em p', l')".
ORDEM_PARCIAL = []


def valid_positions(b):
    return range(MAX_POINT - BLOCKS[b] + 1)


def span(b, p):
    return range(p, p + BLOCKS[b])


def spans_overlap(b1, p1, b2, p2):
    return bool(set(span(b1, p1)) & set(span(b2, p2)))


def construir(initial, goal, T, ordem=()):
    nxt = [0]

    def new_var():
        nxt[0] += 1
        return nxt[0]

    at, lev, clr, mv = {}, {}, {}, {}
    cov, occ, blk = {}, {}, {}
    names = list(BLOCKS)
    supports = names + [TABLE]
    slots = range(MAX_POINT)
    levels = range(MAX_LEVEL + 1)

    # ---------------- Variaveis (at, lev, clr, mv + auxiliares) ----------------
    for t in range(T + 1):
        for b in names:
            for p in valid_positions(b):
                at[(b, p, t)] = new_var()
            for l in levels:
                lev[(b, l, t)] = new_var()
            clr[(b, t)] = new_var()
            for i in slots:
                for l in levels:
                    cov[(b, i, l, t)] = new_var()
                    blk[(b, i, l, t)] = new_var()
        for i in slots:
            for l in levels:
                occ[(i, l, t)] = new_var()
    for t in range(T):
        for b in names:
            for y in supports:
                if y == b:
                    continue
                for p in valid_positions(b):
                    mv[(b, y, p, t)] = new_var()

    clauses = []

    def add(*lits):
        clauses.append(list(lits))

    # [1] Estado inicial: unitarias em t=0
    for b, (p, l) in initial.items():
        add(at[(b, p, 0)])
        add(lev[(b, l, 0)])
    # [2] Meta: unitarias em t=T
    for b, (p, l) in goal.items():
        add(at[(b, p, T)])
        add(lev[(b, l, T)])

    # ---------------- Axiomas de estado (para todo t) ----------------
    for t in range(T + 1):
        for b in names:
            # [3] Unicidade de posicao: exatamente um at(b,p,t)
            ps = [at[(b, p, t)] for p in valid_positions(b)]
            add(*ps)
            for u, v in combinations(ps, 2):
                add(-u, -v)
            # [4] Unicidade de nivel: exatamente um lev(b,l,t)
            ls = [lev[(b, l, t)] for l in levels]
            add(*ls)
            for u, v in combinations(ls, 2):
                add(-u, -v)

        # [Aux] definicao exata de cov(b,i,l,t)
        for b in names:
            for i in slots:
                for l in levels:
                    c = cov[(b, i, l, t)]
                    covering = [p for p in valid_positions(b) if i in span(b, p)]
                    for p in covering:
                        add(-at[(b, p, t)], -lev[(b, l, t)], c)
                    add(-c, lev[(b, l, t)])
                    add(-c, *[at[(b, p, t)] for p in covering])
        # [Aux] definicao exata de occ(i,l,t)
        for i in slots:
            for l in levels:
                o = occ[(i, l, t)]
                for b in names:
                    add(-cov[(b, i, l, t)], o)
                add(-o, *[cov[(b, i, l, t)] for b in names])

        # [5] Exclusao horizontal: mesmo nivel nao compartilha slot
        for b1, b2 in combinations(names, 2):
            for i in slots:
                for l in levels:
                    add(-cov[(b1, i, l, t)], -cov[(b2, i, l, t)])

        # [6] Estabilidade: >= ceil(len/2) slots apoiados no nivel abaixo
        for b in names:
            need = (BLOCKS[b] + 1) // 2
            for p in valid_positions(b):
                sl = list(span(b, p))
                for l in levels:
                    if l == 0:
                        continue
                    # "pelo menos need de len" == todo subconjunto de tamanho
                    # len-need+1 tem pelo menos um slot apoiado
                    for sub in combinations(sl, len(sl) - need + 1):
                        add(-at[(b, p, t)], -lev[(b, l, t)],
                            *[occ[(i, l - 1, t)] for i in sub])

        # [7] Clear: clr(b) <-> nada cobre slot de b no nivel acima
        for b in names:
            for i in slots:
                for l in levels:
                    k = blk[(b, i, l, t)]
                    above = occ[(i, l + 1, t)] if l < MAX_LEVEL else None
                    if above is None:
                        add(-k)
                        continue
                    add(-cov[(b, i, l, t)], -above, k)
                    add(-k, cov[(b, i, l, t)])
                    add(-k, above)
            ks = [blk[(b, i, l, t)] for i in slots for l in levels]
            for k in ks:
                add(-clr[(b, t)], -k)
            add(clr[(b, t)], *ks)

    # ---------------- Acoes (para t < T) ----------------
    for t in range(T):
        # [11] Acao unica por passo (no maximo uma)
        acts = [v for (b, y, p, tt), v in mv.items() if tt == t]
        for u, v in combinations(acts, 2):
            add(-u, -v)

        for (b, y, p, tt), m in mv.items():
            if tt != t:
                continue
            # [8] Pre-condicao: topo de b livre
            add(-m, clr[(b, t)])
            # [9] Efeito: b passa a comecar em p
            add(-m, at[(b, p, t + 1)])

            if y == TABLE:
                # [9] Efeito: b passa para o nivel 0
                add(-m, lev[(b, 0, t + 1)])
                # [8] Pre-condicao: nao e no-op
                add(-m, -at[(b, p, t)], -lev[(b, 0, t)])
                # [8] Pre-condicao: slots de destino livres no nivel 0 (alem de b)
                for z in names:
                    if z == b:
                        continue
                    for i in span(b, p):
                        add(-m, -cov[(z, i, 0, t)])
            else:
                # [8] Pre-condicao: span de b sobrepoe span de y
                for q in valid_positions(y):
                    if not spans_overlap(b, p, y, q):
                        add(-m, -at[(y, q, t)])
                for ly in levels:
                    if ly + 1 > MAX_LEVEL:
                        add(-m, -lev[(y, ly, t)])
                        continue
                    # [9] Efeito: b sobe para o nivel imediatamente acima de y
                    add(-m, -lev[(y, ly, t)], lev[(b, ly + 1, t + 1)])
                    # [8] Pre-condicao: nao e no-op
                    add(-m, -lev[(y, ly, t)], -at[(b, p, t)],
                        -lev[(b, ly + 1, t)])
                    # [8] Pre-condicao: slots de destino livres no nivel-alvo (alem de b)
                    for z in names:
                        if z == b:
                            continue
                        for i in span(b, p):
                            add(-m, -lev[(y, ly, t)],
                                -cov[(z, i, ly + 1, t)])

        # [10] Frame axioms: quem nao se move mantem posicao e nivel
        for b in names:
            moves_b = [v for (bb, y, p, tt), v in mv.items()
                       if tt == t and bb == b]
            for p in valid_positions(b):
                add(-at[(b, p, t)], at[(b, p, t + 1)], *moves_b)
            for l in levels:
                add(-lev[(b, l, t)], lev[(b, l, t + 1)], *moves_b)
        # clr nao precisa de frame axiom: e definida exatamente em cada t.

    # ---------------- [12] Ordem parcial (opcional) ----------------
    if ordem:
        g = {}
        for (phi1, phi2) in ordem:
            for (b, p, l) in (phi1, phi2):
                for t in range(T + 1):
                    if (b, p, l, t) in g:
                        continue
                    v = new_var()
                    g[(b, p, l, t)] = v
                    add(-at[(b, p, t)], -lev[(b, l, t)], v)
                    add(-v, at[(b, p, t)])
                    add(-v, lev[(b, l, t)])
            for t in range(1, T + 1):
                # phi2 so passa a valer depois de phi1 ja ter valido antes
                add(-g[(*phi2, t)], g[(*phi2, t - 1)],
                    *[g[(*phi1, tp)] for tp in range(t)])

    maps = {'at': at, 'lev': lev, 'clr': clr, 'mv': mv}
    return nxt[0], clauses, maps


def escrever(num_vars, clauses, maps, T, cnf_path, map_path):
    with open(cnf_path, 'w') as f:
        f.write(f"p cnf {num_vars} {len(clauses)}\n")
        for c in clauses:
            f.write(" ".join(map(str, c)) + " 0\n")
    with open(map_path, 'w') as f:
        f.write(f"# HORIZON {T}\n")
        for nome, d in maps.items():
            for k, v in d.items():
                f.write(f"{v} {nome}({','.join(map(str, k))})\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--situacao', type=int, default=1, choices=[1, 2, 3])
    ap.add_argument('--inicial', default='S0', help='estado inicial (ex.: S0)')
    ap.add_argument('--meta', default=None, help='estado meta (ex.: Sf1, S5)')
    ap.add_argument('--horizonte', type=int, default=4)
    ap.add_argument('--cnf', default='trab01_blocos2SAT.cnf')
    ap.add_argument('--map', default='trab01_blocos2SAT.map')
    a = ap.parse_args()
    est = SITUACOES[a.situacao]
    meta = a.meta or META_PADRAO[a.situacao]
    initial, goal = est[a.inicial], est[meta]
    validar_estado(initial, a.inicial)
    validar_estado(goal, meta)
    n, cls, maps = construir(initial, goal, a.horizonte, ORDEM_PARCIAL)
    escrever(n, cls, maps, a.horizonte, a.cnf, a.map)
    print(f"Situacao {a.situacao}: {a.inicial} -> {meta}, T={a.horizonte}")
    print(f"Gerado: {n} variaveis, {len(cls)} clausulas")
    print(f"Arquivos: {a.cnf}, {a.map}")


if __name__ == '__main__':
    main()