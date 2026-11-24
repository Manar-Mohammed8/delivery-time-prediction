import pandas as pd
import streamlit as st

st.set_page_config(page_title="متى يصل طلبي؟", page_icon="🛵")

st.markdown("<style>.block-container {direction: rtl; text-align: right;}</style>",
            unsafe_allow_html=True)


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
        st.success(f"غالباً يصل طلبك خلال {result['low']:.0f} إلى {result['high']:.0f} دقيقة")
        st.caption(f"المتوسط {result['average']} دقيقة، مبني على {result['orders']} طلب مشابه")