import requests, re, dns.resolver, logging, os, ipaddress, socket
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

def get_public_ip():
    response = requests.get('https://api.ipify.org')
    return response.text

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
        my_resolver.timeout = 5
        my_resolver.lifetime = 5
        my_resolver.query(query, query_type)
        return True
    except dns.resolver.NXDOMAIN:
        return True
    except dns.resolver.Timeout:
        logging.warning(f'Timeout querying {bl}')
        return False
    except dns.resolver.NoNameservers:
        logging.warning(f'No nameservers for {bl}')
        return False
    except dns.resolver.NoAnswer:
        logging.warning(f'No answer for {bl}')
        return False
    except Exception as e:
        logging.error(f'Error occurred while checking IP {ipaddr} against {bl} blacklist: {str(e)}')
        return False
    
def dns_query_tests(ipaddr, bl, query_type):
    try:
        my_resolver = dns.resolver.Resolver()
        query = '.'.join(reversed(str(ipaddr).split("."))) + "." + bl
        my_resolver.timeout = 10
        my_resolver.lifetime = 10
        my_resolver.query(query, query_type)
        return True, None
    except dns.resolver.NXDOMAIN:
        return True, None
    except dns.resolver.Timeout:
        logging.error(f'Timeout querying {bl}')
        return False, f'Timeout querying {bl}'
    except dns.resolver.NoNameservers:
        logging.error(f'No nameservers for {bl}')
        return False, f'No nameservers for {bl}'
    except dns.resolver.NoAnswer:
        logging.error(f'No answer for {bl}')
        return False, f'No answer for {bl}'
    except Exception as e:
        logging.error(f'Error occurred while checking IP {ipaddr} against {bl} blacklist: {str(e)}')
        return False, f'Error occurred while checking IP {ipaddr} against {bl} blacklist: {str(e)}'


def bls_test_conn():
    try:
        message = ""
        bls = blserver.split(',')
        ipaddr = get_public_ip()
        message += f'🟢: Connected\n🔴: Not Connected\n\nHasil Koneksi:'
        for bl in bls:
            success, error = dns_query_tests(ipaddr, bl, "A")
            if success:
                success, error = dns_query_tests(ipaddr, bl, "TXT")
            
            if success:
                message += f'\n🟢 {bl}'
            else:
                message += f'\n🔴 {bl} ({error})'
        
        message += f'\n\n<pre>Pemeriksaan ke server blacklist melalui alamat IP {ipaddr}.</pre>'

    except Exception as e:
        logging.error('bltest: ' + str(e))
    
    return message

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
        try:
            if dns_query(ipaddr, bl, "A") and dns_query(ipaddr, bl, "TXT"):
                GOOD = GOOD + 1
                continue
            else:
                BAD = BAD + 1
                badlist += f"- {bl}\n"
        except Exception as e:
            WARN = WARN + 1
            notconn += f'- {bl} ({e})\n'
            message += f'\n🔴 {bl}'

    
    if BAD >= 1:
        message += f'\nAlamat IP tersebut tercatat buruk di server blacklist:\n{badlist}'
        message += f'\n<pre>IP tercatat buruk {BAD} dari {GOOD+BAD} server blacklist. Informasi blacklist:</pre>/blinfo'

    elif WARN == bltotal:
        message += '\nMohon maaf sepertinya ada yang tidak beres antara koneksi kami dengan server blacklist'
        
    elif WARN >= 1:
        message += f'\nTidak terhubung ke server blacklist:\n{notconn}'
        
    else:
        message += f'\n✅ Alamat IP sehat dari {GOOD+BAD} server blacklist.\n Informasi Blacklist: /blinfo'

    return message
