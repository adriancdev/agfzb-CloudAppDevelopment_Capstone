import requests
import json
from .models import CarDealer
from .models import DealerReview
from requests.auth import HTTPBasicAuth


# Create a `get_request` to make HTTP GET requests
def get_request(url, api_key=None, **kwargs):
    print(kwargs)
    print("GET from {} ".format(url))
    
    response = None  # Initialize response to None
    
    try:
        headers = {'Content-Type': 'application/json'}
        
        if api_key:
            response = requests.get(url, params=kwargs, headers=headers,
                                    auth=HTTPBasicAuth('apikey', api_key))
        else:
            # Call get method of requests library with URL and parameters
            response = requests.get(url, headers=headers, params=kwargs)
            
    except Exception as e:
        # If any error occurs
        print(f"Network exception occurred: {e}")
        return None
    
    status_code = response.status_code
    print("With status {} ".format(status_code))
    
    try:
        json_data = response.json()
    except json.JSONDecodeError:
        json_data = None
    
    return json_data

# Create a `post_request` to make HTTP POST requests
def post_request(url, json_payload, **kwargs):
    try:
        response = requests.post(url, params=kwargs, json=json_payload)
        response.raise_for_status()  # Raise an HTTPError for bad responses
        return response.json()  # Return the JSON content of the response
    except requests.exceptions.RequestException as e:
        print(f"Error making POST request: {e}")
        return None


# Create a get_dealers_from_cf method to get dealers from a cloud function
def get_dealers_from_cf(url, **kwargs):
    results = []
    # Call get_request with a URL parameter
    json_result = get_request(url)
    if json_result:
        # Get the row list in JSON as dealers
        dealers = json_result 
        # For each dealer object
        for dealer in dealers:
            # Get its content in `doc` object
            dealer_doc = dealer
            # Create a CarDealer object with values in `doc` object
            dealer_obj = CarDealer(address=dealer_doc["address"], city=dealer_doc["city"], full_name=dealer_doc["full_name"],
                                   id=dealer_doc["id"], lat=dealer_doc["lat"], long=dealer_doc["long"],
                                   short_name=dealer_doc["short_name"],
                                   st=dealer_doc["st"], zip=dealer_doc["zip"])
            results.append(dealer_obj)

    return results

# Create a get_dealer_reviews_from_cf method to get reviews by dealer id from a cloud function
def get_dealer_reviews_from_cf(url, dealer_id):
    url_with_id = f"{url}?id={dealer_id}"

    response_data = get_request(url_with_id)

    if response_data is not None:
        for review in response_data:
            review_obj = DealerReview(
                dealership=review["dealership"],
                name=review["name"],
                purchase=review["purchase"],
                review=review["review"],
                purchase_date=review["purchase_date"],
                car_make=review["car_make"],
                car_model=review["car_model"],
                car_year=review["car_year"],
                sentiment=None,
                id=review["id"]
            )
            review_obj.sentiment = analyze_review_sentiments(review_obj.review)

            return review_obj
    else:
        # Return None or handle the error as needed
        return None


# Create an `analyze_review_sentiments` method to call Watson NLU and analyze text
def analyze_review_sentiments(text):
    url = "https://api.us-south.natural-language-understanding.watson.cloud.ibm.com/instances/XXXXXX/v1/analyze"

    response = get_request(url,
        api_key="",
        text=text,
        version='2022-04-07',
        features=['sentiment'],
        return_analyzed_text=True)
    print(response)
    if response:
        sentiment = response.get('sentiment', {}).get('document', {}).get('label')
        return sentiment
    return None