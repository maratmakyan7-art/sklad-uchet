import streamlit as st
from pathlib import Path
import sys
from datetime import datetime

sys.path.append(str(Path(__file__).parent))
from database import init_db, get_connection, IMAGES_DIR

# ====================== НАСТРОЙКА ======================
st.set_page_config(
    page_title="Склад Учета",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

init_db()

# ====================== СОВРЕМЕННЫЕ СТИЛИ ======================
st.markdown("""
<style>
    /* Общий фон */
    .stApp {
        background-color: #f5f7fa;
    }
    
    /* Сайдбар */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1b5e20 0%, #2e7d32 100%);
    }
    [data-testid="stSidebar"] * {
        color: white !important;
    }
    [data-testid="stSidebar"] .stRadio label {
        padding: 8px 12px;
        border-radius: 8px;
        margin-bottom: 2px;
    }
    [data-testid="stSidebar"] .stRadio label:hover {
        background-color: rgba(255,255,255,0.1);
    }
    
    /* Карточки */
    .product-card {
        background: white;
        border-radius: 16px;
        padding: 20px;
        margin-bottom: 16px;
        box-shadow: 0 2px 12px rgba(0,0,0,0.06);
        border: 1px solid #e8ecef;
        transition: all 0.2s ease;
    }
    .product-card:hover {
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        transform: translateY(-2px);
    }
    
    /* Заголовки */
    h1 {
        color: #1a1a1a !important;
        font-weight: 700 !important;
        letter-spacing: -0.5px;
    }
    h2, h3 {
        color: #2d3748 !important;
    }
    
    /* Метрики */
    [data-testid="stMetric"] {
        background: white;
        padding: 16px 20px;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    }
    
    /* Кнопки */
    .stButton > button {
        border-radius: 10px !important;
        font-weight: 500 !important;
        transition: all 0.2s;
    }
    
    /* Поля ввода */
    .stTextInput > div > div > input,
    .stSelectbox > div > div,
    .stTextArea > div > div > textarea {
        border-radius: 10px !important;
    }
    
    /* Табы */
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px 8px 0 0;
        font-weight: 500;
    }
</style>
""", unsafe_allow_html=True)


# ====================== БОКОВОЕ МЕНЮ ======================
with st.sidebar:
    st.markdown("## 🏭 Склад Учета")
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
    st.caption("Версия 0.2 • Один общий доступ")


# ====================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ======================
def get_stock(product_id):
    """Считает текущий остаток товара"""
    conn = get_connection()
    row = conn.execute("""
        SELECT 
            COALESCE(SUM(CASE WHEN movement_type = 'приход' THEN quantity ELSE 0 END), 0) -
            COALESCE(SUM(CASE WHEN movement_type = 'расход' THEN quantity ELSE 0 END), 0) as stock
        FROM movements 
        WHERE product_id = ?
    """, (product_id,)).fetchone()
    conn.close()
    return row["stock"] if row else 0


# ====================== СТРАНИЦЫ ======================

if menu == "📊 Панель управления":
    st.title("Панель управления")
    
    conn = get_connection()
    total_products = conn.execute("SELECT COUNT(*) as cnt FROM products").fetchone()["cnt"]
    total_machines = conn.execute("SELECT COUNT(*) as cnt FROM machines").fetchone()["cnt"]
    total_incomings = conn.execute("SELECT COUNT(*) as cnt FROM movements WHERE movement_type = 'приход'").fetchone()["cnt"]
    total_outgoings = conn.execute("SELECT COUNT(*) as cnt FROM movements WHERE movement_type = 'расход'").fetchone()["cnt"]
    conn.close()

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Товаров в справочнике", total_products)
    with col2:
        st.metric("Машин / механизмов", total_machines)
    with col3:
        st.metric("Приходов", total_incomings)
    with col4:
        st.metric("Расходов", total_outgoings)

    st.markdown("---")
    st.subheader("Последние движения")
    
    conn = get_connection()
    recent = conn.execute("""
        SELECT m.*, p.article, p.name 
        FROM movements m
        JOIN products p ON m.product_id = p.id
        ORDER BY m.created_at DESC
        LIMIT 10
    """).fetchall()
    conn.close()

    if not recent:
        st.info("Пока нет движений. Они появятся после первых приходов и расходов.")
    else:
        for r in recent:
            icon = "📥" if r["movement_type"] == "приход" else "📤"
            st.markdown(f"""
            <div class="product-card">
                {icon} <b>{r['article']}</b> — {r['name']}<br>
                <small>{r['movement_type'].title()} • {r['quantity']} • {r['movement_date'][:16] if r['movement_date'] else ''}</small>
            </div>
            """, unsafe_allow_html=True)


elif menu == "📦 Товары":
    st.title("Справочник товаров")
    
    tab1, tab2 = st.tabs(["📋 Список товаров", "➕ Добавить / Редактировать"])

    with tab1:
        search = st.text_input("🔍 Поиск по артикулу, названию, назначению, месту...", 
                               placeholder="Начните вводить...")

        conn = get_connection()
        products = conn.execute("SELECT * FROM products ORDER BY id DESC").fetchall()
        conn.close()

        if not products:
            st.info("Товаров пока нет. Добавьте первый товар во вкладке «Добавить / Редактировать».")
        else:
            shown = 0
            for p in products:
                if search:
                    s = search.lower()
                    if not any(s in str(p[field] or "").lower() for field in 
                               ["article", "name", "purpose", "storage_place", "category", "notes"]):
                        continue
                
                shown += 1
                stock = get_stock(p["id"])
                
                with st.container():
                    cols = st.columns([1.2, 4.5, 1.3])
                    
                    with cols[0]:
                        if p["photo_path"] and Path(p["photo_path"]).exists():
                            st.image(p["photo_path"], use_container_width=True)
                        else:
                            st.markdown("""
                            <div style="background:#f0f0f0; border-radius:12px; height:120px; 
                                        display:flex; align-items:center; justify-content:center; color:#999;">
                                📷 нет фото
                            </div>
                            """, unsafe_allow_html=True)
                    
                    with cols[1]:
                        st.markdown(f"### {p['article']} — {p['name']}")
                        
                        info_parts = []
                        if p["purpose"]:
                            info_parts.append(f"🔧 {p['purpose']}")
                        info_parts.append(f"📐 {p['unit']}")
                        if p["storage_place"]:
                            info_parts.append(f"📍 {p['storage_place']}")
                        if p["category"]:
                            info_parts.append(f"🏷 {p['category']}")
                        
                        st.caption("  •  ".join(info_parts))
                        
                        if p["notes"]:
                            st.caption(f"💬 {p['notes']}")
                        
                        color = "#2e7d32" if stock > 0 else "#c62828"
                        st.markdown(f"<span style='color:{color}; font-weight:600; font-size:1.1em;'>Остаток: {stock} {p['unit']}</span>", 
                                    unsafe_allow_html=True)
                    
                    with cols[2]:
                        st.write("")
                        if st.button("✏️ Изменить", key=f"edit_{p['id']}", use_container_width=True):
                            st.session_state["edit_product_id"] = p["id"]
                            st.rerun()
                        if st.button("🗑️ Удалить", key=f"del_{p['id']}", use_container_width=True):
                            conn = get_connection()
                            conn.execute("DELETE FROM products WHERE id = ?", (p["id"],))
                            conn.commit()
                            conn.close()
                            st.rerun()
                    
                    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

            if shown == 0 and search:
                st.warning("Ничего не найдено по вашему запросу.")

    with tab2:
        st.subheader("Добавить / Редактировать товар")

        edit_id = st.session_state.get("edit_product_id")
        product_data = None
        if edit_id:
            conn = get_connection()
            product_data = conn.execute("SELECT * FROM products WHERE id = ?", (edit_id,)).fetchone()
            conn.close()
            st.info(f"✏️ Редактирование товара: **{product_data['article']}**")
            if st.button("← Отменить редактирование"):
                del st.session_state["edit_product_id"]
                st.rerun()

        with st.form("product_form", clear_on_submit=not bool(edit_id)):
            col_left, col_right = st.columns([1, 1.6])

            with col_left:
                st.markdown("#### 📷 Фото товара")
                photo_file = st.file_uploader("Загрузить фото (JPG, PNG)", type=["jpg", "jpeg", "png"])
                if product_data and product_data["photo_path"] and Path(product_data["photo_path"]).exists():
                    st.image(product_data["photo_path"], use_container_width=True)
                    st.caption("Текущее фото")

            with col_right:
                article = st.text_input("Артикул *", value=product_data["article"] if product_data else "",
                                        placeholder="Например: 56126561")
                name = st.text_input("Наименование товара *", value=product_data["name"] if product_data else "",
                                     placeholder="Например: Масло Г2к")
                purpose = st.text_input("Для чего предназначен", 
                                        value=product_data["purpose"] if product_data else "",
                                        placeholder="Например: Для трактора МТЗ")

                c1, c2 = st.columns(2)
                with c1:
                    units = ["шт", "кг", "л", "м", "м²", "комплект", "упаковка"]
                    unit_idx = 0
                    if product_data and product_data["unit"] in units:
                        unit_idx = units.index(product_data["unit"])
                    unit = st.selectbox("Единица измерения *", units, index=unit_idx)
                with c2:
                    storage_place = st.text_input("Место хранения", 
                                                  value=product_data["storage_place"] if product_data else "",
                                                  placeholder="Полка №1 / Коробка №23")

                categories = ["", "Запчасти", "Семена", "Удобрения", "ГСМ", "Инструмент", "Расходники", "Прочее"]
                cat_idx = 0
                if product_data and product_data["category"] in categories:
                    cat_idx = categories.index(product_data["category"])
                category = st.selectbox("Категория", categories, index=cat_idx)

                notes = st.text_area("Примечания", value=product_data["notes"] if product_data else "",
                                     placeholder="Дополнительная информация...")

            submitted = st.form_submit_button("💾 Сохранить товар", use_container_width=True, type="primary")

            if submitted:
                if not article.strip() or not name.strip():
                    st.error("Артикул и Наименование обязательны!")
                else:
                    photo_path = product_data["photo_path"] if product_data else None
                    if photo_file:
                        safe_article = "".join(c for c in article if c.isalnum() or c in "-_")
                        photo_filename = f"{safe_article}_{photo_file.name}"
                        photo_path = str(IMAGES_DIR / photo_filename)
                        with open(photo_path, "wb") as f:
                            f.write(photo_file.getbuffer())

                    conn = get_connection()
                    try:
                        if edit_id:
                            conn.execute("""
                                UPDATE products SET
                                    article=?, name=?, purpose=?, unit=?, storage_place=?,
                                    notes=?, category=?, photo_path=?, updated_at=CURRENT_TIMESTAMP
                                WHERE id=?
                            """, (article.strip(), name.strip(), purpose.strip(), unit,
                                  storage_place.strip(), notes.strip(), category or None, photo_path, edit_id))
                            st.success("✅ Товар успешно обновлён!")
                            if "edit_product_id" in st.session_state:
                                del st.session_state["edit_product_id"]
                        else:
                            conn.execute("""
                                INSERT INTO products (article, name, purpose, unit, storage_place, notes, category, photo_path)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                            """, (article.strip(), name.strip(), purpose.strip(), unit,
                                  storage_place.strip(), notes.strip(), category or None, photo_path))
                            st.success("✅ Товар успешно добавлен!")
                        conn.commit()
                    except Exception as e:
                        if "UNIQUE" in str(e):
                            st.error("Такой артикул уже существует!")
                        else:
                            st.error(f"Ошибка: {e}")
                    finally:
                        conn.close()
                    st.rerun()


elif menu == "🚜 Машины / Механизмы":
    st.title("Справочник машин и механизмов")
    
    tab1, tab2 = st.tabs(["📋 Список", "➕ Добавить"])

    with tab1:
        search_m = st.text_input("🔍 Поиск машины или инвентарного номера...")
        conn = get_connection()
        machines = conn.execute("SELECT * FROM machines ORDER BY name").fetchall()
        conn.close()

        if not machines:
            st.info("Машин пока нет. Добавьте первую во вкладке «Добавить».")
        else:
            for m in machines:
                if search_m:
                    s = search_m.lower()
                    if s not in (m["name"] or "").lower() and s not in (m["inventory_number"] or "").lower():
                        continue
                
                cols = st.columns([5, 1])
                with cols[0]:
                    st.markdown(f"""
                    <div class="product-card">
                        <b style="font-size:1.15em;">🚜 {m['name']}</b><br>
                        {"Инв. №: " + m['inventory_number'] if m['inventory_number'] else ""}
                        {"<br>" + m['notes'] if m['notes'] else ""}
                    </div>
                    """, unsafe_allow_html=True)
                with cols[1]:
                    st.write("")
                    st.write("")
                    if st.button("🗑️", key=f"del_m_{m['id']}", help="Удалить"):
                        conn = get_connection()
                        conn.execute("DELETE FROM machines WHERE id = ?", (m["id"],))
                        conn.commit()
                        conn.close()
                        st.rerun()

    with tab2:
        with st.form("machine_form", clear_on_submit=True):
            name = st.text_input("Название машины / механизма *", placeholder="Например: Трактор МТЗ-82")
            inv_number = st.text_input("Инвентарный номер", placeholder="Необязательно")
            notes = st.text_area("Примечания")
            if st.form_submit_button("💾 Сохранить", type="primary", use_container_width=True):
                if name.strip():
                    conn = get_connection()
                    conn.execute(
                        "INSERT INTO machines (name, inventory_number, notes) VALUES (?, ?, ?)",
                        (name.strip(), inv_number.strip(), notes.strip())
                    )
                    conn.commit()
                    conn.close()
                    st.success("✅ Машина добавлена!")
                    st.rerun()
                else:
                    st.error("Укажите название")


elif menu == "📥 Поступления (Приход)":
    st.title("Поступление товара (Приход)")
    st.caption("Оформление прихода по счёт-фактуре или накладной")

    conn = get_connection()
    products = conn.execute("SELECT id, article, name, unit FROM products ORDER BY name").fetchall()
    conn.close()

    if not products:
        st.warning("Сначала добавьте товары в справочник.")
    else:
        with st.form("incoming_form", clear_on_submit=True):
            st.subheader("Данные документа")
            
            c1, c2 = st.columns(2)
            with c1:
                doc_number = st.text_input("Номер документа *", placeholder="Счёт-фактура / накладная №")
            with c2:
                doc_date = st.date_input("Дата документа", value=datetime.now())

            st.subheader("Товар")
            
            product_options = {f"{p['article']} — {p['name']}": p for p in products}
            selected = st.selectbox("Выберите товар *", options=list(product_options.keys()))
            product = product_options[selected]

            c1, c2, c3 = st.columns(3)
            with c1:
                quantity = st.number_input(f"Количество ({product['unit']}) *", min_value=0.01, step=1.0, value=1.0)
            with c2:
                price = st.number_input("Цена за ед. (руб.) *", min_value=0.0, step=0.01, format="%.2f")
            with c3:
                vat_percent = st.number_input("НДС (%)", min_value=0.0, max_value=100.0, value=20.0, step=1.0)

            # Автоматический расчёт
            vat_amount = round(price * quantity * (vat_percent / 100), 2)
            total_with_vat = round(price * quantity + vat_amount, 2)

            st.markdown("#### Расчёт")
            col_a, col_b, col_c = st.columns(3)
            col_a.metric("Сумма без НДС", f"{price * quantity:,.2f} ₽")
            col_b.metric("НДС", f"{vat_amount:,.2f} ₽")
            col_c.metric("Сумма с НДС", f"{total_with_vat:,.2f} ₽")

            comment = st.text_area("Комментарий / Примечание")

            submitted = st.form_submit_button("📥 Оформить приход", type="primary", use_container_width=True)

            if submitted:
                if not doc_number.strip():
                    st.error("Укажите номер документа!")
                elif quantity <= 0:
                    st.error("Количество должно быть больше 0")
                else:
                    conn = get_connection()
                    conn.execute("""
                        INSERT INTO movements (
                            product_id, movement_type, quantity, document_number,
                            price_per_unit, vat_percent, vat_amount, total_with_vat,
                            comment, movement_date
                        ) VALUES (?, 'приход', ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        product["id"], quantity, doc_number.strip(),
                        price, vat_percent, vat_amount, total_with_vat,
                        comment.strip(), str(doc_date)
                    ))
                    conn.commit()
                    conn.close()
                    st.success(f"✅ Приход оформлен! {product['article']} +{quantity} {product['unit']}")
                    st.balloons()
                    st.rerun()


elif menu == "📤 Расходы":
    st.title("Расход товара")
    st.caption("Списание на технику или место")

    conn = get_connection()
    products = conn.execute("SELECT id, article, name, unit FROM products ORDER BY name").fetchall()
    machines = conn.execute("SELECT id, name FROM machines ORDER BY name").fetchall()
    conn.close()

    if not products:
        st.warning("Сначала добавьте товары в справочник.")
    else:
        with st.form("outgoing_form", clear_on_submit=True):
            product_options = {f"{p['article']} — {p['name']}": p for p in products}
            selected = st.selectbox("Товар *", options=list(product_options.keys()))
            product = product_options[selected]

            current_stock = get_stock(product["id"])
            st.info(f"Текущий остаток: **{current_stock} {product['unit']}**")

            quantity = st.number_input(f"Количество ({product['unit']}) *", min_value=0.01, step=1.0, value=1.0)

            dest_type = st.radio("Куда списываем?", ["На машину / механизм", "На место / помещение"], horizontal=True)

            machine_id = None
            destination = ""

            if dest_type == "На машину / механизм":
                if machines:
                    machine_options = {m["name"]: m["id"] for m in machines}
                    selected_machine = st.selectbox("Выберите машину", options=list(machine_options.keys()))
                    machine_id = machine_options[selected_machine]
                else:
                    st.warning("Сначала добавьте машины в справочник.")
                    destination = st.text_input("Или укажите вручную")
            else:
                destination = st.text_input("Место / помещение *", placeholder="Например: Склад №2, Ангар, Поле и т.д.")

            comment = st.text_area("Комментарий")

            submitted = st.form_submit_button("📤 Оформить расход", type="primary", use_container_width=True)

            if submitted:
                if quantity <= 0:
                    st.error("Количество должно быть больше 0")
                elif quantity > current_stock:
                    st.error(f"Недостаточно товара! Доступно только {current_stock} {product['unit']}")
                elif dest_type == "На место / помещение" and not destination.strip():
                    st.error("Укажите место назначения")
                else:
                    conn = get_connection()
                    conn.execute("""
                        INSERT INTO movements (
                            product_id, movement_type, quantity, machine_id, destination, comment
                        ) VALUES (?, 'расход', ?, ?, ?, ?)
                    """, (product["id"], quantity, machine_id, destination.strip(), comment.strip()))
                    conn.commit()
                    conn.close()
                    st.success(f"✅ Расход оформлен! {product['article']} −{quantity} {product['unit']}")
                    st.rerun()


elif menu == "📋 Остатки":
    st.title("Остатки на складе")

    search = st.text_input("🔍 Поиск по остаткам...", placeholder="Артикул, название, место...")

    conn = get_connection()
    products = conn.execute("SELECT * FROM products ORDER BY name").fetchall()
    conn.close()

    if not products:
        st.info("Товаров пока нет.")
    else:
        items_with_stock = []
        for p in products:
            stock = get_stock(p["id"])
            items_with_stock.append((p, stock))

        if search:
            s = search.lower()
            items_with_stock = [
                (p, stock) for p, stock in items_with_stock
                if any(s in str(p[field] or "").lower() for field in 
                       ["article", "name", "purpose", "storage_place", "category"])
            ]

        items_with_stock.sort(key=lambda x: (-x[1], x[0]["name"]))

        total_positions = len([1 for _, s in items_with_stock if s > 0])
        st.caption(f"Позиций с остатком > 0: **{total_positions}**")

        for p, stock in items_with_stock:
            with st.container():
                cols = st.columns([1, 4, 1.5])
                
                with cols[0]:
                    if p["photo_path"] and Path(p["photo_path"]).exists():
                        st.image(p["photo_path"], use_container_width=True)
                    else:
                        st.markdown("""
                        <div style="background:#eee; border-radius:12px; height:100px; 
                                    display:flex; align-items:center; justify-content:center; color:#aaa;">
                            📷
                        </div>
                        """, unsafe_allow_html=True)
                
                with cols[1]:
                    st.markdown(f"**{p['article']}** — {p['name']}")
                    details = []
                    if p["purpose"]:
                        details.append(p["purpose"])
                    if p["storage_place"]:
                        details.append(f"📍 {p['storage_place']}")
                    if p["category"]:
                        details.append(p["category"])
                    st.caption(" • ".join(details) if details else "")
                
                with cols[2]:
                    color = "#2e7d32" if stock > 0 else "#9e9e9e"
                    st.markdown(f"""
                    <div style="text-align:right; padding-top:10px;">
                        <span style="font-size:1.4em; font-weight:700; color:{color};">{stock}</span>
                        <span style="color:#666;">{p['unit']}</span>
                    </div>
                    """, unsafe_allow_html=True)
                
                st.markdown("<hr style='margin:8px 0; border:none; border-top:1px solid #eee;'>", unsafe_allow_html=True)


elif menu == "📍 Места хранения":
    st.title("Места хранения")
    st.info("В этой версии места хранения указываются прямо в карточке товара. Отдельный справочник можно добавить позже при необходимости.")


elif menu == "📈 Отчёты":
    st.title("Отчёты")
    
    report_type = st.selectbox("Тип отчёта", [
        "Движение за период",
        "Остатки на текущий момент"
    ])

    if report_type == "Движение за период":
        c1, c2 = st.columns(2)
        with c1:
            date_from = st.date_input("С даты", value=datetime.now().replace(day=1))
        with c2:
            date_to = st.date_input("По дату", value=datetime.now())

        if st.button("Сформировать отчёт", type="primary"):
            conn = get_connection()
            rows = conn.execute("""
                SELECT m.*, p.article, p.name, p.unit
                FROM movements m
                JOIN products p ON m.product_id = p.id
                WHERE date(m.movement_date) BETWEEN ? AND ?
                ORDER BY m.movement_date DESC
            """, (str(date_from), str(date_to))).fetchall()
            conn.close()

            if not rows:
                st.info("За выбранный период движений нет.")
            else:
                for r in rows:
                    icon = "📥" if r["movement_type"] == "приход" else "📤"
                    extra = ""
                    if r["document_number"]:
                        extra += f" | Док: {r['document_number']}"
                    if r["total_with_vat"]:
                        extra += f" | Сумма: {r['total_with_vat']:,.2f} ₽"
                    st.markdown(f"""
                    {icon} **{r['article']}** — {r['name']}  
                    {r['movement_type'].title()}: **{r['quantity']} {r['unit']}** • {r['movement_date'][:10] if r['movement_date'] else ''}{extra}
                    """)
                    st.markdown("---")

    else:
        st.info("Отчёт по остаткам — смотрите раздел «Остатки».")


elif menu == "⚙️ Настройки":
    st.title("Настройки")
    st.markdown("""
    ### Информация о системе
    - База данных: SQLite (`sklad.db`)
    - Фотографии хранятся в папке `images/`
    - Версия: 0.2
    
    ### Важно
    На Streamlit Cloud данные могут сбрасываться при перезапуске приложения.  
    В следующих версиях сделаем постоянное хранение.
    """)
