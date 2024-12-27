import fitz  # PyMuPDF
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
import os
import re
import uuid
from dotenv import load_dotenv
import asyncio

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
KEYWORD9 = "End of itinerary receipt"
KEYWORD10 = "Payment receipt"

# S7
KEYWORD11 = "Стоимость"
KEYWORD12 = "Офис оформления"

# Ключевые слова для запуска функций
keyword_actions = {
    "(itinerary/receipt)": lambda file_path, output_pdf: tkp(file_path, output_pdf, KEYWORD1, KEYWORD2), #ТКП
    "SERVICE CONFIRMATION VOUCHER": lambda file_path, output_pdf: vaucher(file_path, output_pdf, image_path, image_path2, KEYWORD3, KEYWORD4), #Ваучер
    "ЭЛЕКТРОННЫЙ БИЛЕТ. КОНТРОЛЬНЫЙ КУПОН": lambda file_path, output_pdf: rzd(file_path, output_pdf, KEYWORD5, KEYWORD6), #РЖД
    "Мой Агент / My Agent": lambda file_path, output_pdf: agent(file_path, output_pdf, KEYWORD7, KEYWORD8, KEYWORD9, KEYWORD10), #МойАгент
    "Маршрутная квитанция": lambda file_path, output_pdf: s7(file_path, output_pdf, KEYWORD11, KEYWORD12), #S7
}

################################################################################################################ S7
"""
- Закрашивает текст между KEYWORD11 и KEYWORD12.
"""
def s7(file_path, output_pdf, KEYWORD11, KEYWORD12):
    try:
        with fitz.open(file_path) as doc:
            page_number = 0
            for page_number in range(doc.page_count):  # Итерация по страницам документа
                page = doc.load_page(page_number) # Загружаем страницу

                # Ищем первое ключевое слово
                text_instances0 = page.search_for(KEYWORD11)

                if text_instances0:
                    inst0 = text_instances0[0]
                    # Координаты первого ключевого слова
                    x0, y0 = inst0.x0, inst0.y0 # Левый верхний угол границы слова

                    # Ограничиваем область поиска второго ключевого слова
                    search_area = fitz.Rect(0, y0, page.rect.width, page.rect.height)
                    text_instances1 = page.search_for(KEYWORD12, clip=search_area)

                    if text_instances1:
                        inst1 = text_instances1[0]  # Берем первое совпадение
                        y1 = inst1.y0 # Верхняя граница слова

                        if y0 and y1:
                            # Закрашиваем область
                            rect_to_redact = fitz.Rect(x0, y0, page.rect.width, y1-8)
                            page.draw_rect(rect_to_redact, color=(1, 1, 1), fill=1)

            doc.save(output_pdf, deflate=True)

    except Exception as e:
        print(f"Error in s7 with file {file_path}: {e}")

################################################################################################################ Мой Агент
"""
- Если на одной странице KEYWORD9 и KEYWORD10, закрашивает текст от KEYWORD9 до конца страницы.
- Если на странице только KEYWORD10, удаляет эту страницу.
- Закрашивает текст между KEYWORD7 и KEYWORD8.
"""

def agent(file_path, output_pdf, KEYWORD7, KEYWORD8, KEYWORD9, KEYWORD10):
    try:
        with fitz.open(file_path) as doc:
            page_number = 0

            while page_number < doc.page_count:  # Итерация по страницам документа
                page = doc.load_page(page_number)  # Загружаем страницу

                # Ищем ключевые слова с помощью search_for
                text_instances0 = page.search_for(KEYWORD9)

                if text_instances0:
                    y0 = text_instances0[0].y0
                    search_area = fitz.Rect(0, y0, page.rect.width, page.rect.height)
                    text_instances1 = page.search_for(KEYWORD10)

                    # Закрашиваем область от KEYWORD9 до конца страницы
                    if text_instances1:
                        y0 = text_instances0[0].y0 # Левая верхняя граница слова
                        area = fitz.Rect(0, y0, page.rect.width, page.rect.height)
                        page.draw_rect(area, color=(1, 1, 1), fill=1)

                # Удаляем страницу, если только KEYWORD10 присутствует
                if not text_instances0:
                    doc.delete_page(page_number)
                    continue  # Переходим к следующей странице, так как эта удалена

                # Поиск и закрашивание областей между KEYWORD7 и KEYWORD8
                text_instances2 = page.search_for(KEYWORD7)

                if text_instances2:
                    y2 = text_instances2[0].y1  # Нижняя граница KEYWORD7
                    search_area = fitz.Rect(0, y2, page.rect.width, page.rect.height)
                    text_instances3 = page.search_for(KEYWORD8, clip=search_area)
                    y3 = text_instances3[0].y0  # Верхняя граница KEYWORD8

                    # Закрашиваем область между ними
                    if text_instances3:
                        area = fitz.Rect(0, y2, page.rect.width, y3)
                        page.draw_rect(area, color=(1, 1, 1), fill=1)

                # Переход к следующей странице
                page_number += 1

            # Сохраняем обработанный PDF
            doc.save(output_pdf, deflate=True)

    except Exception as e:
        print(f"Error in agent with file {file_path}: {e}")

################################################################################################################ ТКП

def tkp(file_path, output_pdf, KEYWORD1, KEYWORD2):
    try:
        with fitz.open(file_path) as doc:
            for page_number in range(doc.page_count):  # Итерация по страницам документа
                page = doc.load_page(page_number) # Итерируем по страницам
                # Поиск первого ключевого слова
                text_instances1 = page.search_for(KEYWORD1)
                if text_instances1:
                    y1 = text_instances1[0].y0  # Нижняя граница первого ключевого слова

                    # Для второго ключевого слова ищем только ниже первого
                    search_area = fitz.Rect(0, y1, page.rect.width, page.rect.height)
                    text_instances2 = page.search_for(KEYWORD2, clip=search_area)

                    if text_instances2:
                        y2 = text_instances2[0].y1  # Нижняя граница второго ключевого слова

                        # Закрашиваем область от первого ключевого слова до второго
                        rect_to_redact = fitz.Rect(0, y1, page.rect.width, y2+5)
                        page.draw_rect(rect_to_redact, color=(1, 1, 1), fill=1)

            # Сохраняем изменения
            doc.save(output_pdf, deflate=True)

    except Exception as e:
        print(f"Error in tkp with file {file_path}: {e}")


########################################################################################################################## Ваучер

def vaucher(file_path, output_pdf, image_path, image_path2, KEYWORD3, KEYWORD4):
    try:
        with fitz.open(file_path) as doc:
            for page_number in range(doc.page_count):  # Итерация по страницам документа
                page = doc.load_page(page_number)

                # Поиск первого ключевого слова (KEYWORD3)
                text_instances1 = page.search_for(KEYWORD3)
                if text_instances1:
                    # Берем верхнюю границу первого ключевого слова
                    y1 = text_instances1[0].y0  # Нижняя граница первого ключевого слова

                    # Для второго ключевого слова (KEYWORD4) ищем только ниже первого ключевого слова
                    search_area = fitz.Rect(0, y1, page.rect.width, page.rect.height)
                    text_instances2 = page.search_for(KEYWORD4, clip=search_area)

                    if text_instances2:
                        # Берем нижнюю границу второго ключевого слова
                        y2 = text_instances2[0].y1

                        # Закрашивание области сверху страницы до первого ключевого слова
                        page.draw_rect(fitz.Rect(0, 0, page.rect.width, y1), color=(1, 1, 1), fill=1)
                        # Закрашивание области от второго ключевого слова до конца страницы
                        page.draw_rect(fitz.Rect(0, y2 + 20, page.rect.width, page.rect.height), color=(1, 1, 1), fill=1)

                        # Вставка изображений
                        page.insert_image(fitz.Rect(386, 36, 559, 69), filename=image_path)  # Координаты изображения 1
                        page.insert_image(fitz.Rect(36, 78, 551, 79), filename=image_path2)  # Координаты изображения 2

            # Сохранение документа
            doc.save(output_pdf, deflate=True)

    except Exception as e:
        print(f"Error in vaucher with file {file_path}: {e}")

################################################################################################################ РЖД

def rzd(file_path, output_pdf, KEYWORD5, KEYWORD6):
    try:
        with fitz.open(file_path) as doc:
            page_number = 0

            while page_number < doc.page_count:
                page = doc.load_page(page_number)

                # Проверяем наличие строки "Квитанция об оплате / Payment receipt"
                if page.search_for("Квитанция об оплате / Payment receipt"):
                    doc.delete_page(page_number)  # Удаляем страницу
                    continue  # Переходим к следующей странице, так как эта удалена

                # Ищем первое ключевое слово
                text_instances1 = page.search_for(KEYWORD5)
                if text_instances1:
                    y1 = text_instances1[0].y0  # Нижняя граница первого ключевого слова

                    # Ищем второе ключевое слово только ниже первого
                    search_area = fitz.Rect(0, y1, page.rect.width, page.rect.height)
                    text_instances2 = page.search_for(KEYWORD6, clip=search_area)

                    if text_instances2:
                        y2 = text_instances2[0].y1  # Нижняя граница второго ключевого слова

                        # Закрашиваем область от первого до второго ключевого слова
                        rect_to_redact = fitz.Rect(0, y1, page.rect.width, y2-1)
                        page.draw_rect(rect_to_redact, color=(1, 1, 1), fill=1)

                # Переход к следующей странице
                page_number += 1

            # Сохраняем изменения
            doc.save(output_pdf, deflate=True)

    except Exception as e:
        print(f"Error in rzd with file {file_path}: {e}")
    
################################################################################################################

def find_keywords_in_pdf(file_path, output_pdf, keyword_actions):
    try:
        with fitz.open(file_path) as doc:
            print('Файл открыт')

            # Составляем регулярное выражение из всех ключевых слов
            keywords_pattern = "|".join(re.escape(keyword) for keyword in keyword_actions)
            compiled_pattern = re.compile(keywords_pattern, re.IGNORECASE)

            # Проверяем только первую страницу
            page = doc[0].get_text()
            match = compiled_pattern.search(page)
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
    try:
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
        print(f"Файл сохранён: {file_path}")

        output_pdf = f'temp_files/{file_name}'
        
        # Выполняем обработку
        find_keywords_in_pdf(file_path, output_pdf, keyword_actions)

        # Отправляем результат пользователю
        with open(output_pdf, 'rb') as f:
            await update.message.reply_document(f, caption="")

    except Exception as e:
        await update.message.reply_text(f"Произошла ошибка при обработке файла: {e}. Возможно файл не поддерживается")

    if os.path.exists('temp_files'):
    # Очистка содержимого папки
        for filename in os.listdir('temp_files'):
            file_path = os.path.join('temp_files', filename)
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)  # Удаляем файл
            except:
                break

################################################################################################################

# Основная функция для запуска бота
def main():
    # Загрузить переменные из .env файла
    load_dotenv('.env')

    # Получить значение токена
    token = os.getenv("TELEGRAM_BOT_TOKEN")

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