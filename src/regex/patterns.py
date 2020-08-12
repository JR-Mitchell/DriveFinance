# -*- coding: utf-8 -*-

PURCHASE = (r"^(?:spent\s)?(£?\d+(?:.\d\d)?)"
    + r"(?:\sspent)?\son\s(.+?)"
    + r"(?:(?:\spaid)?\s(?:by|from|using)(\s.+?)?)?$")
    # (spent) {amount}
    # (spent) on {object}
    # paid (by|from|using) {account}

TRANSFER = (r"^(£?\d+(?:.\d\d)?)"
    + r"(?:(?:\stransferred|\staken(?:\sout)?)?\sfrom/s(.+?))?"
    + r"(?:(?:\stransferred)?\sto\s(.+?))?(\staken\sout)?")
    # {amount}
    # ((transferred|taken (out)) from {sender}
    # (transferred) to {recipient}|taken out)

DATELIST = [
    r"(\d\d)", #            'DD'
    r"\/(\d\d)", #          '/MM'
    r"\/(\d\d)", #          '/YY'
    r"\ ?(\d\d)", #          ' hh'
    r":(\d\d)", #           ':mm'
    r":(\d\d)", #           ':ss'
    r"\.?(\d\d\d\d\d\d)"] #  '.uuuuuu'
