from crew_setup import trading_crew
from datetime import datetime, timedelta

if __name__ == '__main__':
    print("## Starting the Autonomous Analyst Crew")

    # Calculate dates
    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)

    # Format dates as strings
    formatted_end_date = end_date.strftime('%Y-%m-%d')
    formatted_start_date = start_date.strftime('%Y-%m-%d')

    inputs = {
        'assets_of_interest': ['SPY', 'QQQ'],
        'start_date': formatted_start_date,
        'end_date': formatted_end_date
    }

    # Kickoff the crew with the prepared inputs
    result = trading_crew.kickoff(inputs=inputs)

    print("## Crew Run Complete!")
    print("--- Final Result ---")
    print(result)
