import streamlit as st
import pandas as pd
import numpy_financial as npf
import altair as alt

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Retirement Goal Calculator", page_icon="🟢", layout="wide")

# --- CUSTOM CSS FOR "PIXEL PERFECT" LOOK ---
st.markdown("""
<style>
    /* Force light theme elements */
    .stApp {
        background-color: #fcfcfc;
    }
    
    /* Metrics Cards Styling */
    div[data-testid="stMetric"], div[data-testid="metric-container"] {
        background-color: #ffffff;
        border: 1px solid #eeeeee;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.02);
    }
    
    /* Metrics Text Styling */
    [data-testid="stMetricLabel"] {
        font-size: 0.9rem;
        color: #666666;
        font-weight: 500;
    }
    [data-testid="stMetricValue"] {
        font-size: 1.6rem;
        color: #2e7d32; /* Green */
        font-weight: 700;
    }
    
    /* Chart Container Styling */
    .chart-container {
        background-color: white;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #eeeeee;
        box-shadow: 0 4px 6px rgba(0,0,0,0.02);
        margin-bottom: 20px;
    }
    
    /* Important Notes Box */
    .info-box {
        background-color: #fff8e1; /* Light Yellow */
        border-left: 5px solid #ffb300; /* Amber border */
        padding: 15px;
        border-radius: 5px;
        color: #5d4037;
        font-size: 0.9rem;
        margin-top: 30px;
    }
</style>
""", unsafe_allow_html=True)

# --- HELPER: CURRENCY FORMATTER ---
def format_inr(number):
    if number < 100000:
        return f"₹{number:,.0f}"
    elif number < 10000000:
        return f"₹{number/100000:.2f} L"
    else:
        return f"₹{number/10000000:.2f} Cr"
    
# --- HEADER SECTION ---
st.markdown("""
<div style="display: flex; align-items: center; margin-bottom: 30px;">
    <div style="background-color: #1b5e20; padding: 12px; border-radius: 12px; margin-right: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
        <span style="font-size: 28px; color: white;">🧮</span>
    </div>
    <div>
        <h1 style="margin: 0; font-size: 28px; color: #1b5e20; font-family: sans-serif; font-weight: 700;">Retirement Goal Calculator</h1>
        <p style="margin: 0; color: #757575; font-size: 16px; margin-top: 4px;">Plan your financial freedom with clarity</p>
    </div>
</div>
""", unsafe_allow_html=True)

# --- SIDEBAR INPUTS ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=50)
    st.title("Personal Details")
    
    current_age = st.number_input("Current Age", 20, 80, 31)
    retire_age = st.number_input("Retirement Age", current_age+1, 90, 35)
    life_expectancy = st.number_input("Life Expectancy", retire_age+1, 110, 85)
    
    st.markdown("---")
    st.title("Financial Details")
    monthly_expenses = st.number_input("Monthly Expenses", value=135000, step=5000)
    existing_savings = st.number_input("Existing Savings", value=36000000, step=100000)
    emergency_months = st.slider("Emergency Fund (Months)", 3, 24, 6)
    
    st.markdown("---")
    st.title("Return Assumptions")
    inflation = st.slider("Expected Inflation", 0.0, 15.0, 6.5, 0.1, format="%0.1f%%") / 100
    pre_ret_return = st.slider("Pre-Retirement Return", 0.0, 20.0, 8.0, 0.1, format="%0.1f%%") / 100
    post_ret_return = st.slider("Post-Retirement Return", 0.0, 20.0, 8.0, 0.1, format="%0.1f%%") / 100

# --- CALCULATIONS ---
years_to_grow = retire_age - current_age
retire_duration = life_expectancy - retire_age

# 1. Targets
future_monthly_expenses = npf.fv(inflation, years_to_grow, 0, -monthly_expenses)
real_rate = ((1 + post_ret_return) / (1 + inflation)) - 1
corpus_needed = npf.pv(real_rate/12, retire_duration*12, -future_monthly_expenses, 0, when='begin')
emergency_fund = monthly_expenses * emergency_months

# 2. SIP Calculation
existing_grown = npf.fv(pre_ret_return, years_to_grow, 0, -existing_savings)
shortfall = corpus_needed - existing_grown
if shortfall > 0:
    sip_required = npf.pmt(pre_ret_return/12, years_to_grow*12, 0, -shortfall, when='begin')
else:
    sip_required = 0

# --- DASHBOARD METRICS ---
col1, col2, col3 = st.columns(3)
col1.metric("Retirement Corpus Needed", format_inr(corpus_needed), "Target Goal")
col2.metric("Monthly SIP Required", format_inr(sip_required), "For next " + str(years_to_grow) + " years")
col3.metric("Monthly Expenses @ Retirement", format_inr(future_monthly_expenses), "Inflation Adjusted")

st.markdown("<br>", unsafe_allow_html=True)

col4, col5, col6 = st.columns(3)
col4.metric("Emergency Fund", format_inr(emergency_fund), f"{emergency_months} Months Cover")
col5.metric("Years to Retirement", f"{years_to_grow} Years", "Accumulation Phase")
col6.metric("Retirement Duration", f"{retire_duration} Years", "Distribution Phase")

st.markdown("---")

# --- CHART 1: SIP JOURNEY (Accumulation) ---
st.subheader("Your SIP Journey")
st.caption("Growth of your investments until retirement")

# Data Gen
acc_data = []
curr_bal = existing_savings
invested = existing_savings

for age in range(current_age, retire_age + 1):
    acc_data.append({"Age": age, "Total Value": curr_bal, "Invested": invested})
    if age < retire_age:
        curr_bal = curr_bal * (1 + pre_ret_return) + (sip_required * 12)
        invested += (sip_required * 12)

df_acc = pd.DataFrame(acc_data)

# Altair Chart
base = alt.Chart(df_acc).encode(x=alt.X('Age:O', axis=alt.Axis(labelAngle=0)))
area_val = base.mark_area(color='#a5d6a7', opacity=0.5).encode(y='Total Value')
line_val = base.mark_line(color='#2e7d32').encode(y='Total Value')
line_inv = base.mark_line(color='#ff7043', strokeDash=[5,5]).encode(y='Invested')

c1 = (area_val + line_val + line_inv).properties(height=300).interactive()
st.altair_chart(c1, use_container_width=True)


# --- CHART 2: CORPUS GROWTH TIMELINE (Target vs Actual) ---
# This replicates the middle chart in your screenshot
st.subheader("Corpus Growth Timeline")
st.caption("Path to your retirement goal")

# Add a 'Target Line' just for visualization
df_acc['Target Goal'] = corpus_needed 

base2 = alt.Chart(df_acc).encode(x=alt.X('Age:O'))
line_growth = base2.mark_line(point=True, color='#1b5e20').encode(y='Total Value', tooltip=['Age', 'Total Value'])
line_target = base2.mark_rule(color='#d32f2f', strokeDash=[4, 4]).encode(y='Target Goal')

c2 = (line_growth + line_target).properties(height=250).interactive()
st.altair_chart(c2, use_container_width=True)


# --- CHART 3: POST-RETIREMENT SUSTAINABILITY (Decumulation) ---
# This replicates the bottom chart (Drawdown)
st.subheader("Post-Retirement Sustainability")
st.caption("How your corpus supports your lifestyle until age " + str(life_expectancy))

dec_data = []
retirement_bal = corpus_needed
annual_drawdown = future_monthly_expenses * 12

for age in range(retire_age, life_expectancy + 1):
    dec_data.append({
        "Age": age, 
        "Remaining Corpus": max(0, retirement_bal),
        "Annual Withdrawal": annual_drawdown
    })
    
    # Logic: Grow the remaining corpus, subtract expenses
    growth = retirement_bal * post_ret_return
    retirement_bal = (retirement_bal + growth) - annual_drawdown
    
    # Inflate expenses for next year
    annual_drawdown = annual_drawdown * (1 + inflation)

df_dec = pd.DataFrame(dec_data)

# Combo Chart: Area for Corpus, Bars for Withdrawal
base3 = alt.Chart(df_dec).encode(x=alt.X('Age:O', axis=alt.Axis(labelAngle=0)))

# Corpus Area (Green)
corpus_chart = base3.mark_area(
    color=alt.Gradient(
        gradient='linear',
        stops=[alt.GradientStop(color='#ffffff', offset=0),
               alt.GradientStop(color='#c8e6c9', offset=1)],
        x1=1, x2=1, y1=1, y2=0
    ),
    line={'color':'#2e7d32'}
).encode(y='Remaining Corpus')

# Withdrawal Bar (Orange)
withdraw_chart = base3.mark_bar(color='#ffcc80', opacity=0.8).encode(
    y=alt.Y('Annual Withdrawal', axis=alt.Axis(title='Annual Withdrawal', titleColor='#ef6c00'))
)

c3 = alt.layer(corpus_chart, withdraw_chart).resolve_scale(y='independent').properties(height=350).interactive()
st.altair_chart(c3, use_container_width=True)

# --- IMPORTANT NOTES SECTION ---
st.markdown("""
<div class="info-box">
    <strong>💡 Important Notes</strong>
    <ul>
        <li>These calculations assume consistent returns and inflation rates over decades.</li>
        <li>Consider building the emergency fund (₹8.10 L) before starting your aggressive SIPs.</li>
        <li>Review and adjust your plan annually based on life changes (e.g., Veda's education).</li>
        <li>Actual returns may vary; diversify your investments appropriately.</li>
    </ul>
</div>
""", unsafe_allow_html=True)