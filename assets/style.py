"""
SolarPro Financial Modelling — CSS (loaded as Python string)
Injected via st.markdown(unsafe_allow_html=True)
"""

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap');

:root {
  --primary:#00D4AA; --primary-glow:#00D4AA33; --secondary:#6C63FF;
  --bg-base:#0A0E1A; --bg-card:#141828; --bg-card2:#1A2035;
  --border:#252D45; --text-primary:#E8EAF0; --text-secondary:#94A3B8; --text-muted:#4A5568;
  --success:#10B981; --warning:#F59E0B; --danger:#EF4444;
  --gradient-2:linear-gradient(135deg,#00D4AA 0%,#6C63FF 100%);
  --font-main:'Inter',-apple-system,sans-serif; --font-mono:'JetBrains Mono',monospace;
  --radius:12px; --radius-sm:8px; --shadow:0 4px 24px rgba(0,0,0,.4);
  --shadow-glow:0 0 32px rgba(0,212,170,.12);
}
*{box-sizing:border-box}
html,body,[data-testid="stAppViewContainer"]{font-family:var(--font-main)!important;background:var(--bg-base)!important;color:var(--text-primary)!important}
[data-testid="stSidebar"]{background:var(--bg-card)!important;border-right:1px solid var(--border)!important}

/* Metric Cards */
.metric-card{background:var(--bg-card);border:1px solid var(--border);border-radius:var(--radius);padding:20px 24px;position:relative;overflow:hidden;transition:transform .2s,box-shadow .2s}
.metric-card:hover{transform:translateY(-2px);box-shadow:var(--shadow-glow)}
.metric-card::before{content:'';position:absolute;top:0;left:0;right:0;height:3px;background:var(--gradient-2)}
.metric-card .card-label{font-size:11px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:var(--text-secondary);margin-bottom:8px}
.metric-card .card-value{font-size:28px;font-weight:800;color:var(--primary);line-height:1;font-family:var(--font-mono)}
.metric-card .card-delta{font-size:12px;color:var(--text-muted);margin-top:6px}
.metric-card .card-icon{position:absolute;top:16px;right:18px;font-size:28px;opacity:.15}

/* Buttons */
.stButton>button{background:var(--gradient-2)!important;color:#fff!important;border:none!important;border-radius:var(--radius-sm)!important;font-weight:600!important;transition:all .2s!important;padding:8px 20px!important}
.stButton>button:hover{opacity:.9!important;transform:translateY(-1px)!important;box-shadow:0 4px 16px rgba(0,212,170,.3)!important}

/* Tabs */
.stTabs [data-baseweb="tab-list"]{background:var(--bg-card)!important;border-radius:var(--radius)!important;border:1px solid var(--border)!important;padding:4px!important;gap:4px!important}
.stTabs [data-baseweb="tab"]{border-radius:var(--radius-sm)!important;color:var(--text-secondary)!important;font-weight:500!important;transition:all .2s!important}
.stTabs [aria-selected="true"]{background:var(--gradient-2)!important;color:#fff!important}

/* Progress */
.stProgress>div>div>div>div{background:var(--gradient-2)!important;border-radius:4px!important}

/* File uploader */
[data-testid="stFileUploadDropzone"]{border:2px dashed var(--border)!important;border-radius:var(--radius)!important;background:var(--bg-card)!important}
[data-testid="stFileUploadDropzone"]:hover{border-color:var(--primary)!important}

/* Hero */
.hero-banner{background:linear-gradient(135deg,#00D4AA11,#6C63FF11);border:1px solid var(--border);border-radius:16px;padding:32px 36px;margin-bottom:28px;position:relative;overflow:hidden}
.hero-banner h1{font-size:26px;font-weight:800;margin:0 0 8px;background:var(--gradient-2);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}
.hero-banner p{color:var(--text-secondary);margin:0;font-size:14px}

/* Plan Cards */
.plan-card{background:var(--bg-card);border:1px solid var(--border);border-radius:var(--radius);padding:24px;text-align:center;transition:all .2s;position:relative;overflow:hidden}
.plan-card.featured{border-color:var(--primary)!important;box-shadow:var(--shadow-glow)}
.plan-card:hover{transform:translateY(-4px);box-shadow:var(--shadow)}
.plan-price{font-size:36px;font-weight:800;color:var(--primary);font-family:var(--font-mono)}
.plan-label{font-size:13px;font-weight:600;color:var(--text-primary);margin-top:8px}
.plan-sub{font-size:12px;color:var(--text-secondary);margin-top:4px}

/* RTL */
.rtl-layout{direction:rtl!important;text-align:right!important}

/* Badges */
.badge-base{display:inline-block;border-radius:20px;padding:2px 10px;font-size:11px;font-weight:600}
.badge-pending{background:#F59E0B22;color:#F59E0B;border:1px solid #F59E0B44}
.badge-progress{background:#6C63FF22;color:#A5B4FC;border:1px solid #6C63FF44}
.badge-completed{background:#10B98122;color:#34D399;border:1px solid #10B98144}

/* Table */
[data-testid="stDataFrame"]{border-radius:var(--radius)!important;overflow:hidden!important;border:1px solid var(--border)!important}

/* Scrollbar */
::-webkit-scrollbar{width:6px;height:6px}
::-webkit-scrollbar-track{background:var(--bg-base)}
::-webkit-scrollbar-thumb{background:var(--border);border-radius:3px}
::-webkit-scrollbar-thumb:hover{background:var(--primary)}
</style>
"""
