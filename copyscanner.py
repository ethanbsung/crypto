import pandas as pd
import requests
from dontshare import BIRDEYE_KEY

# Define a function for colored printing (optional, or use standard print)
def cprint(message, fg_color='white', bg_color='on_red'):
    print(f"{message}")

def fetch_wallet_holdings(address):
    # My birdeye API Key
    API_KEY = BIRDEYE_KEY

    # Define an empty DataFrame with appropriate columns
    df = pd.DataFrame(columns=['Mint Address', 'Amount', 'USD Value'])

    # API endpoint and headers
    url = "https://public-api.birdeye.so/v1/wallet/token_list?wallet=0xf584f8728b874a6a5c7a8d4d387c9aae9172d621"
    headers = {
        "accept": "application/json",
        "x-chain": "ethereum",
        "X-API-KEY": BIRDEYE_KEY
    }

    try:
        response = requests.get(url, headers=headers)
        print(response.text)
        # Check for a successful API call
        if response.status_code == 200:
            json_response = response.json()
            

            # Parse the response if the structure is correct
            if 'data' in json_response and 'items' in json_response['data']:
                df = pd.DataFrame(json_response['data']['items'])
                df = df[['address', 'uiAmount', 'valueUsd']].rename(columns={
                    'address': 'Mint Address',
                    'uiAmount': 'Amount',
                    'valueUsd': 'USD Value'
                })
                df = df.dropna()
                df = df[df['USD Value'] > 0.05]
            else:
                cprint("No data available in the response.", 'white', 'on_red')
        
        else:
            cprint(f"Failed to retrieve token list for {address}. HTTP Status: {response.status_code}", 'white', 'on_red')

    except Exception as e:
        cprint(f"Error occurred while fetching wallet holdings: {str(e)}", 'white', 'on_red')
    
    # Print the DataFrame if it's not empty
    if not df.empty:
        print(df)
        cprint(f'** Total USD balance is {df["USD Value"].sum()}', 'white', 'on_red')
        
        # Save the filtered DataFrame to a CSV file
        TOKEN_PER_ADDY_CSV = 'filtered_wallet_holdings.csv'
        df.to_csv(TOKEN_PER_ADDY_CSV, index=False)
        cprint(f"Filtered wallet holdings saved to {TOKEN_PER_ADDY_CSV}", 'green', 'on_white')
    else:
        cprint("No wallet holdings to display.", 'white', 'on_red')
    
    return df

# Replace with the wallet address to analyze
# This is a wallet of a random trader who makes a lot of money on cryptocurrencies
copy_address = '2JMC8J5ypBULTpPQ9i7G4tbXrAEQGvRn7UJ4CNkJ6rLF'

# Fetch and process the wallet holdings
copy_open_positions = fetch_wallet_holdings(copy_address)