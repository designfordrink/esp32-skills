#include <stdio.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_log.h"

static const char *TAG = "HELTEC_LVGL";

void app_main(void)
{
    ESP_LOGI(TAG, "Heltec LVGL Test starting...");
    
    // Will add LVGL + SSD1306 init when dependencies are installed
    
    while (1) {
        printf(".");
        fflush(stdout);
        vTaskDelay(pdMS_TO_TICKS(1000));
    }
}
