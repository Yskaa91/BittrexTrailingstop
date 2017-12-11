# Bittrex trailing stop

Automatic trailing stop and profit taking script for Bittrex exchange  
<i>For people who are sick of missing those pumps overnight</i>

Depends: BCinclude, requests, hmac, time, hashlib, sys, csv  
Python 3.x

Follows the bid price of given coins/tokens at the Bittrex exchange. Sells the assets when stop target is reached (see CSV description below)  
Requires a Bittrex apikey and secret. Remember to allow the API key to buy and sell assets.

CSV has 4 values
1: bittrex coin/token name/index (BCC, ETH ..)  
2: buy price  
3: trailing percentage. Used for stoploss, or when using the margin option
   it is the maximum loss or profit (2 - trailing percentage) that has to
   be reached before selling.  
4: type  
    - stoploss: trailing stop with loss taking allowed  
    - stophigh: trailing stop, but only sell when it is above the buy price  
    - margin: sell when a certain loss or profit is reached  

EXAMPLES  
THC, 0.00000870, 0.90, stoploss  
XEM, 0.00003425, 0.95, margin  
 - last one sells when the price dropped 5% (0.95), or has risen 5% (2-0.95 = 1.05)
