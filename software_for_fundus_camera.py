import cv2
import numpy as np
import serial
import time
import os


# Параметры для редактирования
square_size = 300  # Размер квадрата
square_x = 182     # Координата X верхнего левого угла квадрата
square_y = 84     # Координата Y верхнего левого угла квадрата
circle_radius = 87  # Радиус круговой маски

# Инициализация порта для команды "snap"
ser = serial.Serial('COM12', 9600, timeout=1)
time.sleep(2)  # Подождем, пока установится соединение с платой

# Папка для сохранения снимков
output_dir = "snapshots"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# Флаг для предотвращения многократного снимка
snap_flag = False

# Функция для получения изображения с камеры и обработки
def process_frame(frame):
    global square_size, square_x, square_y, circle_radius
    
    height, width, _ = frame.shape
    
    # Обрезаем изображение до квадрата
    x1 = square_x
    y1 = square_y
    x2 = square_x + square_size
    y2 = square_y + square_size
    
    # Убедимся, что квадрат не выходит за пределы изображения
    x1 = max(0, min(x1, width))
    y1 = max(0, min(y1, height))
    x2 = max(0, min(x2, width))
    y2 = max(0, min(y2, height))
    
    cropped_frame = frame[y1:y2, x1:x2]
    
    # Получаем новые размеры обрезанного изображения
    crop_height, crop_width, _ = cropped_frame.shape
    
    # Создаём черную маску
    mask = np.zeros((crop_height, crop_width), dtype=np.uint8)
    
    # Центр изображения для маски
    center_x = crop_width // 2
    center_y = crop_height // 2
    
    # Рисуем белый круг на маске
    cv2.circle(mask, (center_x, center_y), circle_radius, 255, -1)
    
    # Применяем маску к изображению (все, что вне круга, станет черным)
    result = cv2.bitwise_and(cropped_frame, cropped_frame, mask=mask)
    
    return result

# Функция для сохранения текущего кадра с обработкой
def take_snapshot(count, processed_frame):
    filename = f'{output_dir}/snapshot_{count}.png'
    cv2.imwrite(filename, processed_frame)
    print(f"Снимок сохранен: {filename}")
    return filename

# Функция для объединения двух изображений
def detect_white_glare(image, threshold=218):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, white_glare_mask = cv2.threshold(gray, threshold, 255, cv2.THRESH_BINARY)
    return white_glare_mask

def detect_purple_glare(image):
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    lower_purple = np.array([120, 50, 50])
    upper_purple = np.array([150, 255, 255])
    purple_glare_mask = cv2.inRange(hsv, lower_purple, upper_purple)
    return purple_glare_mask

def remove_glare(image, combined_glare_mask):
    result = image.copy()
    result[combined_glare_mask == 255] = [0, 0, 0]
    return result

def merge_images(images, masks):
    merged_image = np.zeros_like(images[0])
    for i in range(len(images)):
        merged_image = np.where(masks[i][:, :, None] == 0, images[i], merged_image)
    return merged_image

def process_images(image_paths):
    images = [cv2.imread(path) for path in image_paths]
    glare_masks = []
    for image in images:
        white_glare_mask = detect_white_glare(image)
        purple_glare_mask = detect_purple_glare(image)
        combined_glare_mask = cv2.bitwise_or(white_glare_mask, purple_glare_mask)
        glare_masks.append(combined_glare_mask)
    processed_images = [remove_glare(image, mask) for image, mask in zip(images, glare_masks)]
    final_image = merge_images(processed_images, glare_masks)
    return final_image

# Функция для обработки ползунков
def update_square_size(val):
    global square_size
    square_size = val

def update_circle_radius(val):
    global circle_radius
    circle_radius = val

def update_square_x(val):
    global square_x
    square_x = val

def update_square_y(val):
    global square_y
    square_y = val

# Создание окон с ползунками
cv2.namedWindow('Processed Frame')
cv2.createTrackbar('Square Size', 'Processed Frame', square_size, 500, update_square_size)
cv2.createTrackbar('Circle Radius', 'Processed Frame', circle_radius, 500, update_circle_radius)
cv2.createTrackbar('Square X', 'Processed Frame', square_x, 500, update_square_x)
cv2.createTrackbar('Square Y', 'Processed Frame', square_y, 500, update_square_y)

# Подключение к камере
cap = cv2.VideoCapture(0)
snapshot_count = 0
snapshots = []

# Основной цикл
while True:
    ret, frame = cap.read()
    if not ret:
        print("Не удалось получить кадр")
        break

    # Обрабатываем текущий кадр с ползунками
    processed_frame = process_frame(frame)
    
    # Отображение текущего обработанного изображения
    cv2.imshow("Processed Frame", processed_frame)

    # Проверка на команду "snap"
    if ser.in_waiting > 0:
        line = ser.readline().decode('utf-8').strip()
        if line == "snap" and not snap_flag:
            snap_flag = True
            time.sleep(0.1)  # Задержка перед снимком для синхронизации
            snapshot_count += 1
            snapshot_file = take_snapshot(snapshot_count, processed_frame)  # Сохраняем обработанный кадр
            snapshots.append(snapshot_file)
    
    # Если сохранено два изображения, обрабатываем их
    if len(snapshots) == 2:
        result = process_images(snapshots)
        cv2.imwrite('merged_image.jpg', result)
        cv2.imshow('Merged Image', result)
        snapshots = []  # Очищаем список после объединения

    # Сбрасываем флаг, если не "snap"
    if not (ser.in_waiting > 0 and line == "snap"):
        snap_flag = False

    # Выход по нажатию 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Освобождаем ресурсы
cap.release()
ser.close()
cv2.destroyAllWindows()
