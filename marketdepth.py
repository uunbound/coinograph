import argparse
import json
import requests
from decimal import Decimal
from recordtype import recordtype
from termcolor import colored, cprint
import sys

BidLevel = recordtype('BidLevel', [('price', 0.0), ('quantity', 0.0)])

parser = argparse.ArgumentParser(description='Market depth ratio calculator.')
parser.add_argument('--pair', nargs='+', dest='pairs',
                    help='Pair(s) to use.')
parser.add_argument('--exchange', dest='exchange', default='bittrex',
                    help='Exchange to use.')
parser.add_argument('-wp', type=int, dest='window_percentage', default=10,
                    help='Market depth window in percentage.')

args = parser.parse_args()

if len(args.pairs) < 2:
    sys.exit('argument --pair: expected at least two arguments')

def fetch_order_book(pair_from, pair_to):
    url = 'https://bittrex.com/api/v1.1/public/getorderbook?market={pair_to}-{pair_from}&type=both'.format(
        pair_to=pair_to,
        pair_from=pair_from,
    )
    resp = requests.get(url)
    res = json.loads(resp.content)
    return res['result']

def fetch_ticker(pair_from, pair_to):
    url = 'https://bittrex.com/api/v1.1/public/getticker?market={pair_to}-{pair_from}'.format(
        pair_to=pair_to,
        pair_from=pair_from,
    )
    resp = requests.get(url)
    res = json.loads(resp.content)
    last = Decimal(res['result']['Last']).quantize(Decimal('.00000001'))
    bid = Decimal(res['result']['Bid']).quantize(Decimal('.00000001'))
    ask = Decimal(res['result']['Ask']).quantize(Decimal('.00000001'))
    return last, bid, ask

def create_depth_levels(bids, asks, window_percentage):
    middle = Decimal((asks[0]['Rate'] - bids[0]['Rate']) / 2 + bids[0]['Rate']).quantize(Decimal('.00000001'))
    unit = middle / 100  # one percent unit
    bid_levels = []
    ask_levels = []
    bidl = askl = middle
    for step in range(0, window_percentage):
        bidl -= unit
        bid_levels.append(BidLevel(price=bidl, quantity=0.0))
        askl += unit
        ask_levels.append(BidLevel(price=askl, quantity=0.0))

    for bid_level in bid_levels:
        for item in bids:
            if item['Rate'] >= bid_level.price and item['Rate'] < bid_level.price + unit:
                bid_level.quantity += item['Quantity']

    for ask_level in ask_levels:
        for item in asks:
            if item['Rate'] <= ask_level.price and item['Rate'] > ask_level.price - unit:
                ask_level.quantity += item['Quantity']
    return bid_levels, ask_levels

def calculate_ratio(bid_levels, ask_levels, window_percentage):
    bid_wq = 0
    ask_wq = 0

    for level, bid_level in enumerate(bid_levels):
        bid_wq += (window_percentage - level) * bid_level.quantity

    for level, ask_level in enumerate(ask_levels):
        ask_wq += (window_percentage - level) * ask_level.quantity

    bid_ratio = Decimal(bid_wq / (bid_wq + ask_wq) * 100).quantize(Decimal('.01'))
    ask_ratio = Decimal(ask_wq / (bid_wq + ask_wq) * 100).quantize(Decimal('.01'))

    return bid_ratio, ask_ratio

pairs = []
for dest_currency in args.pairs[1:]:
    pairs.append((args.pairs[0], dest_currency))

for pair in pairs:
    # fetch order book
    order_book = fetch_order_book(pair[0], pair[1])
    # create depth levels
    bid_levels, ask_levels = create_depth_levels(order_book['buy'], order_book['sell'], args.window_percentage)
    # calculate bid/ask ratio
    bid_ratio, ask_ratio = calculate_ratio(bid_levels, ask_levels, args.window_percentage)
    # fetch ticker
    market_price, bid, ask = fetch_ticker(pair[0], pair[1])


    print 'exchange:', args.exchange
    print 'pair:', '/'.join(pair)
    print 'market price:', market_price
    print 'bid/ask:', bid, ask
    print 'bid/ask ratio:', colored('{} / {}'.format(bid_ratio, ask_ratio), 'green' if bid_ratio > ask_ratio else 'red')
    print '-------------'
