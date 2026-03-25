from pathlib import Path
import sys

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd

try:
    import plotly.graph_objects as go
    import plotly.express as px
except Exception:
    go = None
    px = None

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.main import run_pipeline
from backend.utils.search import search_stock
from backend.utils.stocks import INDEX_FUNDS, STOCKS
from backend.collector.stock_data import fetch_index_quotes
from backend.advisor.portfolio import analyze_portfolio

# Page Config
st.set_page_config(page_title="Acclewealth", layout="wide")


# Custom CSS styling (animations, typography, layout) - strictly NO EMOJIS
st.markdown("""
<style>
/* Animations */
@keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
}
@keyframes slideUp {
    from { opacity: 0; transform: translateY(15px); }
    to { opacity: 1; transform: translateY(0); }
}
.fade-in { animation: fadeIn 0.8s ease-in-out; }
.slide-up { animation: slideUp 0.6s ease-out; }

/* Custom Font mapping for clean look */
html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, system-ui, sans-serif;
}

/* Range Bar Styles */
.range-container {
    width: 100%;
    margin: 15px 0;
    font-family: monospace;
    font-size: 13px;
    color: #c9d1d9;
}
.range-labels {
    display: flex;
    justify-content: space-between;
    margin-bottom: 5px;
}
.range-bar-bg {
    width: 100%;
    height: 6px;
    background-color: #30363d;
    border-radius: 3px;
    position: relative;
}
.range-indicator {
    position: absolute;
    width: 12px;
    height: 12px;
    background-color: #58a6ff;
    border-radius: 50%;
    top: -3px;
    transform: translateX(-50%);
    box-shadow: 0 0 6px #58a6ff;
}

/* Card Styles */
.info-card {
    background-color: #161b22;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 16px;
    margin-bottom: 16px;
    transition: transform 0.2s;
}
.info-card:hover {
    border-color: #8b949e;
}

/* Clean up Streamlit elements */
.stMetric {
    background: #161b22;
    padding: 15px;
    border-radius: 8px;
    border: 1px solid #30363d;
}
</style>
""", unsafe_allow_html=True)


# Ticker Tape (No Emojis, clean UI)
@st.cache_data(ttl=120, show_spinner=False)
def get_index_data():
    return fetch_index_quotes(INDEX_FUNDS)

def render_ticker_tape():
    index_data = get_index_data()
    if not index_data:
        return

    items_html = ""
    for name, info in index_data.items():
        price = info["price"]
        change = info["change_pct"]
        
        if change > 0:
            arrow = "[UP]"
            css_class = "ticker-up"
            sign = "+"
        elif change < 0:
            arrow = "[DN]"
            css_class = "ticker-down"
            sign = ""
        else:
            arrow = "[--]"
            css_class = "ticker-flat"
            sign = ""

        items_html += f'''
        <span class="ticker-item">
            <span class="ticker-name">{name}</span>
            <span class="ticker-price">INR {price:,.2f}</span>
            <span class="{css_class}">{arrow} {sign}{change:.2f}%</span>
        </span>
        <span class="ticker-sep">|</span>
        '''

    ticker_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            background: transparent;
            overflow: hidden;
            font-family: 'Inter', -apple-system, sans-serif;
        }}
        .ticker-wrap {{
            width: 100%;
            overflow: hidden;
            background: linear-gradient(90deg, #0d1117 0%, #161b22 50%, #0d1117 100%);
            border-radius: 8px;
            padding: 12px 0;
            border: 1px solid #30363d;
        }}
        .ticker-content {{
            display: inline-flex;
            white-space: nowrap;
            animation: ticker-scroll 35s linear infinite;
        }}
        .ticker-content:hover {{
            animation-play-state: paused;
        }}
        @keyframes ticker-scroll {{
            0%   {{ transform: translateX(0); }}
            100% {{ transform: translateX(-50%); }}
        }}
        .ticker-item {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 0 20px;
            font-size: 13px;
            color: #c9d1d9;
        }}
        .ticker-name {{
            font-weight: 700;
            color: #f0f6fc;
            letter-spacing: 0.3px;
        }}
        .ticker-price {{ color: #c9d1d9; }}
        .ticker-up {{ color: #3fb950; font-weight: 600; }}
        .ticker-down {{ color: #f85149; font-weight: 600; }}
        .ticker-flat {{ color: #8b949e; font-weight: 600; }}
        .ticker-sep {{ color: #30363d; padding: 0 2px; font-size: 16px; }}
    </style>
    </head>
    <body>
        <div class="ticker-wrap">
            <div class="ticker-content">
                {items_html}{items_html}
            </div>
        </div>
    </body>
    </html>
    """
    components.html(ticker_html, height=50, scrolling=False)


# Sidebar Navigation
st.sidebar.title("Acclewealth")
app_mode = st.sidebar.radio("Navigation", ["Stock Analysis", "Portfolio Dashboard"])


@st.cache_data(ttl=300, show_spinner=False)
def analyze_stock(symbol):
    return run_pipeline(symbol)

def build_price_chart(raw_data):
    if not isinstance(raw_data, pd.DataFrame) or raw_data.empty:
        return None

    df = raw_data.copy()

    close_obj = None
    if "Close" in df.columns:
        close_obj = df["Close"]
    else:
        for col in df.columns:
            if str(col).lower() == "close":
                close_obj = df[col]
                break

    if close_obj is None:
        return None

    if isinstance(close_obj, pd.DataFrame):
        close_series = None
        for idx in range(close_obj.shape[1]):
            candidate = pd.to_numeric(close_obj.iloc[:, idx], errors="coerce")
            if candidate.notna().any():
                close_series = candidate
                break
        if close_series is None:
            return None
    else:
        close_series = pd.to_numeric(close_obj, errors="coerce")

    chart_df = pd.DataFrame({"Close": close_series})
    chart_df["MA20"] = chart_df["Close"].rolling(window=5, min_periods=1).mean()
    chart_df = chart_df.dropna(subset=["Close"]).reset_index(drop=True)

    if go is not None:
        fig = go.Figure()
        fig.add_trace(go.Scatter(y=chart_df["Close"], mode="lines", name="Close", line=dict(color="#58a6ff", width=2)))
        fig.add_trace(go.Scatter(y=chart_df["MA20"], mode="lines", name="MA20", line=dict(color="#f0883e", width=2, dash="dot")))
        fig.update_layout(
            height=360, margin=dict(l=20, r=20, t=30, b=20),
            plot_bgcolor="#0d1117", paper_bgcolor="#0d1117",
            font_color="#c9d1d9", legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        return fig
    return None

def build_financial_bar_chart(years, values, title, color):
    if not years or not values or go is None:
        return None
    min_len = min(len(years), len(values))
    df = pd.DataFrame({"Year": years[:min_len], "Value": values[:min_len]})
    df = df.dropna()
    if df.empty:
        return None
    
    fig = px.bar(df, x="Year", y="Value", title=title, color_discrete_sequence=[color])
    fig.update_layout(
        height=300, margin=dict(l=20, r=20, t=40, b=20),
        plot_bgcolor="#0d1117", paper_bgcolor="#0d1117", font_color="#c9d1d9"
    )
    return fig

def render_range_bar(label, low, high, current):
    if low is None or high is None or current is None or low == high:
        st.write(f"**{label}**: Data unavailable")
        return
        
    pct = ((current - low) / (high - low)) * 100
    pct = max(0, min(100, pct))  # Clamp between 0 and 100
    
    st.markdown(f"""
    <div class="range-container">
        <div class="range-labels">
            <span>{label} Low: INR {low:,.2f}</span>
            <span style="color:#58a6ff; font-weight:bold;">Current: INR {current:,.2f}</span>
            <span>{label} High: INR {high:,.2f}</span>
        </div>
        <div class="range-bar-bg">
            <div class="range-indicator" style="left: {pct}%;"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)


if app_mode == "Stock Analysis":
    st.title("AccleWealth")
    st.caption("Comprehensive analysis of NSE Indian Stocks")
    
    render_ticker_tape()

    query = st.text_input(
        "Search by company name, ticker, or abbreviation",
        placeholder="e.g. TCS, Reliance, bajaj, INFY, zomato..."
    )

    if query:
        results = search_stock(query)

        if results:
            top_match = list(results.keys())[0]
            if query.lower().strip() != top_match.lower().strip():
                st.caption(f"Best match: **{top_match}** ({results[top_match]})")

            selected = st.selectbox("Select Company", list(results.keys()))
            symbol = results[selected]

            if st.button("Analyze Stock", type="primary"):
                with st.spinner(f"Analyzing {selected}..."):
                    try:
                        result = analyze_stock(symbol)
                    except ValueError as err:
                        analyze_stock.clear()
                        st.warning(str(err))
                        st.stop()
                    except Exception as err:
                        analyze_stock.clear()
                        import traceback
                        st.error(f"We could not analyze this stock right now. Please try again. Error: {type(err).__name__} - {str(err)}")
                        st.code(traceback.format_exc())
                        st.stop()
                        
                    st.markdown(f"<h2 class='slide-up'>{selected} ({symbol})</h2>", unsafe_allow_html=True)
                    
                    # Decision Banner
                    decision = result["decision"]
                    confidence = result.get("confidence", 50)
                        
                    if decision == "BUY":
                        st.success(f"Action Reccomendation: BUY ({confidence}% confidence)")
                    elif decision == "SELL":
                        st.error(f"Action Reccomendation: SELL ({confidence}% confidence)")
                    else:
                        st.warning(f"Action Reccomendation: HOLD ({confidence}% confidence)")

                    # Core Metrics Row (Animated)
                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("Tech: RSI", f"{result['rsi']:.2f}")
                    col2.metric("Tech: Moving Avg", f"INR {result['moving_avg']:.2f}")
                    col3.metric("News Sentiment", result["sentiment"])
                    col4.metric("AI Score", f"{result['score']:+.1f}")

                    if True:
                        st.markdown("<div class='fade-in'>", unsafe_allow_html=True)
                        tab1, tab2, tab3, tab4 = st.tabs(["Overview", "Fundamentals", "Financials", "News"])
                        
                        # --- TAB 1: OVERVIEW ---
                        with tab1:
                            st.subheader("AI Insight")
                            st.info(result["reason"])
                            
                            st.subheader("Price Action")
                            fig_price = build_price_chart(result.get("data"))
                            if fig_price:
                                st.plotly_chart(fig_price, use_container_width=True)
                            else:
                                st.warning("Chart data unavailable")
                                
                            fund = result.get("fundamentals", {})
                            st.subheader("Trading Range")
                            render_range_bar("Day Range", fund.get("day_low"), fund.get("day_high"), fund.get("current_price"))
                            render_range_bar("52-Week Range", fund.get("fifty_two_week_low"), fund.get("fifty_two_week_high"), fund.get("current_price"))

                        # --- TAB 2: FUNDAMENTALS ---
                        with tab2:
                            fund = result.get("fundamentals", {})
                            if not fund:
                                st.warning("Fundamental data not currently available for this stock.")
                            else:
                                st.subheader("Key Statistics")
                                fcol1, fcol2, fcol3 = st.columns(3)
                                
                                mcap = fund.get("market_cap")
                                mcap_str = f"INR {mcap / 1e7:,.2f} Cr" if mcap else "N/A"
                                fcol1.metric("Market Cap", mcap_str)
                                
                                pe = fund.get("pe_ratio")
                                fcol2.metric("PE Ratio", f"{pe:,.2f}" if pe else "N/A")
                                
                                pb = fund.get("pb_ratio")
                                fcol3.metric("PB Ratio", f"{pb:,.2f}" if pb else "N/A")
                                
                                fcol4, fcol5, fcol6 = st.columns(3)
                                
                                ind_pe = fund.get("industry_pe")
                                fcol4.metric("Industry PE", f"{ind_pe:,.2f}" if ind_pe else "N/A")
                                
                                dte = fund.get("debt_to_equity")
                                fcol5.metric("Debt to Equity", f"{dte:,.2f}%" if dte else "N/A")
                                
                                roe = fund.get("roe")
                                fcol6.metric("Return on Equity (ROE)", f"{roe*100:,.2f}%" if roe else "N/A")
                                
                                fcol7, fcol8, fcol9 = st.columns(3)
                                div = fund.get("dividend_yield")
                                fcol7.metric("Dividend Yield", f"{div*100:,.2f}%" if div else "N/A")
                                bv = fund.get("book_value")
                                fcol8.metric("Book Value", f"INR {bv:,.2f}" if bv else "N/A")
                                fv = fund.get("face_value")
                                fcol9.metric("Face Value", f"INR {fv:,.2f}" if fv else "N/A")

                        # --- TAB 3: FINANCIALS ---
                        with tab3:
                            fin = result.get("financials", {})
                            years = fin.get("years", [])
                            if not years:
                                st.warning("Yearly financial data is not currently available.")
                            else:
                                st.subheader("Yearly Performance Trend")
                                
                                rev_fig = build_financial_bar_chart(years, fin.get("revenue"), "Total Revenue", "#58a6ff")
                                if rev_fig: st.plotly_chart(rev_fig, use_container_width=True)
                                
                                inc_fig = build_financial_bar_chart(years, fin.get("net_income"), "Net Profit (Income)", "#3fb950")
                                if inc_fig: st.plotly_chart(inc_fig, use_container_width=True)
                                
                                nw_fig = build_financial_bar_chart(years, fin.get("net_worth"), "Total Equity (Net Worth)", "#f0883e")
                                if nw_fig: st.plotly_chart(nw_fig, use_container_width=True)

                        # --- TAB 4: NEWS ---
                        with tab4:
                            news_list = result.get("news", [])
                            if not news_list:
                                st.info("No recent news found.")
                            else:
                                st.subheader("Recent Headlines")
                                for article in news_list:
                                    st.markdown(f"""
                                    <div class="info-card">
                                        <h4>{article.get('title', 'Headline Unavailable')}</h4>
                                        <p style="color: #8b949e; font-size: 13px;">
                                            Publisher: {article.get('publisher', 'Unknown')} | Date: {article.get('date', 'Recent')}
                                        </p>
                                        <a href="{article.get('link', '#')}" target="_blank" style="color: #58a6ff; text-decoration: none;">Read Full Article ></a>
                                    </div>
                                    """, unsafe_allow_html=True)
                        st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.warning("No matching stocks found. Try a different name.")

elif app_mode == "Portfolio Dashboard":
    st.title("Portfolio Dashboard")
    st.caption("Analyze your holdings for diversification and risk management")
    
    # Initialize session state for mock portfolio based on user prompt criteria
    if "portfolio" not in st.session_state:
        st.session_state.portfolio = [
            {"Company": "Torrent Power", "Symbol": "TORNTPOWER.NS", "Quantity": 30},
            {"Company": "Inox Wind", "Symbol": "INOXWIND.NS", "Quantity": 30},
            {"Company": "JSW Energy", "Symbol": "JSWENERGY.NS", "Quantity": 40},
        ]
    
    st.subheader("Your Holdings")
    
    # Simple form to add new stocks
    with st.expander("Add Stock to Portfolio", expanded=False):
        c1, c2, c3 = st.columns([3, 1, 1])
        with c1:
            query_port = st.text_input("Search Company", key="port_search")
        with c2:
            qty = st.number_input("Quantity", min_value=1, value=10, key="port_qty")
        with c3:
            st.write("") # spacer
            st.write("")
            add_btn = st.button("Add", use_container_width=True)
            
        if add_btn and query_port:
            res = search_stock(query_port)
            if res:
                c_name = list(res.keys())[0]
                c_sym = res[c_name]
                st.session_state.portfolio.append({"Company": c_name, "Symbol": c_sym, "Quantity": qty})
                st.success(f"Added {qty} units of {c_name}")
                st.rerun()
            else:
                st.error("Stock not found.")

    # Data Editor for the portfolio
    df_port = pd.DataFrame(st.session_state.portfolio)
    edited_df = st.data_editor(
        df_port, 
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True
    )
    st.session_state.portfolio = edited_df.to_dict('records')
    
    if st.button("Run Portfolio Analysis", type="primary"):
        with st.spinner("Analyzing portfolio holdings..."):
            port_input = [{"name": r["Company"], "symbol": r["Symbol"], "quantity": r["Quantity"]} for r in st.session_state.portfolio if r.get("Symbol")]
            
            if not port_input:
                st.warning("Your portfolio is empty.")
            else:
                analysis = analyze_portfolio(port_input)
                
                # Top metrics
                st.markdown("<div class='slide-up'>", unsafe_allow_html=True)
                tc1, tc2 = st.columns(2)
                tc1.metric("Total Portfolio Value", f"INR {analysis['total_value']:,.2f}")
                tc2.metric("Total Holdings", len(analysis['stocks']))
                
                tabP1, tabP2 = st.tabs(["Diversification Analysis", "Holding Details"])
                
                with tabP1:
                    sc1, sc2 = st.columns([1, 1])
                    with sc1:
                        st.subheader("Sector Allocation")
                        sec_alloc = analysis["sector_allocation"]
                        if sec_alloc and px is not None:
                            df_pie = pd.DataFrame(list(sec_alloc.items()), columns=["Sector", "Allocation Pct"])
                            fig_pie = px.pie(df_pie, names="Sector", values="Allocation Pct", hole=0.4)
                            fig_pie.update_layout(
                                plot_bgcolor="#0d1117", paper_bgcolor="#0d1117", font_color="#c9d1d9",
                                margin=dict(t=20, b=20, l=20, r=20)
                            )
                            st.plotly_chart(fig_pie, use_container_width=True)
                        elif not px:
                            st.write(sec_alloc)
                    
                    with sc2:
                        st.subheader("Strategic Insights")
                        if analysis["warnings"]:
                            for w in analysis["warnings"]:
                                st.error(str(w))
                        
                        if analysis["suggestions"]:
                            for s in analysis["suggestions"]:
                                st.info(str(s))
                                
                        if not analysis["warnings"] and not analysis["suggestions"]:
                            st.success("Your portfolio looks well diversified!")
                            
                with tabP2:
                    st.subheader("Individual Metrics")
                    for s in analysis["stocks"]:
                        with st.expander(f"{s['name']}  -  Weight: {s['weight']:.1f}%", expanded=False):
                            rc1, rc2, rc3 = st.columns(3)
                            rc1.metric("Current Price", f"INR {s['price']:,.2f}" if s['price'] else "N/A")
                            rc2.metric("Total Value", f"INR {s['value']:,.2f}")
                            rc3.metric("Broad Sector", s['broad_sector'])
                            
                            rc4, rc5, rc6 = st.columns(3)
                            pe = s.get("pe_ratio")
                            rc4.metric("PE Ratio", f"{pe:.1f}" if pe else "N/A")
                            dte = s.get("debt_to_equity")
                            rc5.metric("Debt to Equity", f"{dte:.1f}%" if dte else "N/A")
                            div = s.get("dividend_yield")
                            rc6.metric("Div Yield", f"{div*100:.2f}%" if div else "N/A")
                st.markdown("</div>", unsafe_allow_html=True)
