import pandas as pd
import streamlit as st
import altair as alt

st.set_page_config(page_title="متى يصل طلبي؟", page_icon="🛵")

st.markdown(
    "<style>.block-container, [data-testid='stSidebar'] "
    "{direction: rtl; text-align: right;}</style>",
    unsafe_allow_html=True,
)


@st.cache_data
def load_data():
    return pd.read_csv("data/clean.csv")


df = load_data()

WEATHER = {"مشمس": "Sunny", "غائم": "Cloudy", "ضباب": "Fog",
           "عاصف": "Stormy", "رياح": "Windy", "عواصف رملية": "Sandstorms"}
TRAFFIC = {"خفيف": "Low", "متوسط": "Medium", "عالي": "High", "ازدحام شديد": "Jam"}
DISTANCE = {"أقل من 5 كم": (0, 5), "من 5 إلى 10 كم": (5, 10),
            "من 10 إلى 15 كم": (10, 15), "أكثر من 15 كم": (15, 25)}


def estimate_delivery_time(weather, traffic, distance_range, min_orders=30):
    low_km, high_km = distance_range
    similar = df[
        (df["Weatherconditions"] == weather)
        & (df["Road_traffic_density"] == traffic)
        & (df["Distance_km"] > low_km)
        & (df["Distance_km"] <= high_km)
    ]["Time_taken(min)"]

    if len(similar) < min_orders:
        return None

    return {
        "orders": len(similar),
        "average": round(similar.mean(), 1),
        "low": similar.quantile(0.25),
        "high": similar.quantile(0.75),
    }


x=alt.X("group:N", sort=None, title=xlabel, axis=alt.Axis(labelAngle=0)),    # رسم أعمدة تفاعلية (تظهر القيمة لما تمرّين الماوس على العمود)
    data = values.reset_index()
    data.columns = ["group", "avg"]
    data["group"] = data["group"].astype(str)
    chart = (
        alt.Chart(data)
        .mark_bar()
        .encode(
            x=alt.X("group:N", sort=None, title=xlabel),
            y=alt.Y("avg:Q", title="Average delivery time (min)"),
            tooltip=["group", "avg"],
        )
        .properties(title=title)
    )
    st.altair_chart(chart, use_container_width=True)


def highest_lowest(values):
    # جملة تلخص أعلى وأقل متوسط في الرسمة (إذا فيه أكثر من عمود)
    if len(values) >= 2:
        st.write(f"الأعلى: {values.idxmax()} ({values.max()} دقيقة)، "
                 f"والأقل: {values.idxmin()} ({values.min()} دقيقة).")


# ---------- تقدير وقت الوصول ----------
st.title("🛵 متى يصل طلبي؟")
st.write("اختر ظروف التوصيل، وبنقدّر لك وقت الوصول من طلبات مشابهة سابقة.")

weather_label = st.selectbox("حالة الطقس", list(WEATHER.keys()))
traffic_label = st.selectbox("الازدحام المروري", list(TRAFFIC.keys()))
distance_label = st.selectbox("المسافة بين المطعم وموقعك", list(DISTANCE.keys()))

if st.button("قدّر وقت الوصول"):
    result = estimate_delivery_time(
        WEATHER[weather_label], TRAFFIC[traffic_label], DISTANCE[distance_label]
    )
    if result is None:
        st.warning("ما فيه طلبات مشابهة كافية لهذي الظروف، جرّب تغيّر أحد الخيارات.")
    else:
        st.success(f"نصف الطلبات المشابهة وصلت خلال {result['low']:.0f} إلى {result['high']:.0f} دقيقة")
        st.caption(f"المتوسط {result['average']} دقيقة، مبني على {result['orders']} طلب مشابه")


# ---------- فلاتر الاكتشافات ----------
st.sidebar.header("فلاتر الاكتشافات")
st.sidebar.caption("تؤثر على قسم الاكتشافات فقط، وما تؤثر على تقدير وقت الوصول.")

weather_pick = st.sidebar.multiselect("حالة الطقس", list(WEATHER.keys()),
                                      default=list(WEATHER.keys()))
traffic_pick = st.sidebar.multiselect("الازدحام المروري", list(TRAFFIC.keys()),
                                      default=list(TRAFFIC.keys()))
distance_pick = st.sidebar.multiselect("المسافة", list(DISTANCE.keys()),
                                       default=list(DISTANCE.keys()))

# نطبق الفلتر فقط إذا المستخدم قلّل الخيارات، عشان الوضع الافتراضي يعرض كل الطلبات
fdf = df
if len(weather_pick) < len(WEATHER):
    fdf = fdf[fdf["Weatherconditions"].isin([WEATHER[w] for w in weather_pick])]
if len(traffic_pick) < len(TRAFFIC):
    fdf = fdf[fdf["Road_traffic_density"].isin([TRAFFIC[t] for t in traffic_pick])]
if len(distance_pick) < len(DISTANCE):
    in_range = pd.Series(False, index=fdf.index)
    for label in distance_pick:
        low_km, high_km = DISTANCE[label]
        in_range = in_range | ((fdf["Distance_km"] > low_km) & (fdf["Distance_km"] <= high_km))
    fdf = fdf[in_range]

# ---------- الاكتشافات ----------
st.divider()
st.header("الاكتشافات من البيانات")

if fdf.empty:
    st.warning("ما فيه طلبات تطابق هذي الفلاتر، جرّب تختار خيارات أكثر.")
    st.stop()

st.caption(f"متوسط وقت التوصيل (دقيقة) حسب كل عامل، من {len(fdf):,} طلب.")

col1, col2, col3 = st.columns(3)
col1.metric("عدد الطلبات", f"{len(fdf):,}")
col2.metric("متوسط وقت التوصيل", f"{fdf['Time_taken(min)'].mean():.1f} دقيقة")
col3.metric("أبطأ طلب", f"{fdf['Time_taken(min)'].max()} دقيقة")

traffic_order = ["Low", "Medium", "High", "Jam"]
traffic_avg = (fdf[fdf["Road_traffic_density"].isin(traffic_order)]
               .groupby("Road_traffic_density")["Time_taken(min)"]
               .mean().reindex(traffic_order).dropna().round(1))
draw_bar(traffic_avg, "Average delivery time by traffic density", "Traffic density")
highest_lowest(traffic_avg)

weather_order = ["Sunny", "Windy", "Cloudy", "Fog", "Stormy", "Sandstorms"]
weather_avg = (fdf[fdf["Weatherconditions"].isin(weather_order)]
               .groupby("Weatherconditions")["Time_taken(min)"]
               .mean().reindex(weather_order).dropna().round(1))
draw_bar(weather_avg, "Average delivery time by weather condition", "Weather condition")
highest_lowest(weather_avg)

dist_bins = [0, 5, 10, 15, 100]
dist_labels = ["<5 km", "5-10 km", "10-15 km", ">15 km"]
dist_group = pd.cut(fdf["Distance_km"], bins=dist_bins, labels=dist_labels)
dist_avg = fdf.groupby(dist_group, observed=True)["Time_taken(min)"].mean().round(1)
draw_bar(dist_avg, "Average delivery time by distance", "Distance group")
highest_lowest(dist_avg)

# ---------- الخلاصة (على كل البيانات، ما تتأثر بالفلاتر) ----------
st.divider()
st.header("الخلاصة والتوصيات")
st.caption("الأرقام هنا من كل البيانات (45,593 طلب)، وما تتغير بالفلاتر.")
st.markdown("""
| الاكتشاف | الرقم | التوصية للعميل |
| :--- | :--- | :--- |
| الزحمة ترفع وقت التوصيل | من 21.3 دقيقة (Low) إلى 31.2 دقيقة (Jam)، والفرق 9.9 دقيقة | إذا صار فيه زحمة شديدة (Jam) الأفضل التطبيق يعرض وقت متوقع أطول للعميل، مع تنبيه أن الزحمة ممكن تسبب تأخير قريب من 10 دقائق مقارنة بالزحمة الخفيفة |
| الجو غير المشمس يبطئ التوصيل | من 21.9 دقيقة (Sunny) إلى 28.9 دقيقة (Cloudy و Fog)، والفرق 7.0 دقائق | الأفضل ندخل حالة الطقس في حساب الوقت المتوقع، ونزود التقدير كم دقيقة في Cloudy و Fog بدل ما نستخدم نفس تقدير الجو المشمس |
| المسافة تزيد الوقت لحد فئة 10 إلى 15 كم تقريباً | من 22.2 دقيقة (أقل من 5 كم) إلى 29.8 دقيقة (من 10 إلى 15 كم)، وبعدين يثبت تقريباً (29.9 لأكثر من 15 كم) | المفروض الأداة تعتمد على المسافة في حساب وقت التوصيل، بس ما نفترض زيادة كبيرة بعد 15 كم لأن البيانات بينت أن المتوسط يثبت تقريباً بعد هذي النقطة |
""")
