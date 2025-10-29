#include <arpa/inet.h>
#include <sys/socket.h>
#include <unistd.h>
#include <time.h>
#include <stdio.h>

int tcp_health_check(const char* ip, int port, double* rtt_ms) {
    int sock = socket(AF_INET, SOCK_STREAM, 0);
    if (sock < 0) return 0;

    struct sockaddr_in addr = {0};
    addr.sin_family = AF_INET;
    addr.sin_port = htons(port);
    inet_pton(AF_INET, ip, &addr.sin_addr);

    struct timespec start, end;
    clock_gettime(CLOCK_MONOTONIC, &start);
    int ok = connect(sock, (struct sockaddr*)&addr, sizeof(addr));
    clock_gettime(CLOCK_MONOTONIC, &end);
    close(sock);

    if (ok == 0) {
        *rtt_ms = (end.tv_sec - start.tv_sec) * 1000.0 +
                  (end.tv_nsec - start.tv_nsec) / 1e6;
        return 1;
    }
    return 0;
}
