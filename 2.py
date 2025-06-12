import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="做题平台", layout="wide")

# =====================
# 通用函数与缓存数据
# =====================
@st.cache_data
def load_data(sheet_name):
    df = pd.read_excel("test.xlsx", sheet_name=sheet_name, engine="openpyxl")
    return df


@st.cache_data
def load_cloze_passages():
    df = pd.read_excel("test.xlsx", sheet_name="wanxing", engine="openpyxl")
    passages = []
    for _, row in df.iterrows():
        raw_text = row["raw_text"]
        try:
            answers = eval(row["answers"])
            if not isinstance(answers, list) or len(answers) != 10:
                answers = [""] * 10
        except:
            answers = [""] * 10
        explanation = row.get("explanation", "（暂无解析）")
        passages.append({
            "raw_text": raw_text,
            "answers": answers,
            "explanation": explanation
        })
    return passages


def preprocess_question_text(text):
    text = re.sub(r"^\d+\.", "", text).strip()
    pattern = r'([A-D])\. '
    match = re.search(pattern, text)
    if match:
        question_part = text[:match.start()].strip()
        options_part = text[match.start():]
        return question_part, options_part
    return text, ""


def parse_options(options_text):
    pattern = r'([A-D])\.([^\nA-D]*)'
    matches = re.findall(pattern, options_text)
    options = []
    for label in ['A', 'B', 'C', 'D']:
        content = ""
        for match in matches:
            if match[0] == label:
                content = match[1].strip()
                break
        options.append(f"{label}. {content}")
    return options


def render_question_html(text):
    return text.replace("____",
                        "<u style='text-decoration: none; border-bottom: 2px solid black; display: inline-block; width: 80px; height: 24px; line-height: 24px;'>____</u>")


# =====================
# 页面状态初始化
# =====================
if 'question_index' not in st.session_state:
    st.session_state.question_index = 0
    st.session_state.answers = {}

if "current_index" not in st.session_state:
    st.session_state.current_index = 0  # 完型题索引

# =====================
# 侧边栏 - 题型选择
# =====================
st.sidebar.title("题型导航")
question_type = st.sidebar.radio(
    "选择题型",
    ("词汇题", "完型题", "阅读题", "翻译题")
)

sheet_mapping = {
    "词汇题": "vocabulary",
    "完型题": "wanxing",
    "阅读题": "reading",
    "翻译题": "translation"
}

# =====================
# 完型填空单独处理
# =====================
if question_type == "完型题":
    # === 完型填空相关 ===
    cloze_passages = load_cloze_passages()
    idx = st.session_state.current_index
    total = len(cloze_passages)
    current = cloze_passages[idx]

    st.title(f"📘 完形填空练习（第 {idx + 1} / {total} 题）")
    st.markdown("### 📄 文章内容")
    st.markdown(current["raw_text"])

    st.markdown("---")
    st.markdown("### ✍️ 请填写每个空（共10个）")
    user_answers = []
    for row in range(2):
        cols = st.columns(5)
        for i in range(5):
            blank_idx = row * 5 + i
            with cols[i]:
                ans = st.text_input(f"（{blank_idx+1}）", key=f"input_{idx}_{blank_idx}", placeholder="填写词")
                user_answers.append(ans.strip())

    if st.button("✅ 提交答案", key=f"submit_{idx}"):
        st.markdown("### 🧾 结果对比")
        correct = current["answers"]
        correct_count = 0
        for i, (u, c) in enumerate(zip(user_answers, correct)):
            is_right = u.lower() == c.lower()
            st.markdown(f"**（{i+1}）** 你的答案：`{u}` | 正确答案：`{c}`" + (" ✅" if is_right else " ❌"))
            if is_right:
                correct_count += 1
        st.success(f"🎉 答对 {correct_count} / 10")

    with st.expander("📖 点击查看参考解析"):
        st.markdown(current["explanation"])

    col_prev, col_next = st.columns([1, 1])
    with col_prev:
        if st.button("⬅️ 上一题", disabled=idx == 0):
            st.session_state.current_index = max(0, idx - 1)
            st.rerun()
    with col_next:
        if st.button("➡️ 下一题", disabled=idx == total - 1):
            st.session_state.current_index = min(total - 1, idx + 1)
            st.rerun()

# =====================
# 其他题型统一处理（词汇、阅读、翻译）
# =====================
else:
    df = load_data(sheet_mapping[question_type])
    total_questions = len(df)

    # 切换题型时重置索引
    if 'last_type' not in st.session_state or st.session_state.last_type != question_type:
        st.session_state.question_index = 0
        st.session_state.last_type = question_type
        st.session_state.answers = {}

    idx = st.session_state.question_index
    st.header(f"{question_type}（第 {idx + 1} 题 / 共 {total_questions} 题）")

    if idx < total_questions:
        row = df.iloc[idx]
        raw_text = row['题目']

        question_text, options_text = preprocess_question_text(raw_text)
        options = parse_options(options_text)
        question_html = render_question_html(question_text)
        st.markdown(f"**题目 {idx + 1}:**<br>{question_html}", unsafe_allow_html=True)

        if question_type == "翻译题":
            user_answer = st.text_area("请输入你的翻译", key=f"text_answer_{idx}", height=100)
            st.session_state.answers[idx] = user_answer
        else:
            default_answer = st.session_state.answers.get(idx, None)
            selected_option = st.radio(
                "请选择答案:",
                options,
                index=options.index(default_answer) if default_answer in options else 0,
                key=f"radio_{idx}"
            )
            if selected_option:
                st.session_state.answers[idx] = selected_option

        if question_type != "翻译题":
            with st.expander("查看答案"):
                st.markdown(f"**正确答案:** {row['答案']}")

        with st.expander("查看解析"):
            st.markdown(row['解析'])

        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            if st.button("上一题", key="prev_btn") and idx > 0:
                st.session_state.question_index -= 1
                st.rerun()
        with col3:
            if st.button("下一题", key="next_btn"):
                if idx + 1 < total_questions:
                    st.session_state.question_index += 1
                    st.rerun()
                else:
                    st.warning("已经是最后一题了。")
    else:
        st.info("没有更多题目，请返回选择其他题型或刷新页面。")
