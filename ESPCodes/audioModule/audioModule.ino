#include <WiFi.h>
#include <driver/i2s.h>

// Wi-Fi credentials and server IP/port
const char* ssid = "RP_SCAN";
const char* password = "12345678";
const char* server_ip = "192.168.0.101";
const uint16_t server_port = 12346;

WiFiClient client;

// I2S Pins
#define I2S_WS 11
#define I2S_SD 10
#define I2S_SCK 12
#define I2S_PORT I2S_NUM_0

bool recording = false;

void setup() {
  Serial.begin(115200);

  // Initialize Wi-Fi
  WiFi.begin(ssid, password);
  Serial.println("Connecting to Wi-Fi...");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nConnected to Wi-Fi.");

  // Connect to the server
  Serial.println("Connecting to server...");
  while (!client.connect(server_ip, server_port)) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nConnected to server.");

  // Initialize I2S
  i2s_install();
  i2s_setpin();
  i2s_start(I2S_PORT);
}

void loop() {
  // Check for incoming commands
  if (client.available()) {
    String command = client.readStringUntil('\n');
    command.trim(); // Remove any whitespace

    if (command.equalsIgnoreCase("START")) {
      recording = true;
      Serial.println("Recording started.");
    } else if (command.equalsIgnoreCase("STOP")) {
      recording = false;
      Serial.println("Recording stopped.");
    }
  }

  // If recording is active, read and send audio data
  if (recording) {
    const int buffer_len = 1024;
    int16_t buffer[buffer_len];
    size_t bytes_read = 0;

    // Read data from I2S
    esp_err_t result = i2s_read(I2S_PORT, buffer, sizeof(buffer), &bytes_read, 0); // Non-blocking read
    if (result == ESP_OK && bytes_read > 0) {
      // Send raw data over TCP
      client.write((uint8_t*)buffer, bytes_read);
    }
  }

  // Small delay to yield to other tasks
  delay(10);
}

void i2s_install() {
  const i2s_config_t i2s_config = {
    .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_RX),
    .sample_rate = 44100,
    .bits_per_sample = I2S_BITS_PER_SAMPLE_16BIT,
    .channel_format = I2S_CHANNEL_FMT_ONLY_LEFT,
    .communication_format = I2S_COMM_FORMAT_I2S,
    .intr_alloc_flags = ESP_INTR_FLAG_LEVEL1,
    .dma_buf_count = 8,
    .dma_buf_len = 1024,
    .use_apll = false,
    .tx_desc_auto_clear = false,
    .fixed_mclk = 0
  };

  i2s_driver_install(I2S_PORT, &i2s_config, 0, NULL);
}

void i2s_setpin() {
  const i2s_pin_config_t pin_config = {
    .bck_io_num = I2S_SCK,
    .ws_io_num = I2S_WS,
    .data_out_num = I2S_PIN_NO_CHANGE,
    .data_in_num = I2S_SD
  };

  i2s_set_pin(I2S_PORT, &pin_config);
}
