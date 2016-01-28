def list_chunker(seq, size):
    """
    Splits a list into chunks of size "size".
    chunker(['cat', 'dog', 'rabbit', 'duck', 'bird', 'cow', 'gnu', 'fish'], 3) ->
        [['cat', 'dog', 'rabbit'], ['duck', 'bird', 'cow'], ['gnu', 'fish']]
    """
    return (seq[pos:pos + size] for pos in xrange(0, len(seq), size))