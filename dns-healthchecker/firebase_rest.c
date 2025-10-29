#include <curl/curl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// Traduce el código de región a país
void get_country_for_region(const char* region, char* country_out, size_t size) {
    if (strcmp(region, "na") == 0)
        snprintf(country_out, size, "US");
    else if (strcmp(region, "eu") == 0)
        snprintf(country_out, size, "DE");
    else if (strcmp(region, "sa") == 0)
        snprintf(country_out, size, "BR");
    else if (strcmp(region, "ca") == 0)
        snprintf(country_out, size, "CA");
    else if (strcmp(region, "as") == 0)
        snprintf(country_out, size, "JP");
    else if (strcmp(region, "oc") == 0)
        snprintf(country_out, size, "AU");
    else if (strcmp(region, "af") == 0)
        snprintf(country_out, size, "ZA");
    else
        snprintf(country_out, size, "ZZ");
}

void update_health_in_firebase(const char* fqdn,
                               const char* target_id,
                               const char* ip,
                               const char* region,
                               const char* status,
                               double rtt) {
    CURL *curl = curl_easy_init();
    if (!curl) {
        fprintf(stderr, "[Firebase] Error: could not initialize curl\n");
        return;
    }

    // Traducir región a país
    char country[8];
    get_country_for_region(region, country, sizeof(country));

    // Construir el cuerpo JSON con región + país + ip
    char json_body[1024];
    snprintf(json_body, sizeof(json_body),
        "{"
        "\"fqdn\":\"%s\"," 
        "\"target_id\":\"%s\"," 
        "\"ip\":\"%s\"," 
        "\"region\":\"%s\"," 
        "\"status\":\"%s\"," 
        "\"rtt\":%.2f," 
        "\"country\":\"%s\"," 
        "\"region_name\":\"%s\""
        "}",
        fqdn, target_id, ip, region, status, rtt, country, region
    );

    const char* url = "http://dns-api:8080/api/update_health";

    struct curl_slist *headers = NULL;
    headers = curl_slist_append(headers, "Content-Type: application/json");

    curl_easy_setopt(curl, CURLOPT_URL, url);
    curl_easy_setopt(curl, CURLOPT_POST, 1L);
    curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);
    curl_easy_setopt(curl, CURLOPT_POSTFIELDS, json_body);

    CURLcode res = curl_easy_perform(curl);
    if (res == CURLE_OK) {
        printf("[Firebase] Updated %s (%s -> %s, %.2fms, country=%s)\n",
               fqdn, target_id, status, rtt, country);
    } else {
        fprintf(stderr, "[Firebase] Error: %s\n", curl_easy_strerror(res));
    }

    curl_slist_free_all(headers);
    curl_easy_cleanup(curl);
}
