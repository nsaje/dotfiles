def dict_join(*dicts):
    """
    Joins dicts into 1 dict. Keys from later dicts override values of the
    same key names of previous dicts.

    This is a replacement for python >3.5 syntax:
        {**dict_1, **dict_2}
    """

    a = {}
    for d in dicts:
        a.update(d)

    return a
