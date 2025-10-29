#include <curl/curl.h>
#include <stdio.h>

int http_health_check(const char* url, double* rtt_ms, int* http_code) {
    CURL *curl = curl_easy_init();
    if (!curl) return 0;

    curl_easy_setopt(curl, CURLOPT_URL, url);
    curl_easy_setopt(curl, CURLOPT_NOBODY, 1L);
    curl_easy_setopt(curl, CURLOPT_TIMEOUT_MS, 3000L);

    CURLcode res = curl_easy_perform(curl);
    if (res != CURLE_OK) {
        curl_easy_cleanup(curl);
        return 0;
    }

    curl_easy_getinfo(curl, CURLINFO_RESPONSE_CODE, http_code);
    curl_easy_getinfo(curl, CURLINFO_TOTAL_TIME, rtt_ms);
    curl_easy_cleanup(curl);
    return 1;
}
