def fista_debugs(fista):
    '''
    Debugging parameters.
    '''
    fista.noiselevelreached_debug = True
    fista.solve_debug = True
    fista.adaptlamb_debug = True
    fista.fistacore_debug = True # fistacore is above corealgo
    fista.corealgo_debug = False