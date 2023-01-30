def get_data(final_data, date):

    if final_data is None or len(final_data) == 0:
        return ''

    unique_times = final_data.index.unique(0)
    if date is None:
        latest_at_time = -1
    else:
        # Get all timestamps with at least one ticker data and find index of nearest (previous) timestamp to input
        latest_at_time = unique_times.get_indexer([date], method='pad')[0]

        # Given date in the past (no data)
        if latest_at_time == -1:
            return ''

    # Get nearest (previous) timestamp and get corresponding row
    time = unique_times[latest_at_time]
    search = final_data.loc[time].reset_index()

    # Format price and signal to match required output in assessment Word doc
    search['info'] = search[['price', 'signal']]\
        .astype('str')\
        .apply(lambda row: ','.join(row), axis=1)

    # Left align 'price,signal' and timestamp and get output string in required format
    formatters = {'info': f'{{:<{search["info"].str.len().max()}s}}'.format}
    return search[['ticker', 'info']].to_string(
        header=False,
        index_names=False,
        sparsify=False,
        index=False,
        col_space={'ticker': 8},
        formatters=formatters,
        justify='left'
    )

