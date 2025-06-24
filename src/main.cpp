#include <Arduino.h>
#include <SoftwareSerial.h>

// ESP-12F LD2412 串列埠轉發器
// LD2412 TX -> ESP-12F GPIO15 (SoftwareSerial接收)
// LD2412 RX -> ESP-12F GPIO2 (硬體UART1 TX發送)
// 轉發到UART0讓電腦接收

SoftwareSerial ld2412Receive(15, -1); // 只用GPIO15接收LD2412數據

void setup() {
  // UART0與電腦通信 (GPIO1=TX, GPIO3=RX)
  Serial.begin(115200);
  
  // SoftwareSerial接收LD2412數據
  ld2412Receive.begin(115200);
  
  // 硬體UART1 TX (GPIO2) 發送給LD2412
  Serial1.begin(115200);
  
  delay(1000);
  
  // 清空緩衝區
  while (Serial.available()) Serial.read();
  while (ld2412Receive.available()) ld2412Receive.read();
  
  Serial.println("ESP-12F LD2412 串列埠轉發器已啟動");
  Serial.println("配置: LD2412 TX->GPIO15(SoftwareSerial接收), LD2412 RX->GPIO2(硬體UART1 TX發送)");
  Serial.println("波特率: 115200 bps");
  Serial.println("等待LD2412自動發送數據...");
  
  delay(100);
}

void loop() {
  static unsigned long lastPrint = 0;
  static int byteCount = 0;
  
  // LD2412 -> 電腦 (透過GPIO15接收，轉發到UART0)
  if (ld2412Receive.available()) {
    uint8_t data = ld2412Receive.read();
    Serial.write(data);  // 透過UART0發送給電腦
    Serial.flush();
    byteCount++;
  }
  
  // 電腦 -> LD2412 (透過UART0接收，轉發到硬體UART1 TX)
  if (Serial.available()) {
    uint8_t data = Serial.read();
    Serial1.write(data);  // 透過硬體UART1 TX發送給LD2412
    Serial1.flush();
  }
  
  // 每5秒顯示統計信息
  if (millis() - lastPrint > 5000) {
    Serial.print("已接收字節數: ");
    Serial.println(byteCount);
    lastPrint = millis();
    
    if (byteCount == 0) {
      Serial.println("提示: 如果沒有收到數據，請檢查:");
      Serial.println("  1. LD2412電源是否正常(3.3V)");
      Serial.println("  2. GPIO15接線是否正確");
      Serial.println("  3. LD2412是否正常工作");
    }
  }
} 