import ipaddress
import subprocess
from tabulate import tabulate


def gen_hosts_list(first_ip, last_ip):
    ip_start = int(ipaddress.ip_address(first_ip))
    ip_end = int(ipaddress.ip_address(last_ip))
    iplist = [ipaddress.ip_address(ip_el) for ip_el in range(ip_start, ip_end + 1)]
    return iplist


def host_ping(hosts):
    res = dict()
    for addr in hosts:
        args = ['ping', str(addr)]
        subproc_ping = subprocess.Popen(args, stdout=subprocess.PIPE)
        m_list = []
        for line in subproc_ping.stdout:
            line = line.decode('cp866').encode('utf-8').decode('utf-8')
            m_list.append(line)
        if 'TTL' in m_list[3]:
            res[addr] = ['Доступен']
        else:
            res[addr] = ['Недоступен']
    return tabulate(res, headers='keys', tablefmt="grid")


print(host_ping(gen_hosts_list('192.168.25.101', '192.168.25.102')))
