# %%
import requests
import base64
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import linregress
import time
import os
from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path)  # This loads the environment variables from .env
TIME_LIMIT = 0.02 # for API requests

def query_api(endpoint):
    user = os.getenv("API_USER")
    password = os.getenv("API_PASSWORD")
    encoded_credentials = base64.b64encode(f"{user}:{password}".encode("UTF-8")).decode("UTF-8")
    headers = {"Authorization": f"Basic {encoded_credentials}"}
    response = requests.get(endpoint, headers=headers)
    response.raise_for_status()
    return response.json()

def fetch_sessions_tss(user_id):
    """
    Fetches sessions TSS for the specified user.
    """
    # start_time = time.time()
    URL = f'https://athletica-demo1.herokuapp.com/users/{user_id}/sessions'
    sessions = query_api(URL)
    
    session_details = []
    for session_id in sessions:
        details = query_api(URL + '/' + str(session_id))
        session_details.append({'date': details['date'], 'TSS': details['TSS']})
        time.sleep(TIME_LIMIT)  # Rate limit handling

    df = pd.DataFrame(session_details)
    df['date'] = pd.to_datetime(df['date'])
    
    # end_time = time.time() 
    # print(f"fetch_sessions_tss completed in {end_time - start_time:.2f} seconds.")
    
    return df.sort_values(by='date').reset_index(drop=True)

def calculate_ctl_atl_tsb(df, ctl_start=0, atl_start=0):
    """
    Calculates CTL, ATL, and TSB for each day, 
    filling in missing dates with TSS=0.
    
    Parameters:
    - df: DataFrame with 'date' and 'TSS' columns.
    - ctl_start: Starting value for CTL calculation.
    - atl_start: Starting value for ATL calculation.
    
    Returns:
    - DataFrame with added columns for 'ctl', 'atl', and 'tsb', covering every date.
    """
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values(by='date')
    
    # Remove rows with NaN TSS and fill missing dates
    df_clean = df.dropna(subset=['TSS']).copy()
    all_dates = pd.date_range(start=df_clean['date'].min(), end=df_clean['date'].max())
    df_clean.set_index('date', inplace=True)
    df_clean = df_clean.reindex(all_dates).rename_axis('date').reset_index()
    
    # Fill in only TSS with 0 where missing
    df_clean['TSS'].fillna(0, inplace=True)

    df_clean['ctl'] = np.nan
    df_clean['atl'] = np.nan
    df_clean['tsb'] = np.nan

    ctl = ctl_start
    atl = atl_start

    # Calculate CTL, ATL, and TSB for each day
    for i in range(len(df_clean)):
        tss = df_clean.iloc[i]['TSS']
        ctl = ctl + (tss - ctl) / 42  # Using the simplified daily increment formula
        atl = atl + (tss - atl) / 7
        df_clean.loc[i, 'ctl'] = ctl
        df_clean.loc[i, 'atl'] = atl
        df_clean.loc[i, 'tsb'] = ctl - atl
    
    return df_clean

def plot_ctl_atl_tsb(df):
    """
    Plots CTL, ATL, and TSB over time using different colors.
    """
    plt.figure(figsize=(10, 6))
    plt.plot(df['date'], df['ctl'], label='CTL (Fitness)', color='blue')
    plt.plot(df['date'], df['atl'], label='ATL (Fatigue)', color='red')
    plt.plot(df['date'], df['tsb'], label='TSB (Form)', color='green')
    plt.axhline(y=0, color='grey', linestyle='--')
    plt.title('Training Load and Form Over Time')
    plt.xlabel('Date')
    plt.ylabel('Score')
    plt.legend()
    plt.gcf().autofmt_xdate()
    plt.show()
    plt.close()



def fetch_power_profile(user_id, session_id):
    """
    Fetches power profile for specified user and session using the query_api function.
    
    Returns a DataFrame with columns ['time', 'power'].
    """
    URL = f'https://athletica-demo1.herokuapp.com/users/{user_id}/sessions/{session_id}/profile'
    
    power_profile = query_api(URL)['power_profile']

    df = pd.DataFrame(list(power_profile.items()), columns=['time', 'power'])
    df['time'] = df['time'].astype(int)
    df.sort_values(by='time', inplace=True)

    return df


def fit_cp_w_prime(df):
    """
    Fits a model y = slope * x + intercept where y = power * time to the data,
    interpreting slope as CP and intercept as W'.

    Parameters:
    - df: DataFrame with 'Time (s)' and 'Power (W)' columns.
    
    Returns:
    - CP: Critical Power (slope of the regression).
    - CP_err: Standard error of the slope.
    - W_prime: Work capacity above CP (intercept of the regression).
    - W_prime_err: Standard error of the intercept.
    """
    x = df['time']
    y = df['power'] * df['time']
    
    regression_result = linregress(x, y)
    
    CP = regression_result.slope
    CP_err = regression_result.stderr
    W_prime = regression_result.intercept
    W_prime_err = regression_result.intercept_stderr
    
    return CP, CP_err, W_prime, W_prime_err

def plot_power_vs_time(df, CP=None, W_prime=None):
    """
    Plots the Power (W) versus Time (s) from the df_power_profile DataFrame.
    Optionally adds a CP model fit line if CP and W_prime are provided.
    
    Parameters:
    - df: DataFrame with 'Time (s)' and 'Power (W)' columns.
    - CP: Optional; Critical Power, the slope from the linear fit.
    - W_prime: Optional; Work capacity above CP, the intercept from the linear fit.
    """
    plt.figure(figsize=(10, 6))
    plt.plot(df['time'], df['power'], marker='o', linestyle='-', color='blue')
    
    if CP is not None and W_prime is not None:
        t_values = np.linspace(df['time'].min(), df['time'].max(), 100)
        fitted_power = CP + W_prime / t_values
        plt.plot(t_values, fitted_power, label='CP Model Fit', color='red', linestyle='--')
    
    
    plt.title('Power vs. Time')
    plt.xlabel('Time (s)')
    plt.ylabel('Power (W)')
    plt.grid(True)
    plt.legend()
    plt.show()
    plt.close()

#%% 
''' Using functions for the tasks: uncomment to use

USER_ID = 14
df_tss = fetch_sessions_tss(USER_ID)
df_scores = calculate_ctl_atl_tsb(df_tss)
plot_ctl_atl_tsb(df_scores)
# %%
# Save JSON for app task 
df_scores['date'] = df_scores['date'].dt.strftime('%Y-%m-%d')
df_json = df_scores[['date', 'ctl']]
json_file_path = 'ctl_scores.json' 
df_json.to_json(json_file_path, orient='records', date_format='iso')
# %%
df_power_profile = fetch_power_profile(1, 195)
CP, CP_err, W_prime, W_prime_err = fit_cp_w_prime(df_power_profile)
print(f"CP: {CP}, CP_err: {CP_err}, W': {W_prime}, W'_err: {W_prime_err}")
# %%
plot_power_vs_time(df_power_profile, CP, W_prime)
# %%
'''