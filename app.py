import streamlit as st
from crew_setup import trading_crew
from datetime import datetime, timedelta

# Set the page layout to wide
st.set_page_config(layout='wide', page_title='Autonomous Analyst Trading Crew')

# Display the title
st.title('Autonomous Analyst Trading Crew')

# --- Sidebar for Configuration ---
with st.sidebar:
    st.header('Crew Configuration')

    # Asset selection
    selected_asset = st.selectbox(
        'Select an asset to analyze:',
        ('SPY', 'QQQ', 'DIA', 'IWM')
    )

    # Run button
    run_button = st.button('Run Crew')

# --- Main Page for Operations Log ---
st.header('Crew Operations Log')

# Core logic to run the crew when the button is clicked
if run_button:
    st.info('Crew has been dispatched...')

    # Calculate dates for the historical data query
    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)

    # Format dates as strings
    formatted_end_date = end_date.strftime('%Y-%m-%d')
    formatted_start_date = start_date.strftime('%Y-%m-%d')

    # Create the inputs dictionary for the crew
    inputs = {
        'assets_of_interest': [selected_asset],
        'start_date': formatted_start_date,
        'end_date': formatted_end_date
    }

    # Execute the crew's kickoff method within a spinner
    with st.spinner('Agents are working... Please wait.'):
        result = trading_crew.kickoff(inputs=inputs)

    # Display the final result
    st.header('Crew Run Complete!')
    st.code(result, language='text')
