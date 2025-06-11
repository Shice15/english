import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="做题平台", layout="wide")


@st.cache_data
def load_data(sheet_name):
    file_path = "test.xlsx"  # 请替换成你的 Excel 路径
    df = pd.read_excel(file_path, sheet_name=sheet_name)
    return df


def preprocess_question_text(text):
    """预处理题干，替换空白为下划线占位符并分离选项"""
    # 去掉开头数字编号
    text = re.sub(r"^\d+\.", "", text).strip()

    # 分离题干和选项
    pattern = r'([A-D])\. '
    match = re.search(pattern, text)
    if match:
        question_part = text[:match.start()].strip()
        options_part = text[match.start():]
        return question_part, options_part
    return text, ""


def parse_options(options_text):
    """解析选项文本为列表，确保有A-D四个选项"""
    # 提取所有选项
    pattern = r'([A-D])\.([^\nA-D]*)'
    matches = re.findall(pattern, options_text)

    # 确保有A-D四个选项
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
    """渲染题干下划线样式"""
    return text.replace("____",
                        "<u style='text-decoration: none; border-bottom: 2px solid black; display: inline-block; width: 80px; height: 24px; line-height: 24px;'>____</u>")


if 'question_index' not in st.session_state:
    st.session_state.question_index = 0
    st.session_state.answers = {}

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

df = load_data(sheet_mapping[question_type])
total_questions = len(df)

# 题型切换重置状态
if 'last_type' not in st.session_state or st.session_state.last_type != question_type:
    st.session_state.question_index = 0
    st.session_state.last_type = question_type
    st.session_state.answers = {}

idx = st.session_state.question_index
st.header(f"{question_type}（第 {idx + 1} 题 / 共 {total_questions} 题）")

if idx < total_questions:
    row = df.iloc[idx]
    raw_text = row['题目']

    # 分离题干和选项
    question_text, options_text = preprocess_question_text(raw_text)
    options = parse_options(options_text)

    # 渲染题干HTML
    question_html = render_question_html(question_text)
    st.markdown(f"**题目 {idx + 1}:**<br>{question_html}", unsafe_allow_html=True)

    # 针对翻译题使用文本输入框
    if question_type == "翻译题":
        user_answer = st.text_area("请输入你的翻译", key=f"text_answer_{idx}", height=100)
        st.session_state.answers[idx] = user_answer
    else:
        # 其他题型显示选项按钮
        default_answer = st.session_state.answers.get(idx, None)
        selected_option = st.radio(
            "请选择答案:",
            options,
            index=options.index(default_answer) if default_answer in options else 0,
            key=f"radio_{idx}"
        )
        if selected_option:
            st.session_state.answers[idx] = selected_option

    # 非翻译题显示答案组件
    if question_type != "翻译题":
        with st.expander("查看答案"):
            st.markdown(f"**正确答案:** {row['答案']}")

    # 解析显示
    with st.expander("查看解析"):
        st.markdown(row['解析'])

    # 导航按钮
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
