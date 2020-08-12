import filereader,balances,payments,scheduled,shortcuts

def autoparse(key,file,rep_dict=None):
    """ Convenience function for taking a docfile and parsing it with the
    correct parser

    :param key: the name of the parser to use (one of "Balances", "Payments",
        "Scheduled" and "Shortcuts")
    :type key: str
    :param rep_dict: a shortcut replacement dict, defaults to None
    :type rep_dict: dict
    """
    lookup = {
        "Balances": balances.ParsedBalances,
        "Payments": payments.ParsedPayments,
        "Scheduled": scheduled.ParsedSchedule,
        "Shortcuts": shortcuts.ParsedShortcuts}
    if rep_dict is None:
        return lookup[key](file)
    else:
        return lookup[key](file,rep_dict)
