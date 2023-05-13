#!/bin/bash

BLSEVER="b.barracudacentral.adsasdorg,b.barracudacentral.org,zen.spamhaus.org,spam.dnsbl.sorbs.net,dnsbl.sorbs.net,cbl.abuseat.org,spam.abuse.ch,bl.spamcop.net,bl.blocklist.de,dbl.spamhaus.org,dnsbl-1.uceprotect.net,dnsbl-2.uceprotect.net,dnsbl-3.uceprotect.net"

for server in $(echo $BLSEVER | tr "," "\n"); do
  if dig +short $server >/dev/null; then
    echo "Connected to $server"
  else
    echo "Failed to connect to $server"
  fi
done
