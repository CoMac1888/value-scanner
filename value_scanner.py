import streamlit as st
import requests
import pandas as pd
import os

# API setup (use env var on deploy, hardcode for local testing)
API_KEY = '8e2403d4149ca74fd3ef3007e4fae874'  # Replace with your Odds API key
BASE_URL = 'https://api.the-odds-api.com/v4'

st.title("🔍 ValueScan AI – UK Sharp Edge Finder")
st.write("Pick a sport, set your prob – spot value bets on EPL & more. Built by a restricted punter. (Not advice.)")

# Free tier counter (resets per session – upgrade later for persistence)
if 'scans' not in st.session_state:
    st.session_state.scans = 0

# Inputs
sport = st.selectbox("Sport:", [
    'soccer_epl', 
    'soccer_efl_championship', 
    'cricket_test_matches', 
    'rugby_union_england_premiership'
], format_func=lambda x: x.replace('soccer_', '').replace('_', ' ').replace('rugby_union_', '').title().replace('Epl', 'Premier League'))
your_prob_home = st.number_input("Your Prob for Home Win (%):", min_value=0.0, max_value=100.0, value=50.0) / 100
markets = st.selectbox("Market:", ['h2h'], help="Moneyline only for now – spreads/totals soon!")
game_limit = st.slider("Games to Scan:", 1, 10, 5, help="Max games to check (API-friendly)")

if st.button("Scan for Value 🚀") and your_prob_home:
    if st.session_state.scans < 3:  # Free limit
        with st.spinner("Hunting edges across UK books..."):
            url = f'{BASE_URL}/sports/{sport}/odds/?apiKey={API_KEY}&regions=uk&markets={markets}'
            response = requests.get(url)
            if response.status_code != 200:
                if response.status_code == 404:
                    st.warning(f"No active games or invalid sport for {sport.replace('_', ' ').title()}. Try Premier League or Championship!")
                else:
                    st.error(f"API error: {response.status_code} – Check key or try later. Details: {response.text[:200]}...")
                st.stop()  # Exit early
            if response.status_code == 200:
                data = response.json()
                values = []
                for game in data[:game_limit]:  # Limit to user-selected games
                    home_team = game['home_team']
                    away_team = game['away_team']
                    commence = game['commence_time']
                    
                    for book in game['bookmakers']:
                        for market in book['markets']:
                            if market['key'] == markets:
                                for outcome in market['outcomes']:
                                    if outcome['name'] == home_team:
                                        dec_odds = outcome.get('price', None)
                                        if dec_odds:
                                            implied_prob = 1 / dec_odds
                                            value = (your_prob_home * dec_odds) - 1  # Your edge formula
                                            if value > 0.05:  # 5%+ edge threshold
                                                values.append({
                                                    'Game': f"{home_team} vs {away_team}",
                                                    'Book': book['title'],
                                                    'Odds (Dec)': f"{dec_odds:.2f}",
                                                    'Your Prob': f"{your_prob_home:.1%}",
                                                    'Edge': f"{value:.1%}",
                                                    'Kickoff': commence
                                                })
                
                st.session_state.scans += 1
                st.success(f"Free scans left today: {3 - st.session_state.scans} | API calls left: {response.headers.get('x-requests-remaining', 'N/A')}")
                
                if values:
                    st.subheader("Value Bets Found:")
                    st.dataframe(pd.DataFrame(values))
                    st.info("Pro tip: Cross-check line moves & vig. Upgrade for email alerts + AI probs.")
                else:
                    st.warning(f"No edges >5% for {your_prob_home:.1%} prob. Try another sport or prob.")
    else:
        st.error("Free limit hit! Unlock unlimited scans for £7/mo.")

# Premium tease
st.markdown("[**Go Pro: Unlimited Scans + Email Alerts (£7/mo)**](https://gumroad.com/your-link)", unsafe_allow_html=True)

st.sidebar.markdown("---")
st.sidebar.info("Built for UK punters: EPL, Championship, cricket. Email: scan@fake.com")
st.sidebar.warning("For entertainment only. Always bet responsibly.")