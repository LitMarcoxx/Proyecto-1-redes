#define _POSIX_C_SOURCE 200112L
#include "dnsParser.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <arpa/inet.h>
#include <sys/socket.h>
#include <errno.h>
#include <curl/curl.h>
#include <ctype.h>

#define BUF_SIZE 512
#define DNS_PORT 53
#define API_URL_RESOLVE "http://dns-api-dns-project-api.dns.svc.cluster.local:8080/api/resolve"
#define API_URL_DNSRESOLVER "http://dns-api-dns-project-api.dns.svc.cluster.local:8080/api/dns_resolver"

struct memory
{
    char *response;
    size_t size;
};

static size_t write_callback(void *data, size_t size, size_t nmemb, void *userp)
{
    size_t realsize = size * nmemb;
    struct memory *mem = (struct memory *)userp;
    mem->response = realloc(mem->response, mem->size + realsize + 1);
    memcpy(&(mem->response[mem->size]), data, realsize);
    mem->size += realsize;
    mem->response[mem->size] = 0;
    return realsize;
}

/* --- función auxiliar Base64 (para /api/dns_resolver) --- */
static const char b64_table[] = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";

static char *base64_encode(const unsigned char *src, size_t len)
{
    char *out, *pos;
    const unsigned char *end, *in;
    size_t olen = 4 * ((len + 2) / 3);
    out = malloc(olen + 1);
    if (!out)
        return NULL;
    end = src + len;
    in = src;
    pos = out;
    while (end - in >= 3)
    {
        *pos++ = b64_table[in[0] >> 2];
        *pos++ = b64_table[((in[0] & 0x03) << 4) | (in[1] >> 4)];
        *pos++ = b64_table[((in[1] & 0x0f) << 2) | (in[2] >> 6)];
        *pos++ = b64_table[in[2] & 0x3f];
        in += 3;
    }
    if (end - in)
    {
        *pos++ = b64_table[in[0] >> 2];
        if (end - in == 1)
        {
            *pos++ = b64_table[(in[0] & 0x03) << 4];
            *pos++ = '=';
        }
        else
        {
            *pos++ = b64_table[((in[0] & 0x03) << 4) | (in[1] >> 4)];
            *pos++ = b64_table[(in[1] & 0x0f) << 2];
        }
        *pos++ = '=';
    }
    *pos = '\0';
    return out;
}

static size_t base64_decode(const char *in, unsigned char *out, size_t outlen)
{
    static const unsigned char dtable[256] = {
        ['A'] = 0, ['B'] = 1, ['C'] = 2, ['D'] = 3, ['E'] = 4, ['F'] = 5, ['G'] = 6, ['H'] = 7, ['I'] = 8, ['J'] = 9, ['K'] = 10, ['L'] = 11, ['M'] = 12, ['N'] = 13, ['O'] = 14, ['P'] = 15, ['Q'] = 16, ['R'] = 17, ['S'] = 18, ['T'] = 19, ['U'] = 20, ['V'] = 21, ['W'] = 22, ['X'] = 23, ['Y'] = 24, ['Z'] = 25, ['a'] = 26, ['b'] = 27, ['c'] = 28, ['d'] = 29, ['e'] = 30, ['f'] = 31, ['g'] = 32, ['h'] = 33, ['i'] = 34, ['j'] = 35, ['k'] = 36, ['l'] = 37, ['m'] = 38, ['n'] = 39, ['o'] = 40, ['p'] = 41, ['q'] = 42, ['r'] = 43, ['s'] = 44, ['t'] = 45, ['u'] = 46, ['v'] = 47, ['w'] = 48, ['x'] = 49, ['y'] = 50, ['z'] = 51, ['0'] = 52, ['1'] = 53, ['2'] = 54, ['3'] = 55, ['4'] = 56, ['5'] = 57, ['6'] = 58, ['7'] = 59, ['8'] = 60, ['9'] = 61, ['+'] = 62, ['/'] = 63};
    size_t len = strlen(in);
    unsigned char *p = out;
    unsigned char block[4];
    int pad = 0;
    for (size_t i = 0; i < len; i++)
        if (in[i] == '=')
            pad++;
    for (size_t i = 0; i < len;)
    {
        for (int k = 0; k < 4 && i < len; i++)
            if (in[i] != '\r' && in[i] != '\n')
                block[k++] = dtable[(unsigned char)in[i]];
        *p++ = (block[0] << 2) | (block[1] >> 4);
        *p++ = (block[1] << 4) | (block[2] >> 2);
        *p++ = (block[2] << 6) | block[3];
    }
    return (p - out) - pad;
}

/* --- función para enviar query al API --- */
int send_to_api_and_get_response(const char *qname, const char *client_ip,
                                 char *resolved_ip, size_t ip_buflen)
{
    CURL *curl;
    CURLcode res;
    struct memory chunk = {0};
    int success = 0;

    curl_global_init(CURL_GLOBAL_DEFAULT);
    curl = curl_easy_init();
    if (curl)
    {
        struct curl_slist *headers = NULL;
        headers = curl_slist_append(headers, "Content-Type: application/json");

        char json_body[512];
        snprintf(json_body, sizeof(json_body),
                 "{\"host\":\"%s\", \"client_ip\":\"%s\"}", qname, client_ip);

        curl_easy_setopt(curl, CURLOPT_URL, API_URL_RESOLVE);
        curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);
        curl_easy_setopt(curl, CURLOPT_POSTFIELDS, json_body);
        curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, write_callback);
        curl_easy_setopt(curl, CURLOPT_WRITEDATA, &chunk);
        curl_easy_setopt(curl, CURLOPT_TIMEOUT_MS, 3000L);

        res = curl_easy_perform(curl);
        if (res == CURLE_OK && chunk.response)
        {
            /* Buscar el campo "ip" en la respuesta JSON */
            char *start = strstr(chunk.response, "\"ip\":\"");
            if (start)
            {
                start += strlen("\"ip\":\"");
                char *end = strchr(start, '"');
                if (end)
                {
                    size_t len = end - start;
                    if (len >= ip_buflen)
                        len = ip_buflen - 1;
                    memcpy(resolved_ip, start, len);
                    resolved_ip[len] = '\0';
                    printf("[DNS] API returned IP: %s\n", resolved_ip);
                    success = 1;
                }
            }
        }
        else
        {
            fprintf(stderr, "[DNS] CURL error: %s\n", curl_easy_strerror(res));
        }

        curl_slist_free_all(headers);
        curl_easy_cleanup(curl);
        if (chunk.response)
            free(chunk.response);
        curl_global_cleanup();
    }

    return success;
}

/* --- función para enviar paquete DNS a /api/dns_resolver --- */
int send_to_api_dns_resolver(const unsigned char *query, size_t query_len,
                             unsigned char *response_buf, size_t *response_len)
{
    CURL *curl;
    CURLcode res;
    struct memory chunk = {0};
    int success = 0;

    char *encoded = base64_encode(query, query_len);
    if (!encoded)
        return 0;

    curl_global_init(CURL_GLOBAL_DEFAULT);
    curl = curl_easy_init();
    if (curl)
    {
        struct curl_slist *headers = NULL;
        headers = curl_slist_append(headers, "Content-Type: application/json");

        char json_body[1024];
        snprintf(json_body, sizeof(json_body),
                 "{\"base64_data\":\"%s\", \"timeout_ms\":2000}", encoded);

        curl_easy_setopt(curl, CURLOPT_URL, API_URL_DNSRESOLVER);
        curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);
        curl_easy_setopt(curl, CURLOPT_POSTFIELDS, json_body);
        curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, write_callback);
        curl_easy_setopt(curl, CURLOPT_WRITEDATA, &chunk);
        curl_easy_setopt(curl, CURLOPT_TIMEOUT_MS, 5000L);

        res = curl_easy_perform(curl);
        if (res == CURLE_OK && chunk.response)
        {
            char *start = strstr(chunk.response, "\"response_base64\":\"");
            if (start)
            {
                start += strlen("\"response_base64\":\"");
                char *end = strchr(start, '"');
                if (end)
                {
                    *end = '\0';
                    *response_len = base64_decode(start, response_buf, BUF_SIZE);
                    printf("[DNS] Non-standard response decoded (%zu bytes)\n", *response_len);
                    success = 1;
                }
            }
        }
        else
        {
            fprintf(stderr, "[DNS] CURL error: %s\n", curl_easy_strerror(res));
        }

        curl_slist_free_all(headers);
        curl_easy_cleanup(curl);
        if (chunk.response)
            free(chunk.response);
        curl_global_cleanup();
    }

    free(encoded);
    return success;
}

/* Construye una respuesta DNS simple tipo A (una sola respuesta IPv4) */
size_t build_dns_response(const unsigned char *query, size_t query_len,
                          const dns_header_t *hdr, const dns_question_t *q,
                          const char *resolved_ip,
                          unsigned char *outbuf, size_t outlen)
{
    if (!resolved_ip)
        return 0;

    /* Copiar el header y question originales */
    memcpy(outbuf, query, query_len);
    size_t offset = query_len;

    /* Modificar campos del header: QR=1, RCODE=0, ANCOUNT=1 */
    uint16_t flags = ntohs(*(uint16_t *)(outbuf + 2));
    flags |= 0x8000;  // establecer bit QR=1 (respuesta)
    flags &= ~0x020F; // limpiar TC y RCODE
    *(uint16_t *)(outbuf + 2) = htons(flags);
    *(uint16_t *)(outbuf + 6) = htons(1); // ANCOUNT = 1

    /* Crear la sección Answer */
    // Nombre en formato puntero (offset 0xC0 0x0C -> apunta al QNAME original)
    if (offset + 16 > outlen)
        return 0;
    outbuf[offset++] = 0xC0;
    outbuf[offset++] = 0x0C;

    // TYPE (A = 1)
    *(uint16_t *)(outbuf + offset) = htons(1);
    offset += 2;
    // CLASS (IN = 1)
    *(uint16_t *)(outbuf + offset) = htons(1);
    offset += 2;
    // TTL (5 min)
    *(uint32_t *)(outbuf + offset) = htonl(300);
    offset += 4;
    // RDLENGTH (4 bytes para IPv4)
    *(uint16_t *)(outbuf + offset) = htons(4);
    offset += 2;

    // Dirección IP
    struct in_addr ip_addr;
    if (inet_pton(AF_INET, resolved_ip, &ip_addr) != 1)
        return 0;
    memcpy(outbuf + offset, &ip_addr.s_addr, 4);
    offset += 4;

    return offset;
}

/* --- Fallback: reenviar query DNS a servidor upstream (8.8.8.8) --- */
int forward_to_upstream_dns(const unsigned char *query, size_t query_len,
                            unsigned char *response_buf, size_t *response_len)
{
    int sockfd;
    struct sockaddr_in upstream_addr;
    socklen_t addr_len = sizeof(upstream_addr);
    int success = 0;

    /* Crear socket UDP */
    if ((sockfd = socket(AF_INET, SOCK_DGRAM, 0)) < 0)
    {
        perror("[DNS-Fallback] socket failed");
        return 0;
    }

    memset(&upstream_addr, 0, sizeof(upstream_addr));
    upstream_addr.sin_family = AF_INET;
    upstream_addr.sin_port = htons(53);
    inet_pton(AF_INET, "8.8.8.8", &upstream_addr.sin_addr);

    /* Enviar query al upstream */
    ssize_t sent = sendto(sockfd, query, query_len, 0,
                          (struct sockaddr *)&upstream_addr, sizeof(upstream_addr));
    if (sent < 0)
    {
        perror("[DNS-Fallback] sendto failed");
        close(sockfd);
        return 0;
    }

    /* Esperar respuesta */
    struct timeval tv;
    tv.tv_sec = 2;
    tv.tv_usec = 0;
    setsockopt(sockfd, SOL_SOCKET, SO_RCVTIMEO, &tv, sizeof(tv));

    ssize_t n = recvfrom(sockfd, response_buf, BUF_SIZE, 0, NULL, NULL);
    if (n > 0)
    {
        *response_len = n;
        success = 1;
        printf("[DNS-Fallback] Got %zd bytes from 8.8.8.8\n", n);
    }
    else
    {
        perror("[DNS-Fallback] recvfrom failed or timed out");
    }

    close(sockfd);
    return success;
}

int main(void)
{
    int sockfd;
    struct sockaddr_in server_addr, client_addr;
    unsigned char buffer[BUF_SIZE];
    socklen_t addr_len = sizeof(client_addr);

    printf("[DNS-Interceptor] Listening on UDP port %d...\n", DNS_PORT);
    fflush(stdout);

    if ((sockfd = socket(AF_INET, SOCK_DGRAM, 0)) < 0)
    {
        perror("socket failed");
        exit(EXIT_FAILURE);
    }

    memset(&server_addr, 0, sizeof(server_addr));
    server_addr.sin_family = AF_INET;
    server_addr.sin_addr.s_addr = INADDR_ANY;
    server_addr.sin_port = htons(DNS_PORT);

    if (bind(sockfd, (const struct sockaddr *)&server_addr, sizeof(server_addr)) < 0)
    {
        perror("bind failed");
        close(sockfd);
        exit(EXIT_FAILURE);
    }

    printf("[DNS-Interceptor] Waiting for DNS packets...\n");
    fflush(stdout);

    while (1)
    {
        ssize_t n = recvfrom(sockfd, buffer, BUF_SIZE, 0,
                             (struct sockaddr *)&client_addr, &addr_len);
        if (n <= 0)
            continue;

        char client_ip[INET_ADDRSTRLEN];
        inet_ntop(AF_INET, &client_addr.sin_addr, client_ip, sizeof(client_ip));

        dns_header_t hdr;
        dns_question_t q;
        memset(&hdr, 0, sizeof(hdr));
        memset(&q, 0, sizeof(q));

        if (parse_dns_query(buffer, n, &hdr, &q) == 0)
        {
            printf("[DNS] From %s | ID=0x%04x | QNAME=%s | QTYPE=%u | forwarding to API...\n",
                   client_ip, hdr.id, q.qname, q.qtype);
            fflush(stdout);

            char resolved_ip[64] = {0};
            unsigned char response_buf[BUF_SIZE];
            size_t resp_len = 0;

            uint16_t opcode = (ntohs(hdr.flags) >> 11) & 0x0F;
            if (opcode != 0 || q.qtype != 1) // 1 = A (IPv4)
            {
                printf("[DNS] Non-standard query detected (OPCODE=%u, QTYPE=%u) — using /api/dns_resolver...\n",
                       opcode, q.qtype);

                unsigned char response_buf[BUF_SIZE];
                size_t resp_len = 0;

                if (send_to_api_dns_resolver(buffer, n, response_buf, &resp_len) && resp_len > 0)
                {
                    sendto(sockfd, response_buf, resp_len, 0,
                           (struct sockaddr *)&client_addr, addr_len);
                    printf("[DNS] Responded to %s via /api/dns_resolver (%zu bytes)\n",
                           client_ip, resp_len);
                }
                else
                {
                    printf("[DNS] /api/dns_resolver failed for OPCODE=%u, QTYPE=%u — trying fallback...\n",
                           opcode, q.qtype);

                    unsigned char fallback_buf[BUF_SIZE];
                    size_t fallback_len = 0;
                    if (forward_to_upstream_dns(buffer, n, fallback_buf, &fallback_len))
                    {
                        sendto(sockfd, fallback_buf, fallback_len, 0,
                               (struct sockaddr *)&client_addr, addr_len);
                        printf("[DNS-Fallback] Responded to %s via 8.8.8.8 (%zu bytes)\n",
                               client_ip, fallback_len);
                    }
                    else
                    {
                        printf("[DNS-Fallback] Upstream 8.8.8.8 failed for %s\n", q.qname);
                    }
                }

                fflush(stdout);
                continue; // saltar al siguiente ciclo del loop principal
            }

            if (send_to_api_and_get_response(q.qname, client_ip, resolved_ip, sizeof(resolved_ip)))
            {
                resp_len = build_dns_response(buffer, n, &hdr, &q, resolved_ip, response_buf, sizeof(response_buf));
                if (resp_len > 0)
                {
                    sendto(sockfd, response_buf, resp_len, 0,
                           (struct sockaddr *)&client_addr, addr_len);
                    printf("[DNS] Responded to %s with %s (%zu bytes)\n", client_ip, resolved_ip, resp_len);
                }
                else
                {
                    printf("[DNS] Failed to build DNS response for %s\n", q.qname);
                }
            }
            else
            {
                printf("[DNS] API call failed or no IP for %s — trying fallback...\n", q.qname);

                unsigned char fallback_buf[BUF_SIZE];
                size_t fallback_len = 0;
                if (forward_to_upstream_dns(buffer, n, fallback_buf, &fallback_len))
                {
                    sendto(sockfd, fallback_buf, fallback_len, 0,
                           (struct sockaddr *)&client_addr, addr_len);
                    printf("[DNS-Fallback] Responded to %s via 8.8.8.8 (%zu bytes)\n",
                           client_ip, fallback_len);
                }
                else
                {
                    printf("[DNS-Fallback] Upstream 8.8.8.8 failed for %s\n", q.qname);
                }
            }

            fflush(stdout);
        }
        else
        {
            printf("[DNS] Malformed packet from %s\n", client_ip);
            fflush(stdout);
        }
    }

    close(sockfd);
    return 0;
}
