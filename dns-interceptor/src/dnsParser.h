#ifndef DNS_PARSER_H
#define DNS_PARSER_H

#include <stdint.h>
#include <stddef.h>

/* Estructura base del header DNS (RFC1035 sección 4.1.1) */
typedef struct {
    uint16_t id;
    uint16_t flags;
    uint16_t qdcount;
    uint16_t ancount;
    uint16_t nscount;
    uint16_t arcount;
} dns_header_t;

/* Estructura para representar una pregunta */
typedef struct {
    char qname[256];
    uint16_t qtype;
    uint16_t qclass;
} dns_question_t;

int parse_dns_query(const uint8_t *buffer, size_t len, dns_header_t *header, dns_question_t *question);

#endif /* DNS_PARSER_H */
