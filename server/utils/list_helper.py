def list_chunker(seq, size):
    """
    Splits a list into chunks of size "size".
    chunker(['cat', 'dog', 'rabbit', 'duck', 'bird', 'cow', 'gnu', 'fish'], 3) ->
        [['cat', 'dog', 'rabbit'], ['duck', 'bird', 'cow'], ['gnu', 'fish']]
    """
    return (seq[pos:pos + size] for pos in range(0, len(seq), size))


def flatten(coll, nesting_depth=2):
    if nesting_depth == 2:
        return (x for z in coll for x in z)
    raise Exception('Unsupported nesting_depth')
