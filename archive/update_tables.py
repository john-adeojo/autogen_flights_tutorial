from sqlalchemy import create_engine
import json
import os
import yaml
from sqlalchemy import create_engine, text

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
        
    return api_key, api_secret, host, password

# Database connection function
def make_engine(username, password, host, database):
    conn_str = f'postgresql://{username}:{password}@{host}/{database}?sslmode=require'
    engine = create_engine(conn_str)
    return engine

# Main processing function
def process_amadeus_data(data, engine):
    json_data = json.dumps(data) 
    flight_offers = json.loads(json_data)
    print(flight_offers)

    with engine.begin() as connection:
        for offer in flight_offers:
            # Insert or update Flights table
            flight_id = insert_update_flight(offer, connection)

            # Process Itineraries
            for itinerary in offer['itineraries']:
                itinerary_id = insert_update_itinerary(itinerary, flight_id, connection)

                # Process Segments
                for segment in itinerary['segments']:
                    segment_id = insert_update_segment(segment, itinerary_id, connection)

                    # Process Stops if present
                    if 'stops' in segment and segment['stops']:
                        for stop in segment['stops']:
                            insert_update_stop(stop, segment_id, connection)

            # Process Prices
            price_id = insert_update_price(offer['price'], flight_id, connection)

            # Process Fees
            for fee in offer['price']['fees']:
                insert_update_fee(fee, price_id, connection)

            # Process TravelerPricings
            for traveler_pricing in offer['travelerPricings']:
                traveler_pricing_id = insert_update_traveler_pricing(traveler_pricing, flight_id, connection)

                # Process FareDetailsBySegment
                for fare_detail in traveler_pricing['fareDetailsBySegment']:
                    insert_update_fare_detail(fare_detail, traveler_pricing_id, connection)

# Function for inserting or updating flights
def insert_update_flight(offer, connection):
    flight_sql = """
    INSERT INTO flights (id, type, source, instantTicketingRequired, nonHomogeneous, oneWay, 
    lastTicketingDate, lastTicketingDateTime, numberOfBookableSeats, validatingAirlineCodes)
    VALUES (:id, :type, :source, :instantTicketingRequired, :nonHomogeneous, :oneWay, :lastTicketingDate, 
    :lastTicketingDateTime, :numberOfBookableSeats, :validatingAirlineCodes)
    ON CONFLICT (id) DO UPDATE SET
    type = EXCLUDED.type, source = EXCLUDED.source, instantTicketingRequired = EXCLUDED.instantTicketingRequired,
    nonHomogeneous = EXCLUDED.nonHomogeneous, oneWay = EXCLUDED.oneWay, lastTicketingDate = EXCLUDED.lastTicketingDate,
    lastTicketingDateTime = EXCLUDED.lastTicketingDateTime, numberOfBookableSeats = EXCLUDED.numberOfBookableSeats,
    validatingAirlineCodes = EXCLUDED.validatingAirlineCodes
    RETURNING id;
    """
    params = {
        'id': offer['id'],
        'type': offer['type'],
        'source': offer['source'],
        'instantTicketingRequired': offer['instantTicketingRequired'],
        'nonHomogeneous': offer['nonHomogeneous'],
        'oneWay': offer['oneWay'],
        'lastTicketingDate': offer['lastTicketingDate'],
        'lastTicketingDateTime': offer['lastTicketingDateTime'],
        'numberOfBookableSeats': offer['numberOfBookableSeats'],
        'validatingAirlineCodes': json.dumps(offer['validatingAirlineCodes'])
    }
    flight_id = connection.execute(text(flight_sql), params).fetchone()[0]
    return flight_id

# Function for inserting or updating itineraries
def insert_update_itinerary(itinerary, flight_id, connection):
    itinerary_sql = """
    INSERT INTO itineraries (id, flight_id, duration)
    VALUES (:id, :flight_id, :duration)
    ON CONFLICT (id) DO UPDATE SET
    flight_id = EXCLUDED.flight_id, duration = EXCLUDED.duration
    RETURNING id;
    """
    params = {
        'id': itinerary.get('id', flight_id),  # Provide a default value or logic to handle missing 'id'
        'flight_id': flight_id,
        'duration': itinerary.get('duration', 'default_duration')  # Handle missing 'duration' similarly
    }
    itinerary_id = connection.execute(text(itinerary_sql), params).fetchone()[0]
    return itinerary_id

# Function for inserting or updating segments
def insert_update_segment(segment, itinerary_id, connection):
    segment_sql = """
    INSERT INTO segments (id, itinerary_id, departure_iataCode, departure_terminal, departure_at, 
    arrival_iataCode, arrival_terminal, arrival_at, carrierCode, number, aircraft_code, 
    operating_carrierCode, duration, numberOfStops, blacklistedInEU)
    VALUES (:id, :itinerary_id, :departure_iataCode, :departure_terminal, :departure_at, 
    :arrival_iataCode, :arrival_terminal, :arrival_at, :carrierCode, :number, :aircraft_code, 
    :operating_carrierCode, :duration, :numberOfStops, :blacklistedInEU)
    ON CONFLICT (id) DO UPDATE SET
    itinerary_id = EXCLUDED.itinerary_id, departure_iataCode = EXCLUDED.departure_iataCode, 
    departure_terminal = EXCLUDED.departure_terminal, departure_at = EXCLUDED.departure_at, 
    arrival_iataCode = EXCLUDED.arrival_iataCode, arrival_terminal = EXCLUDED.arrival_terminal, 
    arrival_at = EXCLUDED.arrival_at, carrierCode = EXCLUDED.carrierCode, number = EXCLUDED.number, 
    aircraft_code = EXCLUDED.aircraft_code, operating_carrierCode = EXCLUDED.operating_carrierCode, 
    duration = EXCLUDED.duration, numberOfStops = EXCLUDED.numberOfStops, blacklistedInEU = EXCLUDED.blacklistedInEU
    RETURNING id;
    """
    params = {
        'id': segment['id'],
        'itinerary_id': itinerary_id,
        'departure_iataCode': segment['departure']['iataCode'],
        'departure_terminal': segment['departure'].get('terminal'),
        'departure_at': segment['departure']['at'],
        'arrival_iataCode': segment['arrival']['iataCode'],
        'arrival_terminal': segment['arrival'].get('terminal'),
        'arrival_at': segment['arrival']['at'],
        'carrierCode': segment['carrierCode'],
        'number': segment['number'],
        'aircraft_code': segment['aircraft']['code'],
        'operating_carrierCode': segment['operating']['carrierCode'],
        'duration': segment['duration'],
        'numberOfStops': segment['numberOfStops'],
        'blacklistedInEU': segment['blacklistedInEU']
    }
    segment_id = connection.execute(text(segment_sql), params).fetchone()[0]
    return segment_id

# Function for inserting or updating stops
def insert_update_stop(stop, segment_id, connection):
    # Assuming 'id' key should be present in stop dictionary
    if 'id' not in stop:
        # Handle the missing 'id'. You can skip or use a default value
        return  # Skipping the record

    stop_sql = """
    INSERT INTO stops (id, segment_id, iataCode, duration, arrivalAt, departureAt)
    VALUES (:id, :segment_id, :iataCode, :duration, :arrivalAt, :departureAt)
    ON CONFLICT (id) DO UPDATE SET
    segment_id = EXCLUDED.segment_id, iataCode = EXCLUDED.iataCode, 
    duration = EXCLUDED.duration, arrivalAt = EXCLUDED.arrivalAt, departureAt = EXCLUDED.departureAt;
    """
    params = {
        'id': segment_id,
        'segment_id': segment_id,
        'iataCode': stop['iataCode'],
        'duration': stop['duration'],
        'arrivalAt': stop['arrivalAt'],
        'departureAt': stop['departureAt']
    }
    connection.execute(text(stop_sql), params)

# Function for inserting or updating prices
def insert_update_price(price, flight_id, connection):
    price_sql = """
    INSERT INTO prices (id, flight_id, currency, total, base, grandTotal)
    VALUES (:id, :flight_id, :currency, :total, :base, :grandTotal)
    ON CONFLICT (id) DO UPDATE SET
    flight_id = EXCLUDED.flight_id, currency = EXCLUDED.currency, total = EXCLUDED.total, 
    base = EXCLUDED.base, grandTotal = EXCLUDED.grandTotal
    RETURNING id;
    """
    params = {
        'id': price.get('id', flight_id),  # Provide a default or handle missing 'id'
        'flight_id': flight_id,
        'currency': price['currency'],
        'total': price['total'],
        'base': price['base'],
        'grandTotal': price['grandTotal']
    }
    price_id = connection.execute(text(price_sql), params).fetchone()[0]
    return price_id

# Function for inserting or updating fees
def insert_update_fee(fee, price_id, connection):
    if 'id' not in fee:
        # Skip this fee or handle the lack of an 'id' appropriately
        return
    
    fee_sql = """
    INSERT INTO fees (id, price_id, amount, type)
    VALUES (:id, :price_id, :amount, :type)
    ON CONFLICT (id) DO UPDATE SET
    price_id = EXCLUDED.price_id, amount = EXCLUDED.amount, type = EXCLUDED.type;
    RETURNING id;
    """
    params = {
        'id': fee['id'],
        'price_id': price_id,
        'amount': fee['amount'],
        'type': fee['type']
    }
    connection.execute(text(fee_sql), params)

# Function for inserting or updating traveler pricings
def insert_update_traveler_pricing(traveler_pricing, flight_id, connection):
    # Check for 'id' in traveler_pricing, if not present, use a default value or skip
    traveler_pricing_id_value = traveler_pricing.get('id')
    if traveler_pricing_id_value is None:
        # Handle the absence of 'id' appropriately
        return None  # Or some logic to provide a default or skip this entry

    traveler_pricing_sql = """
    INSERT INTO travelerpricings (id, flight_id, travelerId, fareOption, travelerType, currency, total, base)
    VALUES (:id, :flight_id, :travelerId, :fareOption, :travelerType, :currency, :total, :base)
    ON CONFLICT (id) DO UPDATE SET
    flight_id = EXCLUDED.flight_id, travelerId = EXCLUDED.travelerId, fareOption = EXCLUDED.fareOption, 
    travelerType = EXCLUDED.travelerType, currency = EXCLUDED.currency, total = EXCLUDED.total, base = EXCLUDED.base
    RETURNING id;
    """
    params = {
        'id': traveler_pricing_id_value,
        'flight_id': flight_id,
        'travelerId': traveler_pricing['travelerId'],
        'fareOption': traveler_pricing['fareOption'],
        'travelerType': traveler_pricing['travelerType'],
        'currency': traveler_pricing['price']['currency'],
        'total': traveler_pricing['price']['total'],
        'base': traveler_pricing['price']['base']
    }
    traveler_pricing_id = connection.execute(text(traveler_pricing_sql), params).fetchone()[0]
    return traveler_pricing_id

# Function for inserting or updating fare details by segment
def insert_update_fare_detail(fare_detail, traveler_pricing_id, connection):
    if 'id' not in fare_detail:
        # Handle the missing 'id'. You can skip or use a default value
        return  # Skipping the record

    fare_detail_sql = """
    INSERT INTO faredetailsbysegment (
        id, travelerPricing_id, segmentId, cabin, fareBasis, class, 
        includedCheckedBags_quantity, includedCheckedBags_weight, includedCheckedBags_weightUnit
    )
    VALUES (:id, :travelerPricing_id, :segmentId, :cabin, :fareBasis, :class, 
    :includedCheckedBags_quantity, :includedCheckedBags_weight, :includedCheckedBags_weightUnit)
    ON CONFLICT (id) DO UPDATE SET
        travelerPricing_id = EXCLUDED.travelerPricing_id,
        segmentId = EXCLUDED.segmentId,
        cabin = EXCLUDED.cabin,
        fareBasis = EXCLUDED.fareBasis,
        class = EXCLUDED.class,
        includedCheckedBags_quantity = EXCLUDED.includedCheckedBags_quantity,
        includedCheckedBags_weight = EXCLUDED.includedCheckedBags_weight,
        includedCheckedBags_weightUnit = EXCLUDED.includedCheckedBags_weightUnit;
    """
    params = {
        'id': fare_detail[traveler_pricing_id],
        'travelerPricing_id': traveler_pricing_id,
        'segmentId': fare_detail['segmentId'],
        'cabin': fare_detail['cabin'],
        'fareBasis': fare_detail['fareBasis'],
        'class': fare_detail['class'],
        'includedCheckedBags_quantity': fare_detail['includedCheckedBags'].get('quantity') if 'includedCheckedBags' in fare_detail else None,
        'includedCheckedBags_weight': fare_detail['includedCheckedBags'].get('weight') if 'includedCheckedBags' in fare_detail else None,
        'includedCheckedBags_weightUnit': fare_detail['includedCheckedBags'].get('weightUnit') if 'includedCheckedBags' in fare_detail else None
    }
    connection.execute(text(fare_detail_sql), params)
