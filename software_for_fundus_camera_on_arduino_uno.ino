int buttonState = 0;  
int lastButtonState = 1;  // Предположим, что кнопка не нажата при старте
int trigger = 0;  
const int firstLed = 9;   // Пины светодиодов
const int secondLed = 10;
const int thirdLed = 11;

void setup() {
  Serial.begin(9600);  // Настраиваем скорость передачи данных
  pinMode(2, INPUT_PULLUP);  
  pinMode(firstLed, OUTPUT);  
  pinMode(secondLed, OUTPUT); 
  pinMode(thirdLed, OUTPUT);  

  digitalWrite(firstLed, HIGH);  // Включаем первый светодиод по умолчанию
}

void loop() {
  buttonState = digitalRead(2);  

  if (buttonState == LOW && lastButtonState == HIGH) {  // Кнопка была нажата
    trigger = 1;  

    // Выключаем первый светодиод перед включением других
    digitalWrite(firstLed, LOW);
    
    // Включаем второй светодиод и добавляем задержку перед отправкой команды
    digitalWrite(secondLed, HIGH);  
    delay(55);  // Задержка 50 мс для включения светодиода
    Serial.println("snap");  // Отправляем команду для фото
    delay(150);  // Задержка после отправки команды
    digitalWrite(secondLed, LOW);  
    
    // Включаем третий светодиод и добавляем задержку перед отправкой команды
    digitalWrite(thirdLed, HIGH);  
    delay(43);  // Задержка 50 мс для включения светодиода
    Serial.println("snap");  // Отправляем команду для фото
    delay(150);  // Задержка после отправки команды
    digitalWrite(thirdLed, LOW);  
    
    // После завершения работы двух светодиодов снова включаем первый
    digitalWrite(firstLed, HIGH);
  }

  lastButtonState = buttonState;  
}
