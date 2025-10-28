import firebase_admin
from firebase_admin import firestore
from firebase_functions import https_fn
from crew_setup import create_trading_crew
from datetime import datetime, timedelta

# Initialize Firebase Admin SDK
firebase_admin.initialize_app()
db = firestore.client()

@https_fn.on_call(secrets=["GEMINI_API_KEYS", "ALPACA_API_KEY", "ALPACA_SECRET_KEY"])
def run_trading_crew(req: https_fn.CallableRequest):
    """
    HTTPS-triggered Cloud Function to initiate a trading crew run.
    """
    # 1. Extract parameters from the request
    asset = req.data.get('asset')
    if not asset:
        raise https_fn.HttpsError('invalid-argument', 'The function must be called with a "asset" argument.')

    # 2. Prepare inputs for the crew
    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)
    inputs = {
        'assets_of_interest': [asset],
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d')
    }
    
    # 3. Create a run document in Firestore for logging
    run_ref = db.collection('runs').document()
    run_ref.set({
        'asset': asset,
        'startTime': firestore.SERVER_TIMESTAMP,
        'status': 'RUNNING'
    })

    try:
        # 4. Initialize and run the crew
        trading_crew = create_trading_crew()
        result = trading_crew.kickoff(inputs=inputs)

        # 5. Update the run document with the result
        run_ref.update({
            'endTime': firestore.SERVER_TIMESTAMP,
            'status': 'COMPLETED',
            'finalOutcome': str(result)
        })
        
        return {'status': 'success', 'runId': run_ref.id, 'result': str(result)}

    except Exception as e:
        # 6. Log any errors and update the status
        run_ref.update({
            'endTime': firestore.SERVER_TIMESTAMP,
            'status': 'FAILED',
            'error': str(e)
        })
        raise https_fn.HttpsError('internal', f'Crew execution failed: {str(e)}')
