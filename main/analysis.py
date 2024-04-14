import easyocr
import re
import os
from ultralytics import YOLO
from transliterate import translit

results = []


def levenshtein_distance(s1, s2):
    #Вычисляем расстояние Левенштейна между двумя строками
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)

    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))

            # Проверяем наличие возможности провести транспозицию символов
            if i > 0 and j > 0 and s1[i] == s2[j - 1] and s1[i - 1] == s2[j]:
                current_row[-1] = min(current_row[-1], previous_row[j - 1] + 1)

        previous_row = current_row

    return previous_row[-1]

def correct_spelling(input_string, dictionary, max_distance=2):
    #Исправляем опечатки в строке на основе предоставленного словаря
    words = input_string.split()
    corrected_words = []
    for word in words:
        min_distance = float('inf')
        corrected_word = word
        for dict_word in dictionary:
            distance = levenshtein_distance(word, dict_word)
            if distance < min_distance and distance <= max_distance:
                min_distance = distance
                corrected_word = dict_word
        corrected_words.append(corrected_word)
    return ' '.join(corrected_words)


def text_recognition(file):
    try:
        reader = easyocr.Reader((["ru", "en"]), recog_network='best_accuracy')
    except:
        reader = easyocr.Reader((["ru", "en"]))
    result = reader.readtext(file)
    full_str = ""
    for(bbox, text, procent) in result:
        full_str += text
        full_str += " "
    full_str = replace_commas_with_dots(full_str)
    full_str = full_str.lower()
    dictionary = {'энергетическая', 'ценность', 'белки', 'жиры', 'углеводы', 'сахар', 'сахароза', 'натрий', 'калий',
                  'фрукты', 'месяцев', 'лет', 'года', 'пальмовое', 'масло', 'каша', 'пюре', 'печенье', 'молочный',
                  'йогурт', 'агуша', 'nestle', 'heinz', 'придонья', 'малютка', 'фрутоняня', 'semper', 'nutrilon', 'няня',
                  'смесь', 'батончик', 'творог', 'ароматизатор', 'краситель', 'эмульгатор', 'витамин', 'подсластитель',
                  'консервант', 'загуститель', 'омега3', 'бифидобактерии', 'напиток', 'малышам', 'бабушкино', 'лукошко',
                  'мука', 'года', 'сахара', 'гмо', 'добавления', 'без', 'низким', 'содержанием', 'содержит', 'полезно',
                  'улучшает', 'идеально'}
    full_str = correct_spelling(full_str, dictionary)
    find_nutritional_info(full_str)
    return full_str


def check_words(txt, keywords):
    for keyword in keywords:
        index = txt.find(keyword)
        matches = []
        if index != -1:
            substr = txt[index + len(keyword):]
            matches = re.search(r'\b\d+(\.\d+)?\b', substr)
        if not matches:
            value = "нет данных"
        else:
            value = matches[0]
    return value


def check_match(txt, keywords, match):
    if not match:
        val = check_words(txt, keywords)
    else:
        val = match[0]
    return val


def replace_commas_with_dots(text):
    pattern = r'(\d+),(\d+)'
    replaced_text = re.sub(pattern, r'\1.\2', text)
    return replaced_text


def find_substance_info(text, keywords):
    found_words = []
    for word in text.split():
        if word.lower() in keywords:
            found_words.append(word)
    return found_words


def find_phrases_in_text(dictionary, text):
    found_phrases = []
    for phrase in dictionary:
        if phrase in text:
            if phrase == "мука":
                found_phrases.append("продукция с содержанием муки")
            else:
                found_phrases.append(phrase)
    return found_phrases


def find_nutritional_info(text):
    keywords_protein = ['белки', 'белки:', 'белки;', 'белок', 'белок:', 'белок;', 'белка', 'белка:', 'белка;', 'белок,',
                'белки,', 'белка,', 'белок,г', 'белки,г', 'белка,г']
    keywords_fats = ['жир', 'жир:', 'жир;', 'жир,', 'жир,г', 'жира', 'жира:', 'жира;', 'жира,', 'жира,г', 'жиры',
                     'жиры:', 'жиры;', 'жиры,', 'жиры,г']
    keywords_carbohydrates = ['углевод', 'углевод:', 'углевод;', 'углевод,', 'углевод,г', 'углеводы', 'углеводы:', 'углеводы;', 'углеводы,', 'углеводы,г', 'углеводов',
                     'углеводов:', 'углеводов;', 'углеводов,', 'углеводов,г']
    keywords_ka = ['калий', 'калий:', 'калий;', 'калий,', 'калий,мг', 'калия', 'калия:', 'калия;', 'калия,', 'калия,мг']
    keywords_na = ['натрий', 'натрий:', 'натрий;', 'натрий,', 'натрий,мг', 'натрия', 'натрия:', 'натрия;', 'натрия,', 'натрия,мг']
    keywords_energy = ['энергетическая', 'энергетическая:', 'энергетическая;', 'энергетическая,', 'энергетическая,ккал', 'энергетическая,ккал/кдж', 'энергетическая,кдж/ккал', 'энергетическая,дж', 'энергетическая,кдж',
                       'энергетический', 'энергетический:', 'энергетический;', 'энергетический,', 'энергетический,ккал', 'энергетический,ккал/кдж', 'энергетический,кдж/ккал', 'энергетический,дж', 'энергетический,кдж',
                       'энергетической', 'энергетической:', 'энергетической;', 'энергетической,', 'энергетической,ккал', 'энергетической,ккал/кдж', 'энергетической,кдж/ккал', 'энергетической,дж', 'энергетической,кдж']
    keywords_sugar = ['сахар', 'сахар:', 'сахар;', 'сахар,', 'сахар,г', 'сахара', 'сахара:', 'сахара;', 'сахара,', 'сахара,г',
                      'сахароза', 'сахароза:', 'сахароза;', 'сахароза,', 'сахароза,г', 'сахарозы', 'сахарозы:', 'сахарозы;', 'сахарозы,', 'сахарозы,г']

    pattern_energy = r'(?<!\d)(?<!\d\s)(\d+(?:\.\d+)?)\s?(?:кДж|Дж|кал|ккал)(?!\d)'
    pattern_proteins = r'(?:(?:белки|белки:|белки;|белок|белок:|белок;|белка|белка:|белка;)\s*(:?[\d.]+))'
    pattern_fats = r'(?:жиры|жиры,г|жиры;|жиры,|жиров,г|жиров;|жиров,|жиров|жир,г|жир;|жир,|жир):?\s?(\d+(?:\.\d+)?)'
    pattern_carbohydrates = r'(?:углеводы|углеводы,г|углеводы;|углеводы,|углеводов,г|углеводов;|углеводов,|углеводов):?\s?(\d+(?:\.\d+)?)'
    pattern_kaliy = r'(?:калий|калий,мг|калий;|калий,|калия,мг|калия;|калия,|калия):?\s?(\d+(?:\.\d+)?)'
    pattern_na = r'(?:натрий|натрий,мг|натрий;|натрий,|натрия,мг|натрия;|натрия,|натрия):?\s?(\d+(?:\.\d+)?)'
    pattern_sugar = r'(?:сахар|сахар,г|сахар;|сахар,|сахара,г|сахара;|сахара,|сахара|сахароза,г|сахароза;|сахароза,|сахароза):?\s?(\d+(?:\.\d+)?)'
    pattern_age = r'(?:\b(\d+)\b\s+(месяцев|лет|год|года)\b|\b(месяцев|лет|год|года)\s+\b(\d+)\b)'

    matches_energy = re.findall(pattern_energy, text, re.IGNORECASE)
    matches_proteins = re.findall(pattern_proteins, text, re.IGNORECASE)
    matches_fats = re.findall(pattern_fats, text, re.IGNORECASE)
    matches_carbohydrates = re.findall(pattern_carbohydrates, text, re.IGNORECASE)
    matches_kaliy = re.findall(pattern_kaliy, text, re.IGNORECASE)
    matches_na = re.findall(pattern_na, text, re.IGNORECASE)
    matches_sugar = re.findall(pattern_sugar, text, re.IGNORECASE)
    matches_age = re.findall(pattern_age, text, re.IGNORECASE)

    keywords_bad = ["ароматизатор", "краситель", "эмульгатор", "подсластитель", "консервант", "пальмовое", "загуститель"]
    keywords_good = ["витамин", "омега3", "бифидобактерии"]
    keywords_type = ["йогурт", "пюре", "пюре фруктовое", "фруктовое пюре", "пюре овощное", "овощное пюре", "каша", "смесь", "печенье", "батончик", "творог", "молочный", "напиток", "мука"]
    keywords_brand = ["агуша", "nestle", "heinz", "сады придонья", "малютка", "фрутоняня", "semper", "nutrilon", "няня", "малышам", "бабушкино лукошко"]
    keywords_marketing = ["без содержания сахар", "без гмо", "без добавления", "с низким содержанием", "содержит",
                          "полезно", "улучшает", 'идеально']
    bad = find_substance_info(text, keywords_bad)
    bad = list(set(bad))
    good = find_substance_info(text, keywords_good)
    good = list(set(good))
    types = find_phrases_in_text(keywords_type, text)
    brand = find_phrases_in_text(keywords_brand, text)
    market = find_phrases_in_text(keywords_marketing, text)
    market = list(set(market))
    bad_sub = ""
    good_sub = ""
    marketing = ""
    recom = ""
    for i, word in enumerate(bad):
        if i == len(bad)-1:
            bad_sub += word
            bad_sub += "."
        else:
            bad_sub += word
            bad_sub += ", "

    for t, word1 in enumerate(good):
        if t == len(good)-1:
            good_sub += word1
            good_sub += "."
        else:
            good_sub += word1
            good_sub += ", "

    if not market:
        marketing = "Недопустимые заявления производителя: нет данных"
    else:
        marketing = "Недопустимые заявления производителя: "
        for n, word2 in enumerate(market):
            if n == len(market) - 1:
                marketing += word2
                marketing += "."
            else:
                marketing += word2
                marketing += ", "

    if not matches_age:
        age = "нет данных"
    else:
        age = str(matches_age[0])
    types = list(set(types))
    brand = list(set(brand))
    if not types:
        type_pr = "нет данных"
    else:
        type_pr = str(types[0])
    if not brand:
        brand_pr = "нет данных"
    else:
        brand_pr = str(brand[0])

    if bad_sub:
        recom = "Рекомендации: продукт нежелателен к употреблению по причине содержания потенциально вредных для здоровья веществ"
    else:
        recom = "Рекомендации: нет данных"

    results.append("Категория продукта: " + type_pr)
    results.append("Производитель: " + brand_pr)
    results.append("Рекомендуемый возраст: " + age)
    results.append("Потенциально вредные вещества в составе: " + bad_sub)
    results.append("Потенциально полезные вещества в составе: " + good_sub)
    results.append(marketing)
    results.append("Белки: " + check_no_data(check_match(text, keywords_protein, matches_proteins), " г"))
    results.append("Жиры: " + check_no_data(check_match(text, keywords_fats, matches_fats), " г"))
    results.append("Углеводы: " + check_no_data(check_match(text, keywords_carbohydrates, matches_carbohydrates), " г"))
    results.append("Энергетическая ценность: " + check_no_data(check_match(text, keywords_energy, matches_energy), " кДж (ккал)"))
    results.append("Калий: " + check_no_data(check_match(text, keywords_ka, matches_kaliy), " мг"))
    results.append("Натрий: " + check_no_data(check_match(text, keywords_na, matches_na), " мг"))
    results.append("Сахар: " + check_no_data(check_match(text, keywords_sugar, matches_sugar), " г"))
    results.append(recom)
    results.append(" ")
    results.append(" ")


def check_no_data(txt, unit):
    if txt == "нет данных":
        return txt
    else:
        txt += unit
        return txt


def process_image(img_path):
    model = YOLO(f"detect_model/best.pt")
    results_yolo = model(img_path)  # return a list of Results objects

    for result in results_yolo:
        boxes = result.boxes  # Boxes object for bounding box outputs
        masks = result.masks  # Masks object for segmentation masks outputs
        keypoints = result.keypoints  # Keypoints object for pose outputs
        probs = result.probs  # Probs object for classification outputs
        result.save(filename='result.jpg', dir=f"uploads")  # save to disk
    return results_yolo


def handle_uploaded_file(f):
    global results
    results.clear()
    for file1 in f:
        russian_filename = file1.name
        english_filename = translit(russian_filename, 'ru', reversed=True)
        print(english_filename)
        with open(f"uploads/{english_filename}", "wb+") as destination:
            for chunk in file1.chunks():
                destination.write(chunk)
        #process_image(f"uploads/{file1.name}")
        print(text_recognition(f"uploads/{english_filename}"))
