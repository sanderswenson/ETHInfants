import requests
import json

def inspect_transaction(tx_hash, api_key):
    """
    Fetch and display all available data for a specific transaction
    """
    base_url = "https://api.etherscan.io/api"
    
    # Get transaction details
    params = {
        "module": "proxy",
        "action": "eth_getTransactionByHash",
        "txhash": tx_hash,
        "apikey": api_key
    }
    
    try:
        # Get basic transaction data
        response = requests.get(base_url, params=params)
        tx_data = response.json()
        
        # Get transaction receipt (contains contract address if created)
        receipt_params = {
            "module": "proxy",
            "action": "eth_getTransactionReceipt",
            "txhash": tx_hash,
            "apikey": api_key
        }
        receipt_response = requests.get(base_url, params=receipt_params)
        receipt_data = receipt_response.json()
        
        print("\n=== Transaction Data ===")
        print(json.dumps(tx_data, indent=2))
        
        print("\n=== Transaction Receipt ===")
        print(json.dumps(receipt_data, indent=2))
        
    except Exception as e:
        print(f"Error fetching transaction: {e}")

def main():
    API_KEY = "Q5EY3ZSAVHA3F46NGW7185SV82YI4J35IX"
    TX_HASH = "0xfc7edd11ee6dc6f35c94dbbb9e3173cfb863ddec19d20cfd2c570265f59727ab"
    
    inspect_transaction(TX_HASH, API_KEY)

if __name__ == "__main__":
    main()