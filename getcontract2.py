import requests
import json
import csv
from typing import List, Dict

class BlockchainDataCollector:
    def __init__(self, api_key: str):
        self.base_url = "https://mainnet.infura.io/v3/"
        self.api_key = api_key

    def create_batch_request(self, start_block: int, end_block: int) -> List[Dict]:
        """
        Creates a batch request for multiple blocks
        """
        batch_request = []
        for block_num in range(start_block, end_block + 1):
            batch_request.append({
                "jsonrpc": "2.0",
                "id": block_num,
                "method": "eth_getBlockByNumber",
                "params": [hex(block_num), True]  # True to get full transaction objects
            })
        return batch_request

    def fetch_blocks(self, start_block: int, end_block: int) -> List[Dict]:
        """
        Fetches multiple blocks in a single batch request
        """
        batch_request = self.create_batch_request(start_block, end_block)
        
        print(f"\nMaking batch request for blocks {start_block} to {end_block}")
        print(f"Number of blocks in batch: {len(batch_request)}")
        
        try:
            response = requests.post(
                f"{self.base_url}{self.api_key}",
                json=batch_request,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            
            print(f"Response status code: {response.status_code}")
            return response.json()
            
        except requests.RequestException as e:
            print(f"Error fetching blocks: {e}")
            return []

    def filter_contract_creations(self, blocks_data: List[Dict]) -> List[Dict]:
        """
        Filters contract creation transactions from block data
        """
        contract_creations = []
        
        for block in blocks_data:
            if 'result' not in block or not block['result']:
                continue
                
            transactions = block['result'].get('transactions', [])
            block_number = int(block['result']['number'], 16)
            
            for tx in transactions:
                if tx['to'] is None:  # Contract creation transaction
                    # Wait for contract address to be available
                    contract_info = {
                        'txHash': tx['hash'],
                        'blockNumber': block_number,
                        'creator': tx['from'],
                        'value': tx['value'],
                        'gasPrice': tx['gasPrice']
                    }
                    
                    # If we can determine the contract address
                    if 'creates' in tx and tx['creates']:
                        verification_info = self.check_contract_verification(tx['creates'])
                        contract_info.update({
                            'contractAddress': tx['creates'],
                            'verified': verification_info['verified'],
                            'verificationMessage': verification_info['message']
                        })
                    
                    contract_creations.append(contract_info)
        
        return contract_creations

    def save_to_csv(self, contracts: List[Dict], filename: str = 'contract_creations.csv'):
        """
        Saves contract creation data to CSV
        """
        if not contracts:
            print("No contracts to save")
            return
            
        try:
            with open(filename, 'w', newline='') as csvfile:
                fieldnames = contracts[0].keys()
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(contracts)
                print(f"Saved {len(contracts)} contracts to {filename}")
        except IOError as e:
            print(f"Error saving to CSV: {e}")

    def check_contract_verification(self, contract_address: str) -> Dict:
        """
        Checks if a contract is verified on Etherscan
        
        :param contract_address: The contract address to check
        :return: Dictionary containing verification status and source code if verified
        """
        etherscan_url = "https://api.etherscan.io/api"
        params = {
            "module": "contract",
            "action": "getabi",
            "address": contract_address,
            "apikey": self.etherscan_api_key  # You'll need to add this in __init__
        }
        
        print(f"\nChecking verification status for contract: {contract_address}")
        
        try:
            response = requests.get(etherscan_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            is_verified = data['status'] == '1'
            
            return {
                'address': contract_address,
                'verified': is_verified,
                'message': data.get('message', 'Unknown'),
                'result': data.get('result', None)
            }
            
        except requests.RequestException as e:
            print(f"Error checking verification status: {e}")
            return {
                'address': contract_address,
                'verified': False,
                'message': str(e),
                'result': None
            }

def main():
    API_KEY = "1e786b822d40462187b2a3a046e3ab49"
    collector = BlockchainDataCollector(API_KEY)
    
    # Define block range
    start_block = 21323237
    end_block = 21323337  # Start with a small range for testing
    
    # Fetch blocks in batch
    blocks_data = collector.fetch_blocks(start_block, end_block)
    
    if blocks_data:
        # Filter for contract creations
        contract_creations = collector.filter_contract_creations(blocks_data)
        
        print(f"\nFound {len(contract_creations)} contract creations")
        if contract_creations:
            print("\nFirst contract creation found:")
            print(json.dumps(contract_creations[0], indent=2))
            
            # Save results
            collector.save_to_csv(contract_creations)

if __name__ == "__main__":
    main()
