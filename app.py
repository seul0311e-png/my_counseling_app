import streamlit as st
import pandas as pd
import random

st.set_page_config(page_title="상담 배정 마법사", layout="wide")
st.title("🏫 선생님 전용 상담 배정 (지망 반영)")
st.caption("날짜(가로/열) x 시간(세로/행) 배정 및 지능형 배정 로직 탑재")

# --- 데이터 저장소 초기화 ---
if 'student_list' not in st.session_state: st.session_state.student_list = []
if 'disabled_slots' not in st.session_state: st.session_state.disabled_slots = set()
if 'current_choices' not in st.session_state: st.session_state.current_choices = []

# --- 기능 함수 ---
def save_student():
    name = st.session_state.student_input.strip()
    if not name:
        st.warning("⚠️ 학생 이름을 입력해 주세요.")
        return
    existing_names = [s['이름'] for s in st.session_state.student_list]
    if name in existing_names:
        st.error(f"⚠️ '{name}' 학생은 이미 등록되어 있습니다. 동명이인이라면 '이름A', '이름B'로 구분해 주세요.")
        return
    if name and st.session_state.current_choices:
        choices = st.session_state.current_choices + ["선택안함"] * (3 - len(st.session_state.current_choices))
        st.session_state.student_list.append({"이름": name, "지망": choices[:3]})
        st.session_state.current_choices, st.session_state.student_input = [], ""
        st.toast(f"✅ {name} 학생 저장 완료!")
    else:
        st.warning("⚠️ 지망 시간을 최소 1개 이상 선택해 주세요.")

def delete_student(idx):
    st.session_state.student_list.pop(idx)
    st.rerun()

def toggle_slot(slot):
    if slot in st.session_state.current_choices:
        st.session_state.current_choices.remove(slot)
    elif len(st.session_state.current_choices) < 3:
        st.session_state.current_choices.append(slot)

# --- 사이드바: 데이터 관리 ---
with st.sidebar:
    st.header("⚙️ 데이터 관리")
    if st.button("🔄 전체 데이터 초기화", type="primary", use_container_width=True):
        st.session_state.student_list = []
        st.session_state.disabled_slots = set()
        st.session_state.current_choices = []
        st.rerun()
    st.caption("모든 데이터를 지우고 처음부터 다시 시작합니다.")

# --- 1단계: 날짜 및 시간대 설정 ---
with st.expander("📅 1단계: 날짜 및 시간대 설정", expanded=False):
    c_d, c_t = st.columns(2)
    dates = [d.strip() for d in c_d.text_area("🗓️ 날짜", value="3.30(월)\n3.31(화)\n4.1(수)\n4.2(목)\n4.3(금)").split('\n') if d.strip()]
    times = [t.strip() for t in c_t.text_area("⏰ 시간대", value="14:00\n14:20\n14:40\n15:00\n15:20\n15:40").split('\n') if t.strip()]

# --- 1단계: 불가 시간 설정 ---
st.subheader("🚫 1단계: 상담 불가 시간 체크")
header = st.columns([1.2] + [1]*len(dates))
header[0].write("**시간**")
for i, d in enumerate(dates): header[i+1].write(f"**{d}**")

for t in times:
    cols = st.columns([1.2] + [1]*len(dates))
    cols[0].write(f"**{t}**") 
    for i, d in enumerate(dates):
        slot = f"{d} {t}"
        is_dis = slot in st.session_state.disabled_slots
        btn_lbl = "🚫" if is_dis else f"{t}"
        if cols[i+1].button(btn_lbl, key=f"set_{slot}"):
            if is_dis: st.session_state.disabled_slots.remove(slot)
            else: st.session_state.disabled_slots.add(slot)
            st.rerun()

# --- 2단계: 학생 지망 입력 ---
st.write("---")
st.subheader("✍️ 2단계: 학생 지망 입력")
col_l, col_r = st.columns([1, 2.5])

with col_l:
    st.text_input("1️⃣ 학생 이름 입력", key="student_input", placeholder="예: 김철수")
    st.button("➕ 명단에 추가하기", on_click=save_student, type="primary", use_container_width=True)
    if st.session_state.student_list:
        st.write(f"**현재 명단 ({len(st.session_state.student_list)}명)**")
        for idx, s in enumerate(st.session_state.student_list):
            with st.container(border=True):
                c1, c2 = st.columns([4, 1])
                c1.write(f"**{idx+1}. {s['이름']}**")
                # 📌 요청하신 대로 '1지망:', '2지망:' 형태로 수정했습니다.
                c1.caption(f"1지망: {s['지망'][0]}\n2지망: {s['지망'][1]}\n3지망: {s['지망'][2]}")
                if c2.button("🗑️", key=f"del_{idx}"): delete_student(idx)

with col_r:
    st.write("#### 2️⃣ 지망 시간 클릭")
    h_sel = st.columns([1.2] + [1]*len(dates))
    h_sel[0].write("**시간**")
    for i, d in enumerate(dates): h_sel[i+1].write(f"**{d}**")
    for t in times:
        cols = st.columns([1.2] + [1]*len(dates))
        cols[0].write(f"**{t}**") 
        for i, d in enumerate(dates):
            slot = f"{d} {t}"
            if slot in st.session_state.disabled_slots:
                cols[i+1].button("🚫 불가", key=f"lock_{slot}", disabled=True)
            else:
                if slot in st.session_state.current_choices:
                    rank = st.session_state.current_choices.index(slot) + 1
                    lbl, tp = f"{rank}지망", "primary"
                else: lbl, tp = f"{t}", "secondary"
                cols[i+1].button(lbl, key=f"sel_{slot}", on_click=toggle_slot, args=(slot,), type=tp)

# --- 3단계: 배정 알고리즘 ---
st.write("---")
if st.button("🚀 '양보와 타협' 최적 배정 시작", type="primary", use_container_width=True):
    if not st.session_state.student_list: 
        st.error("명단이 없습니다. 학생을 먼저 추가해 주세요.")
    else:
        # 📌 최신 설정값 정제
        final_dates = [d.strip() for d in dates if d.strip()]
        final_times = [t.strip() for t in times if t.strip()]
        all_slots = [f"{d} {t}" for d in final_dates for t in final_times if f"{d} {t}" not in st.session_state.disabled_slots]
        
        students = st.session_state.student_list.copy()
        # 지망이 적은(간절한) 학생부터 정렬
        students.sort(key=lambda x: len([c for c in x['지망'] if c != "선택안함"]))
        
        match = {}
        for r in range(3):
            random.shuffle(students)
            for std in students:
                if any(m['name'] == std['이름'] for m in match.values()): continue
                wish = std['지망'][r]
                if wish != "선택안함" and wish in all_slots and wish not in match:
                    match[wish] = {'name': std['이름'], 'rank': r + 1}

        assigned = [m['name'] for m in match.values()]
        for std in students:
            if std['이름'] not in assigned:
                empty = [s for s in all_slots if s not in match]
                if empty:
                    pick = random.choice(empty)
                    match[pick] = {'name': std['이름'], 'rank': "수동"}

        st.subheader("🗓️ 최종 상담 시간표")
        grid = pd.DataFrame("", index=final_times, columns=final_dates)
        
        # 안전장치 적용
        for s in st.session_state.disabled_slots:
            try:
                d, t = s.rsplit(' ', 1)
                if d in final_dates and t in final_times:
                    grid.at[t, d] = "🚫 불가"
            except: continue
            
        for slot, info in match.items():
            try:
                d, t = slot.rsplit(' ', 1)
                if d in final_dates and t in final_times:
                    rank_lbl = f"{info['rank']}지망" if isinstance(info['rank'], int) else "수동"
                    grid.at[t, d] = f"★{info['name']}★({rank_lbl})"
            except: continue
        
        st.table(grid)
        st.success("✅ 선생님, 최적의 배정이 완료되었습니다!")

# 10. 엑셀(CSV) 다운로드 기능 (한글 깨짐 방지 처리)
        csv_data = grid.to_csv().encode('utf-8-sig')
        st.download_button(
            label="📥 최종 시간표 엑셀(CSV) 다운로드",
            data=csv_data,
            file_name="상담_최종시간표.csv",
            mime="text/csv"
        )
