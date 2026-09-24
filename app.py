import streamlit as st
from pathlib import Path
import sys
from datetime import datetime, date
import pandas as pd
import io

sys.path.append(str(Path(__file__).parent))
from database import init_db, get_connection, IMAGES_DIR, UPLOADS_DIR

st.set_page_config(
    page_title="Склад Учета",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

init_db()

# ====================== СТИЛИ ======================
st.markdown("""
<style>
    .stApp { background-color: #f0f2f5; }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1b5e20 0%, #2e7d32 100%);
    }
    [data-testid="stSidebar"] * { color: white !important; }
    [data-testid="stSidebar"] .stRadio label {
        padding: 10px 14px; border-radius: 8px; margin-bottom: 3px;
    }
    [data-testid="stSidebar"] .stRadio label:hover {
        background-color: rgba(255,255,255,0.12);
    }
    h1 { color: #1a1a1a !important; font-weight: 700 !important; }
    .stButton > button { border-radius: 8px !important; font-weight: 500; }
    div[data-testid="stMetric"] {
        background: white; padding: 12px 16px; border-radius: 10px;
        box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    }
</style>
""", unsafe_allow_html=True)

# ====================== МЕНЮ ======================
with st.sidebar:
    st.markdown("## 🏭 Склад Учета")
    st.caption("Система управления запасами")
    st.markdown("---")
    menu = st.radio(
        "Навигация",
        [
            "📦 Склады",
            "📋 Товары",
            "🚜 Машины / Механизмы",
            "🏢 Поставщики",
            "📥 Приход",
            "📤 Расход",
            "📊 Отчёты",
            "📥 Импорт / Экспорт",
            "⚙️ Настройки"
        ],
        label_visibility="collapsed"
    )
    st.markdown("---")
    st.caption("Версия 0.3")


# ====================== ВСПОМОГАТЕЛЬНЫЕ ======================
def get_warehouses():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM warehouses ORDER BY sort_order").fetchall()
    conn.close()
    return rows

def get_stock_by_warehouse(warehouse_id, search=""):
    conn = get_connection()
    query = """
        SELECT s.id as stock_id, s.quantity, s.storage_place,
               p.id as product_id, p.article, p.name, p.purpose, p.size,
               p.weight_volume, p.unit, p.condition, p.photo_path, p.category, p.notes
        FROM stock s
        JOIN products p ON s.product_id = p.id
        WHERE s.warehouse_id = ? AND s.quantity > 0
    """
    params = [warehouse_id]
    if search:
        query += """ AND (
            p.article LIKE ? OR p.name LIKE ? OR p.purpose LIKE ? OR
            s.storage_place LIKE ? OR p.condition LIKE ? OR p.category LIKE ?
        )"""
        s = f"%{search}%"
        params.extend([s, s, s, s, s, s])
    query += " ORDER BY p.name"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return rows


# ====================== СТРАНИЦЫ ======================

if menu == "📦 Склады":
    st.title("Склады")
    warehouses = get_warehouses()
    tabs = st.tabs([w["name"] for w in warehouses])

    for i, wh in enumerate(warehouses):
        with tabs[i]:
            search = st.text_input("🔍 Поиск по всем полям...", key=f"search_wh_{wh['id']}",
                                   placeholder="Артикул, название, место, состояние...")

            items = get_stock_by_warehouse(wh["id"], search)

            if not items:
                st.info("На этом складе пока нет остатков.")
            else:
                # Заголовок таблицы
                header_cols = st.columns([0.4, 0.8, 1.1, 1.8, 1.4, 0.8, 0.9, 1.0, 1.0, 1.2])
                headers = ["№", "Фото", "Артикул", "Наименование", "Назначение", "Размер", "Масса/объём", "Кол-во", "Состояние", "Место"]
                for col, h in zip(header_cols, headers):
                    col.markdown(f"**{h}**")

                st.markdown("---")

                for idx, item in enumerate(items, 1):
                    cols = st.columns([0.4, 0.8, 1.1, 1.8, 1.4, 0.8, 0.9, 1.0, 1.0, 1.2])
                    cols[0].write(idx)

                    with cols[1]:
                        if item["photo_path"] and Path(item["photo_path"]).exists():
                            st.image(item["photo_path"], width=55)
                        else:
                            st.caption("—")

                    cols[2].write(item["article"])
                    cols[3].write(item["name"])
                    cols[4].write(item["purpose"] or "—")
                    cols[5].write(item["size"] or "—")
                    cols[6].write(item["weight_volume"] or "—")
                    cols[7].markdown(f"**{item['quantity']}** {item['unit']}")
                    cols[8].write(item["condition"] or "—")
                    cols[9].write(item["storage_place"] or "—")

                    st.markdown("<hr style='margin:4px 0; border-color:#eee'>", unsafe_allow_html=True)


elif menu == "📋 Товары":
    st.title("Справочник товаров")

    tab_list, tab_add = st.tabs(["Список товаров", "➕ Добавить товар"])

    with tab_list:
        search = st.text_input("🔍 Поиск...", key="search_products")
        conn = get_connection()
        products = conn.execute("SELECT * FROM products ORDER BY name").fetchall()
        conn.close()

        if not products:
            st.info("Товаров пока нет.")
        else:
            for p in products:
                if search:
                    s = search.lower()
                    if not any(s in str(p[f] or "").lower() for f in ["article", "name", "purpose", "category", "notes"]):
                        continue

                cols = st.columns([1, 4, 1.2])
                with cols[0]:
                    if p["photo_path"] and Path(p["photo_path"]).exists():
                        st.image(p["photo_path"], width=70)
                    else:
                        st.caption("📷")
                with cols[1]:
                    st.markdown(f"**{p['article']}** — {p['name']}")
                    st.caption(f"{p['purpose'] or ''} • {p['unit']} • {p['condition'] or ''} • {p['category'] or ''}")
                with cols[2]:
                    if st.button("Открыть", key=f"open_p_{p['id']}"):
                        st.session_state["edit_product_id"] = p["id"]
                        st.rerun()
                st.markdown("---")

    with tab_add:
        edit_id = st.session_state.get("edit_product_id")
        product = None
        if edit_id:
            conn = get_connection()
            product = conn.execute("SELECT * FROM products WHERE id = ?", (edit_id,)).fetchone()
            conn.close()
            st.info(f"Редактирование: **{product['article']}**")
            if st.button("← Отмена"):
                del st.session_state["edit_product_id"]
                st.rerun()

        with st.form("product_form"):
            c1, c2 = st.columns(2)
            with c1:
                article = st.text_input("Артикул *", value=product["article"] if product else "")
                name = st.text_input("Наименование *", value=product["name"] if product else "")
                purpose = st.text_input("Назначение", value=product["purpose"] if product else "")
                size = st.text_input("Размер", value=product["size"] if product else "")
            with c2:
                weight_volume = st.text_input("Масса / объём", value=product["weight_volume"] if product else "")
                unit = st.selectbox("Ед. изм. *", ["шт", "кг", "л", "м", "м²", "комплект", "упаковка"],
                                    index=0 if not product else max(0, ["шт", "кг", "л", "м", "м²", "комплект", "упаковка"].index(product["unit"]) if product["unit"] in ["шт", "кг", "л", "м", "м²", "комплект", "упаковка"] else 0))
                condition = st.selectbox("Состояние", ["Новый", "Б/У", "Не годный", "Требует ремонта", "Восстановленный"],
                                         index=0 if not product else max(0, ["Новый", "Б/У", "Не годный", "Требует ремонта", "Восстановленный"].index(product["condition"]) if product["condition"] in ["Новый", "Б/У", "Не годный", "Требует ремонта", "Восстановленный"] else 0))
                category = st.selectbox("Категория", ["", "Запчасти", "Семена", "Удобрения", "ГСМ", "Инструмент", "Расходники", "Прочее"])

            notes = st.text_area("Примечания", value=product["notes"] if product else "")
            photo = st.file_uploader("Фото", type=["jpg", "jpeg", "png"])

            if st.form_submit_button("💾 Сохранить", type="primary"):
                if not article.strip() or not name.strip():
                    st.error("Артикул и наименование обязательны")
                else:
                    photo_path = product["photo_path"] if product else None
                    if photo:
                        fname = f"{article.strip().replace('/', '_')}_{photo.name}"
                        photo_path = str(IMAGES_DIR / fname)
                        with open(photo_path, "wb") as f:
                            f.write(photo.getbuffer())

                    conn = get_connection()
                    try:
                        if edit_id:
                            conn.execute("""
                                UPDATE products SET article=?, name=?, purpose=?, size=?, weight_volume=?,
                                unit=?, condition=?, category=?, photo_path=?, notes=?, updated_at=CURRENT_TIMESTAMP
                                WHERE id=?
                            """, (article.strip(), name.strip(), purpose, size, weight_volume, unit, condition,
                                  category or None, photo_path, notes, edit_id))
                            st.success("Обновлено")
                            if "edit_product_id" in st.session_state:
                                del st.session_state["edit_product_id"]
                        else:
                            conn.execute("""
                                INSERT INTO products (article, name, purpose, size, weight_volume, unit, condition, category, photo_path, notes)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (article.strip(), name.strip(), purpose, size, weight_volume, unit, condition,
                                  category or None, photo_path, notes))
                            st.success("Товар добавлен")
                        conn.commit()
                    except Exception as e:
                        st.error(str(e))
                    finally:
                        conn.close()
                    st.rerun()


elif menu == "🚜 Машины / Механизмы":
    st.title("Машины и механизмы")

    tab1, tab2 = st.tabs(["Список", "➕ Добавить"])

    with tab1:
        search = st.text_input("🔍 Поиск...", key="search_machines")
        conn = get_connection()
        machines = conn.execute("SELECT * FROM machines ORDER BY name").fetchall()
        conn.close()

        if not machines:
            st.info("Машин пока нет.")
        else:
            for m in machines:
                if search and search.lower() not in (m["name"] or "").lower() and search.lower() not in (m["model"] or "").lower() and search.lower() not in (m["plate_number"] or "").lower():
                    continue
                cols = st.columns([1, 4, 1])
                with cols[0]:
                    if m["photo_path"] and Path(m["photo_path"]).exists():
                        st.image(m["photo_path"], width=70)
                    else:
                        st.caption("🚜")
                with cols[1]:
                    st.markdown(f"**{m['name']}** {m['model'] or ''}")
                    st.caption(f"Гос.№: {m['plate_number'] or '—'} • VIN: {m['vin'] or '—'} • Водитель: {m['driver'] or '—'} • Владелец: {m['owner'] or '—'}")
                with cols[2]:
                    if st.button("Открыть", key=f"open_m_{m['id']}"):
                        st.session_state["edit_machine_id"] = m["id"]
                        st.rerun()
                st.markdown("---")

    with tab2:
        edit_id = st.session_state.get("edit_machine_id")
        machine = None
        if edit_id:
            conn = get_connection()
            machine = conn.execute("SELECT * FROM machines WHERE id=?", (edit_id,)).fetchone()
            conn.close()
            st.info(f"Редактирование: **{machine['name']}**")
            if st.button("← Отмена", key="cancel_m"):
                del st.session_state["edit_machine_id"]
                st.rerun()

        with st.form("machine_form"):
            c1, c2 = st.columns(2)
            with c1:
                name = st.text_input("Наименование *", value=machine["name"] if machine else "")
                model = st.text_input("Модель", value=machine["model"] if machine else "")
                plate = st.text_input("Гос. номер", value=machine["plate_number"] if machine else "")
            with c2:
                vin = st.text_input("VIN код", value=machine["vin"] if machine else "")
                driver = st.text_input("Водитель", value=machine["driver"] if machine else "")
                owner = st.text_input("Владелец", value=machine["owner"] if machine else "")
            notes = st.text_area("Примечания", value=machine["notes"] if machine else "")
            photo = st.file_uploader("Фото", type=["jpg", "jpeg", "png"], key="m_photo")

            if st.form_submit_button("💾 Сохранить", type="primary"):
                if not name.strip():
                    st.error("Укажите наименование")
                else:
                    photo_path = machine["photo_path"] if machine else None
                    if photo:
                        fname = f"machine_{name.strip()[:20]}_{photo.name}"
                        photo_path = str(IMAGES_DIR / fname)
                        with open(photo_path, "wb") as f:
                            f.write(photo.getbuffer())
                    conn = get_connection()
                    if edit_id:
                        conn.execute("""
                            UPDATE machines SET name=?, model=?, plate_number=?, vin=?, driver=?, owner=?, photo_path=?, notes=?
                            WHERE id=?
                        """, (name, model, plate, vin, driver, owner, photo_path, notes, edit_id))
                        if "edit_machine_id" in st.session_state:
                            del st.session_state["edit_machine_id"]
                    else:
                        conn.execute("""
                            INSERT INTO machines (name, model, plate_number, vin, driver, owner, photo_path, notes)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (name, model, plate, vin, driver, owner, photo_path, notes))
                    conn.commit()
                    conn.close()
                    st.success("Сохранено")
                    st.rerun()


elif menu == "🏢 Поставщики":
    st.title("Поставщики")

    tab1, tab2 = st.tabs(["Список", "➕ Добавить"])

    with tab1:
        search = st.text_input("🔍 Поиск...", key="search_sup")
        conn = get_connection()
        suppliers = conn.execute("SELECT * FROM suppliers ORDER BY name").fetchall()
        conn.close()

        if not suppliers:
            st.info("Поставщиков пока нет.")
        else:
            for s in suppliers:
                if search and search.lower() not in (s["name"] or "").lower() and search.lower() not in (s["inn"] or "").lower():
                    continue
                cols = st.columns([4, 1])
                with cols[0]:
                    st.markdown(f"**{s['name']}**")
                    st.caption(f"ИНН: {s['inn'] or '—'} • {s['address'] or ''} • {s['contacts'] or ''} • {s['shop'] or ''}")
                with cols[1]:
                    if st.button("Открыть", key=f"open_s_{s['id']}"):
                        st.session_state["edit_supplier_id"] = s["id"]
                        st.rerun()
                st.markdown("---")

    with tab2:
        edit_id = st.session_state.get("edit_supplier_id")
        sup = None
        if edit_id:
            conn = get_connection()
            sup = conn.execute("SELECT * FROM suppliers WHERE id=?", (edit_id,)).fetchone()
            conn.close()
            st.info(f"Редактирование: **{sup['name']}**")
            if st.button("← Отмена", key="cancel_s"):
                del st.session_state["edit_supplier_id"]
                st.rerun()

        with st.form("supplier_form"):
            name = st.text_input("Наименование *", value=sup["name"] if sup else "")
            inn = st.text_input("ИНН", value=sup["inn"] if sup else "")
            address = st.text_input("Адрес", value=sup["address"] if sup else "")
            contacts = st.text_input("Контактные данные", value=sup["contacts"] if sup else "")
            shop = st.text_input("Магазин", value=sup["shop"] if sup else "")
            notes = st.text_area("Примечания", value=sup["notes"] if sup else "")

            if st.form_submit_button("💾 Сохранить", type="primary"):
                if not name.strip():
                    st.error("Укажите наименование")
                else:
                    conn = get_connection()
                    if edit_id:
                        conn.execute("""
                            UPDATE suppliers SET name=?, inn=?, address=?, contacts=?, shop=?, notes=? WHERE id=?
                        """, (name, inn, address, contacts, shop, notes, edit_id))
                        if "edit_supplier_id" in st.session_state:
                            del st.session_state["edit_supplier_id"]
                    else:
                        conn.execute("""
                            INSERT INTO suppliers (name, inn, address, contacts, shop, notes)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (name, inn, address, contacts, shop, notes))
                    conn.commit()
                    conn.close()
                    st.success("Сохранено")
                    st.rerun()


elif menu == "📥 Приход":
    st.title("Приход товара")
    st.caption("Один документ может содержать несколько позиций")

    conn = get_connection()
    products = conn.execute("SELECT id, article, name, unit FROM products ORDER BY name").fetchall()
    suppliers = conn.execute("SELECT id, name FROM suppliers ORDER BY name").fetchall()
    warehouses = conn.execute("SELECT id, name FROM warehouses ORDER BY sort_order").fetchall()
    conn.close()

    if not products:
        st.warning("Сначала добавьте товары в справочник (или загрузите через Импорт).")
    else:
        with st.form("incoming_form"):
            st.subheader("Шапка документа")
            c1, c2, c3 = st.columns(3)
            with c1:
                doc_number = st.text_input("№ документа *")
            with c2:
                doc_date = st.date_input("Дата", value=date.today())
            with c3:
                sup_options = {s["name"]: s["id"] for s in suppliers}
                sup_options["— не выбран —"] = None
                selected_sup = st.selectbox("Поставщик", list(sup_options.keys()))

            notes = st.text_area("Примечание к документу")
            file = st.file_uploader("Прикрепить файл (скан)", type=["pdf", "jpg", "jpeg", "png"])

            st.subheader("Позиции")
            st.caption("Пока можно добавить одну позицию. Возможность нескольких строк добавим в следующей итерации.")

            prod_options = {f"{p['article']} — {p['name']}": p for p in products}
            selected_prod = st.selectbox("Товар *", list(prod_options.keys()))
            product = prod_options[selected_prod]

            c1, c2, c3, c4 = st.columns(4)
            with c1:
                qty = st.number_input(f"Количество ({product['unit']})", min_value=0.01, value=1.0)
            with c2:
                price = st.number_input("Цена за ед.", min_value=0.0, value=0.0, format="%.2f")
            with c3:
                vat = st.number_input("НДС %", min_value=0.0, max_value=100.0, value=20.0)
            with c4:
                wh_options = {w["name"]: w["id"] for w in warehouses}
                selected_wh = st.selectbox("Склад *", list(wh_options.keys()))

            storage_place = st.text_input("Место хранения", placeholder="Полка / Коробка")

            vat_amount = round(price * qty * vat / 100, 2)
            total = round(price * qty + vat_amount, 2)
            st.metric("Сумма с НДС", f"{total:,.2f} ₽")

            if st.form_submit_button("📥 Оформить приход", type="primary"):
                if not doc_number.strip():
                    st.error("Укажите номер документа")
                else:
                    file_path = None
                    if file:
                        fname = f"in_{doc_number}_{file.name}"
                        file_path = str(UPLOADS_DIR / fname)
                        with open(file_path, "wb") as f:
                            f.write(file.getbuffer())

                    conn = get_connection()
                    cur = conn.cursor()
                    cur.execute("""
                        INSERT INTO incoming_documents (document_number, document_date, supplier_id, file_path, notes)
                        VALUES (?, ?, ?, ?, ?)
                    """, (doc_number, str(doc_date), sup_options[selected_sup], file_path, notes))
                    doc_id = cur.lastrowid

                    cur.execute("""
                        INSERT INTO incoming_items (document_id, product_id, warehouse_id, quantity, price, vat_percent, vat_amount, total_with_vat, storage_place)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (doc_id, product["id"], wh_options[selected_wh], qty, price, vat, vat_amount, total, storage_place))

                    # Обновляем / создаём остаток
                    existing = cur.execute("""
                        SELECT id, quantity FROM stock
                        WHERE product_id=? AND warehouse_id=? AND IFNULL(storage_place,'') = IFNULL(?, '')
                    """, (product["id"], wh_options[selected_wh], storage_place)).fetchone()

                    if existing:
                        cur.execute("UPDATE stock SET quantity = quantity + ? WHERE id = ?", (qty, existing["id"]))
                    else:
                        cur.execute("""
                            INSERT INTO stock (product_id, warehouse_id, quantity, storage_place)
                            VALUES (?, ?, ?, ?)
                        """, (product["id"], wh_options[selected_wh], qty, storage_place))

                    conn.commit()
                    conn.close()
                    st.success("Приход оформлен!")
                    st.balloons()
                    st.rerun()


elif menu == "📤 Расход":
    st.title("Расход товара")
    st.info("Раздел будет доработан в следующей версии (выбор нескольких позиций + привязка к машине).")


elif menu == "📊 Отчёты":
    st.title("Отчёты")
    st.info("Отчёты по технике и поставщикам появятся после накопления данных.")


elif menu == "📥 Импорт / Экспорт":
    st.title("Импорт и Экспорт")

    st.subheader("Импорт товаров из Excel")
    st.markdown("""
    Подготовь Excel-файл со следующими колонками (названия могут быть на русском):

    | Артикул | Наименование | Назначение | Размер | Масса/объём | Ед.изм. | Состояние | Категория | Примечания |
    """)

    uploaded = st.file_uploader("Выбери Excel-файл (.xlsx)", type=["xlsx"])

    if uploaded:
        try:
            df = pd.read_excel(uploaded)
            st.write("Предпросмотр:")
            st.dataframe(df.head(10))

            # Простая нормализация названий колонок
            col_map = {}
            for col in df.columns:
                cl = str(col).lower().strip()
                if "артикул" in cl or "article" in cl:
                    col_map["article"] = col
                elif "наимен" in cl or "name" in cl or "назван" in cl:
                    col_map["name"] = col
                elif "назнач" in cl or "purpose" in cl:
                    col_map["purpose"] = col
                elif "размер" in cl or "size" in cl:
                    col_map["size"] = col
                elif "масс" in cl or "объём" in cl or "объем" in cl or "weight" in cl:
                    col_map["weight_volume"] = col
                elif "ед" in cl or "unit" in cl:
                    col_map["unit"] = col
                elif "состоян" in cl or "condition" in cl:
                    col_map["condition"] = col
                elif "категор" in cl or "category" in cl:
                    col_map["category"] = col
                elif "примечан" in cl or "note" in cl:
                    col_map["notes"] = col

            if "article" not in col_map or "name" not in col_map:
                st.error("Не найдены обязательные колонки: Артикул и Наименование")
            else:
                if st.button("🚀 Загрузить в базу", type="primary"):
                    conn = get_connection()
                    added = 0
                    skipped = 0
                    for _, row in df.iterrows():
                        article = str(row[col_map["article"]]).strip()
                        name = str(row[col_map["name"]]).strip()
                        if not article or article == "nan" or not name or name == "nan":
                            continue
                        try:
                            conn.execute("""
                                INSERT OR IGNORE INTO products (article, name, purpose, size, weight_volume, unit, condition, category, notes)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (
                                article,
                                name,
                                str(row.get(col_map.get("purpose"), "") or ""),
                                str(row.get(col_map.get("size"), "") or ""),
                                str(row.get(col_map.get("weight_volume"), "") or ""),
                                str(row.get(col_map.get("unit"), "шт") or "шт"),
                                str(row.get(col_map.get("condition"), "Новый") or "Новый"),
                                str(row.get(col_map.get("category"), "") or ""),
                                str(row.get(col_map.get("notes"), "") or ""),
                            ))
                            added += 1
                        except:
                            skipped += 1
                    conn.commit()
                    conn.close()
                    st.success(f"Загружено: {added} товаров. Пропущено: {skipped}")
        except Exception as e:
            st.error(f"Ошибка чтения файла: {e}")

    st.markdown("---")
    st.subheader("Экспорт")
    if st.button("📥 Скачать справочник товаров (Excel)"):
        conn = get_connection()
        df = pd.read_sql_query("SELECT article as Артикул, name as Наименование, purpose as Назначение, size as Размер, weight_volume as 'Масса/объём', unit as 'Ед.изм.', condition as Состояние, category as Категория, notes as Примечания FROM products ORDER BY name", conn)
        conn.close()
        buffer = io.BytesIO()
        df.to_excel(buffer, index=False)
        st.download_button("Скачать Excel", buffer.getvalue(), "tovary.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


elif menu == "⚙️ Настройки":
    st.title("Настройки")
    st.markdown("""
    ### Текущая версия: 0.3

    **Что уже работает:**
    - 3 склада с остатками
    - Справочник товаров (с фото, состоянием, размером и т.д.)
    - Машины / механизмы
    - Поставщики
    - Приход (одна позиция + файл)
    - Импорт товаров из Excel
    - Экспорт товаров в Excel

    **Что будет доработано дальше:**
    - Несколько позиций в одном приходе
    - Полноценный расход с привязкой к машине
    - Карточки (детальный просмотр)
    - Отчёты по технике и поставщикам
    """)
