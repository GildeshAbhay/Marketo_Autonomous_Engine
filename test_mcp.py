import requests

headers = {
    'Content-Type': 'application/json',
    'Accept': 'application/json, text/event-stream'
}

data = {
    "input_value": "give me details of campaign 212"
}

response = requests.post('http://localhost:8002/mcp', 
                        headers=headers,
                        json=data)
print(response.json())