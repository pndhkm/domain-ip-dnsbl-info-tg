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

def content_test(url, ipaddr):
    try:
        response = requests.get(url)
        html_content = response.text
        retcode = response.status_code
        matches = retcode == 200
        matches = matches and re.findall(ipaddr, html_content)
        return len(matches) == 0
    except Exception as e:
        logging.error(f'{url} - {ipaddr}: {str(e)}')


def dns_query(ipaddr, bl, query_type):
    try:
        my_resolver = dns.resolver.Resolver()
        query = '.'.join(reversed(str(ipaddr).split("."))) + "." + bl
        my_resolver.timeout = 10
        my_resolver.lifetime = 10
        answers = my_resolver.query(query, query_type)
        if answers:
            return True
        else:
            return False
    except dns.resolver.NXDOMAIN:
        return False
    except dns.resolver.Timeout:
        logging.warning('- Timeout querying ')
        return False
    except dns.resolver.NoNameservers:
        logging.warning('- No nameservers ')
        return False
    except dns.resolver.NoAnswer:
        logging.warning('- No answer ')
        return False
    except Exception as e:
        logging.error(f'Error occurred while checking IP {ipaddr} against {bl} blacklist: {str(e)}')
        return False
    
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
        message += "{:<15}: <code>{}</code>\n".format('Alamat IP', data['ip'])
        message += "{:<12}: <code>{}</code>\n".format('Nama Host', data['hostname'])
        message += "{:<12}: <code>{}</code>\n".format('AS Number', data['org'])
        message += "{:<17}: <code>{}, {}</code>\n".format('Negara', data['country'], data['city'])

        # Remove readme
        if 'readme' in data:
            message = message.replace(data['readme'], '')

    except Exception as e:
        logging.error(f'whois occurred while checking IP {ipaddr}: {str(e)}')
    
    bls = blserver.split(',')
    badlist = ''
    notconn = ''
    bltotal = len(bls)  
    
    for bl in bls:
        if not dns_query(ipaddr, bl, "A") or not dns_query(ipaddr, bl, "TXT"):
            GOOD = GOOD + 1
        elif dns_query(ipaddr, bl, "A") or dns_query(ipaddr, bl, "TXT"):
            BAD = BAD + 1
            badlist += f"- {bl}\n"
        else:
            WARN = WARN + 1
            notconn += f'- {bl} ({error})\n'
            message += f'\n🔴 {bl}'

    
    if BAD >= 1:
        message += f'\nAlamat IP tersebut tercatat buruk di server blacklist:\n{badlist}'
        message += f'\n<pre>IP tercatat buruk {BAD} dari {GOOD+BAD} server blacklist. Daftar server blacklist:</pre>/blserver_lists'

    elif WARN == bltotal:
        message += '\nMohon maaf sepertinya ada yang tidak beres antara koneksi kami dengan server blacklist'
        
    elif WARN >= 1:
        message += f'\nTidak terhubung ke server blacklist:\n{notconn}'
        
    else:
        message += f'\n✅ Alamat IP sehat dari {GOOD+BAD} server blacklist.\n Daftar server blacklist: /blserver_lists'

    return message
