import sqlite3, requests, hmac, time, hashlib, sys, csv

c = sqlite3.connect("FILELOCATION/BittrexDB.db", isolation_level=None).dbcon.cursor()
c.execute('PRAGMA journal_mode=wal')

apikey = ''
secret = ''

while True:
    with open('wallet.csv', 'r', encoding='utf-8') as f:
        reader = csv.reader(f, delimiter=',')
        kw_list = list(reader)
    
    rmstr = ''
    for kw in kw_list:
        rmstr += '"' + kw[0] + '", '
    
    rmstr = rmstr[:-2]
    c.execute('DELETE FROM last_prices WHERE AC NOT IN ({ac})'.format(ac=rmstr))
    BCinclude.dbcon.commit()
    
    for kw in kw_list:
        trailing_perc = float(kw[2])
        c.execute('SELECT price FROM last_prices WHERE AC="{ac}"'.format(ac=kw[0]))
        dbres = c.fetchall()
        
        try:
            r = requests.get('https://bittrex.com/api/v1.1/public/getticker?market=BTC-{cr}'.format(cr=kw[0])).json()
        except json.decoder.JSONDecodeError:
            continue;
            
        if not r['success']:
            sys.exit(r['message'])

        curr_price = float(r['result']['Bid'])

        nonce = str(int(time.time()))
        url = 'https://bittrex.com/api/v1.1/account/getbalances?apikey={ak}&nonce={no}'.format(ak=apikey, no=nonce)
        sign = hmac.new(bytes(secret, 'utf-8'), bytes(url, 'utf-8'), hashlib.sha512).hexdigest()
        
        try:
            r = requests.get(url, headers={'apisign': sign}).json()
        except json.decoder.JSONDecodeError:
            continue
            
        if not r['success']:
            sys.exit(r['message'])

        volume = 0
        for ac in r['result']:
            if (ac['Currency'] == kw[0]):
                volume = float(ac['Available'])

        if len(dbres) > 0:
            peak_price = float(dbres[0][0])
            print(kw[0], ": ", str(volume))
            print("Current (peak) price: {cp:5.10f} ({pp:5.10f})".format(cp=curr_price, pp=peak_price))
            
            if kw[3] == 'stoploss' or kw[3] == 'stophigh':
                if curr_price > peak_price:
                    print("Current price higher: updating database")
                    c.execute(
                        'UPDATE last_prices SET price={prc} WHERE AC="{ac}"'.format(ac=kw[0], prc=curr_price))
                    BCinclude.dbcon.commit()
                elif (curr_price <= peak_price * trailing_perc):
                    if (kw[3] == 'stophigh' and curr_price < float(kw[1])):
                        print("Not allowed to sell at a loss")
                        print("--------------")
                        continue
                    
                    if volume <= 0:
                        print("Current price below threshold: cannot sale, funds unavailable")
                        print("--------------")
                        continue

                    print("Current price below threshold: selling")
                    last_ask_str = "%5.10f" % (0.98 * curr_price)  # To compensate
                    quantity_str = "%10.10f" % volume
                    print(kw[0] + ", asking: ", last_ask_str)

                    nonce = str(int(time.time()))
                    url = 'https://bittrex.com/api/v1.1/market/selllimit?apikey={ak}&nonce={no}&market=BTC-{cr}&quantity={qa}&rate={ra}'.format(
                        ak=apikey, no=nonce, cr=kw[0], qa=quantity_str, ra=last_ask_str)
                    sign = hmac.new(bytes(secret, 'utf-8'), bytes(url, 'utf-8'), hashlib.sha512).hexdigest()
                    try:
                        r = requests.get(url, headers={'apisign': sign}).json()
                    except json.decoder.JSONDecodeError:
                        continue

                    print(r['message'])
                else:
                    print("Price within range: doing nothing")
            else:
                if curr_price <= trailing_perc*peak_price or curr_price >= (2 - trailing_perc)*peak_price:
                    if volume <= 0:
                        print("Cannot sale, funds unavailable")
                        print("--------------")
                        continue

                    print("Current price above or below threshold: selling")
                    last_ask_str = "%5.10f" % (0.98 * curr_price)  # To compensate
                    quantity_str = "%10.10f" % volume
                    print(kw[0] + ", asking: ", last_ask_str)

                    nonce = str(int(time.time()))
                    url = 'https://bittrex.com/api/v1.1/market/selllimit?apikey={ak}&nonce={no}&market=BTC-{cr}&quantity={qa}&rate={ra}'.format(
                        ak=apikey, no=nonce, cr=kw[0], qa=quantity_str, ra=last_ask_str)
                    sign = hmac.new(bytes(secret, 'utf-8'), bytes(url, 'utf-8'), hashlib.sha512).hexdigest()
                    try:
                        r = requests.get(url, headers={'apisign': sign}).json()
                    except json.decoder.JSONDecodeError:
                        continue

                    print(r['message'])
                    
            print("--------------")
        elif len(dbres) == 0:
            c.execute(
                'INSERT INTO last_prices VALUES ("{ac}", {prc})'.format(ac=kw[0], prc=float(kw[1])))
            BCinclude.dbcon.commit()
            
    
    print("\n End of cycle\n\n")
    time.sleep(20)
