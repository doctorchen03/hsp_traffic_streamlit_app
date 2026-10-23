import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# ==========================================
# 1. 頁面基本配置 (Streamlit Page Config)
# ==========================================
st.set_page_config(
    page_title="新竹科學園區 (竹科) 晨尖峰車流熱力與政企協商決策系統",
    page_icon="🚘",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自訂樣式美化
st.markdown("""
<style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 800;
        color: #1A365D;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        font-size: 1.05rem;
        color: #4A5568;
        margin-bottom: 1.2rem;
    }
    .metric-card {
        background-color: #F7FAFC;
        border-radius: 8px;
        padding: 12px;
        border-left: 4px solid #3182CE;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">🚘 新竹科學園區 (竹科) 晨尖峰車流熱力與政企協商決策系統</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">數據驅動跨域治理平台｜結合開放資料（TDX / VD 車輛偵測器）、體感塞車指數 (PTCI) 演算法與 ESG Scope 3 減碳算力引擎，破解竹科數十年交通瓶頸</div>', unsafe_allow_html=True)

# ==========================================
# 2. 側邊欄控制面板 (Sidebar Controls)
# ==========================================
st.sidebar.header("⚙️ 竹科政企協商參數設定")

st.sidebar.markdown("### 🏢 企業與園區規模")
emp_scope = st.sidebar.radio(
    "試算範疇選擇",
    ["單一指標半導體旗艦企業 (如台積電/聯發科/聯電)", "竹科全園區總體推估"],
    index=0
)

if emp_scope == "單一指標半導體旗艦企業 (如台積電/聯發科/聯電)":
    total_emp = st.sidebar.number_input(
        "企業常日班與研發同仁人數",
        min_value=500, max_value=40000, value=12000, step=500,
        help="常日班（R&D、自動化工程、IT、行政管理）為尖峰車流主要來源；產線採四班二輪者已天然避開晨尖峰"
    )
else:
    total_emp = st.sidebar.number_input(
        "竹科全園區總就業人口",
        min_value=50000, max_value=200000, value=165000, step=5000,
        help="竹科從業人員約 16.5 萬至 17 萬人"
    )

flex_ratio = st.sidebar.slider(
    "📊 彈性工時推動參與率 (%)",
    min_value=0, max_value=50, value=30, step=5,
    help="推動「核心工時 10:00–16:00 ✕ 三梯次 (07:30 / 08:30 / 09:30) 分流到勤」之人數佔比"
) / 100.0

st.sidebar.markdown("### 🌱 ESG 通勤運具與行車參數")
car_ratio = st.sidebar.slider(
    "🚗 汽車通勤比例 (%)",
    min_value=0, max_value=100, value=55, step=5,
    help="竹科跨縣市通勤（竹北、新竹市東區、竹東、苗栗）汽車比例高達 50%–60%"
) / 100.0
scooter_ratio = 1.0 - car_ratio
st.sidebar.caption(f"🛵 機車通勤比例自動連動為：**{int(scooter_ratio*100)}%**")

# 預估每人每日平均省時（依據彈性工時參與率動態估算，30% 參與率基準省時 21.0 分鐘）
time_saved = (flex_ratio * 21.0 / 0.30) if flex_ratio > 0 else 0.0
st.sidebar.info(f"⏱️ 避開最尖峰估計單人每日省時：**{time_saved:.1f}** 分鐘")

st.sidebar.markdown("### 🌉 焦點聯外廊道")
corridors = [
    "慈雲路 / 經國大橋 (竹北往竹科)",
    "光復路 / 國1新竹交流道",
    "介壽路 / 金山街生活圈",
    "園區二路 / 新安路匝道",
    "寶山路 / 雙溪交流道 (寶山二期)"
]
selected_corridor = st.sidebar.selectbox("選擇重點檢視廊道", corridors)

# ==========================================
# 3. 數據與模擬計算引擎 (Data & Engine)
# ==========================================
time_slots = [
    "07:00", "07:15", "07:30", "07:45",
    "08:00", "08:15", "08:30", "08:45",
    "09:00", "09:15", "09:30"
]

# 竹科五大關鍵聯外廊道容量與基準 V/C（晨間 07:00–09:30）
corridor_data_map = {
    "慈雲路 / 經國大橋 (竹北往竹科)": {
        "capacity": 6800,
        "base_vc": [0.65, 0.78, 0.95, 1.20, 1.34, 1.38, 1.25, 1.08, 0.85, 0.68, 0.54],
        "free_speed": 60.0
    },
    "光復路 / 國1新竹交流道": {
        "capacity": 6200,
        "base_vc": [0.62, 0.75, 0.92, 1.18, 1.30, 1.35, 1.22, 1.05, 0.82, 0.65, 0.52],
        "free_speed": 50.0
    },
    "介壽路 / 金山街生活圈": {
        "capacity": 4500,
        "base_vc": [0.55, 0.68, 0.85, 1.05, 1.22, 1.26, 1.15, 0.96, 0.75, 0.58, 0.45],
        "free_speed": 50.0
    },
    "園區二路 / 新安路匝道": {
        "capacity": 5800,
        "base_vc": [0.60, 0.72, 0.90, 1.15, 1.28, 1.32, 1.20, 1.00, 0.80, 0.62, 0.50],
        "free_speed": 60.0
    },
    "寶山路 / 雙溪交流道 (寶山二期)": {
        "capacity": 5000,
        "base_vc": [0.52, 0.65, 0.82, 1.02, 1.20, 1.25, 1.12, 0.94, 0.76, 0.58, 0.46],
        "free_speed": 50.0
    }
}

# (A) 車流轉移模型計算
curr_info = corridor_data_map[selected_corridor]
capacity = curr_info["capacity"]
free_speed = curr_info["free_speed"]
base_vc_arr = np.array(curr_info["base_vc"])
base_volume = np.round(base_vc_arr * capacity).astype(int)

# 模擬三分流將 08:00–08:45 最尖峰車流削平轉移至 07:30 與 09:30
shifted_volume = base_volume.copy().astype(float)
peak_indices = [4, 5, 6, 7]  # 08:00 - 08:45
reduction = shifted_volume[peak_indices] * (flex_ratio * 0.68)
shifted_volume[peak_indices] -= reduction
shifted_volume[2] += np.sum(reduction) * 0.50  # 移至 07:30 梯次
shifted_volume[8] += np.sum(reduction) * 0.50  # 移至 09:30 梯次

sim_vc_arr = shifted_volume / capacity
max_vc_before = float(np.max(base_vc_arr))
max_vc_after = float(np.max(sim_vc_arr))
vc_reduction_pct = (max_vc_before - max_vc_after) / max_vc_before * 100.0 if max_vc_before > 0 else 0.0

# (B) 體感塞車指數 (PTCI) 函數
def calculate_ptci(vc_series, free_spd):
    ptci_list = []
    w1, w2, w3 = 0.45, 0.35, 0.20
    alpha, beta = 1.5, 1.2
    occ_crit = 0.25
    
    for idx, vc in enumerate(vc_series):
        # 估計實際車速 (km/h)
        v_act = free_spd * max(0.12, 1.0 - 0.78 * (vc ** 1.3))
        # 估計佔空率 (%)
        occupancy = min(0.50, 0.08 + 0.24 * (vc ** 1.5))
        
        # 速度落差感
        speed_term = max(0.0, 1.0 - (v_act / free_spd)) ** alpha
        # 容量壓迫感
        vc_term = (vc) ** beta
        # 走走停停衝擊波
        occ_term = min(2.0, occupancy / occ_crit)
        
        # 晨尖峰時間壓力加權 (08:00-08:45 打卡生死線 = 1.25)
        if idx in [4, 5, 6, 7]:
            w_time = 1.25
        elif idx in [2, 3]:
            w_time = 1.10
        else:
            w_time = 1.00
            
        raw_ptci = 100.0 * (w1 * speed_term + w2 * vc_term + w3 * occ_term) * w_time
        clamped_ptci = min(100.0, max(0.0, raw_ptci))
        ptci_list.append(round(clamped_ptci, 1))
    return ptci_list

base_ptci = calculate_ptci(base_vc_arr, free_speed)
sim_ptci = calculate_ptci(sim_vc_arr, free_speed)

# (C) ESG Scope 3 減碳算力引擎
part_emp = int(total_emp * flex_ratio)
car_users = int(part_emp * car_ratio)
scooter_users = int(part_emp * scooter_ratio)

CAR_IDLING_EF = 0.025        # kg CO2 / min (汽車怠速)
SCOOTER_IDLING_EF = 0.008    # kg CO2 / min (機車怠速)
CAR_SPEED_EF_DIFF = 0.055    # kg CO2 / km (走走停停低速 vs 順暢巡航排放差)
SCOOTER_SPEED_EF_DIFF = 0.017 # kg CO2 / km
avg_commute_km = 22.0        # 竹科跨區通勤單趟平均里程 (竹北/竹東/苗栗至園區)

daily_car_co2 = (car_users * time_saved * CAR_IDLING_EF) + (car_users * avg_commute_km * CAR_SPEED_EF_DIFF)
daily_scooter_co2 = (scooter_users * time_saved * SCOOTER_IDLING_EF) + (scooter_users * avg_commute_km * SCOOTER_SPEED_EF_DIFF)
daily_total_co2_kg = daily_car_co2 + daily_scooter_co2
annual_co2_tons = (daily_total_co2_kg * 250.0) / 1000.0
equivalent_trees = int((daily_total_co2_kg * 250.0) / 12.0)

# ==========================================
# 4. 頂部關鍵指標卡片 (KPI Summary Cards)
# ==========================================
kpi1, kpi2, kpi3, kpi4 = st.columns(4)

with kpi1:
    st.metric(
        label="晨尖峰最高 V/C 飽和度",
        value=f"{max_vc_after:.2f}",
        delta=f"-{vc_reduction_pct:.1f}% 緩解",
        delta_color="inverse"
    )

with kpi2:
    los_text = "LOS D (接近順暢)" if max_vc_after > 1.3 else ("LOS E (容量邊緣)" if max_vc_after < 1.0 else "LOS F (嚴重壅塞)")
    st.metric(
        label="改善後道路服務水準 (LOS)",
        value=los_text,
        delta=f"原先最高 V/C: {max_vc_before:.2f}"
    )

with kpi3:
    st.metric(
        label="年度 Scope 3 減碳總量",
        value=f"{annual_co2_tons:,.1f} 公噸",
        delta=f"每日減碳 {daily_total_co2_kg:,.1f} kg"
    )

with kpi4:
    st.metric(
        label="等同每年造林吸收量",
        value=f"{equivalent_trees:,} 株樹木",
        delta="綠色通勤 ESG 績效"
    )

st.divider()

# ==========================================
# 5. 主圖表分頁 (Main Analytics Tabs)
# ==========================================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 車流削峰填谷模擬",
    "🔥 五大聯外廊道熱力圖",
    "🧮 體感塞車指數 (PTCI)",
    "🌿 企業 ESG 減碳盤查報告",
    "🏛️ 竹科政企協商 ✕ 100 天落地"
])

# ------------------------------------------
# Tab 1: 車流削峰填谷對比
# ------------------------------------------
with tab1:
    st.subheader(f"📍 【{selected_corridor}】晨尖峰車流時序：現況集中 vs 三分流模擬")
    st.caption("透過企業推動「核心工時 10:00–16:00 ✕ 07:30 / 08:30 / 09:30 三梯次到勤」，將 08:00–08:45 的超飽和車流削平轉移至肩峰時段。")
    
    fig_flow = go.Figure()
    
    # 現況車流
    fig_flow.add_trace(go.Scatter(
        x=time_slots, y=base_volume,
        mode='lines+markers',
        name='現況集中到勤 (無分流)',
        line=dict(color='#E53E3E', width=3.5),
        marker=dict(size=8)
    ))
    
    # 改善後車流
    fig_flow.add_trace(go.Scatter(
        x=time_slots, y=np.round(shifted_volume).astype(int),
        mode='lines+markers',
        name=f'三分流模擬 (參與率 {int(flex_ratio*100)}%)',
        line=dict(color='#319795', width=3.5),
        marker=dict(size=8)
    ))
    
    # 道路容量臨界線
    fig_flow.add_trace(go.Scatter(
        x=time_slots, y=[capacity] * len(time_slots),
        mode='lines',
        name=f'道路最大極限容量 ({capacity:,} 輛/15min)',
        line=dict(color='#4A5568', width=2, dash='dash')
    ))
    
    fig_flow.update_layout(
        xaxis_title="晨間時間區段 (每 15 分鐘)",
        yaxis_title="車流量 (輛 / 15分鐘)",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=20, r=20, t=30, b=20)
    )
    st.plotly_chart(fig_flow, use_container_width=True)
    
    col_stat1, col_stat2, col_stat3 = st.columns(3)
    col_stat1.info(f"🛣️ **道路極限容量**：{capacity:,} 輛 / 15分鐘")
    col_stat2.warning(f"🚨 **現況尖峰最高流量**：{int(np.max(base_volume)):,} 輛（超載 {int(np.max(base_volume)-capacity):,} 輛）")
    col_stat3.success(f"✅ **分流後尖峰最高流量**：{int(np.max(shifted_volume)):,} 輛（削峰降幅 {vc_reduction_pct:.1f}%）")

# ------------------------------------------
# Tab 2: 五大聯外廊道熱力圖
# ------------------------------------------
with tab2:
    st.subheader("🔥 竹科五大進園區聯外廊道 15 分鐘 V/C 飽和度動態矩陣")
    
    # 構建矩陣
    corr_names = list(corridor_data_map.keys())
    matrix_base = np.array([corridor_data_map[c]["base_vc"] for c in corr_names])
    matrix_sim = matrix_base * (1.0 - flex_ratio * 0.28)
    
    heatmap_view = st.radio(
        "切換檢視情境：",
        ["現況未分流 V/C 矩陣", f"推行彈性工時模擬後 V/C 矩陣 (參與率 {int(flex_ratio*100)}%)"],
        horizontal=True
    )
    
    target_matrix = matrix_base if "現況" in heatmap_view else matrix_sim
    
    fig_heat = px.imshow(
        target_matrix,
        labels=dict(x="晨尖峰時間區段", y="關鍵進園區廊道", color="V/C 飽和度"),
        x=time_slots,
        y=corr_names,
        color_continuous_scale="YlOrRd",
        text_auto=".2f",
        zmin=0.4,
        zmax=1.4
    )
    fig_heat.update_layout(margin=dict(l=20, r=20, t=20, b=20))
    st.plotly_chart(fig_heat, use_container_width=True)
    
    st.markdown(r"""
    **💡 熱力圖數據判讀說明：**
    * **$V/C < 0.85$ (黃色/米白)**：道路運作順暢，服務水準 LOS A~B。
    * **$0.85 \le V/C < 1.00$ (橘黃色)**：接近臨界容量，行車微幅延滯，LOS C~D。
    * **$V/C \ge 1.00$ (深橘/紅色)**：超飽和塞車，車流進入強迫流與走走停停衝擊波，LOS E~F。經國大橋與光復路於 08:15–08:30 現況最高達 **1.35–1.38**。
    """)

# ------------------------------------------
# Tab 3: 體感塞車指數 (PTCI)
# ------------------------------------------
with tab3:
    st.subheader("🧮 體感塞車指數 (PTCI, Perceived Traffic Congestion Index)")
    st.caption("傳統 V/C 無法反映半導體工程師在打卡生死線前的心理焦慮。PTCI 綜合速度落差、容量壓迫與走走停停衝擊波，以非線性放大還原真實痛苦體驗。")
    
    st.latex(r"""
    \mathbf{PTCI} = \min\left(100, \; 100 \times \left[ w_1 \left(1 - \frac{v_{\text{act}}}{v_{\text{free}}}\right)^{1.5} + w_2 \left(\frac{V}{C}\right)^{1.2} + w_3 \left(\frac{\text{Occupancy}}{\text{Occ}_{\text{crit}}}\right) \right] \times W_{\text{time}} \right)
    """)
    
    fig_ptci = go.Figure()
    fig_ptci.add_trace(go.Scatter(
        x=time_slots, y=base_ptci,
        mode='lines+markers',
        name='現況 PTCI 體感指數',
        line=dict(color='#805AD5', width=3.5)
    ))
    fig_ptci.add_trace(go.Scatter(
        x=time_slots, y=sim_ptci,
        mode='lines+markers',
        name=f'分流後 PTCI 體感指數 (參與率 {int(flex_ratio*100)}%)',
        line=dict(color='#38A169', width=3.5)
    ))
    
    # 標註極度痛苦警戒線
    fig_ptci.add_shape(
        type="line", x0=time_slots[0], x1=time_slots[-1], y0=85, y1=85,
        line=dict(color="red", width=1.5, dash="dot")
    )
    fig_ptci.add_annotation(
        x=time_slots[1], y=87, text="85分以上：極度痛苦/走走停停停車場 (LOS F)",
        showarrow=False, font=dict(color="red")
    )
    
    fig_ptci.update_layout(
        xaxis_title="時間區段", yaxis_title="PTCI 體感塞車分數 (0–100)",
        yaxis=dict(range=[0, 105]),
        hovermode="x unified"
    )
    st.plotly_chart(fig_ptci, use_container_width=True)
    
    # PTCI 與 LOS/TTI 對照表格
    ptci_mapping = pd.DataFrame({
        "PTCI 分數區間": ["0 – 30 分", "31 – 60 分", "61 – 85 分", "86 – 100 分"],
        "體感描述": ["🟢 輕微/順暢 (一路綠燈暢行)", "🟡 車多緩慢 (偶有減速停等)", "🟠 顯著塞車 (走走停停，焦慮漸增)", "🟣 極度痛苦 (定點停車場，打卡遲到)"],
        "客觀 V/C 範圍": ["V/C < 0.85", "0.85 ≤ V/C < 1.00", "1.00 ≤ V/C < 1.20", "V/C ≥ 1.20 (超飽和)"],
        "服務水準 (LOS)": ["LOS A ~ B", "LOS C ~ D", "LOS E", "LOS F (強迫流)"],
        "旅程時間指數 (TTI)": ["TTI ≈ 1.00", "TTI 1.10 ~ 1.30", "TTI 1.30 ~ 1.50", "TTI ≥ 1.75 (耗時近2倍)"]
    })
    st.table(ptci_mapping)

# ------------------------------------------
# Tab 4: 企業 ESG 範疇三減碳盤查
# ------------------------------------------
with tab4:
    st.subheader("🌿 企業推動彈性工時 ESG Scope 3 (Category 7 員工通勤) 減碳盤查明細")
    st.caption("依據溫室氣體盤查議定書 (GHG Protocol)，避開尖峰低速怠速與走走停停，可直接列為企業年度 ESG 報告書之減碳實績。")
    
    esg_summary_data = {
        "ESG 盤查指標項目": [
            "企業/園區計算基礎人數",
            "彈性分流參與人數",
            "汽車通勤分流人數",
            "機車通勤分流人數",
            "單人每日節省通勤時間",
            "每日汽車減碳貢獻",
            "每日機車減碳貢獻",
            "每日合計溫室氣體減量",
            "年度預估減碳總量 (250 工作日)",
            "相當於年度造林效益"
        ],
        "盤查數值與單位": [
            f"{total_emp:,} 人",
            f"{part_emp:,} 人 ({int(flex_ratio*100)}%)",
            f"{car_users:,} 人 ({int(car_ratio*100)}%)",
            f"{scooter_users:,} 人 ({int(scooter_ratio*100)}%)",
            f"{time_saved:.1f} 分鐘 / 人 / 日",
            f"{daily_car_co2:,.2f} kg CO₂e",
            f"{daily_scooter_co2:,.2f} kg CO₂e",
            f"{daily_total_co2_kg:,.2f} kg CO₂e / 日",
            f"{annual_co2_tons:,.2f} 公噸 CO₂e / 年",
            f"{equivalent_trees:,} 株樹木吸收量 / 年"
        ]
    }
    df_esg = pd.DataFrame(esg_summary_data)
    st.table(df_esg)
    
    csv_bytes = df_esg.to_csv(index=False).encode('utf-8-sig')
    st.download_button(
        label="📥 匯出竹科企業 ESG Scope 3 減碳盤查報告 (CSV)",
        data=csv_bytes,
        file_name="hsp_esg_scope3_commute_reduction_report.csv",
        mime="text/csv"
    )

# ------------------------------------------
# Tab 5: 竹科政企協商 ✕ 100 天落地
# ------------------------------------------
with tab5:
    st.subheader("🏛️ 竹科政企協商公版配套 ✕ 100 天落地里程碑")
    
    st.markdown("### 💡 解決半導體廠「三大營運痛點」的公版管理方案")
    exp1, exp2, exp3 = st.columns(3)
    
    with exp1:
        st.markdown("""
        **1. 跨部門協作與晨會溝通斷層**
        * **公版機制**：強制推行 **「10:00–16:00 核心工時 (Core Hours)」**。
        * **效益**：確保重要實體晨會、跨廠會議與 Daily Standup 集中在 10:00–16:00 進行，早到者下午 4 點後可離席，晚到者 10 點前完成進場，消除協作溝通真空。
        """)
        
    with exp2:
        st.markdown("""
        **2. 產能產值與產線排程顧慮**
        * **公版機制**：產線採「四班二輪/三班輪值」本已避開晨尖峰；彈性工時專注於 **常日班（研發、產品工程、行政、IT）**。
        * **效益**：研發工程師免於在經國橋塞車 1 小時耗盡心力，抵達公司後專注力與研發產出實質提升 10%–15%。
        """)
        
    with exp3:
        st.markdown("""
        **3. 考勤管理與勞基法合規負擔**
        * **公版機制**：導入三梯次固定分流（A組 07:30–16:30、B組 08:30–17:30、C組 09:30–18:30）或非同步刷卡工時系統。
        * **效益**：系統自動檢核滿 8 小時打卡，並由竹科管理局與新竹縣市政府提供公版考勤模版與勞檢免罰輔導期。
        """)
    
    st.divider()
    
    st.markdown("### 🎯 竹科跨域聯防 100 天落地行動時程表 (竹科管理局 ✕ 新竹市 ✕ 新竹縣)")
    st.markdown("""
    * **Day 1–30（數據盤點與儀表板上線｜預算 250 萬）**：
      * 串接交通部 TDX、高公局、新竹市與新竹縣 VD 即時路況 API。
      * 上線竹科即時車流熱力與 PTCI 監測儀表板。
      * 聯合竹科園區公會問卷調查前 100 大科技廠之常日班考勤制度。
    * **Day 31–60（公版核心工時範本 ✕ 首批標竿企業簽約｜預算 500 萬）**：
      * 竹科管理局正式發布「10:00–16:00 核心工時公版範本」。
      * 招募首批 20% 標竿企業（如台積電、聯發科等示範廠）簽署分流倡議。
      * 啟用經國大橋、慈雲路、光復路等幹道尖峰「動態綠廊連鎖 (ITS)」。
    * **Day 61–90（園區直達快線 ✕ 尖峰動態差別費率試辦｜預算 750 萬）**：
      * 加開「竹北高鐵站 / 新竹火車站 直達竹科園區核心」綠能快線專車，尖峰 5–8 分鐘一班。
      * 試辦園區公有及周邊停車場尖峰動態累進費率，並提供高乘載 (HOV 3+) 免費停車。
    * **Day 91–100（首期成果發表會 ✕ 頒發 ESG 綠色通勤標章｜預算 500 萬）**：
      * 召開 100 天治堵成果記者會，公布尖峰 V/C 下降 15%–20% 實測數據。
      * 竹科管理局與縣市政府聯合頒發市府「ESG 綠色通勤認證標章」，提供地價稅/房屋稅抵減誘因。
    """)
