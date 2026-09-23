import streamlit as st
from pathlib import Path
import sys

# Добавляем текущую папку в путь
sys.path.append(str(Path(__file__).parent))

from database import init_db, get_connection, IMAGES_DIR

# ====================== НАСТРОЙКА СТРАНИЦЫ ======================
st.set_page_config(
    page_title="Склад Учета",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Инициализация базы при первом запуске
init_db()

# ====================== СТИЛИ ======================
st.markdown("""
<style>
    /* Основной цвет */
    :root {
        --primary: #2e7d32;
    }
    
    /* Сайдбар */
    [data-testid="stSidebar"] {
        background-color: #f8faf8;
    }
    
    /* Кнопки */
    .stButton > button {
        border-radius: 8px;
    }
    
    /* Заголовки */
    h1, h2, h3 {
        color: #1b5e20;
    }
</style>
""", unsafe_allow_html=True)


# ====================== БОКОВОЕ МЕНЮ ======================
with st.sidebar:
    st.markdown("### 🏭 Склад Учета")
    st.caption("Система управления запасами")
    st.markdown("---")

    menu = st.radio(
        "Навигация",
        options=[
            "📊 Панель управления",
            "📦 Товары",
            "🚜 Машины / Механизмы",
            "📥 Поступления (Приход)",
            "📤 Расходы",
            "📋 Остатки",
            "📍 Места хранения",
            "📈 Отчёты",
            "⚙️ Настройки"
        ],
        label_visibility="collapsed"
    )

    st.markdown("---")
    st.caption("Версия 0.1 • Один общий доступ")


# ====================== СТРАНИЦЫ ======================

if menu == "📊 Панель управления":
    st.title("Панель управления")
    st.info("Здесь будет сводка по складу: общее количество позиций, последние движения и т.д.")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Товаров в справочнике", "—")
    with col2:
        st.metric("Всего позиций на складе", "—")
    with col3:
        st.metric("Приходов за месяц", "—")
    with col4:
        st.metric("Расходов за месяц", "—")

    st.markdown("---")
    st.subheader("Последние движения")
    st.write("Пока пусто. Появятся после первых операций.")


elif menu == "📦 Товары":
    st.title("Справочник товаров")
    
    tab1, tab2 = st.tabs(["📋 Список товаров", "➕ Добавить / Редактировать"])

    with tab1:
        st.subheader("Список товаров")
        
        # Поиск
        search = st.text_input("🔍 Поиск по артикулу, названию, назначению...", key="search_products")
        
        conn = get_connection()
        query = "SELECT * FROM products ORDER BY id DESC"
        products = conn.execute(query).fetchall()
        conn.close()

        if not products:
            st.info("Товаров пока нет. Добавьте первый товар во вкладке «Добавить / Редактировать».")
        else:
            for p in products:
                # Простой фильтр поиска
                if search:
                    search_lower = search.lower()
                    if not (search_lower in (p["article"] or "").lower() or
                            search_lower in (p["name"] or "").lower() or
                            search_lower in (p["purpose"] or "").lower() or
                            search_lower in (p["storage_place"] or "").lower()):
                        continue

                with st.container():
                    cols = st.columns([1, 4, 1])
                    
                    with cols[0]:
                        if p["photo_path"] and Path(p["photo_path"]).exists():
                            st.image(p["photo_path"], width=120)
                        else:
                            st.markdown("📷\n*нет фото*")
                    
                    with cols[1]:
                        st.markdown(f"**{p['article']}** — {p['name']}")
                        st.caption(f"Назначение: {p['purpose'] or '—'}  |  Ед.: {p['unit']}  |  Место: {p['storage_place'] or '—'}")
                        if p["notes"]:
                            st.caption(f"Примечание: {p['notes']}")
                        if p["category"]:
                            st.caption(f"Категория: {p['category']}")
                    
                    with cols[2]:
                        if st.button("✏️", key=f"edit_{p['id']}", help="Редактировать"):
                            st.session_state["edit_product_id"] = p["id"]
                            st.rerun()
                        if st.button("🗑️", key=f"del_{p['id']}", help="Удалить"):
                            st.session_state["delete_product_id"] = p["id"]
                    
                    st.markdown("---")

    with tab2:
        st.subheader("Добавить / Редактировать товар")

        # Если редактируем
        edit_id = st.session_state.get("edit_product_id")
        product_data = None
        if edit_id:
            conn = get_connection()
            product_data = conn.execute("SELECT * FROM products WHERE id = ?", (edit_id,)).fetchone()
            conn.close()
            st.info(f"Редактирование товара ID: {edit_id}")

        with st.form("product_form", clear_on_submit=True):
            col_left, col_right = st.columns([1, 1.5])

            with col_left:
                st.markdown("#### Фото товара")
                photo_file = st.file_uploader(
                    "Загрузить фото (JPG, PNG)",
                    type=["jpg", "jpeg", "png"],
                    key="photo_uploader"
                )
                if product_data and product_data["photo_path"] and Path(product_data["photo_path"]).exists():
                    st.image(product_data["photo_path"], width=250)
                    st.caption("Текущее фото")

            with col_right:
                article = st.text_input("Артикул *", value=product_data["article"] if product_data else "")
                name = st.text_input("Наименование товара *", value=product_data["name"] if product_data else "")
                purpose = st.text_input("Для чего предназначен", value=product_data["purpose"] if product_data else "",
                                        placeholder="Например: на трактор МТЗ-82, на сеялку и т.д.")
                
                col_u, col_s = st.columns(2)
                with col_u:
                    unit = st.selectbox(
                        "Единица измерения *",
                        options=["шт", "кг", "л", "м", "м²", "комплект", "упаковка"],
                        index=0 if not product_data else ["шт", "кг", "л", "м", "м²", "комплект", "упаковка"].index(product_data["unit"]) if product_data["unit"] in ["шт", "кг", "л", "м", "м²", "комплект", "упаковка"] else 0
                    )
                with col_s:
                    storage_place = st.text_input("Место хранения", value=product_data["storage_place"] if product_data else "",
                                                  placeholder="Полка №1 / Коробка №23")

                category = st.selectbox(
                    "Категория",
                    options=["", "Запчасти", "Семена", "Удобрения", "ГСМ", "Инструмент", "Расходники", "Прочее"],
                    index=0
                )
                notes = st.text_area("Примечания", value=product_data["notes"] if product_data else "")

            submitted = st.form_submit_button("💾 Сохранить товар", use_container_width=True, type="primary")

            if submitted:
                if not article or not name:
                    st.error("Артикул и Наименование обязательны для заполнения!")
                else:
                    # Сохраняем фото
                    photo_path = product_data["photo_path"] if product_data else None
                    if photo_file:
                        ext = photo_file.name.split(".")[-1]
                        photo_filename = f"{article.replace('/', '_')}_{photo_file.name}"
                        photo_path = str(IMAGES_DIR / photo_filename)
                        with open(photo_path, "wb") as f:
                            f.write(photo_file.getbuffer())

                    conn = get_connection()
                    try:
                        if edit_id:
                            conn.execute("""
                                UPDATE products SET
                                    article = ?, name = ?, purpose = ?, unit = ?,
                                    storage_place = ?, notes = ?, category = ?, photo_path = ?,
                                    updated_at = CURRENT_TIMESTAMP
                                WHERE id = ?
                            """, (article, name, purpose, unit, storage_place, notes, category or None, photo_path, edit_id))
                            st.success("Товар успешно обновлён!")
                            if "edit_product_id" in st.session_state:
                                del st.session_state["edit_product_id"]
                        else:
                            conn.execute("""
                                INSERT INTO products (article, name, purpose, unit, storage_place, notes, category, photo_path)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                            """, (article, name, purpose, unit, storage_place, notes, category or None, photo_path))
                            st.success("Товар успешно добавлен!")
                        conn.commit()
                    except Exception as e:
                        st.error(f"Ошибка: {e}")
                    finally:
                        conn.close()
                    st.rerun()


elif menu == "🚜 Машины / Механизмы":
    st.title("Справочник машин и механизмов")
    
    tab1, tab2 = st.tabs(["📋 Список", "➕ Добавить"])

    with tab1:
        search_m = st.text_input("🔍 Поиск машины...", key="search_machines")
        conn = get_connection()
        machines = conn.execute("SELECT * FROM machines ORDER BY name").fetchall()
        conn.close()

        if not machines:
            st.info("Машин пока нет. Добавьте первую.")
        else:
            for m in machines:
                if search_m and search_m.lower() not in (m["name"] or "").lower() and search_m.lower() not in (m["inventory_number"] or "").lower():
                    continue
                cols = st.columns([4, 1])
                with cols[0]:
                    st.markdown(f"**{m['name']}**")
                    if m["inventory_number"]:
                        st.caption(f"Инв. №: {m['inventory_number']}")
                    if m["notes"]:
                        st.caption(m["notes"])
                with cols[1]:
                    if st.button("🗑️", key=f"del_m_{m['id']}"):
                        conn = get_connection()
                        conn.execute("DELETE FROM machines WHERE id = ?", (m["id"],))
                        conn.commit()
                        conn.close()
                        st.rerun()
                st.markdown("---")

    with tab2:
        with st.form("machine_form", clear_on_submit=True):
            name = st.text_input("Название машины / механизма *")
            inv_number = st.text_input("Инвентарный номер")
            notes = st.text_area("Примечания")
            if st.form_submit_button("💾 Сохранить", type="primary"):
                if name:
                    conn = get_connection()
                    conn.execute(
                        "INSERT INTO machines (name, inventory_number, notes) VALUES (?, ?, ?)",
                        (name, inv_number, notes)
                    )
                    conn.commit()
                    conn.close()
                    st.success("Машина добавлена!")
                    st.rerun()
                else:
                    st.error("Укажите название")


elif menu == "📥 Поступления (Приход)":
    st.title("Поступление товара (Приход)")
    st.info("Раздел в разработке. Здесь будет форма прихода по счёт-фактуре / накладной с ценами и НДС.")


elif menu == "📤 Расходы":
    st.title("Расход товара")
    st.info("Раздел в разработке. Здесь будет списание на машину или место.")


elif menu == "📋 Остатки":
    st.title("Остатки на складе")
    st.info("Раздел в разработке. Здесь будут текущие остатки с фото.")


elif menu == "📍 Места хранения":
    st.title("Места хранения")
    st.info("Можно будет вести отдельный справочник мест (полки, стеллажи, коробки).")


elif menu == "📈 Отчёты":
    st.title("Отчёты")
    st.info("Отчёты по остаткам и движению появятся позже.")


elif menu == "⚙️ Настройки":
    st.title("Настройки")
    st.write("Пока настроек нет.")
    st.markdown("---")
    st.caption("База данных: `sklad.db`")
    st.caption("Фото хранятся в папке `images/`")
