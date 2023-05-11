import whois, datetime, os, requests, dns.resolver, logging
from dotenv import load_dotenv


logging.basicConfig(
    filename='app.log',
    filemode='a',
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.ERROR
)

load_dotenv()
my_ips = os.getenv('HOSTING_IPS')
my_server_name = os.getenv('HOSTING_NAME')

def domain(update):
    domain = update
    message = ""
    
    try:
        response = requests.get(f'http://{domain}', timeout=5)
        response.raise_for_status()
        status_code = response.status_code
        message += f'{domain} dapat diakses ({status_code})\n\n'
    except requests.exceptions.RequestException as e:
        message += f'{domain} tidak dapat diakses\n\n'


    # Get WHOIS information
    try:
        domain_info = whois.whois(domain)
        if domain_info.status == None:
            message += 'Domain tidak terdaftar'
        else:
            date_info = {}

            creation_dates = domain_info.creation_date if isinstance(domain_info.creation_date, list) else [domain_info.creation_date]
            for date in creation_dates:
                date_info['Dibuat'] = date.strftime('%d %B %Y')

            updated_dates = domain_info.updated_date if isinstance(domain_info.updated_date, list)else [domain_info.updated_date]
            if isinstance(domain_info.updated_date, list):
                latest_update = max(domain_info.updated_date)
            else:
                latest_update = domain_info.updated_date
            date_info['Diperbarui'] = latest_update.strftime('%d %B %Y')

            expiration_dates = domain_info.expiration_date if isinstance(domain_info.expiration_date, list) else [domain_info.expiration_date]
            for date in expiration_dates:
                date_info['Kadaluarsa'] = date.strftime('%d %B %Y')

            message += f"Dibuat: {date_info['Dibuat']}\n"
            message += f"Diperbarui: {date_info['Diperbarui']}\n"
            message += f"Kadaluarsa: {date_info['Kadaluarsa']}\n"
            message += f"Registrar: {domain_info.registrar}\n"
            
            status = domain_info.status if isinstance(domain_info.status, list) else [domain_info.status]
            message += f"Status: {', '.join(status)}\n"
            
            # Check if domain can be transferred
            days_to_expiry = (expiration_dates[0] - datetime.datetime.now()).days
            if days_to_expiry < 14:
                message += "Domain tidak dapat ditransfer karena masa aktifnya kurang dari 14 hari\n"
            elif creation_dates[0] > (datetime.datetime.now() - datetime.timedelta(days=60)):
                message += "Domain tidak dapat ditransfer karena belum berumur lebih dari 60 hari\n"
            else:
                message += "Domain dapat ditransfer ke Registrar lain\n"        

    except Exception as e:
        if str(e) == "DOMAIN NOT FOUND":
            message += 'Domain tidak terdaftar'
        else:
            logging.error(f'{domain}: {str(e)}')


    # Get A record information
    message += "\nA record:\n"
    try:
        a_records = dns.resolver.query(domain, 'A')
        for a_record in a_records:
            message += f"{a_record.to_text()}\n"
        ip_address = a_records[0].to_text()
        if ip_address in my_ips.split(','):
            message += f"Hosting di {my_server_name}\n"
        else:
            message += f"Tidak hosting di {my_server_name}\n"
    except:
        message += 'Tidak ada A record\n'

    # Get CNAME record information
    message += '\nCNAME record:\n'
    try:
        cname_records = dns.resolver.query(domain, 'CNAME')
        for cname in cname_records:
            message += f'{cname}\n'
    except:
        message += 'Tidak ada CNAME record\n'

    # Get MX record information
    message += '\nMX record:\n'
    try:
        mx_records = dns.resolver.query(domain, 'MX')
        for mx in mx_records:
            message += f'{mx.preference} {mx.exchange}\n'
    except:
        message += 'Tidak ada MX record\n'

    # Get NS record information
    message += f"\nNS record:\n"
    try:
        ns_records = dns.resolver.query(domain, 'NS')
        for rdata in ns_records:
            message += f"{rdata.to_text()}\n"
    except:
        message += 'Tidak ada NS record\n'

    return message

