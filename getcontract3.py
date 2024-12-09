import requests
import json
import csv
from typing import List, Dict
import configparser

class ContractGet:
    """
    A class to fetch Ethereum blockchain data using Infura and Etherscan APIs.
    """
    def __init__(self) -> None:
        config = configparser.ConfigParser()
        config.read('config.ini')
        self.base_url = "https://mainnet.infura.io/v3/"
        self.infura_key = config['API']['infura_key']
        self.etherscan_key = config['API']['etherscan_key']
        self.start_block = int(config['BLOCKCHAIN']['start_block'])
        self.block_width = int(config['BLOCKCHAIN']['block_width'])

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
        print(f"Infura URL: {self.base_url}{self.infura_key[:6]}...")  # Only show first 6 chars of key
        
        try:
            response = requests.post(
                f"{self.base_url}{self.infura_key}",
                json=batch_request,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            
            print(f"Response status code: {response.status_code}")
            print(f"Response size: {len(response.text)} bytes")
            
            json_response = response.json()
            print(f"Number of blocks returned: {len(json_response)}")
            return json_response
            
        except requests.RequestException as e:
            print(f"Error fetching blocks: {e}")
            print(f"Response content: {response.text if 'response' in locals() else 'No response'}")
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
                    contract_info = {
                        'txHash': tx['hash'],
                        'blockNumber': block_number,
                        'from': tx['from'],
                        'to': tx['to'],
                        'creator': tx['from'],
                        'value': tx['value'],
                        'gasPrice': tx['gasPrice']
                    }
                    
                    # If we can determine the contract address
                    if 'creates' in tx and tx['creates']:
                        contract_address = tx['creates']
                        verification_info = self.check_contract_verification(contract_address)
                        contract_info.update({
                            'contractAddress': contract_address,
                            'verified': verification_info['verified'],
                            'verificationMessage': verification_info['message']
                        })
                    
                    contract_creations.append(contract_info)
        
        return contract_creations
    
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
            "apikey": self.etherscan_key
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
    
def main() -> None:
    """
    Main function to execute the contract fetching process.
    """
    # Initialize contract getter with API keys from config
    contract_getter = ContractGet()
    
    # Define block range from config
    start_block = contract_getter.start_block
    end_block = start_block + contract_getter.block_width
    
    # Fetch blocks in batch
    blocks_data = contract_getter.fetch_blocks(start_block, end_block)
    
    if blocks_data:
        # First extract contract creations from blocks
        contract_creations = contract_getter.filter_contract_creations(blocks_data)
        
        print(f"\nFound {len(contract_creations)} contract creations")
        
        if contract_creations:
            # Save results to CSV
            contract_getter.save_to_csv(contract_creations)
            print("\nResults saved to CSV file")

if __name__ == "__main__":
    main()