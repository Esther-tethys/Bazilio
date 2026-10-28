Hanoi |:
    Resolver 5 0 1 2
:|

Resolver n origen destino auxiliar |:
    if n > 0 |:
        Resolver n - 1 origen auxiliar destino
        <:> C + origen * 7 + n
        Resolver n - 1 auxiliar destino origen
    :|
:|