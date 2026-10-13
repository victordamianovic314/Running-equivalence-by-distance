import math
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(
    page_title="Dynamic Pacing Decay Predictor", page_icon="🏃‍♂️", layout="wide"
)

# --- Helper Functions ---
def hhmmss_to_seconds(time_str):
  try:
    parts = list(map(int, time_str.replace(" ", "").split(":")))
    if len(parts) == 3:
      return parts[0] * 3600 + parts[1] * 60 + parts[2]
    elif len(parts) == 2:
      return parts[0] * 60 + parts[1]
    return float(time_str)
  except:
    return None


def seconds_to_hhmmss(seconds):
  seconds = round(seconds)
  hours, minutes, secs = (
      seconds // 3600,
      (seconds % 3600) // 60,
      seconds % 60,
  )
  if hours > 0:
    return f"{hours}h {minutes:02d}m {secs:02d}s"
  return f"{minutes}m {secs:02d}s"


# --- App Header ---
st.title("🏃‍♂️ Fluid Sliding-Scale Race Predictor")
st.write(
    "A professional performance model powered by your variable pace-decay"
    " framework."
)
st.markdown("---")

# --- Sidebar Inputs ---
st.sidebar.header("⚙️ Configuration")
mode = st.sidebar.radio(
    "Calculator Precision Mode:", ["2 Baseline PBs", "3 Baseline PBs (More Precise)"]
)

st.sidebar.markdown("---")
st.sidebar.header("🎯 Target Distance")
target_distance = st.sidebar.number_input(
    "Desired Target Distance (meters)",
    min_value=1500,
    max_value=42195,
    value=10000,
    step=100,
)

st.sidebar.markdown("---")
st.sidebar.header("📋 Baseline Performances")

# PB 1 Inputs
st.sidebar.subheader("Baseline 1 (Short)")
d1 = st.sidebar.number_input(
    "Distance 1 (meters)", min_value=100, value=3000, step=100, key="d1"
)
t1_in = st.sidebar.text_input("Time 1 (H:MM:SS or MM:SS)", value="7:26", key="t1")

# PB 2 Inputs
st.sidebar.subheader("Baseline 2 (Mid)")
d2 = st.sidebar.number_input(
    "Distance 2 (meters)", min_value=int(d1 + 1), value=5000, step=100, key="d2"
)
t2_in = st.sidebar.text_input("Time 2 (H:MM:SS or MM:SS)", value="12:41", key="t2")

if mode == "3 Baseline PBs (More Precise)":
  st.sidebar.subheader("Baseline 3 (Long)")
  d3 = st.sidebar.number_input(
      "Distance 3 (meters)",
      min_value=int(d2 + 1),
      value=42195,
      step=100,
      key="d3",
  )
  t3_in = st.sidebar.text_input(
      "Time 3 (H:MM:SS or MM:SS)", value="2:00:28", key="t3"
  )

  st.sidebar.markdown("---")
  scale_type = st.sidebar.radio(
      "Fatigue Shift Framework:",
      [
          "Logarithmic Scale (Proportional steps)",
          "Linear Scale (Meter-by-meter steps)",
      ],
  )
else:
  d3, t3_in, scale_type = None, None, None

st.sidebar.markdown("---")
pace_unit = st.sidebar.radio(
    "Pace Graph Units:", ["Minutes per KM", "Minutes per Mile"]
)

# --- Main Page Execution ---
t1, t2 = hhmmss_to_seconds(t1_in), hhmmss_to_seconds(t2_in)
t3 = hhmmss_to_seconds(t3_in) if mode == "3 Baseline PBs (More Precise)" else None

valid_inputs = t1 and t2 and (mode == "2 Baseline PBs" or t3)

if valid_inputs:

  # Prediction Engine Function
  def engine(target_d):
    df_short = t2 / (t1 * (d2 / d1))

    if mode == "2 Baseline PBs":
      decaying_factor = df_short
    else:
      df_long = t3 / (t2 * (d3 / d2))

      # Map distances to linear or log scale for sliding shift
      if scale_type == "Logarithmic Scale (Proportional steps)":
        s1, s2, s3, s_new = (
            math.log(d1),
            math.log(d2),
            math.log(d3),
            math.log(target_d),
        )
      else:
        s1, s2, s3, s_new = float(d1), float(d2), float(d3), float(target_d)

      # Linearly interpolate decaying factor base between interval midpoints
      mid_short = (s1 + s2) / 2
      mid_long = (s2 + s3) / 2
      slope = (df_long - df_short) / (mid_long - mid_short)

      decaying_factor = df_short + slope * (s_new - mid_short)
      decaying_factor = max(0.90, min(decaying_factor, 1.30))  # Safety bounding

    # Execute mathematical formula
    exponent = math.log(target_d / d1) / math.log(d2 / d1)
    linear_compensation = (target_d / d1) * t1
    t_predicted = linear_compensation * math.pow(decaying_factor, exponent)

    return t_predicted, decaying_factor

  # Run primary prediction for desired target distance
  pred_seconds, final_decay = engine(target_distance)

  # Display Results
  st.success(
      f"### Predicted Performance for {target_distance:,.0f}m:"
      f" **{seconds_to_hhmmss(pred_seconds)}**"
  )

  if mode == "2 Baseline PBs":
    st.info(f"### Decaying Factor Constant: **{final_decay:.4f}**")
  else:
    st.info(
        f"### Variable Decaying Factor at Target Distance:"
        f" **{final_decay:.4f}**"
    )

  # --- Charts Section Layout ---
  st.markdown("---")
  col1, col2 = st.columns(2)

  test_distances = list(range(1500, 42195 + 1, 250))
  if 42195 not in test_distances:
    test_distances.append(42195)

  plot_rows = []
  for td in test_distances:
    t_sec, df_val = engine(td)
    pm = 1000 if pace_unit == "Minutes per KM" else 1609.34
    pace_val = (t_sec / td) * pm / 60
    plot_rows.append({"Distance": td, "Pace": pace_val, "Decay_Factor": df_val})

  df_plot = pd.DataFrame(plot_rows)

  with col1:
    st.subheader("📈 Performance Pace Curve (1,500m to Marathon)")
    fig_pace = go.Figure()
    fig_pace.add_trace(
        go.Scatter(
            x=df_plot["Distance"],
            y=df_plot["Pace"],
            name="Model Performance Curve",
            line=dict(color="#1f77b4", width=3),
        )
    )

    current_pm = 1000 if pace_unit == "Minutes per KM" else 1609.34
    current_pace = (pred_seconds / target_distance) * current_pm / 60
    fig_pace.add_trace(
        go.Scatter(
            x=[target_distance],
            y=[current_pace],
            mode="markers",
            name="Selected Target",
            marker=dict(color="gold", size=14, symbol="circle"),
        )
    )

    fig_pace.update_layout(
        xaxis_title="Distance (Meters)",
        yaxis_title=f"Pace ({pace_unit})",
        hovermode="x unified",
    )
    st.plotly_chart(fig_pace, use_container_width=True)

  with col2:
    st.subheader("📊 Pacing Decay Factor Profile")
    fig_k = go.Figure()
    fig_k.add_trace(
        go.Scatter(
            x=df_plot["Distance"],
            y=df_plot["Decay_Factor"],
            name="Decaying Factor Value",
            line=dict(color="#d62728", width=3),
        )
    )
    fig_k.add_trace(
        go.Scatter(
            x=[target_distance],
            y=[final_decay],
            mode="markers",
            name="Selected Target Decay",
            marker=dict(color="gold", size=14, symbol="circle"),
        )
    )

    fig_k.update_layout(
        xaxis_title="Distance (Meters)",
        yaxis_title="Decaying Factor Base (Pace Ratio)",
        hovermode="x unified",
    )
    st.plotly_chart(fig_k, use_container_width=True)

else:
  st.warning(
      "⚠️ Please fill out all necessary historical PR times in the sidebar to"
      " populate the performance visualizations."
  )

# --- Methodology & Formula Block (Moved to Bottom) ---
st.markdown("---")
st.subheader("📐 Methodology & Mathematical Framework")

col_desc1, col_desc2 = st.columns(2)

with col_desc1:
  st.write(
      "This platform computes time predictions entirely using an independent"
      " pace-decay framework:"
  )
  st.latex(
      r"T_{\text{new}} = \left(\frac{D_{\text{new}}}{D_1} \times T_1\right)"
      r" \times (\text{Decaying"
      r" Factor})^{\frac{\log(D_{\text{new}}/D_1)}{\log(D_2/D_1)}}"
  )
  st.write("Where the baseline **Decaying Factor** is calculated as:")
  st.latex(r"\text{Decaying Factor} = \frac{T_2}{T_1 \times \frac{D_2}{D_1}}")

with col_desc2:
  st.write(
      "Traditional athletic prediction models use a flat population constant"
      " which assumes every human being slows down at the exact same"
      " exponential rate across all racing metrics. By leveraging distinct"
      " historical marks, this model isolates a true trend line of individual"
      " endurance variance, applying a continuously changing decay factor"
      " specifically fine-tuned to the physiological demands of your target"
      " distance."
  )