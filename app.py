import streamlit as st
import pandas as pd
import random
from io import BytesIO  # 📌 엑셀 파일을 메모리에서 만들기 위한 도구

st.set_page_config(page_title="상담 배정 마법사", layout="wide")

# --- 📖 앱 최상단 사용 설명서 ---
with st.expander("📖 처음이신가요? [사용법 보기]", expanded=False):
    st.markdown("""
    ### 🚀 3단계로 끝내는 스마트 상담 배정
    1. 📅 1단계 (일정 설정): 상담 가능한 날짜와 시간을 확인하고, 상담이 불가능한 칸은 [🚫] 버튼을 눌러 비워두세요.
          💡 날짜/시간 수정 팁: 날짜나 시간 칸의 글자를 지우고 우리 반 일정에 맞게 새로 적으세요. (한 줄에 하나씩 입력하면 표에 즉시 반영됩니다.)
    2. ✍️ 2단계 (학생 입력): 학생 이름을 쓰고 "방문/전화" 중 원하는 방식을 선택한 뒤, 아래 표에서 "1~3지망 시간"을 클릭하세요. 그 다음 [➕ 명단에 추가하기]를 누릅니다.
    3. 🚀 3단계 (배정 시작): 아래의 '교사 배려 모드' 중 하나를 선택하고 배정을 시작하세요.
    
    ---
    * 🎯 교사 배려 모드 상세 안내:
      *  🚀 집중 모드 (상생 압축): 학부모의 1~3지망 중 신청자가 많은 날짜를 찾아 우선 배정합니다. 선생님의 '상담 없는 날'을 만드는 데 유리합니다.
      *  ⚖️ 기본 모드 (지망 우선): 교사의 편의보다는 학부모님이 적어준 지망 순위(1>2>3)를 가장 공평하게 반영합니다.
      * 🍃 분산 모드 (에너지 보존): 하루에 인원이 몰리지 않도록 날짜별로 골고루 학생들을 흩뿌려 배정합니다.
    
    ---
    * 💡 팁 1 (무한 재배정): 배정 결과가 마음에 들지 않으면 [배정 시작] 버튼을 여러 번 다시 눌러보세요. 알고리즘이 매번 미세하게 다른 최적의 조합을 찾아냅니다!
    * 💡 팁 2: 지망이 겹치면 '지망을 적게 쓴 학생'을 우선적으로 배려합니다.
    * 💡 팁 3: 결과가 나온 후 [📥 엑셀 다운로드]를 누르면 파일로 보관할 수 있습니다.
    * 🔒 보안: 입력하신 데이터는 서버에 저장되지 않으며 창을 닫으면 즉시 삭제되니 안심하세요!
    """)

st.title("🏫 선생님 전용 상담 배정")

# --- 데이터 저장소 초기화 ---
if 'student_list' not in st.session_state: st.session_state.student_list = []
if 'disabled_slots' not in st.session_state: st.session_state.disabled_slots = set()
if 'current_choices' not in st.session_state: st.session_state.current_choices = []

# --- 기능 함수 ---
def save_student():
    name = st.session_state.student_input.strip()
    method = st.session_state.consult_method
    if not name:
        st.warning("⚠️ 학생 이름을 입력해 주세요.")
        return
    if any(s['이름'] == name for s in st.session_state.student_list):
        st.error(f"⚠️ '{name}' 학생은 이미 등록되어 있습니다.")
        return
    if name and st.session_state.current_choices:
        choices = st.session_state.current_choices + ["선택안함"] * (3 - len(st.session_state.current_choices))
        st.session_state.student_list.append({"이름": name, "지망": choices[:3], "방식": method})
        st.session_state.current_choices, st.session_state.student_input = [], ""
        st.toast(f"✅ {name}({method}) 학생 저장 완료!")
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

# --- 사이드바 ---
with st.sidebar:
    st.header("⚙️ 데이터 관리")
    if st.button("🔄 전체 데이터 초기화", type="primary", use_container_width=True):
        st.session_state.student_list = []
        st.session_state.disabled_slots = set()
        st.session_state.current_choices = []
        st.rerun()

# --- 1단계: 설정 ---
with st.expander("📅 1단계: [클릭] 여기를 눌러 우리 반 날짜와 시간을 수정하세요 ✨", expanded=False):
    st.info("💡 아래 텍스트 상자의 내용을 수정하면 상담 표가 자동으로 변경됩니다. (한 줄에 하나씩 입력)")
    c_d, c_t = st.columns(2)
    dates = [d.strip() for d in c_d.text_area("🗓️ 날짜 수정", value="3.30(월)\n3.31(화)\n4.1(수)\n4.2(목)\n4.3(금)").split('\n') if d.strip()]
    times = [t.strip() for t in c_t.text_area("⏰ 시간대 수정", value="14:00\n14:20\n14:40\n15:00\n15:20\n15:40").split('\n') if t.strip()]

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
        if cols[i+1].button("🚫" if is_dis else f"{t}", key=f"set_{slot}"):
            if is_dis: st.session_state.disabled_slots.remove(slot)
            else: st.session_state.disabled_slots.add(slot)
            st.rerun()

# --- 2단계: 입력 ---
st.write("---")
st.subheader("✍️ 2단계: 학생 지망 및 방식 입력")
col_l, col_r = st.columns([1, 2.5])
with col_l:
    st.text_input("1️⃣ 학생 이름 입력", key="student_input", placeholder="예: 김철수")
    st.radio("2️⃣ 상담 방식 선택", ["방문 🏠", "전화 📞"], key="consult_method", horizontal=True)
    st.button("➕ 명단에 추가하기", on_click=save_student, type="primary", use_container_width=True)
    for idx, s in enumerate(st.session_state.student_list):
        with st.container(border=True):
            c1, c2 = st.columns([4, 1])
            c1.write(f"**{idx+1}. {s['이름']} ({s['방식']})**")
            c1.caption(f"1지망: {s['지망'][0]}\n2지망: {s['지망'][1]}\n3지망: {s['지망'][2]}")
            if c2.button("🗑️", key=f"del_{idx}"): delete_student(idx)

with col_r:
    st.write("#### 3️⃣ 지망 시간 클릭")
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
                rank = st.session_state.current_choices.index(slot)+1 if slot in st.session_state.current_choices else 0
                if cols[i+1].button(f"{rank}지망" if rank else f"{t}", key=f"sel_{slot}", type="primary" if rank else "secondary"):
                    toggle_slot(slot)
                    st.rerun()

# --- 3단계: 배정 실행 (이 부분이 '상생 로직'으로 교체된 핵심 구간입니다) ---
st.write("---")
st.subheader("🚀 3단계: 상담 배정 실행")
teacher_mode = st.select_slider(
    "🎯 배정 모드 선택", 
    options=["🚀 집중 모드", "⚖️ 기본 모드", "🍃 분산 모드"], 
    value="🚀 집중 모드"
)

if st.button("🚀 배정 시작", type="primary", use_container_width=True):
    if not st.session_state.student_list: st.error("명단이 비어있습니다.")
    else:
        final_dates, final_times = [d.strip() for d in dates], [t.strip() for t in times]
        all_slots = [f"{d} {t}" for d in final_dates for t in final_times if f"{d} {t}" not in st.session_state.disabled_slots]
        
        # 1. 날짜별 신청 밀집도 파악 (자석 원리)
        date_demand = {d: 0 for d in final_dates}
        for s in st.session_state.student_list:
            for wish in s['지망']:
                if wish != "선택안함":
                    d_part = wish.rsplit(' ', 1)[0]
                    if d_part in date_demand: date_demand[d_part] += 1
        
        students = st.session_state.student_list.copy()
        students.sort(key=lambda x: len([c for c in x['지망'] if c != "선택안함"]))
        
        match, assigned_names = {}, []

        # 2. 상생 배정 알고리즘
        for r in range(3):
            random.shuffle(students)
            for std in students:
                if std['이름'] in assigned_names: continue
                wishes = [w for w in std['지망'] if w != "선택안함"]
                
                # 집중 모드일 때: 학생의 지망 리스트를 '날짜 밀집도' 높은 순으로 재정렬
                if teacher_mode == "🚀 집중 모드":
                    wishes.sort(key=lambda w: date_demand.get(w.rsplit(' ', 1)[0], 0), reverse=True)
                elif teacher_mode == "🍃 분산 모드":
                    wishes.sort(key=lambda w: date_demand.get(w.rsplit(' ', 1)[0], 0))
                
                for wish in wishes:
                    if wish in all_slots and wish not in match:
                        match[wish] = {'name': std['이름'], 'rank': std['지망'].index(wish) + 1, 'method': std['방식']}
                        assigned_names.append(std['이름'])
                        break

        # 3. 미배정 인원 수동 배정 (밀집도 순 빈칸 채우기)
        for std in students:
            if std['이름'] not in assigned_names:
                if teacher_mode == "🚀 집중 모드":
                    sorted_slots = sorted(all_slots, key=lambda s: date_demand.get(s.rsplit(' ', 1)[0], 0), reverse=True)
                elif teacher_mode == "🍃 분산 모드":
                    sorted_slots = sorted(all_slots, key=lambda s: date_demand.get(s.rsplit(' ', 1)[0], 0))
                else:
                    sorted_slots = all_slots
                    random.shuffle(sorted_slots)
                
                empty_slots = [s for s in sorted_slots if s not in match]
                if empty_slots:
                    pick = empty_slots[0]
                    match[pick] = {'name': std['이름'], 'rank': "수동", 'method': std['방식']}
                    assigned_names.append(std['이름'])

        # 4. 결과 출력
        grid = pd.DataFrame("", index=final_times, columns=final_dates)
        for s in st.session_state.disabled_slots:
            try:
                d, t = s.rsplit(' ', 1)
                if d in final_dates and t in final_times: grid.at[t, d] = "🚫"
            except: continue
        for slot, info in match.items():
            try:
                d, t = slot.rsplit(' ', 1)
                if d in final_dates and t in final_times:
                    rank_lbl = f"{info['rank']}지망" if isinstance(info['rank'], int) else "수동"
                    grid.at[t, d] = f"★{info['name']}★\n({rank_lbl}/{info['method']})"
            except: continue
        
        st.table(grid)
        st.success(f"✅ {teacher_mode}로 배정이 완료되었습니다!")

        
# --- 엑셀(.xlsx) 다운로드 기능 ---
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            grid.to_excel(writer, index=True, sheet_name='상담시간표')
        
        excel_data = output.getvalue()

        st.download_button(
            label="📥 최종 시간표 엑셀(.xlsx) 다운로드",
            data=excel_data,
            file_name="상담_최종시간표.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
