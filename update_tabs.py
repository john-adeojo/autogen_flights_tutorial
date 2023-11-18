from sqlalchemy import create_engine, text
import json
import os
import yaml
import hashlib

def apis_configs():
    # Construct the full path to the configuration file
    script_dir = "G:/My Drive/Data-Centric Solutions/07. Blog Posts/AutoGen 2 - Flights"
    file_path = os.path.join(script_dir, "amadeus_api.yml")

    with open(file_path, 'r') as yamlfile:
        loaded_yamlfile = yaml.safe_load(yamlfile)
        api_key = loaded_yamlfile['api_key']
        api_secret = loaded_yamlfile['api_secret']
        host = loaded_yamlfile['host']
        password = loaded_yamlfile['password']
        username = loaded_yamlfile['username']
        database = loaded_yamlfile['database']     
           
    return api_key, api_secret, host, password, username, database

# Database connection function
def make_engine(username, password, host, database):
    conn_str = f'postgresql://{username}:{password}@{host}/{database}?sslmode=require'
    engine = create_engine(conn_str)
    return engine

# Main processing function
def process_amadeus_data(data, engine):
    json_data = json.dumps(data) 
    flight_offers = json.loads(json_data)

    with engine.begin() as connection:
        for offer in flight_offers:
            # Insert or update FlightOffer table
            flight_offer_id = insert_update_flight_offer(offer, connection)

            # Process Itineraries
            for itinerary in offer['itineraries']:
                itinerary_id = insert_update_itinerary(itinerary, flight_offer_id, connection)

                # Process Segments
                for segment in itinerary['segments']:
                    segment_id = insert_update_segment(segment, itinerary_id, connection)

            # Process TravelerPricings
            for traveler_pricing in offer['travelerPricings']:
                traveler_pricing_id = insert_update_traveler_pricing(traveler_pricing, flight_offer_id, connection)

                for fare_detail in traveler_pricing['fareDetailsBySegment']:
                    fare_detail_id = insert_update_fare_detail(fare_detail, segment_id, traveler_pricing_id, connection)


def generate_itinerary_id(offer_id, itinerary_data):
    """
    Generate a unique ID for an itinerary based on the flight offer ID and itinerary details.
    """
    itinerary_str = f"{offer_id}-{itinerary_data['duration']}-" + "-".join([segment['id'] for segment in itinerary_data['segments']])
    return hashlib.md5(itinerary_str.encode()).hexdigest()


# Function for inserting or updating FlightOffer
def insert_update_flight_offer(offer, connection):
    flight_offer_sql = """
    INSERT INTO FlightOffer (FlightOfferID, Source, InstantTicketingRequired, NonHomogeneous, OneWay, 
    LastTicketingDate, NumberOfBookableSeats, TotalPrice, Currency, GrandTotal, ValidatingAirlineCodes)
    VALUES (:FlightOfferID, :Source, :InstantTicketingRequired, :NonHomogeneous, :OneWay, 
    :LastTicketingDate, :NumberOfBookableSeats, :TotalPrice, :Currency, :GrandTotal, :ValidatingAirlineCodes)
    ON CONFLICT (FlightOfferID) DO UPDATE SET
    Source = EXCLUDED.Source, InstantTicketingRequired = EXCLUDED.InstantTicketingRequired,
    NonHomogeneous = EXCLUDED.NonHomogeneous, OneWay = EXCLUDED.OneWay, LastTicketingDate = EXCLUDED.LastTicketingDate,
    NumberOfBookableSeats = EXCLUDED.NumberOfBookableSeats, TotalPrice = EXCLUDED.TotalPrice, Currency = EXCLUDED.Currency,
    GrandTotal = EXCLUDED.GrandTotal, ValidatingAirlineCodes = EXCLUDED.ValidatingAirlineCodes
    RETURNING FlightOfferID;
    """
    params = {
        'FlightOfferID': offer['id'],
        'Source': offer['source'],
        'InstantTicketingRequired': offer['instantTicketingRequired'],
        'NonHomogeneous': offer['nonHomogeneous'],
        'OneWay': offer['oneWay'],
        'LastTicketingDate': offer['lastTicketingDate'],
        'NumberOfBookableSeats': offer['numberOfBookableSeats'],
        'TotalPrice': offer['price']['total'],
        'Currency': offer['price']['currency'],
        'GrandTotal': offer['price']['grandTotal'],
        'ValidatingAirlineCodes': json.dumps(offer['validatingAirlineCodes'])
    }
    flight_offer_id = connection.execute(text(flight_offer_sql), params).fetchone()[0]
    return flight_offer_id

# Function for inserting or updating Itinerary
import re
from sqlalchemy import text

def parse_duration(duration_str):
    # Find hours and minutes using regular expressions
    hours_match = re.search(r'(\d+)H', duration_str)
    minutes_match = re.search(r'(\d+)M', duration_str)

    # Convert hours and minutes to float
    hours = float(hours_match.group(1)) if hours_match else 0
    minutes = float(minutes_match.group(1)) if minutes_match else 0

    # Convert minutes to a fraction of an hour and add to hours
    total_duration = hours + minutes / 60
    return total_duration

def insert_update_itinerary(itinerary, flight_offer_id, connection):
    itinerary_id = generate_itinerary_id(flight_offer_id, itinerary)

    # Parse the duration string to convert it into a float
    duration_float = parse_duration(itinerary['duration'])

    itinerary_sql = """
    INSERT INTO Itinerary (ItineraryID, FlightOfferID, Duration)
    VALUES (:ItineraryID, :FlightOfferID, :Duration)
    ON CONFLICT (ItineraryID) DO UPDATE SET
    FlightOfferID = EXCLUDED.FlightOfferID, Duration = EXCLUDED.Duration
    RETURNING ItineraryID;
    """
    
    params = {
        'ItineraryID': itinerary_id,
        'FlightOfferID': flight_offer_id,
        'Duration': duration_float
    }
    result = connection.execute(text(itinerary_sql), params)
    return result.fetchone()[0]
# def insert_update_itinerary(itinerary, flight_offer_id, connection):
#     itinerary_id = generate_itinerary_id(flight_offer_id, itinerary)

#     itinerary_sql = """
#     INSERT INTO Itinerary (ItineraryID, FlightOfferID, Duration)
#     VALUES (:ItineraryID, :FlightOfferID, :Duration)
#     ON CONFLICT (ItineraryID) DO UPDATE SET
#     FlightOfferID = EXCLUDED.FlightOfferID, Duration = EXCLUDED.Duration
#     RETURNING ItineraryID;
#     """
    
#     params = {
#         'ItineraryID': itinerary_id,
#         'FlightOfferID': flight_offer_id,
#         'Duration': itinerary['duration']
#     }
#     result = connection.execute(text(itinerary_sql), params)
#     return result.fetchone()[0]

# Function for inserting or updating Segment
def insert_update_segment(segment, itinerary_id, connection):

    duration_float = parse_duration(segment['duration'])

    segment_sql = """
    INSERT INTO Segment (SegmentID, ItineraryID, DepartureIATACode, DepartureTerminal, DepartureTime,
    ArrivalIATACode, ArrivalTerminal, ArrivalTime, CarrierCode, FlightNumber, AircraftCode,
    Duration, NumberOfStops, BlacklistedInEU)
    VALUES (:SegmentID, :ItineraryID, :DepartureIATACode, :DepartureTerminal, :DepartureTime,
    :ArrivalIATACode, :ArrivalTerminal, :ArrivalTime, :CarrierCode, :FlightNumber, :AircraftCode,
    :Duration, :NumberOfStops, :BlacklistedInEU)
    ON CONFLICT (SegmentID) DO UPDATE SET
    ItineraryID = EXCLUDED.ItineraryID, DepartureIATACode = EXCLUDED.DepartureIATACode, 
    DepartureTerminal = EXCLUDED.DepartureTerminal, DepartureTime = EXCLUDED.DepartureTime, 
    ArrivalIATACode = EXCLUDED.ArrivalIATACode, ArrivalTerminal = EXCLUDED.ArrivalTerminal, 
    ArrivalTime = EXCLUDED.ArrivalTime, CarrierCode = EXCLUDED.CarrierCode, 
    FlightNumber = EXCLUDED.FlightNumber, AircraftCode = EXCLUDED.AircraftCode,
    Duration = EXCLUDED.Duration, NumberOfStops = EXCLUDED.NumberOfStops, 
    BlacklistedInEU = EXCLUDED.BlacklistedInEU
    RETURNING SegmentID;
    """
    params = {
        'SegmentID': segment['id'],
        'ItineraryID': itinerary_id,
        'DepartureIATACode': segment['departure']['iataCode'],
        'DepartureTerminal': segment['departure'].get('terminal', ''),
        'DepartureTime': segment['departure']['at'],
        'ArrivalIATACode': segment['arrival']['iataCode'],
        'ArrivalTerminal': segment['arrival'].get('terminal', ''),
        'ArrivalTime': segment['arrival']['at'],
        'CarrierCode': segment['carrierCode'],
        'FlightNumber': segment['number'],
        'AircraftCode': segment['aircraft']['code'],
        'Duration': duration_float,
        'NumberOfStops': segment.get('numberOfStops', 0),
        'BlacklistedInEU': segment.get('blacklistedInEU', False)
    }
    result = connection.execute(text(segment_sql), params)
    return result.fetchone()[0]


# Function for inserting or updating TravelerPricing
def insert_update_traveler_pricing(traveler_pricing, flight_offer_id, connection):
    traveler_pricing_sql = """
    INSERT INTO TravelerPricing (TravelerPricingID, FlightOfferID, TravelerId, FareOption, 
    TravelerType, PriceTotal, Currency)
    VALUES (:TravelerPricingID, :FlightOfferID, :TravelerId, :FareOption, :TravelerType, 
    :PriceTotal, :Currency)
    ON CONFLICT (TravelerPricingID) DO UPDATE SET
    FlightOfferID = EXCLUDED.FlightOfferID, TravelerId = EXCLUDED.TravelerId, 
    FareOption = EXCLUDED.FareOption, TravelerType = EXCLUDED.TravelerType, 
    PriceTotal = EXCLUDED.PriceTotal, Currency = EXCLUDED.Currency
    RETURNING TravelerPricingID;
    """
    params = {
        'TravelerPricingID': flight_offer_id,  # Assuming travelerId is unique
        'FlightOfferID': flight_offer_id,
        'TravelerId': traveler_pricing['travelerId'],
        'FareOption': traveler_pricing['fareOption'],
        'TravelerType': traveler_pricing['travelerType'],
        'PriceTotal': traveler_pricing['price']['total'],
        'Currency': traveler_pricing['price']['currency']
    }
    result = connection.execute(text(traveler_pricing_sql), params)
    return result.fetchone()[0]


# Function for inserting or updating FareDetailsBySegment
def insert_update_fare_detail(fare_detail, segment_id, traveler_pricing_id, connection):
    fare_detail_sql = """
    INSERT INTO FareDetailsBySegment (FareDetailID, TravelerPricingID, SegmentID, Cabin, 
    FareBasis, Class, IncludedCheckedBagsQuantity)
    VALUES (:FareDetailID, :TravelerPricingID, :SegmentID, :Cabin, :FareBasis, :Class, 
    :IncludedCheckedBagsQuantity)
    ON CONFLICT (FareDetailID) DO UPDATE SET
    TravelerPricingID = EXCLUDED.TravelerPricingID, SegmentID = EXCLUDED.SegmentID, 
    Cabin = EXCLUDED.Cabin, FareBasis = EXCLUDED.FareBasis, Class = EXCLUDED.Class, 
    IncludedCheckedBagsQuantity = EXCLUDED.IncludedCheckedBagsQuantity
    RETURNING FareDetailID;
    """
    # Generate or retrieve the FareDetailID
    fare_detail_id = fare_detail.get('id')  # Replace with your logic if 'id' is not available

    params = {
        'FareDetailID': segment_id,
        'TravelerPricingID': traveler_pricing_id,
        'SegmentID': fare_detail['segmentId'],
        'Cabin': fare_detail['cabin'],
        'FareBasis': fare_detail['fareBasis'],
        'Class': fare_detail['class'],
        'IncludedCheckedBagsQuantity': fare_detail.get('includedCheckedBags', {}).get('quantity', 0)
        # 'IncludedCheckedBagsQuantity': fare_detail['includedCheckedBags']['quantity'] if 'includedCheckedBags' in fare_detail else 0
    }
    result = connection.execute(text(fare_detail_sql), params)
    return result.fetchone()[0]