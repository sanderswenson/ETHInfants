import requests
import json
import csv
from datetime import datetime
import time
from typing import List, Dict

class PoolCollector:
    def __init__(self):
        self.base_url = "https://api.geckoterminal.com/api/v2"
        self.headers = {
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0"  # Good practice to identify your requests
        }
        self.network = "eth"  # Ethereum mainnet

    def get_new_pools(self, page_size: int = 20) -> List[Dict]:
        """
        Fetches the most recently created pools on Ethereum mainnet
        """
        endpoint = f"{self.base_url}/networks/{self.network}/new_pools"
        params = {
            "page": 2,
            "limit": page_size,
            "sort": "created_at"  # Sort by creation time
        }

        try:
            response = requests.get(endpoint, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            return data.get('data', [])
        except requests.RequestException as e:
            print(f"Error fetching pools: {e}")
            return []

    def get_pool_details(self, pool_address: str) -> Dict:
        """
        Fetches detailed information about a specific pool
        """
        # Remove 'eth_' prefix if present
        pool_address = pool_address.replace('eth_', '')
        endpoint = f"{self.base_url}/networks/{self.network}/pools/{pool_address}"

        try:
            response = requests.get(endpoint, headers=self.headers)
            response.raise_for_status()
            return response.json().get('data', {})
        except requests.RequestException as e:
            print(f"Error fetching pool details for {pool_address}: {e}")
            return {}

    def save_to_csv(self, pools: List[Dict], filename: str = None):
        """
        Saves pool data to a CSV file
        """
        if not pools:
            print("No pools to save")
            return

        if filename is None:
            filename = f"eth_pools_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

        try:
            # Flatten the pool data structure
            flattened_pools = []
            for pool in pools:
                pool_data = {
                    'pool_address': pool.get('id'),
                    'created_at': pool.get('attributes', {}).get('created_at'),
                    'name': pool.get('attributes', {}).get('name'),
                    'base_token_price_usd': pool.get('attributes', {}).get('base_token_price_usd'),
                    'quote_token_price_usd': pool.get('attributes', {}).get('quote_token_price_usd'),
                    'pool_created_at': pool.get('attributes', {}).get('pool_created_at'),
                    'reserve_in_usd': pool.get('attributes', {}).get('reserve_in_usd'),
                    'dex_id': pool.get('relationships', {}).get('dex', {}).get('data', {}).get('id')
                }
                flattened_pools.append(pool_data)

            with open(filename, 'w', newline='') as csvfile:
                fieldnames = flattened_pools[0].keys()
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(flattened_pools)
                print(f"Saved {len(flattened_pools)} pools to {filename}")
        except IOError as e:
            print(f"Error saving to CSV: {e}")

def main():
    collector = PoolCollector()
    
    # Get new pools
    print("Fetching new pools...")
    pools = collector.get_new_pools(page_size=20)
    
    if pools:
        print(f"Found {len(pools)} new pools")
        
        # Get additional details for each pool
        detailed_pools = []
        for pool in pools:
            pool_address = pool.get('id')
            if pool_address:
                print(f"Fetching details for pool {pool_address}")
                details = collector.get_pool_details(pool_address)
                if details:
                    detailed_pools.append(details)
                time.sleep(1)  # Rate limiting to be nice to the API
        
        # Save the results
        collector.save_to_csv(detailed_pools)
    else:
        print("No pools found")

if __name__ == "__main__":
    main()
