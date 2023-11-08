# Matías Rivera C.

import socket
import dnslib
from dnslib import DNSRecord
from dnslib.dns import CLASS, QTYPE, RR, A

# dirección de '.'
root_address = ("192.33.4.12", 53)

# definir address y el tamaño del buffer
address = ("localhost", 8000)
buff_size = 4096
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(address)

# esta función toma un mensaje dns y lleva algunas partes como Qname,
# la sección de Answer, Additional y Authority a un diccionario
def simplify(dns_message):
    dict = {}
    # Header
    ANCOUNT = dns_message.header.a
    NSCOUNT = dns_message.header.auth
    ARCOUNT = dns_message.header.ar
    dict["ANCOUNT"] = ANCOUNT
    dict["NSCOUNT"] = NSCOUNT
    dict["ARCOUNT"] = ARCOUNT
    # Question
    query = dns_message.get_q()
    Qname = str(query.get_qname())
    dict["Qname"] = Qname
    # Answer
    if ANCOUNT > 0:
        Answer = dns_message.rr
        dict["Answer"] = Answer
    # Authority
    if NSCOUNT > 0:
        Authority = dns_message.auth
        dict["Authority"] = Authority
    # Additional
    if ARCOUNT > 0:
        Additional = dns_message.ar
        dict["Additional"] = Additional
    return dict

last = []
# si aún no ha ocurrido más de 5 veces el proceso de agregar al caché, este va a
# contener todos esos dominios, de lo contrario, va a tomar todas las consultas,
# (si son más de 20 toma las 20 últimas) y revisa la ocurrencia de las mismas para dejar 5 en el caché
def addCache(domain, ip, c):
    if len(last) < 5:
        last.append((domain, ip))
        c.append((domain, ip))
    else:
        last.append((domain, ip))
        if len(last) < 20:
            last_copy = last.copy()
        else:
            last_copy = last[::-1][:20]
        c = []
        i = 0
        while len(c) < 5 and len(last_copy) > 0:
            i+=1
            counter = 0
            for element in last_copy:
                freq = last_copy.count(element)
                if freq > counter:
                    counter = freq
                    most_common = element
            # esto evita repeticiones en el caché
            for j in range(counter):
                last_copy.remove(most_common)
            c.append(most_common)
    return c

# busca si un dominio se encuentra en el caché, en cuyo caso retorna la ip guardada,
# de no estar retorna un string vacío
def lookCache(domain, c):
    m = dict(c)
    if domain in m:
        return m[domain]
    else:
        return ''

# se encarga de encontrar la ip de un dominio, permitiendo visualizar las consultas que se realizan
# y revisando si un dominio se encontraba en el caché
def resolver(mensaje_consulta, ip, cache):
    try:
        socksock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        if ip==root_address:
            d = DNSRecord.parse(mensaje_consulta)
            qname = simplify(d)["Qname"]
            # se revisa el caché
            ip_cache = lookCache(qname, cache)
            if ip_cache != '':
                print(f"(debug) Caché: '{qname}' con IP '{ip_cache}'")
                # se especifica que es una respuesta
                d.header.qr = 1
                d.add_answer(*RR.fromZone("{} A {}".format(qname, ip_cache)))
                return bytes(d.pack()), cache
            # si no estaba en el caché
            print(f"(debug) Consultando '{qname}' a '.' con dirección IP '192.33.4.12'")
        # se envía la consulta y se espera la respuesta
        socksock.sendto(mensaje_consulta, ip)
        data, _ = socksock.recvfrom(buff_size)
        d = DNSRecord.parse(data)
        dict = simplify(d)
        qname = dict["Qname"]
        # si hay una respuesta del tipo A, se agrega al caché y se retorna el mensaje
        if "Answer" in dict:
            first_answer = d.get_a()
            answer_type = QTYPE.get(first_answer.rtype)
            if answer_type == 'A':
                print(f"(debug) '{qname}' estaba en la IP '{first_answer.rdata}'")
                cache = addCache(qname, str(first_answer.rdata), cache)
                return data, cache
        # si hay respuestas del tipo NS en Authority
        if "Authority" in dict:
            list_auth = dict["Authority"]
            for auth_i in list_auth:
                auth_rdata = auth_i.rdata
                if isinstance(auth_rdata, dnslib.dns.NS):
                    ns_domain = str(auth_rdata)
                    # si encuentra una respuesta de tipo A en Additional
                    if "Additional" in dict:
                        list_add = dict["Additional"]
                        for add_i in list_add:
                            add_type = QTYPE.get(add_i.rclass)
                            if add_type == 'A':
                                add_i_rname = str(add_i.rname)
                                add_i_rdata = str(add_i.rdata)
                                # revisa el caché
                                ip_cache = lookCache(add_i_rname, cache)
                                if ip_cache != '':
                                    print(f"(debug) Caché: '{add_i_rname}' con IP '{ip_cache}'")
                                    d.header.qr = 1
                                    d.add_answer(*RR.fromZone("{} A {}".format(add_i_rname, ip_cache)))
                                    data, cache = resolver(mensaje_consulta, (ip_cache, 53), cache)
                                    return data, cache
                                # si no estaba en el caché, agrega el dominio y se consulta el mensaje en la ip obtenida
                                cache = addCache(add_i_rname, add_i_rdata, cache)
                                print(f"(debug) Consultando '{qname}' a '{add_i_rname}' con dirección IP '{add_i_rdata}'")
                                data, cache = resolver(mensaje_consulta, (add_i_rdata, 53), cache)
                                return data, cache
                    # de lo contrario se busca la ip del dominio del name server y se consulta en ella por el mensaje original
                    q = DNSRecord.question(ns_domain)
                    print(f"(debug) Consultando por la IP de '{ns_domain}'")
                    data, cache = resolver(bytes(q.pack()), root_address, cache)
                    d = DNSRecord.parse(data)
                    first_answer = d.get_a()
                    print(f"(debug) Consultando '{qname}' a '{ns_domain}' con dirección IP '{first_answer.rdata}'")
                    data, cache = resolver(mensaje_consulta, (str(first_answer.rdata), 53), cache)
                    return data, cache
    finally:
        socksock.close()
    # de no encontrarse se retorna None
    return None, cache

# se inicializa el caché vacío y con un ciclo while se reciben mensajes para luego
# resolver la ip, de no ser None se devuelve la respuesta
print("Esperando...")
cache = []
while True:
    data, by = sock.recvfrom(buff_size)
    answer, cache = resolver(data, root_address, cache)
    if answer != None:
        sock.sendto(answer, by)
        print('\n')
    else:
        print("No se pudo resolver el dominio")