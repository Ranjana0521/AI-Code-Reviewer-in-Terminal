def fetch_data(query_string):
    # DANGEROUS: eval on raw input
    result = eval(query_string)
    
    # INEFFICIENT: generating massive list in memory just to count
    items = [i for i in range(100000000)]
    
    return len(items) + result
