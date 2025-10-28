import React, { useState } from 'react';
import { auth, functions, googleProvider } from './firebase';
import { signInWithPopup } from "firebase/auth";
import { httpsCallable } from 'firebase/functions';

function App() {
    const [user, setUser] = useState(null);
    const [selectedAsset, setSelectedAsset] = useState('SPY');
    const [isLoading, setIsLoading] = useState(false);
    const [result, setResult] = useState('');

    auth.onAuthStateChanged((user) => {
        setUser(user);
    });

    const handleSignIn = () => {
        signInWithPopup(auth, googleProvider).catch(alert);
    };

    const handleRunCrew = async () => {
        if (!user) {
            alert("Please sign in to run the crew.");
            return;
        }
        setIsLoading(true);
        setResult('');
        
        const runTradingCrew = httpsCallable(functions, 'run_trading_crew');
        try {
            const response = await runTradingCrew({ asset: selectedAsset });
            setResult(JSON.stringify(response.data, null, 2));
        } catch (error) {
            console.error("Cloud Function error:", error);
            setResult(`Error: ${error.message}`);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div style={{ padding: '20px' }}>
            <h1>Autonomous Analyst Trading Crew</h1>
            {user ? (
                <div>
                    <p>Welcome, {user.displayName}!</p>
                    <hr />
                    <h3>Configure and Run</h3>
                    <select value={selectedAsset} onChange={(e) => setSelectedAsset(e.target.value)}>
                        <option value="SPY">SPY</option>
                        <option value="QQQ">QQQ</option>
                        <option value="DIA">DIA</option>
                        <option value="IWM">IWM</option>
                    </select>
                    <button onClick={handleRunCrew} disabled={isLoading}>
                        {isLoading ? 'Agents are working...' : 'Run Crew'}
                    </button>
                    {result && (
                        <div>
                            <h3>Crew Run Complete!</h3>
                            <pre>{result}</pre>
                        </div>
                    )}
                </div>
            ) : (
                <button onClick={handleSignIn}>Sign in with Google</button>
            )}
        </div>
    );
}

export default App;