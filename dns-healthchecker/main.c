#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <time.h>
#include "regions.h"
#include <curl/curl.h>
#include <jansson.h>

// Prototipos de funciones implementadas en otros módulos
int tcp_health_check(const char* ip, int port, double* rtt_ms);
int http_health_check(const char* url, double* rtt_ms, int* http_code);
void update_health_in_firebase(const char* fqdn,
                               const char* target_id,
                               const char* ip,
                               const char* region,
                               const char* status,
                               double rtt);

typedef struct {
    const char* fqdn;
    const char* target_id;
    const char* ip;
    int port;
    const char* url;
} target_t;

// Targets simulados según Firebase
target_t TEST_TARGETS[] = {
    {"single.example.com", "single-1", "192.0.2.1", 80, "http://192.0.2.1"},
    {"multi.example.com", "multi-1", "192.0.2.1", 80, "http://192.0.2.1"},
    {"multi.example.com", "multi-2", "192.0.2.2", 80, "http://192.0.2.2"},
    {"multi.example.com", "multi-3", "192.0.2.3", 80, "http://192.0.2.3"},
    {"geo.example.com", "us-east", "192.0.2.1", 80, "http://192.0.2.1"},
    {"geo.example.com", "eu-west", "198.51.100.1", 80, "http://198.51.100.1"},
    {"geo.example.com", "asia-pacific", "203.0.113.1", 80, "http://203.0.113.1"},
    {"roundtrip.example.com", "rt-1", "192.0.2.1", 80, "http://192.0.2.1"},
    {"roundtrip.example.com", "rt-2", "198.51.100.1", 80, "http://198.51.100.1"},
    {"roundtrip.example.com", "rt-3", "203.0.113.1", 80, "http://203.0.113.1"}
};

#define TARGET_COUNT (sizeof(TEST_TARGETS) / sizeof(TEST_TARGETS[0]))

struct curl_memory {
    char *response;
    size_t size;
};

static size_t curl_write_cb(void *data, size_t size, size_t nmemb, void *userp)
{
    size_t realsize = size * nmemb;
    struct curl_memory *mem = (struct curl_memory *)userp;
    char *ptr = realloc(mem->response, mem->size + realsize + 1);
    if (!ptr) return 0; /* out of memory */
    mem->response = ptr;
    memcpy(&(mem->response[mem->size]), data, realsize);
    mem->size += realsize;
    mem->response[mem->size] = '\0';
    return realsize;
}


static int parse_targets_from_json(const char *json_str, target_t **out_targets)
{
    json_error_t error;
    json_t *root = json_loads(json_str, 0, &error);
    if (!root) {
        fprintf(stderr, "[HealthChecker] jansson parse error: %s\n", error.text);
        return 0;
    }


    int is_array = json_is_array(root);
    int is_object = json_is_object(root);
    if (!is_array && !is_object) {
        json_decref(root);
        return 0;
    }

    int capacity = 64;
    int count = 0;
    target_t *arr = malloc(sizeof(target_t) * capacity);
    if (!arr) { json_decref(root); return 0; }

    if (is_array) {
        size_t idx;
        json_t *rec;
        json_array_foreach(root, idx, rec) {
            json_t *jfqdn = json_object_get(rec, "fqdn");
            json_t *jtargets = json_object_get(rec, "targets");
            if (!jfqdn || !json_is_string(jfqdn) || !jtargets || !json_is_array(jtargets)) continue;

            const char *fqdn = json_string_value(jfqdn);
            size_t tindex;
            json_t *tobj;
            json_array_foreach(jtargets, tindex, tobj) {
                json_t *jid = json_object_get(tobj, "id");
                json_t *jip = json_object_get(tobj, "ip");
                if (!jid || !jip || !json_is_string(jid) || !json_is_string(jip)) continue;

                const char *tid = json_string_value(jid);
                const char *tip = json_string_value(jip);

                if (count >= capacity) {
                    capacity *= 2;
                    target_t *tmp = realloc(arr, sizeof(target_t) * capacity);
                    if (!tmp) goto parse_cleanup;
                    arr = tmp;
                }

                arr[count].fqdn = strdup(fqdn);
                arr[count].target_id = strdup(tid);
                arr[count].ip = strdup(tip);
                arr[count].port = 80;
                char urlbuf[128];
                snprintf(urlbuf, sizeof(urlbuf), "http://%s", tip);
                arr[count].url = strdup(urlbuf);
                count++;
            }
        }
    } else if (is_object) {
        const char *key;
        json_t *rec;
        json_object_foreach(root, key, rec) {
            json_t *jtargets = json_object_get(rec, "targets");
            if (!jtargets || !json_is_array(jtargets)) continue;

            size_t tindex;
            json_t *tobj;
            json_array_foreach(jtargets, tindex, tobj) {
                json_t *jid = json_object_get(tobj, "id");
                json_t *jip = json_object_get(tobj, "ip");
                if (!jid || !jip || !json_is_string(jid) || !json_is_string(jip)) continue;

                const char *tid = json_string_value(jid);
                const char *tip = json_string_value(jip);

                if (count >= capacity) {
                    capacity *= 2;
                    target_t *tmp = realloc(arr, sizeof(target_t) * capacity);
                    if (!tmp) goto parse_cleanup;
                    arr = tmp;
                }

                arr[count].fqdn = strdup(key);
                arr[count].target_id = strdup(tid);
                arr[count].ip = strdup(tip);
                arr[count].port = 80;
                char urlbuf[128];
                snprintf(urlbuf, sizeof(urlbuf), "http://%s", tip);
                arr[count].url = strdup(urlbuf);
                count++;
            }
        }
    }

    json_decref(root);
    if (count == 0) { free(arr); *out_targets = NULL; return 0; }
    *out_targets = arr;
    return count;

parse_cleanup:
    json_decref(root);
    for (int i = 0; i < count; i++) {
        free((void*)arr[i].fqdn);
        free((void*)arr[i].target_id);
        free((void*)arr[i].ip);
        free((void*)arr[i].url);
    }
    free(arr);
    return 0;
}

static void free_targets(target_t *arr, int count)
{
    if (!arr) return;
    for (int i = 0; i < count; i++) {
        if (arr[i].fqdn) free((void*)arr[i].fqdn);
        if (arr[i].target_id) free((void*)arr[i].target_id);
        if (arr[i].ip) free((void*)arr[i].ip);
        if (arr[i].url) free((void*)arr[i].url);
    }
    free(arr);
}

static int fetch_targets_from_api(target_t **out_targets)
{
    CURL *curl = NULL;
    CURLcode res;
    struct curl_memory mem = {0};
    int parsed = 0;

    curl_global_init(CURL_GLOBAL_DEFAULT);
    curl = curl_easy_init();
    if (!curl) return 0;

    const char *url = "http://dns-api:8080/api/records";
    curl_easy_setopt(curl, CURLOPT_URL, url);
    curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, curl_write_cb);
    curl_easy_setopt(curl, CURLOPT_WRITEDATA, &mem);
    curl_easy_setopt(curl, CURLOPT_TIMEOUT_MS, 3000L);

    res = curl_easy_perform(curl);
    if (res == CURLE_OK && mem.response && mem.size > 0) {
        parsed = parse_targets_from_json(mem.response, out_targets);
    } else {
        fprintf(stderr, "[HealthChecker] Failed to fetch records from API: %s\n", curl_easy_strerror(res));
    }

    if (mem.response) free(mem.response);
    curl_easy_cleanup(curl);
    curl_global_cleanup();
    return parsed;
}

// Simula una latencia distinta por región
double simulated_latency(const char* region) {
    if (strcmp(region, "na") == 0) return 20 + rand() % 60;
    if (strcmp(region, "eu") == 0) return 60 + rand() % 90;
    if (strcmp(region, "sa") == 0) return 100 + rand() % 80;
    if (strcmp(region, "ca") == 0) return 40 + rand() % 70;
    if (strcmp(region, "as") == 0) return 90 + rand() % 100;
    return 999.0;
}

int main() {
    srand(time(NULL));
    printf("[HealthChecker] Simulando %d regiones...\n", REGION_COUNT);

    while (1) {
        target_t *live_targets = NULL;
        int live_count = fetch_targets_from_api(&live_targets);

        for (int r = 0; r < REGION_COUNT; r++) {
            const char* region = REGIONS[r];
            printf("\n[Region %s] Iniciando verificación...\n", region);

            if (live_count > 0 && live_targets) {
                for (int i = 0; i < live_count; i++) {
                    double rtt_ms = simulated_latency(region);
                    const char* status = (rtt_ms > 250) ? "unhealthy" : "healthy";

                    printf("[Live] %s -> %s (%s) desde %s: %.2fms (%s)\n",
                           live_targets[i].fqdn,
                           live_targets[i].target_id,
                           live_targets[i].ip,
                           region,
                           rtt_ms,
                           status);

                    update_health_in_firebase(
                        live_targets[i].fqdn,
                        live_targets[i].target_id,
                        live_targets[i].ip,
                        region,
                        status,
                        rtt_ms
                    );

                    sleep(1);
                }
            } else {
                for (int i = 0; i < TARGET_COUNT; i++) {
                    double rtt_ms = simulated_latency(region);
                    const char* status = (rtt_ms > 250) ? "unhealthy" : "healthy";

                    printf("[Simulado] %s -> %s desde %s: %.2fms (%s)\n",
                           TEST_TARGETS[i].fqdn,
                           TEST_TARGETS[i].target_id,
                           region,
                           rtt_ms,
                           status);

                    update_health_in_firebase(
                        TEST_TARGETS[i].fqdn,
                        TEST_TARGETS[i].target_id,
                        TEST_TARGETS[i].ip,
                        region,
                        status,
                        rtt_ms
                    );

                    sleep(1);
                }
            }
        }

        if (live_targets) {
            free_targets(live_targets, live_count);
            live_targets = NULL;
            live_count = 0;
        }

        printf("\n[HealthChecker] Ciclo completo. Esperando 30s...\n");
        sleep(30);
    }

    return 0;
}
