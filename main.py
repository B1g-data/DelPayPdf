import fitz  # PyMuPDF
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
import os
import re
import uuid
from dotenv import load_dotenv

processing_flag = False #надо подумать, не внедрял, лучше перейти на очередь нормальную

image_path = 'images/stc.png'
image_path2 = 'images/Line 33.png'

# ТКП
KEYWORD1="Сведения об оплате/Payment information"
KEYWORD2="Итого/Total"

# Ваучеры
KEYWORD3="SERVICE CONFIRMATION VOUCHER"
KEYWORD4="COMMENTS"

# РЖД
KEYWORD5="Оплата "
KEYWORD6="Вкл. НДС"

# Мой Агент
KEYWORD7 = "For more detailed information about the baggage"
KEYWORD8 = "Passengers on a journey involving an ultimat"
KEYWORD9 = "Payment receipt"
KEYWORD10 = "End of itinerary receipt"
KEYWORD11 = "Стоимость"
KEYWORD12 = "Офис оформления"

# Ключевые слова для запуска функций
keyword_actions = {
    "(itinerary/receipt)": lambda file_path, output_pdf: tkp(file_path, output_pdf, KEYWORD1, KEYWORD2), #ТКП
    "SERVICE CONFIRMATION VOUCHER": lambda file_path, output_pdf: vaucher(file_path, output_pdf, image_path, image_path2, KEYWORD3, KEYWORD4), #Ваучер
    "ЭЛЕКТРОННЫЙ БИЛЕТ. КОНТРОЛЬНЫЙ КУПОН": lambda file_path, output_pdf: rzd(file_path, output_pdf, KEYWORD5, KEYWORD6), #РЖД
    "Мой Агент / My Agent": lambda file_path, output_pdf: agent(file_path, output_pdf, KEYWORD9, KEYWORD7, KEYWORD8, KEYWORD10), #МойАгент
    "Маршрутная квитанция": lambda file_path, output_pdf: s7(file_path, output_pdf, KEYWORD11, KEYWORD12), #S7
}

################################################################################################################ Мой Агент
def s7(file_path, output_pdf, KEYWORD11, KEYWORD12):
    try:
        # Открытие PDF документа
        with fitz.open(file_path) as doc:
            page_number = 0
            while page_number < doc.page_count:
                page = doc.load_page(page_number)

                # Ищем оба ключевых слова
                text_instances1 = page.search_for(KEYWORD11)
                text_instances2 = page.search_for(KEYWORD12)

                if text_instances1 and text_instances2:
                    
                    for inst1 in text_instances1:
                        for inst2 in text_instances2:
                            # Если ключевые слова найдены, определяем их координаты
                            x1, y1 = inst1.x1, inst1.y1
                            x2, y2 = inst2.x1, inst2.y1
                            
                            if y1 and y2:
                                # Закрашиваем область от верхнего-левого края первого ключевого слова до нижнего края второго (до границы страницы справа)
                                rect_to_redact = fitz.Rect(x1-80, y1-15, page.rect.width, y2-30)
                                page.draw_rect(rect_to_redact, color=(1, 1, 1), fill=1)


                page_number += 1  # Переходим к следующей странице

            # Сохраняем изменения в новый файл PDF
            doc.save(output_pdf)  # Сохраняем результат в новый файл


    except Exception as e:
        pass

################################################################################################################ S7

def agent(file_path, output_pdf, KEYWORD9, KEYWORD7, KEYWORD8, KEYWORD10):
    """
    Оптимизированная функция для обработки PDF:
    - Если на одной странице KEYWORD9 и KEYWORD10, закрашивает текст от KEYWORD10 до конца страницы.
    - Если на странице только KEYWORD9, удаляет эту страницу.
    - Закрашивает текст между KEYWORD7 и KEYWORD8.
    """
    try:
        # Открываем PDF документ
        with fitz.open(file_path) as doc:
            pages_to_delete = []  # Список страниц для удаления

            for page_index in range(doc.page_count):
                page = doc[page_index]
                page_text = page.get_text()

                # Проверка на наличие ключевых слов на странице
                has_keyword9 = KEYWORD9 in page_text
                has_keyword10 = KEYWORD10 in page_text

                if has_keyword9 and has_keyword10:
                    # Закрашиваем область от KEYWORD10 до конца страницы
 
                    for start in page.search_for(KEYWORD10):
                        area = fitz.Rect(0, start.y1, page.rect.width, page.rect.height)
                        page.draw_rect(area, color=(1, 1, 1), fill=1)

                elif has_keyword9:
                    # Удаляем страницу, если только KEYWORD9
                    pages_to_delete.append(page_index)

                # Поиск и закрашивание областей между KEYWORD7 и KEYWORD8
                start_instances = page.search_for(KEYWORD7)
                end_instances = page.search_for(KEYWORD8) if KEYWORD8 else []

                for start in start_instances:
                    y_start = start.y1
                    for end in end_instances:
                        y_end = end.y1
                        if y_start < y_end:
                            area = fitz.Rect(0, y_start + 3, page.rect.width, y_end)
                            page.draw_rect(area, color=(1, 1, 1), fill=1)

            # Удаление страниц
            if pages_to_delete:
                doc.delete_pages(pages_to_delete)

            # Сохранение результата
            doc.save(output_pdf)

    except Exception as e:
        pass


################################################################################################################ ТКП

def tkp(file_path, output_pdf, KEYWORD1, KEYWORD2):    
    try:
        with fitz.open(file_path) as doc:
            for page_number in range(doc.page_count):
                page = doc[page_number]
                
                # Поиск первого и второго ключевых слов
                text_instances1 = page.search_for(KEYWORD1)
                text_instances2 = page.search_for(KEYWORD2)

                if not text_instances1 or not text_instances2:
                    continue

                # Закрашивание областей между найденными ключевыми словами
                y1 = min(inst.y1 for inst in text_instances1)
                y2 = max(inst.y1 for inst in text_instances2)
                
                if y1 < y2:  # Проверяем корректность границ
                    rect_to_redact = fitz.Rect(0, y1 - 10, page.rect.width, y2 + 5)
                    page.draw_rect(rect_to_redact, color=(1, 1, 1), fill=1)

            # Сохраняем изменения
            doc.save(output_pdf)
    
    except Exception as e:
        pass

########################################################################################################################## Ваучер

# Функция для поиска ключевых слов и удаления текста (закрашивания) между ними
def vaucher(file_path, output_pdf, image_path, image_path2, KEYWORD3, KEYWORD4):

    try:
        with fitz.open(file_path) as doc:
            for page_number in range(doc.page_count):  # Итерация по страницам документа
                page = doc.load_page(page_number)

                # Поиск первого и второго ключевых слов
                text_instances1 = page.search_for(KEYWORD3)
                text_instances2 = page.search_for(KEYWORD4)

                # Пропускаем страницу, если любое из ключевых слов не найдено
                if not text_instances1 or not text_instances2:
                    continue

                # Берем верхнюю границу первого ключевого слова и нижнюю второго
                y1 = min(inst.y1 for inst in text_instances1)
                y2 = max(inst.y1 for inst in text_instances2)

                # Проверяем корректность границ
                if y1 >= y2:
                    continue

                # Закрашивание области сверху страницы до первого ключевого слова
                page.draw_rect(fitz.Rect(0, 0, page.rect.width, y1 - 20), color=(1, 1, 1), fill=1)
                # Закрашивание области от второго ключевого слова до конца страницы
                page.draw_rect(fitz.Rect(0, y2 + 20, page.rect.width, page.rect.height), color=(1, 1, 1), fill=1)

                # Вставка изображений
                page.insert_image(fitz.Rect(386, 36, 559, 69), filename=image_path)  # Координаты изображения 1
                page.insert_image(fitz.Rect(36, 78, 551, 79), filename=image_path2)  # Координаты изображения 2

            # Сохранение документа
            doc.save(output_pdf)
    except Exception as e:
        pass
################################################################################################################ РЖД

def rzd(file_path, output_pdf, KEYWORD5, KEYWORD6):
    
    try:
        # Открытие PDF документа
        with fitz.open(file_path) as doc:
            page_number = 0
            while page_number < doc.page_count:
                page = doc.load_page(page_number)
                page_text = page.get_text()  # Получаем текст страницы один раз

                # Проверяем наличие строки "Квитанция об оплате / Payment receipt"
                if "Квитанция об оплате / Payment receipt" in page_text:
                    doc.delete_page(page_number)  # Удаляем страницу
                    continue  # Переходим к следующей странице

                # Ищем оба ключевых слова
                text_instances1 = page.search_for(KEYWORD5)
                text_instances2 = page.search_for(KEYWORD6)

                if text_instances1 and text_instances2:
                    
                    for inst1 in text_instances1:
                        for inst2 in text_instances2:
                            # Если ключевые слова найдены, определяем их координаты
                            x1, y1 = inst1.x1, inst1.y1
                            x2, y2 = inst2.x1, inst2.y1
                            
                            if y1 and y2:
                                # Закрашиваем область от верхнего-левого края первого ключевого слова до нижнего края второго (до границы страницы справа)
                                rect_to_redact = fitz.Rect(x1-22, y1-10, page.rect.width, y2)
                                page.draw_rect(rect_to_redact, color=(1, 1, 1), fill=1)

                page_number += 1  # Переходим к следующей странице

            # Сохраняем изменения в новый файл PDF
            doc.save(output_pdf)  # Сохраняем результат в новый файл

    except Exception as e:
        pass
    
################################################################################################################

def find_keywords_in_pdf(file_path, output_pdf, keyword_actions):

    try:
        with fitz.open(file_path) as doc:
            print('Файл открыт')

            # Составляем регулярное выражение из всех ключевых слов
            keywords_pattern = "|".join(re.escape(keyword) for keyword in keyword_actions)
            compiled_pattern = re.compile(keywords_pattern, re.IGNORECASE)

            # Проверяем только первую страницу
            if len(doc) > 0:
                page = doc[0]
                text = page.get_text()
                match = compiled_pattern.search(text)
                if match:
                    keyword = match.group()
                    print(f"Найдено ключевое слово '{keyword}' на первой странице")
                    # Выполнение действия без преобразования регистра (улучшение)
                    keyword_actions[keyword](file_path, output_pdf)

    except Exception as e:
        print(f"Ошибка при обработке PDF: {e}")

        
# Обработчик команды /start
async def start(update: Update, context: CallbackContext):
    await update.message.reply_text('Привет! Отправь мне PDF файл для обработки. (В случае ошибки обратись ко мне @B1g_data)')
    if os.path.exists('temp_files'):
    # Очистка содержимого папки
        for filename in os.listdir('temp_files'):
            file_path = os.path.join('temp_files', filename)
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)  # Удаляем файл
            except:
                break

# Обработчик получения PDF файла
async def handle_pdf(update: Update, context: CallbackContext):

    # Получаем файл от пользователя
    file = update.message.document
    file_id = file.file_id
    file_name = re.sub(r'[^\w\-_\. ]', '_', file.file_name)
    
    # Проверяем MIME-тип файла
    if file.mime_type != "application/pdf":
        await update.message.reply_text("Пожалуйста, отправьте PDF файл.")
        return
    
    # Загружаем файл
    new_file = await context.bot.get_file(file_id)
    file_path = f"temp_files/input_{uuid.uuid4().hex}_{file_name}"
    await new_file.download_to_drive(file_path)
    print(f"Сохраняем файл в: input_{file_name}'")

    output_pdf = f'temp_files/{file_name}'
    
    # Выполняем обработку
    try:
        find_keywords_in_pdf(file_path, output_pdf, keyword_actions)
        
        
        # Отправляем результат пользователю
        with open(output_pdf, 'rb') as f:
            await update.message.reply_document(f, caption="Вот твой обработанный PDF.")

        # Удаляем временные файлы
        f.close()
        if os.path.exists(file_path):
            os.remove(file_path)
        if os.path.exists(output_pdf):
            os.remove(output_pdf)
    
    except Exception as e:
        await update.message.reply_text(f"Произошла ошибка при обработке файла: {e}")

################################################################################################################

# Основная функция для запуска бота
def main():
    # Загрузить переменные из .env файла
    load_dotenv('BOT_TOKEN.env')

    # Получить значение токена
    token = os.getenv("BOT_TOKEN")

    # Проверьте, что токен загружен
    if not token:
        raise ValueError("Токен бота не найден. Проверьте файл .env.")
    
    # Создаем экземпляр приложения (бота)
    application = Application.builder().token(token).build()
    
    # Обработчики команд
    application.add_handler(CommandHandler("start", start))
    
    # Обработчик получения файла
    application.add_handler(MessageHandler(filters.Document.ALL, handle_pdf))
    
    # Запуск бота
    application.run_polling()

if __name__ == '__main__':
    main()