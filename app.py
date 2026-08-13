import re
from typing import Any

import streamlit as st
from agent import agent, exercise_lookup


# ---------------------------------------------------------
# Налаштування сторінки
# ---------------------------------------------------------

st.set_page_config(
    page_title="VitaCoach AI",
    page_icon="💪",
    layout="centered",
)

st.title("💪 VitaCoach AI")

st.subheader(
    "Персональний AI-помічник для фітнесу "
    "та здорового способу життя"
)

st.caption(
    "Допомагає розрахувати основні показники, "
    "підібрати вправи та враховує дані вашого профілю."
)

left_column, right_column = st.columns(2)

with left_column:
    st.markdown(
        """
        **Можливості**

        - 🧮 Розрахунок ІМТ
        - 🔥 Добова потреба в калоріях
        - 💪 Пошук вправ
        - 👤 Персональний профіль
        """
    )

with right_column:
    st.markdown(
        """
        **Приклади запитів**

        - Розрахуй мій ІМТ
        - Скільки калорій мені потрібно?
        - Покажи вправи на ноги вдома
        - Врахуй мою мету — схуднення
        """
    )


# ---------------------------------------------------------
# Початковий стан застосунку
# ---------------------------------------------------------

EMPTY_PROFILE = {
    "gender": None,
    "age": None,
    "weight": None,
    "height": None,
    "activity": None,
    "goal": None,
}

EXIT_PHRASES = {
    "дякую",
    "дякую!",
    "до побачення",
    "це все",
    "більше немає",
    "нічого більше",
    "достатньо",
}

if "messages" not in st.session_state:
    st.session_state.messages = []

if "profile" not in st.session_state:
    st.session_state.profile = EMPTY_PROFILE.copy()


# ---------------------------------------------------------
# Допоміжні функції
# ---------------------------------------------------------

def normalize_number(value: str) -> float:
    """Перетворює число з комою або крапкою у float."""

    return float(value.replace(",", "."))


def format_number(value: Any) -> str:
    """Форматує число без зайвого .0."""

    if isinstance(value, float) and value.is_integer():
        return str(int(value))

    return str(value)


def find_first_valid_number(
    text: str,
    patterns: list[str],
    minimum: float,
    maximum: float,
) -> float | None:
    """
    Шукає перше число, яке відповідає одному із шаблонів
    і входить у дозволений діапазон.
    """

    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)

        if not match:
            continue

        value = normalize_number(match.group(1))

        if minimum <= value <= maximum:
            return value

    return None


# ---------------------------------------------------------
# Визначення статі
# ---------------------------------------------------------

def extract_gender(text: str) -> str | None:
    """Визначає стать із повідомлення користувача."""

    female_patterns = [
        r"\bжінк\w*",
        r"\bдівчин\w*",
        r"\bжіноч\w*",
        r"\bfemale\b",
    ]

    male_patterns = [
        r"\bчоловік\w*",
        r"\bхлоп\w*",
        r"\bчоловіч\w*",
        r"\bmale\b",
    ]

    if any(re.search(pattern, text) for pattern in female_patterns):
        return "жінка"

    if any(re.search(pattern, text) for pattern in male_patterns):
        return "чоловік"

    return None


# ---------------------------------------------------------
# Визначення ваги
# ---------------------------------------------------------

def extract_weight(text: str) -> float | None:
    """
    Визначає вагу.

    Розпізнає, наприклад:
    - вага 65 кг
    - моя вага становить 65 кг
    - важу приблизно 65 кг
    - 65 кг
    """

    patterns = [
        r"\b(?:моя\s+)?ваг\w*\D{0,30}(\d+(?:[.,]\d+)?)\s*(?:кг)?\b",
        r"\bважу\D{0,30}(\d+(?:[.,]\d+)?)\s*(?:кг)?\b",
        r"\b(\d+(?:[.,]\d+)?)\s*кг\b",
    ]

    return find_first_valid_number(
        text=text,
        patterns=patterns,
        minimum=20,
        maximum=300,
    )


# ---------------------------------------------------------
# Визначення зросту
# ---------------------------------------------------------

def extract_height(text: str) -> float | None:
    """Визначає зріст у сантиметрах, зокрема формати «метр 68» та «1,68 м»."""

    meter_words = re.search(
        r"\b(?:зріст\D{0,20})?метр\D{0,10}(\d{1,2})\b",
        text,
    )
    if meter_words:
        height_cm = 100 + int(meter_words.group(1))
        if 100 <= height_cm <= 250:
            return float(height_cm)

    meters = re.search(
        r"\b(?:зріст\D{0,20})?(1[.,]\d{1,2})\s*м\b",
        text,
    )
    if meters:
        height_cm = normalize_number(meters.group(1)) * 100
        if 100 <= height_cm <= 250:
            return height_cm

    patterns = [
        r"\b(?:мій\s+)?зріст\D{0,30}(\d+(?:[.,]\d+)?)\s*(?:см)?\b",
        r"\bростом\D{0,30}(\d+(?:[.,]\d+)?)\s*(?:см)?\b",
        r"\b(\d+(?:[.,]\d+)?)\s*см\b",
    ]

    return find_first_valid_number(
        text=text,
        patterns=patterns,
        minimum=100,
        maximum=250,
    )


# ---------------------------------------------------------
# Визначення віку
# ---------------------------------------------------------

def extract_age(text: str) -> int | None:
    """
    Визначає вік.

    Розпізнає, наприклад:
    - мені 35 років
    - вік 35
    - 35 років
    """

    patterns = [
        r"\bмені\D{0,10}(\d{1,3})\s*(?:років|роки|рік)\b",
        r"\bвік\D{0,10}(\d{1,3})\b",
        r"\b(\d{1,3})\s*(?:років|роки|рік)\b",
    ]

    value = find_first_valid_number(
        text=text,
        patterns=patterns,
        minimum=14,
        maximum=100,
    )

    if value is None:
        return None

    return int(value)


# ---------------------------------------------------------
# Визначення рівня активності
# ---------------------------------------------------------

def extract_activity(text: str) -> str | None:
    """Визначає рівень фізичної активності."""

    activity_patterns = {
    "мінімальна": [
        r"\bмінімальн\w*",
        r"\bмалорухлив\w*",
        r"\bмало\s+руха\w*",
        r"\bмайже\s+не\s+руха\w*",
        r"\bсидяч\w*",
        r"\bсидж\w*",
        r"\bцілий\s+день\s+сидж\w*",
        r"\bвесь\s+(?:день|час)\s+сидж\w*",
        r"\bпостійно\s+сидж\w*",
        r"\bне\s+тренуюс\w*",
        r"\bне\s+займаюс\w*",
        r"\bбез\s+тренуван\w*",
    ],
    "легка": [
        r"\bлегк\w*",
        r"1\s*[-–—]\s*3\s+раз",
        r"тренуюс\w*\s+(?:один|два|1|2)\s+раз",
        r"займаюс\w*\s+(?:один|два|1|2)\s+раз",
    ],
    "помірна": [
        r"\bпомірн\w*",
        r"3\s*[-–—]\s*5\s+раз",
        r"тренуюс\w*\s+(?:три|чотири|п'ять|3|4|5)\s+раз",
        r"займаюс\w*\s+(?:три|чотири|п'ять|3|4|5)\s+раз",
    ],
    "висока": [
        r"\bвисок\w*",
        r"\bактивн\w*",
        r"6\s*[-–—]\s*7\s+раз",
        r"тренуюс\w*\s+(?:шість|сім|6|7)\s+раз",
        r"займаюс\w*\s+(?:шість|сім|6|7)\s+раз",
    ],
    "екстремальна": [
        r"\bекстремальн\w*",
        r"\bдуже\s+висок\w*",
        r"\bпрофесійн\w*\s+спорт",
        r"\bдвічі\s+на\s+день",
    ],
}

    for activity, patterns in activity_patterns.items():
        if any(re.search(pattern, text) for pattern in patterns):
            return activity

    return None


# ---------------------------------------------------------
# Визначення мети
# ---------------------------------------------------------

def extract_goal(text: str) -> str | None:
    """
    Визначає мету користувача за частинами слів
    і регулярними виразами, а не лише за точними фразами.
    """

    goal_patterns = {
        "схуднення": [
            r"\bсхуд\w*",
            r"\bскин\w*\s+(?:ваг\w*|кілограм\w*)",
            r"\bзниз\w*\s+ваг\w*",
            r"\bзменш\w*\s+(?:ваг\w*|об['’]?єм\w*|живіт\w*|талі\w*)",
            r"\bпозбут\w*\s+(?:ваг\w*|живот\w*|живіт\w*)",
        ],
        "зменшення об'єму талії": [
            r"\bтонш\w*\s+талі\w*",
            r"\bвужч\w*\s+талі\w*",
            r"\bструнк\w*\s+талі\w*",
            r"\bзменш\w*\s+талі\w*",
            r"\bзменш\w*\s+об['’]?єм\w*\s+талі\w*",
        ],
        "набір м'язової маси": [
            r"\bнакач\w*",
            r"\bпідкач\w*",
            r"\bнабрат\w*\s+(?:мас\w*|ваг\w*|м'яз\w*)",
            r"\bнабір\w*\s+(?:мас\w*|м'яз\w*)",
            r"\bзбільш\w*\s+м'яз\w*",
            r"\bнарост\w*\s+м'яз\w*",
            r"\bпідкач\w*",
        ],
        "підтримка ваги": [
            r"\bпідтрим\w*\s+ваг\w*",
            r"\bутрим\w*\s+ваг\w*",
            r"\bзберег\w*\s+(?:ваг\w*|форм\w*)",
            r"\bзалиш\w*\s+ваг\w*",
            r"\bне\s+хочу\s+(?:худнути|набирати)",
        ],
        "покращення фізичної форми": [
            r"\bпокращ\w*\s+(?:форм\w*|витривал\w*|фізичн\w*)",
            r"\bбути\s+у\s+формі",
            r"\bстати\s+сильніш\w*",
            r"\bзміцн\w*\s+тіл\w*",
        ],
    }

    detected_goals = []

    for goal, patterns in goal_patterns.items():
        if any(re.search(pattern, text) for pattern in patterns):
            detected_goals.append(goal)

    if not detected_goals:
        return None

    # Якщо користувач хоче і схуднення, і тоншу талію,
    # зберігаємо об'єднану мету.
    if (
        "схуднення" in detected_goals
        and "зменшення об'єму талії" in detected_goals
    ):
        return "схуднення та зменшення об'єму талії"

    return detected_goals[0]


# ---------------------------------------------------------
# Оновлення профілю
# ---------------------------------------------------------
def update_profile_from_message(message: str) -> None:
    """Оновлює профіль локально, без додаткового виклику моделі."""

    text = message.lower().strip()
    profile = st.session_state.profile

    extracted_values = {
        "gender": extract_gender(text),
        "age": extract_age(text),
        "weight": extract_weight(text),
        "height": extract_height(text),
        "activity": extract_activity(text),
        "goal": extract_goal(text),
    }

    # Явно повідомлене нове значення оновлює попереднє.
    for field, value in extracted_values.items():
        if value is not None:
            profile[field] = value


# ---------------------------------------------------------
# Формування контексту профілю для агента
# ---------------------------------------------------------

def build_profile_context() -> str:
    """Формує текст із даними, які вже повідомив користувач."""

    profile = st.session_state.profile
    known_data = []

    if profile["gender"] is not None:
        known_data.append(f"- Стать: {profile['gender']}")

    if profile["age"] is not None:
        known_data.append(f"- Вік: {profile['age']} років")

    if profile["weight"] is not None:
        known_data.append(
            f"- Вага: {format_number(profile['weight'])} кг"
        )

    if profile["height"] is not None:
        known_data.append(
            f"- Зріст: {format_number(profile['height'])} см"
        )

    if profile["activity"] is not None:
        known_data.append(
            f"- Рівень активності: {profile['activity']}"
        )

    if profile["goal"] is not None:
        known_data.append(f"- Мета: {profile['goal']}")

    if not known_data:
        return (
            "Профіль користувача поки що не містить "
            "збережених параметрів."
        )

    return (
        "Відомі дані користувача, отримані з попередніх "
        "повідомлень:\n"
        + "\n".join(known_data)
        + "\n\nВикористовуй ці дані під час відповіді."
        + "\nНе перепитуй уже відомі параметри."
        + "\nЯкщо для розрахунку бракує обов'язкових даних, "
        "запитай лише відсутні параметри."
        + "\nПід час виклику інструменту передай йому всі потрібні "
        "збережені параметри разом із поточним запитом."
    )

def is_exercise_request(text: str) -> bool:
    """Визначає, чи користувач просить конкретні вправи."""

    text = text.lower()

    exercise_patterns = [
        r"\bвправ\w*",
        r"\bтренуван\w*",
        r"\bукріп\w*",
        r"\bзміцн\w*",
        r"\bпідкач\w*",
        r"\bкачат\w*",
    ]

    muscle_patterns = [
        r"\bгруд\w*",
        r"\bспин\w*",
        r"\b(?:ног|ніг)\w*",
        r"\b(?:прес|живіт|живот)\w*",
        r"\bсідниц\w*",
        r"\bши\w*",
    ]

    has_exercise_intent = any(
        re.search(pattern, text)
        for pattern in exercise_patterns
    )

    has_muscle_group = any(
        re.search(pattern, text)
        for pattern in muscle_patterns
    )

    return has_exercise_intent and has_muscle_group

# ---------------------------------------------------------
# Бічна панель
# ---------------------------------------------------------

with st.sidebar:
    st.header("👤 Профіль користувача")

    profile = st.session_state.profile

    st.write(
        f"**Стать:** {profile['gender'] or 'не вказано'}"
    )

    age_text = (
        f"{profile['age']} років"
        if profile["age"] is not None
        else "не вказано"
    )
    st.write(f"**Вік:** {age_text}")

    weight_text = (
        f"{format_number(profile['weight'])} кг"
        if profile["weight"] is not None
        else "не вказано"
    )
    st.write(f"**Вага:** {weight_text}")

    height_text = (
        f"{format_number(profile['height'])} см"
        if profile["height"] is not None
        else "не вказано"
    )
    st.write(f"**Зріст:** {height_text}")

    st.write(
        f"**Активність:** "
        f"{profile['activity'] or 'не вказано'}"
    )

    st.write(
        f"**Мета:** {profile['goal'] or 'не вказано'}"
    )

    st.divider()


    st.info(
    "💡 Щоб завершити розмову, напишіть: "
    "«дякую», «до побачення» або «це все»."
    )

    if st.button(
        "🗑️ Очистити чат і профіль",
        use_container_width=True,
    ):
        st.session_state.messages = []
        st.session_state.profile = EMPTY_PROFILE.copy()
        st.rerun()


# ---------------------------------------------------------
# Відображення історії повідомлень
# ---------------------------------------------------------

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# ---------------------------------------------------------
# Обробка нового повідомлення
# ---------------------------------------------------------

if prompt := st.chat_input("Поставте запитання..."):

    normalized_prompt = prompt.lower().strip()

    if normalized_prompt in EXIT_PHRASES:
        st.session_state.messages.append(
            {
                "role": "user",
                "content": prompt,
            }
        )

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": (
                    "😊 Дякую за розмову! Рада була допомогти. "
                    "Повертайтеся, якщо виникнуть нові питання."
                ),
            }
        )

        st.rerun()

    # Оновлюємо профіль із нового повідомлення
    update_profile_from_message(prompt)

    # Зберігаємо повідомлення користувача
    user_message = {
        "role": "user",
        "content": prompt,
    }

    st.session_state.messages.append(user_message)

    with st.chat_message("user"):
        st.markdown(prompt)

    # Створюємо окрему історію для агента.
    # Технічний контекст профілю не показується користувачу.
    agent_messages = [
        {
            "role": message["role"],
            "content": message["content"],
        }
        for message in st.session_state.messages
    ]

    profile_context = build_profile_context()

    agent_messages[-1]["content"] = (
        f"{prompt}\n\n"
        f"---\n"
        f"Службовий контекст профілю:\n"
        f"{profile_context}"
    )

    with st.chat_message("assistant"):
        with st.spinner("Думаю..."):
            try:
                if is_exercise_request(prompt):
                    answer = exercise_lookup.invoke(prompt)
                else:
                    response = agent.invoke(
                        {
                            "messages": agent_messages
                        }
                    )

                    answer = response["messages"][-1].content

                if not answer:
                    answer = (
                        "Не вдалося сформувати відповідь. "
                        "Спробуйте переформулювати запит."
                    )

            except Exception as error:
                answer = (
                    "Не вдалося отримати відповідь від агента. "
                    "Будь ласка, спробуйте ще раз.\n\n"
                    f"Технічна інформація: `{error}`"
                )

        st.markdown(answer)

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": answer,
        }
    )


# ---------------------------------------------------------
# Дисклеймер
# ---------------------------------------------------------

st.divider()

st.caption(
    "⚠️ VitaCoach AI є навчальним застосунком і не замінює "
    "консультацію лікаря, дієтолога або сертифікованого тренера."
)