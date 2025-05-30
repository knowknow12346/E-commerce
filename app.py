import streamlit as st
import pandas as pd
import openai

# 读取 API Key
openai.api_key = st.secrets["OPENAI_API_KEY"]

st.set_page_config(page_title="AI 品类运营助手", layout="wide")

st.title("🛍️ AI品类运营助手")

uploaded_file = st.file_uploader("请上传你的销售数据文件（CSV或Excel）", type=["csv", "xlsx"])

def generate_copy(product_name, category, reason):
    prompt = f"""
你是一位电商内容运营专家，请为以下商品撰写小红书风格的种草文案：

商品名称：{product_name}
商品类目：{category}
推荐理由：{reason}

要求：
1. 风格真实、有代入感
2. 控制在80-120字
3. 文案结尾带上2个相关标签，如 #精致生活 #小众好物

请输出完整文案：
    """
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.8
    )
    return response.choices[0].message["content"]

if uploaded_file:
    # 读取文件
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    st.subheader("📊 数据预览")
    st.dataframe(df.head())

    # 数据类型清洗
    df['gmv'] = pd.to_numeric(df['gmv'], errors='coerce')
    df['份数'] = pd.to_numeric(df['份数'], errors='coerce')
    df['毛利'] = pd.to_numeric(df['毛利'], errors='coerce')
    df['is_new'] = df['is_new'].fillna("N")

    # 🔥 持续爆款识别
    st.subheader("🔥 持续爆款识别")
    top = df.groupby('商品').agg({'gmv': 'sum', '份数': 'sum'})
    top['爆款指数'] = top['gmv'].rank(pct=True) + top['份数'].rank(pct=True)
    top_result = top.sort_values('爆款指数', ascending=False).head(10)
    st.dataframe(top_result)

    # 🌱 潜力商品推荐
    st.subheader("🌱 潜力商品推荐")
    potential = df[(df['is_new'] == 'Y') & (df['毛利'] >= df['毛利'].median())]
    st.dataframe(potential.sort_values('份数', ascending=False).head(10))

    # ✨ AI生成文案按钮
    if st.button("✨ 一键生成文案"):
        result = []
        for index, row in potential.sort_values('份数', ascending=False).head(10).iterrows():
            try:
                copy = generate_copy(row['商品'], row['一级品类'], "热销 & 高毛利 & 新品")
            except Exception as e:
                copy = f"⚠️ 生成失败：{e}"
            result.append((row['商品'], copy))

        st.subheader("📢 AI文案推荐")
        for name, text in result:
            st.markdown(f"**{name}**\n\n{text}")

