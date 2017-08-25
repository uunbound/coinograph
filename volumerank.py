import json
import requests
from decimal import Decimal
from termcolor import colored
from terminaltables import AsciiTable
import locale


if __name__ == '__main__':
    resp = requests.get('https://api.coinmarketcap.com/v1/ticker/?limit=200')
    res = json.loads(resp.content)
    ratio_sorted = sorted(res, key=lambda c: Decimal(c['24h_volume_usd']) / Decimal(c['market_cap_usd']), reverse=True)
    table_data = [
        ['#', 'Name', 'Market Cap', 'Volume (24h)', '% Volume/Cap (24h)', '% Change (24h)']
    ]
    locale.setlocale( locale.LC_ALL, '' )
    for coin in ratio_sorted[:50]:
        if coin['percent_change_24h']:
            vol_cap_ratio = Decimal(Decimal(coin['24h_volume_usd']) / Decimal(coin['market_cap_usd']) * 100).quantize(Decimal('0.01'))
            row = [
                coin['rank'],
                coin['name'],
                locale.currency(Decimal(coin['market_cap_usd']), grouping=True),
                locale.currency(Decimal(coin['24h_volume_usd']), grouping=True),
                '{}%'.format(vol_cap_ratio)
            ]
            if Decimal(coin['percent_change_24h']) > 0:
                row.append(colored('{}%'.format(coin['percent_change_24h']), 'green'))
            else:
                row.append(colored('{}%'.format(coin['percent_change_24h']), 'red'))
            table_data.append(row)

    table = AsciiTable(table_data)
    print table.table
