import requests, re, dns.resolver, logging, os, ipaddress
from dotenv import load_dotenv
from urllib.request import urlopen
from json import load

# logging
logging.basicConfig(
    filename='app.log',
    filemode='a',
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.ERROR
)

load_dotenv()
blserver = os.getenv('BLSEVER')

def is_public_ip(ipaddr):
    try:
        ip = ipaddress.ip_address(ipaddr)
        return not ip.is_private and not ip.is_reserved and not ip.is_loopback
    except Exception as e:
        logging.error(f'{ipaddr}: {str(e)}')

def dns_query(ipaddr, bl):
    STATUS = ''
    ERR = ''
    try:
        my_resolver = dns.resolver.Resolver()
        query = '.'.join(reversed(str(ipaddr).split("."))) + "." + bl
        my_resolver.timeout = 1
        my_resolver.lifetime = 1
        answers = my_resolver.query(query, "A")
        answer_txt = my_resolver.query(query, "TXT")

        if answers:
            STATUS = 'BAD'
            ERR = answer_txt[0]
            return STATUS, ERR

    except dns.resolver.NXDOMAIN as e:
        print(f'{e} dns.resolver.NXDOMAIN')
        ERR = "NXDOMAIN"
        STATUS = 'NOTCONN'
        return STATUS, ERR
    except dns.resolver.Timeout as e:
        logging.warning('- Timeout querying {e}')
        STATUS = 'NOTCONN'
        ERR = 'Timeout querying'
        print(f'{e} Timeout querying {e}')
        return STATUS, ERR
    except dns.resolver.NoNameservers as e:
        logging.warning('- No nameservers {e}')
        STATUS = 'NOTCONN'
        ERR = 'No nameservers'
        print(f'{e} No nameservers ')
        return STATUS, ERR
    except dns.resolver.NoAnswer as e:
        logging.warning(f'- No answer {e}')
        STATUS = 'GOOD'
        ERR = 'No answer'
        print(f'{e} No answer ')
        return STATUS, ERR
    except Exception as e:
        logging.warning(f'- No answer {e}')
        STATUS = 'NOTCONN'
        ERR = 'No answer'
        print(f'{e} No answer ')
        return STATUS, ERR

    
def bls_list():
    try:
        bls = blserver.split(',')
        message = ""
        for bl in bls:
            message += f'\n - {bl}'
        return message

    except Exception as e:
        logging.error('Show blacklist servers: ' + str(e))

def ip(ipaddr):
    message = ""
    BAD = 0
    GOOD = 0
    WARN = 0
        
    try:
        if ipaddr == '':
            url = 'https://ipinfo.io/json'
        else:
            url = 'https://ipinfo.io/' + ipaddr + '/json'
        
        res = urlopen(url)
        data = load(res)
        message += "{:<12}: <code>{}</code>\n".format('IP Address', data['ip'])
        message += "{:<11}: <code>{}</code>\n".format('Hostname', data['hostname'])
        message += "{:<11}: <code>{}</code>\n".format('AS Number', data['org'])
        message += "{:<15}: <code>{}, {}</code>\n".format('Country', data['country'], data['city'])

        # Remove readme
        if 'readme' in data:
            message = message.replace(data['readme'], '')

    except Exception as e:
        logging.error(f'whois occurred while checking IP {ipaddr}: {str(e)}')
    
    bls = blserver.split(',')
    badlist = ''
    notconn = ''
    
    for bl in bls:
        status, err = dns_query(ipaddr, bl)
        if status:
            status, err = dns_query(ipaddr, bl)
            
        if status == "GOOD":
            GOOD += 1  
        elif status == "BAD":
            BAD += 1
            badlist += f'- {bl}\n' + str(err) + '\n\n'
        elif status == "NOTCONN":
            if err == "NXDOMAIN":
                GOOD += 1
            else:
                WARN += 1
                notconn += f'\n- {bl} - {err}\n'
        
    if BAD >= 1:
        message += f'\n<b>Bloked:</b>\n{badlist}'
        if WARN >= 1:
            message += f'<b>Connection Failed:</b>{notconn}'
        message += f'\n🟢 {GOOD} 🔴 {BAD} 🟠 {WARN}\nList of blacklist servers: /blserver_lists'
    else:
        message += f'\n✅ Healthy IP addresses from {GOOD+BAD} blacklist servers.\nList of blacklist servers: /blserver_lists'

    return message
