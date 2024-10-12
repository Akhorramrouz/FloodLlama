import io
import json
import requests
import pandas as pd
from PIL import Image

def get_svi_stats_and_tracts(state_abbr, county, theme, op, threshold):

    """
    Retrieve SVI statistics and census tracts based on user-specified conditions,
    and return a JSON string containing the information.

    Parameters:
        state_abbr (str): State abbreviation (e.g., 'NJ').
        county (str): County name (e.g., 'Middlesex').
        theme (str): SVI theme (e.g., 'RPL_THEME4').
        op (str): Comparison operator ('<', '<=', '>', '>=').
        threshold (float): Threshold value for the comparison.

    Returns:
        str: JSON string containing SVI statistics and census tract information.
    """
    # Set the file path and name of the shapefile
    csv_path = r"SVI_2022_US_county.csv"

    # Open the shapefile for reading
    data = pd.read_csv(csv_path)
    data = data.query(f"""ST_ABBR == '{state_abbr}' and COUNTY == '{county}' and {theme} {op} {threshold}""" )
    
    # Check if relevant features are empty
    if len(data)==0:
        return json.dumps({"Statistics": "No data available for the specified conditions."})

     # Create a new DataFrame with FIPS and SVI scores
    new_data = data[['FIPS', theme]].copy()
    new_data['FIPS'] = new_data['FIPS'].astype(int)

    # Calculate SVI statistics
    total_vulnerable_areas = len(new_data)
    max_svi = new_data[theme].max()
    min_svi = new_data[theme].min()
    avg_svi = round(new_data[theme].mean(), 4)

    # Create a dictionary with SVI statistics and census tract information
    result_dict = {
        "Statistics": {
            "Total_Areas": total_vulnerable_areas,
            "Max_SVI": max_svi,
            "Min_SVI": min_svi,
            "Average_SVI": avg_svi
        },
        "Census_Tracts": new_data.to_dict(orient='records')

    }

    # Convert the result dictionary to a JSON-formatted string
    result_json = json.dumps(result_dict, separators=(',', ':'))

    # Return the result as a JSON string
    return result_json
    
######################
def get_flash_flood_warnings(location):
    '''
    Retrieves flash flood warnings for a specified location from the National Weather Service API.

    Parameters:
    - location: Can be "None" for the entire United States or a specific state code (e.g., "NJ").

    Returns:
    - A JSON string of flood alerts. Each alert contains the event, description, time sent, expiration time, and the area description.
    '''

    base_url = "https://api.weather.gov/alerts/active"

    # Provide the location as a parameter, "None" for the entire United States or a state code (e.g., "NJ")
    if location is None:
        params = {"event": "Flood Warning"}
    else:
        params = {"area": location, "event": "Flood Warning"}

    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()

        # Extract the alert details
        alerts = []
        for feature in data['features']:
            properties = feature['properties']
            alert = {
                'event': properties['event'],
                'description': properties['description'],
                'sent': properties['sent'],
                'expires': properties['expires'],
                'areaDesc': properties['areaDesc'],
            }
            alerts.append(alert)

        # Convert the alerts list to a JSON string
        alerts_json = json.dumps(alerts)

        return alerts_json
    except requests.exceptions.RequestException as e:
        # Handle any request errors
        error_message = {"Error": str(e)}
        return json.dumps(error_message)
    
###########################################
FEMA_API_KEY = "H3gZzBLG5pa4IY0ja2E8599jy2ynEFIr3d87gCnk"
def get_flood_data(address, FEMA_API_KEY=FEMA_API_KEY):
    '''
    Retrieves flood risk data for a specified address using the National Flood Data API.
    
    Parameters:
    - address: The address for which flood data is requested.
    
    Returns:
    - A JSON string containing flood data for the specified address. This includes flood zone designation, risk level, and other related information.
    '''
    
    headers = {'x-api-key': FEMA_API_KEY}
    payload = {
      'address': address,
      'searchtype': 'addressparcel',
      'loma': False,
    }
    
    try:
        response = requests.get('https://api.nationalflooddata.com/v3/data', headers=headers, params=payload)
        response.raise_for_status()
        
        result_dict = response.json()
        result_json = json.dumps(result_dict)  
        return result_json
    except requests.exceptions.RequestException as e:
        # Handle any request errors and return a JSON string with the error message
        error_message = {"Error": str(e)}
        return json.dumps(error_message)
    
####################################################
#FEMA_API_KEY = "H3gZzBLG5pa4IY0ja2E8599jy2ynEFIr3d87gCnk"
def get_flood_map(latitude, longitude, zoom, FEMA_API_KEY=FEMA_API_KEY):
    '''
    Retrieves and saves a static map image indicating flood data for a specified location.
    
    Parameters:
    - latitude (float): The latitude of the location in standard geographic coordinate system.
    - longitude (float): The longitude of the location in standard geographic coordinate system.
    - zoom (int): The zoom level for the map.
    
    Returns:
    - A JSON string containing the latitude, longitude, and the name of the saved image file.
      If an error occurs while retrieving the static map, it returns a JSON string with the error message
      and ensures the interactive map will still be displayed.
    '''

    headers = {'x-api-key': FEMA_API_KEY}
    payload = {
      'lat': latitude,
      'lng': longitude,
      'height': 500,
      'width': 800,
      'showMarker': True,
      'showLegend': True,
      'zoom': zoom
    }
    
    try:
        response = requests.get('https://api.nationalflooddata.com/v3/staticmap', headers=headers, params=payload)
        response.raise_for_status()

        content_type = response.headers.get('Content-Type')
##################################################################changes!!!
         # Save response content to a file directly
        with open('output_static_map.png', 'wb') as f:
            f.write(response.content)

        # Open the image from the saved file to ensure it's valid
        try:
            image = Image.open('output_static_map.png')
            image.verify()  # Verify if it's a valid image
        except Exception as e:
            print(f"Error verifying the image: {e}")
            return {"error": "Invalid image file"}

###############################################################################
        if 'image' not in content_type:
            print("Received non-image content:")
            print(response.text)
            raise ValueError("The API did not return an image.")


        image = Image.open(io.BytesIO(response.content))

        # Save the image to a file
        image.save('output_static_map.png')

        # Return a JSON string with the relevant information
        result_json = json.dumps({
            'latitude': latitude,
            'longitude': longitude,
            'image_name': 'output_static_map.png'
        })

        return result_json
    except requests.exceptions.RequestException as e:
        
        # Return a JSON string with the error message
        error_message = {
            'latitude': latitude,
            'longitude': longitude,
            'image_name': f"Interactive map will display but an error occurred while retrieving static map: {str(e)}"
        }
        return json.dumps(error_message)
    

#Chat_base_section:
#f"""<s>[INST] <<SYS>>\n{your_system_message}\n<</SYS>>\n\n{user_message_1} [/INST] {model_reply_1}</s><s>[INST] {user_message_2} [/INST]"""
your_system_message = "You are an assistant that provides flood information relevant to the user queries. You may receive \
                    queries about flood alerts, Social Vulnerability Indexes (SVI) for a location, flood alerts, or display \
                    maps to the request of the user. Interactive maps are always displayed to the user. \
                    Always try your best to answer in natural language easy to understand using the available function calls."

original_prompt = f"""<s>[INST] <<SYS>>\n{your_system_message}\n<</SYS>>\n\n"""

def chat_function (role, message, previous_message= original_prompt):
    """
    Inputs:
    - previous_message: The message from the previous conversation
    - role: The role that generated the current message (e.g., user, system, assistant)
    - message: The new message/question to add to the conversation
    
    
    Returns:
    - Updated conversation log with the new message and answer from the Llama model
    """
    
    if role == 'user':
        if '</s>' not in previous_message:
            previous_message += f"""{message} [/INST]"""
        else:
            previous_message += f"""<s>[INST] {message} [/INST]"""
            
    elif role == 'assistant':
        previous_message += f"""{message}</s>"""
    else:
        print("error")
    
    return previous_message

# #result = get_svi_stats_and_tracts("MA","Middlesex","RPL_THEME2", ">=", 0.5)
# print(result)