import pandas as pd
import streamlit as st
from ortools.sat.python import cp_model
import random
import io
from datetime import datetime, timedelta
import calendar
import plotly.express as px

# --- Parameters you can change ---
YEAR = 2025
MONTH = 9

# --- Generate date range for the month ---
def generate_days(year, month):
    start_date = datetime(year, month, 1)
    # Days in the month:
    if month == 12:
        next_month = datetime(year + 1, 1, 1)
    else:
        next_month = datetime(year, month + 1, 1)
    num_days = (next_month - start_date).days
    days = [(start_date + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(num_days)]
    return days

DAYS = generate_days(YEAR, MONTH)

CHARGE_CANDIDATES = ["Nicole", "Xavier", "Renee", "Sarah"]

# --- Scheduler functions ---
def build_model(prefs, nurses, year, month):
    model = cp_model.CpModel()
    work = {(n, d): model.NewBoolVar(f'{n}_{d}') for n in nurses for d in DAYS}

    start_date = datetime(year, month, 1)
    last_day = datetime(year, month, len(DAYS))

    # Find first Wednesday of the month
    first_wed = start_date
    while first_wed.weekday() != 2:  # 0=Mon, 2=Wed
        first_wed += timedelta(days=1)

    # Assign Xavier to days before first Wednesday
    pre_block_days = []
    day = start_date
    while day < first_wed:
        pre_block_days.append(day.strftime('%Y-%m-%d'))
        day += timedelta(days=1)

    if "Xavier" in nurses:
        for d in pre_block_days:
            model.Add(work[("Xavier", d)] == 1)
    if "Nicole" in nurses:
        for d in pre_block_days:
            model.Add(work[("Nicole", d)] == 0)

    # Alternating 6-day blocks from first Wednesday
    block_length = 7
    total_days = (last_day - first_wed).days + 1
    for week in range(0, total_days, block_length):
        block_start = first_wed + timedelta(days=week)
        block_days = []

        for offset in [0, 1, 2, 4, 5, 6]:  # Wed-Fri, Sun-Tue
            day = block_start + timedelta(days=offset)
            if start_date <= day <= last_day:
                block_days.append(day.strftime('%Y-%m-%d'))

        assign_nicole = (week // block_length) % 2 == 0
        primary = "Nicole" if assign_nicole else "Xavier"
        secondary = "Xavier" if assign_nicole else "Nicole"

        if primary in nurses:
            for d in block_days:
                model.Add(work[(primary, d)] == 1)
        if secondary in nurses:
            for d in block_days:
                model.Add(work[(secondary, d)] == 0)

    # Neither Nicole nor Xavier work Saturdays
    for d in DAYS:
        if datetime.strptime(d, "%Y-%m-%d").weekday() == 5:
            for n in ["Nicole", "Xavier"]:
                if n in nurses:
                    model.Add(work[(n, d)] == 0)

    # Other nurses max 3 shifts/week
    for n in nurses:
        if n not in ["Nicole", "Xavier"]:
            for week_start in range(0, len(DAYS), 7):
                week_days = DAYS[week_start:week_start + 7]
                model.Add(sum(work[(n, d)] for d in week_days) <= 3)

    # Minimum 10 nurses/day
    min_nurses_per_day = min(10, len(nurses))
    for d in DAYS:
        model.Add(sum(work[(n, d)] for n in nurses) >= min_nurses_per_day)

    # Maximize preference satisfaction
    model.Maximize(sum(work[(n, d)] * prefs.loc[n, d] for n in nurses for d in DAYS))

    return model, work

def solve_schedule(model, work, nurses):
    solver = cp_model.CpSolver()
    status = solver.Solve(model)
    if status not in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
        return None, None, status

    schedule = pd.DataFrame("", index=nurses, columns=DAYS)
    charge_nurse_row = pd.Series("", index=DAYS)

    for d in DAYS:
        working_nurses = [n for n in nurses if solver.Value(work[(n, d)]) == 1]
        for n in working_nurses:
            schedule.loc[n, d] = "W"

        weekday = datetime.strptime(d, "%Y-%m-%d").weekday()
        if "Nicole" in working_nurses and weekday != 5:
            charge = "Nicole"
        elif "Xavier" in working_nurses and weekday != 5:
            charge = "Xavier"
        elif weekday == 5:  # Saturday
            charge = next((n for n in ["Renee", "Sarah"] if n in working_nurses), None)
            if not charge and working_nurses:
                charge = random.choice(working_nurses)
        else:
            charge = next((n for n in CHARGE_CANDIDATES if n in working_nurses), None)
            if not charge and working_nurses:
                charge = random.choice(working_nurses)

        charge_nurse_row[d] = f"{charge} ⚡" if charge else "—"

    return schedule, charge_nurse_row, status

def download_excel(schedule, charge_nurse_row, nurses):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        schedule.to_excel(writer, sheet_name="Work Schedule", index=True)
        charge_nurse_row.to_frame(name="Charge Nurse").T.to_excel(writer, sheet_name="Charge Nurses", index=True)

        workbook = writer.book
        worksheet = writer.sheets["Work Schedule"]
        highlight_format = workbook.add_format({
            'bg_color': '#FFF200',
            'bold': True,
            'border': 1
        })

        for col_idx, date_str in enumerate(DAYS, start=1):
            charge_clean = charge_nurse_row[date_str].replace(" ⚡", "")
            for row_idx, nurse in enumerate(nurses, start=1):
                if schedule.loc[nurse, date_str] == "W":
                    if nurse == charge_clean:
                        worksheet.write(row_idx, col_idx, "W", highlight_format)
                    else:
                        worksheet.write(row_idx, col_idx, "W")

    output.seek(0)
    return output

def render_heatmap(schedule):
    st.write("### 📊 Daily Coverage Heatmap")
    nurse_counts = {d: sum(schedule.loc[n, d] == "W" for n in schedule.index) for d in DAYS}
    df = pd.DataFrame({
        "date": pd.to_datetime(list(nurse_counts.keys())),
        "nurses": list(nurse_counts.values())
    })
    fig = px.density_heatmap(
        df, x="date", y=[""] * len(df), z="nurses",
        color_continuous_scale="YlGnBu", nbinsx=30,
        labels={"nurses": "Nurses on Duty", "date": "Date"}
    )
    fig.update_layout(yaxis_visible=False, height=150, title="Nurses Working per Day")
    st.plotly_chart(fig, use_container_width=True)

def render_schedule_calendar(schedule_df):
    cal = calendar.Calendar(calendar.SUNDAY)
    month_days = cal.monthdayscalendar(YEAR, MONTH)
    nurse_counts = {day: int(schedule_df[day].eq("W").sum()) for day in schedule_df.columns}

    st.markdown("### 🗓️ Reference Calendar with Nurse Counts")
    cal_md = "| Su | Mo | Tu | We | Th | Fr | Sa |\n"
    cal_md += "|----|----|----|----|----|----|----|\n"

    for week in month_days:
        row = ""
        for day in week:
            if day == 0:
                row += "|    "
            else:
                date_str = f"{YEAR}-{MONTH:02d}-{day:02d}"
                count = nurse_counts.get(date_str, 0)
                row += f"| {day:2d} ({count})"
        row += "|\n"
        cal_md += row

    st.markdown(cal_md)

# --- Streamlit UI ---
st.title("🩺 Nurse Shift Scheduler")

uploaded_file = st.file_uploader("📤 Upload nurse preferences CSV", type=["csv"])

if uploaded_file:
    prefs = pd.read_csv(uploaded_file, index_col=0)
    # Align prefs columns with DAYS (dynamic for any month)
    prefs.columns = DAYS[:prefs.shape[1]]
    nurses = prefs.index.tolist()

    st.write("### ✅ Preferences Uploaded")
    st.dataframe(prefs)

    if st.button("🚀 Generate Schedule"):
        model, work = build_model(prefs, nurses, YEAR, MONTH)
        schedule, charge_nurse_row, status = solve_schedule(model, work, nurses)

        if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
            st.success("✅ Schedule generated successfully!")

            st.write("### 📋 Work Schedule")
            st.dataframe(schedule)

            st.write("### ⚡ Charge Nurse Assignments")
            st.dataframe(charge_nurse_row.to_frame(name="Charge Nurse").T)

            render_heatmap(schedule)
            render_schedule_calendar(schedule)

            excel_data = download_excel(schedule, charge_nurse_row, nurses)
            st.download_button(
                label="📥 Download Full Schedule (Excel)",
                data=excel_data,
                file_name="nurse_schedule.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.error("❌ No feasible schedule found.")
