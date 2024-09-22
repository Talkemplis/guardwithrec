import streamlit as st
import pandas as pd
import os
from datetime import datetime, time

# נתיב לקובצי CSV
CSV_FILE = 'shomer1.csv'
HISTORY_FILE = 'history1.csv'

# הגדרת סגנון מותאם
st.set_page_config(layout="wide", initial_sidebar_state="collapsed")
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Heebo:wght@400;700&display=swap');
    
    .stApp {
        direction: rtl;
        font-family: 'Heebo', sans-serif;
    }
    .main .block-container {
        max-width: 960px;
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    h1, h2, h3 {
        color: #1E3A8A;
    }
    .stButton>button {
        background-color: #2563EB;
        color: white;
        font-weight: bold;
    }
    .stSelectbox, .stMultiSelect {
        direction: rtl;
    }
    .stTextInput>div>div>input {
        direction: rtl;
        text-align: right;
    }
    .stDateInput, .stTimeInput {
        direction: ltr;
    }
    .styled-table {
        border-collapse: collapse;
        margin: 25px 0;
        font-size: 0.9em;
        font-family: 'Heebo', sans-serif;
        min-width: 400px;
        box-shadow: 0 0 20px rgba(0, 0, 0, 0.15);
    }
    .styled-table thead tr {
        background-color: #2563EB;
        color: #ffffff;
        text-align: right;
    }
    .styled-table th,
    .styled-table td {
        padding: 12px 15px;
        text-align: right;
    }
    .styled-table tbody tr {
        border-bottom: 1px solid #dddddd;
    }
    .styled-table tbody tr:nth-of-type(even) {
        background-color: #f3f3f3;
    }
    .styled-table tbody tr:last-of-type {
        border-bottom: 2px solid #2563EB;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# הגדרת ניקוד לפי סוג תורנות
DUTY_POINTS = {
    "הגנמ": 80,
    "חמל": 10,
    'חמל סופ"ש': 15
}

def load_data():
    if os.path.exists(CSV_FILE):
        try:
            data = pd.read_csv(CSV_FILE, encoding='utf-8-sig')
            data.columns = data.columns.str.strip()
            if "ניקוד" not in data.columns:
                data["ניקוד"] = 0
            return data
        except Exception as e:
            st.error(f"שגיאה בטעינת קובץ: {e}")
            return pd.DataFrame(columns=["שם", "צוות", "מספר משימות", "ניקוד"])
    return pd.DataFrame(columns=["שם", "צוות", "מספר משימות", "ניקוד"])

def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            history = pd.read_csv(HISTORY_FILE, encoding='utf-8-sig')
            history.columns = history.columns.str.strip()
            history = history.fillna('')
            # המרת זמנים למחרוזות בפורמט הנכון
            history['שעת התחלה'] = pd.to_datetime(history['שעת התחלה'], format='%H:%M:%S', errors='coerce').dt.strftime('%H:%M:%S')
            history['שעת סיום'] = pd.to_datetime(history['שעת סיום'], format='%H:%M:%S', errors='coerce').dt.strftime('%H:%M:%S')
            return history
        except Exception as e:
            st.error(f"שגיאה בטעינת היסטוריה: {e}")
            return pd.DataFrame(columns=["שם משימה", "מקום", "תאריך", "שעת התחלה", "שעת סיום", "מספר תורנים", "תורנים", "סוג תורנות"])
    return pd.DataFrame(columns=["שם משימה", "מקום", "תאריך", "שעת התחלה", "שעת סיום", "מספר תורנים", "תורנים", "סוג תורנות"])

def update_soldier_stats(data, history):
    data["מספר משימות"] = 0
    data["ניקוד"] = 0
    
    for _, row in history.iterrows():
        if row["שם משימה"] and row["תורנים"]:
            soldiers = row["תורנים"].split(", ") if isinstance(row["תורנים"], str) else []
            points = DUTY_POINTS.get(row["סוג תורנות"], 0)
            for soldier in soldiers:
                if soldier in data["שם"].values:
                    data.loc[data["שם"] == soldier, "מספר משימות"] += 1
                    data.loc[data["שם"] == soldier, "ניקוד"] += points
    return data

def display_styled_table(df):
    df_display = df.fillna('')
    st.markdown(df_display.to_html(index=False, classes='styled-table'), unsafe_allow_html=True)

def recommend_guard(data, history):
    if data.empty or history.empty:
        return None

    # Sort data by number of tasks and points
    data_sorted = data.sort_values(by=["מספר משימות", "ניקוד"])

    # Get the minimum number of tasks
    min_tasks = data_sorted["מספר משימות"].min()

    # Filter soldiers with minimum number of tasks
    candidates = data_sorted[data_sorted["מספר משימות"] == min_tasks]

    if len(candidates) == 1:
        return candidates.iloc[0]["שם"]
    else:
        # Find the earliest date for each candidate
        earliest_dates = {}
        for soldier in candidates["שם"]:
            soldier_history = history[history["תורנים"].str.contains(soldier, na=False)]
            if not soldier_history.empty:
                earliest_date = pd.to_datetime(soldier_history["תאריך"]).min()
                earliest_dates[soldier] = earliest_date
            else:
                earliest_dates[soldier] = pd.Timestamp.max

        # Return the soldier with the earliest date
        if earliest_dates:
            return min(earliest_dates, key=earliest_dates.get)
        else:
            return candidates.iloc[0]["שם"]  # If no history, return the first candidate

# אפליקציית Streamlit
def main():
    st.title("מערכת תורני מדור אור")

    # טען את הנתונים בכל רענון
    data = load_data()
    history = load_history()

    # עדכן את הסטטיסטיקות של החיילים
    data = update_soldier_stats(data, history)

    tab1, tab2, tab3, tab4 = st.tabs(["ניהול חיילים", "ניהול משימות", "עריכת משימות", "סיכום"])

    with tab1:
        st.header("ניהול חיילים")
        
        col1, col2 = st.columns(2)
        with col1:
            soldier_name = st.text_input("שם החייל:")
        with col2:
            soldier_team = st.text_input("צוות החייל:")
        
        if st.button("הוסף חייל"):
            if soldier_name and soldier_team:
                if soldier_name in data["שם"].values:
                    st.warning("חייל עם שם זה כבר קיים.")
                else:
                    new_soldier = pd.DataFrame({"שם": [soldier_name], "צוות": [soldier_team], "מספר משימות": [0], "ניקוד": [0]})
                    data = pd.concat([data, new_soldier], ignore_index=True)
                    try:
                        data.to_csv(CSV_FILE, index=False, encoding='utf-8-sig')
                        st.success(f"חייל {soldier_name} נוסף בהצלחה!")
                        # Reload data after addition
                        data = load_data()
                    except Exception as e:
                        st.error(f"שגיאה בשמירת החייל: {e}")
            else:
                st.warning("נא להזין שם וצוות.")
        
        if "שם" in data.columns and not data.empty:
            soldier_to_remove = st.selectbox("בחר חייל למחיקה:", data["שם"].tolist())
            if st.button("מחק חייל"):
                data = data[data["שם"] != soldier_to_remove]
                try:
                    data.to_csv(CSV_FILE, index=False, encoding='utf-8-sig')
                    st.success(f"חייל {soldier_to_remove} נמחק בהצלחה!")
                    # Reload data after deletion
                    data = load_data()
                except Exception as e:
                    st.error(f"שגיאה במחיקת החייל: {e}")
        else:
            st.warning("אין חיילים להצגה.")
        
        st.subheader("רשימת חיילים")
        display_styled_table(data)

    with tab2:
        st.header("ניהול משימות")
        
        col1, col2 = st.columns(2)
        with col1:
            task_name = st.text_input("שם המשימה:")
            location = st.text_input("מקום המשימה:")
            date = st.date_input("תאריך המשימה:")
        with col2:
            start_time = st.time_input("שעת התחלה:")
            end_time = st.time_input("שעת סיום:")
            num_soldiers = st.number_input("כמות תורנים:", min_value=1, value=1)
        
        duty_type = st.selectbox("סוג תורנות:", list(DUTY_POINTS.keys()))
        
        available_soldiers = data["שם"].tolist()
        selected_soldiers = st.multiselect("בחר תורנים:", available_soldiers)
        
        if st.button("שמור משימה"):
            if task_name and selected_soldiers:
                if len(selected_soldiers) <= num_soldiers:
                    history_entry = pd.DataFrame({
                        "שם משימה": [task_name],
                        "מקום": [location],
                        "תאריך": [pd.to_datetime(date).strftime('%Y-%m-%d')],
                        "שעת התחלה": [start_time.strftime('%H:%M:%S')],
                        "שעת סיום": [end_time.strftime('%H:%M:%S')],
                        "מספר תורנים": [num_soldiers],
                        "תורנים": [', '.join(map(str, selected_soldiers))],
                        "סוג תורנות": [duty_type]
                    })
                    history = pd.concat([history, history_entry], ignore_index=True)
                    try:
                        history.to_csv(HISTORY_FILE, index=False, encoding='utf-8-sig')
                        # Update soldier stats after adding
                        data = update_soldier_stats(data, history)
                        data.to_csv(CSV_FILE, index=False, encoding='utf-8-sig')
                        st.success(f"משימה {task_name} נוספה בהצלחה!")
                        # Reload history and data
                        history = load_history()
                        data = load_data()
                    except Exception as e:
                        st.error(f"שגיאה בשמירת המשימה: {e}")
                else:
                    st.warning("לא ניתן להקצות יותר תורנים מהנדרש.")
            else:
                st.warning("נא להזין שם משימה ולבחור תורנים.")
        
        # Add the new "Recommend Guard" button
        if st.button("המלץ על תורן"):
            recommended_guard = recommend_guard(data, history)
            if recommended_guard:
                st.success(f"התורן המומלץ הוא: {recommended_guard}")
            else:
                st.warning("לא ניתן להמליץ על תורן כרגע. ייתכן שאין מספיק נתונים.")
        
        st.subheader("היסטוריית משימות")
        display_styled_table(history)

    with tab3:
        st.header("עריכת משימות")
        
        if not history.empty and "שם משימה" in history.columns:
            valid_tasks = [task for task in history["שם משימה"].tolist() if task]
            if valid_tasks:
                task_to_edit = st.selectbox("בחר משימה לעריכה:", valid_tasks)
                if task_to_edit:
                    task_row = history[history["שם משימה"] == task_to_edit]
                    if not task_row.empty:
                        task_row = task_row.iloc[0]
                        col1, col2 = st.columns(2)
                        with col1:
                            new_start_time = st.time_input("שעת התחלה חדשה:", value=datetime.strptime(task_row["שעת התחלה"], '%H:%M:%S').time())
                            new_end_time = st.time_input("שעת סיום חדשה:", value=datetime.strptime(task_row["שעת סיום"], '%H:%M:%S').time())
                        with col2:
                            new_num_soldiers = st.number_input("כמות תורנים חדשה:", min_value=1, value=int(task_row["מספר תורנים"]))
                            new_duty_type = st.selectbox(
                                "סוג תורנות חדש:",
                                list(DUTY_POINTS.keys()),
                                index=list(DUTY_POINTS.keys()).index(task_row["סוג תורנות"]) if task_row["סוג תורנות"] in DUTY_POINTS else 0
                            )
                        
                        current_soldiers = task_row["תורנים"].split(', ') if isinstance(task_row["תורנים"], str) else []
                        new_selected_soldiers = st.multiselect("בחר תורנים חדשים:", available_soldiers, default=current_soldiers)
                        
                        if st.button("עדכן משימה"):
                            if len(new_selected_soldiers) <= new_num_soldiers:
                                history.loc[history["שם משימה"] == task_to_edit, "שעת התחלה"] = new_start_time.strftime('%H:%M:%S')
                                history.loc[history["שם משימה"] == task_to_edit, "שעת סיום"] = new_end_time.strftime('%H:%M:%S')
                                history.loc[history["שם משימה"] == task_to_edit, "מספר תורנים"] = new_num_soldiers
                                history.loc[history["שם משימה"] == task_to_edit, "סוג תורנות"] = new_duty_type
                                history.loc[history["שם משימה"] == task_to_edit, "תורנים"] = ', '.join(new_selected_soldiers)
                                try:
                                    history.to_csv(HISTORY_FILE, index=False, encoding='utf-8-sig')
                                    # Update soldier stats after editing
                                    data = update_soldier_stats(data, history)
                                    data.to_csv(CSV_FILE, index=False, encoding='utf-8-sig')
                                    st.success(f"משימה {task_to_edit} עודכנה בהצלחה!")
                                    # Reload history and data
                                    history = load_history()
                                    data = load_data()
                                except Exception as e:
                                    st.error(f"שגיאה בעדכון המשימה: {e}")
                            else:
                                st.warning("לא ניתן להקצות יותר תורנים מהנדרש.")
                    else:
                        st.warning("לא נמצאה משימה להצגה.")
            else:
                st.warning("אין משימות תקינות להצגה.")
        else:
            st.warning("אין משימות להצגה.")
        
        if "שם משימה" in history.columns and not history.empty:
            valid_tasks = [task for task in history["שם משימה"].tolist() if task]
            if valid_tasks:
                task_to_remove = st.selectbox("בחר משימה למחיקה:", valid_tasks, key="remove_task")
                if st.button("מחק משימה"):
                    history = history[history["שם משימה"] != task_to_remove]
                    try:
                        history.to_csv(HISTORY_FILE, index=False, encoding='utf-8-sig')
                        # Update soldier stats after deletion
                        data = update_soldier_stats(data, history)
                        data.to_csv(CSV_FILE, index=False, encoding='utf-8-sig')
                        st.success(f"משימה {task_to_remove} נמחקה בהצלחה!")
                        # Reload history and data
                        history = load_history()
                        data = load_data()
                    except Exception as e:
                        st.error(f"שגיאה במחיקת המשימה: {e}")
            else:
                st.warning("אין משימות תקינות למחיקה.")
        else:
            st.warning("אין משימות תקינות למחיקה.")

    with tab4:
        st.header("סיכום")
    
        summary_data = data.copy()
        summary_data.sort_values(by=["ניקוד", "מספר משימות"], ascending=False, inplace=True)
        summary_data.reset_index(drop=True, inplace=True)
    
        st.subheader("טבלת סיכום חיילים")
        display_styled_table(summary_data)
    
    # הוספת שורה קטנה בתחתית האפליקציה
    st.markdown("""
    <hr>
    <div style='text-align: center; color: gray; font-size: 0.8em;'>
        פותח ע"י טל קמפליס - 2024
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()