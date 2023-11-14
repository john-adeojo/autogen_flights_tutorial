import os
import yaml
import psycopg2
from sqlalchemy import create_engine, text
import traceback

def get_apikey():
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
_, _, host, password = get_apikey()

database = "flights_data"
username = "john-adeojo"

USERNAME = username
PASSWORD = password
HOST = host
PORT = "5432"
DATABASE = database

print(f"host:{host}, database:{database}, username:{username}, password:{password}")

def create_schema(USERNAME, PASSWORD, HOST, DATABASE):

    USERNAME = USERNAME
    PASSWORD = PASSWORD
    HOST = HOST
    DATABASE = DATABASE

    conn_str = f'postgresql://{USERNAME}:{PASSWORD}@{HOST}/{DATABASE}?sslmode=require'
    engine = create_engine(conn_str)

    print(f"Connection String: {conn_str}")
    print(f"Connection Established: {engine}")

    # Execute SQL commands to create tables
    commands = [
        """
        CREATE TABLE IF NOT EXISTS Flights (
            id SERIAL PRIMARY KEY,
            type VARCHAR(255),
            source VARCHAR(255),
            instantTicketingRequired BOOLEAN,
            nonHomogeneous BOOLEAN,
            oneWay BOOLEAN,
            lastTicketingDate DATE,
            lastTicketingDateTime TIMESTAMP,
            numberOfBookableSeats INT,
            validatingAirlineCodes TEXT
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS Itineraries (
            id SERIAL PRIMARY KEY,
            flight_id INT REFERENCES Flights(id),
            duration INTERVAL
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS Segments (
            id SERIAL PRIMARY KEY,
            itinerary_id INT REFERENCES Itineraries(id),
            departure_iataCode VARCHAR(10),
            departure_terminal VARCHAR(10),
            departure_at TIMESTAMP,
            arrival_iataCode VARCHAR(10),
            arrival_terminal VARCHAR(10),
            arrival_at TIMESTAMP,
            carrierCode VARCHAR(10),
            number VARCHAR(10),
            aircraft_code VARCHAR(10),
            operating_carrierCode VARCHAR(10),
            duration INTERVAL,
            numberOfStops INT,
            blacklistedInEU BOOLEAN
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS Prices (
            id SERIAL PRIMARY KEY,
            flight_id INT REFERENCES Flights(id),
            currency VARCHAR(10),
            total DECIMAL,
            base DECIMAL,
            grandTotal DECIMAL
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS Fees (
            id SERIAL PRIMARY KEY,
            price_id INT REFERENCES Prices(id),
            amount DECIMAL,
            type VARCHAR(255)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS TravelerPricings (
            id SERIAL PRIMARY KEY,
            flight_id INT REFERENCES Flights(id),
            travelerId VARCHAR(255),
            fareOption VARCHAR(255),
            travelerType VARCHAR(255),
            currency VARCHAR(10),
            total DECIMAL,
            base DECIMAL
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS FareDetailsBySegment (
            id SERIAL PRIMARY KEY,
            travelerPricing_id INT REFERENCES TravelerPricings(id),
            segmentId INT,
            cabin VARCHAR(255),
            fareBasis VARCHAR(255),
            class VARCHAR(10),
            includedCheckedBags_quantity INT,
            includedCheckedBags_weight INT,
            includedCheckedBags_weightUnit VARCHAR(10)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS Stops (
            id SERIAL PRIMARY KEY,
            segment_id INT REFERENCES Segments(id),
            iataCode VARCHAR(10),
            duration INTERVAL,
            arrivalAt TIMESTAMP,
            departureAt TIMESTAMP
        )
        """
    ]

    with engine.connect() as conn:
        try:
            for command in commands:
                print(f"Executing command: {command}")
                conn.execute(text(command))

            # After creating tables, query the list of tables to confirm creation
            table_check_query = "SELECT tablename FROM pg_tables WHERE schemaname = 'public';"
            result = conn.execute(text(table_check_query))
            tables = result.fetchall()
            print("List of tables in the 'public' schema:")
            for table in tables:
                print(table[0])  # Instead of print(table['tablename'])


            print("All commands executed successfully.")
        except Exception as e:
            print(f"An error occurred: {e}")
            traceback.print_exc()
            conn.rollback()

    # with engine.connect() as conn:
    #     try:
    #         for command in commands:
    #             conn.execute(text(command))
    #     except Exception as e:
    #         print(f"An error occurred: {e}")
    #         traceback.print_exc()  # Print full traceback
    #         conn.rollback()

create_schema(USERNAME, PASSWORD, HOST, DATABASE)