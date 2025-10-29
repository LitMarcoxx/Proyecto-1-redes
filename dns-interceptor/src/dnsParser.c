#include "dnsParser.h"
#include <stdio.h>
#include <string.h>
#include <arpa/inet.h>

/* Leer el nombre codificado en labels de longitud */
static int read_qname(const uint8_t *buf, size_t len, size_t *offset, char *out) {
    size_t pos = *offset, outpos = 0;
    while (pos < len) {
        uint8_t l = buf[pos++];
        if (l == 0) break;  // terminador
        if (l > 63 || pos + l > len) return -1;  // label inválido
        if (outpos && outpos < 255) out[outpos++] = '.';
        memcpy(out + outpos, buf + pos, l);
        outpos += l;
        pos += l;
    }
    out[outpos] = '\0';
    *offset = pos;
    return 0;
}

/* Función principal de parseo */
int parse_dns_query(const uint8_t *buffer, size_t len, dns_header_t *header, dns_question_t *question) {
    if (len < sizeof(dns_header_t)) return -1;

    header->id      = ntohs(*(uint16_t *)(buffer));
    header->flags   = ntohs(*(uint16_t *)(buffer + 2));
    header->qdcount = ntohs(*(uint16_t *)(buffer + 4));
    header->ancount = ntohs(*(uint16_t *)(buffer + 6));
    header->nscount = ntohs(*(uint16_t *)(buffer + 8));
    header->arcount = ntohs(*(uint16_t *)(buffer + 10));

    if (header->qdcount == 0) return 0;

    size_t offset = 12;
    if (read_qname(buffer, len, &offset, question->qname) < 0) return -1;
    if (offset + 4 > len) return -1;

    question->qtype  = ntohs(*(uint16_t *)(buffer + offset));
    question->qclass = ntohs(*(uint16_t *)(buffer + offset + 2));

    return 0;
}
