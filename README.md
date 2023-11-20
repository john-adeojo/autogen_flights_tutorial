This repository supplements the blog post and YouTube video.

----

## Prerequisites

You need access to:

* [Amadeus](https://developers.amadeus.com/self-service/category/flights/api-doc/flight-offers-search/api-reference) - Sign up to the developer platform to obtain your secret key and API key.
* [Neon](https://neon.tech/) - Sign up to Neon and create a project.
* [OpenAI](https://openai.com/) - Obtain an OpenAI API key.

Set up your Amadeus API key and your Neon Project.

Note - Ensure you name the database `flights_data` to avoid the need for changing this in the code.

## Get Started

Clone this repository to a directory you have access to.
Create a virtual environment and install the libraries in the `requirements.txt` file.

If you're using Anaconda, navigate to the folder where you cloned this repository and follow the steps below:

1. Create a new environment: `conda create -n <your-env-name> python=3.9 pip`
2. Activate the environment: `conda activate <your-environment-name>`
3. Install requirements: `pip install -r requirements.txt`

## Set-Up

Start by amending the credentials in the `amadeus_api.yml` file.
Next, amend the credentials in the `configurations.json` file.

Open the `flights_tutorial_notebook.ipynb` and change the `configurations_path` to point to your `configurations.json`.

Open the `update_tabs.py` and change the `script_dir` path on line 9 to point to your `amadeus_api.yml` file location.

## That's it for the Setup

# Auto Gen Tutorial - Flights Assistant

Notebook written by John Adeojo
Founder, and Chief Data Scientist at [Data-centric Solutions](https://www.data-centric-solutions.com/).

---
# License

This work is licensed under a [Creative Commons Attribution 4.0 International License](http://creativecommons.org/licenses/by/4.0/).

## How to Credit

If you use or adapt this work, please credit the author and the company as follows:

"Auto Gen Flights Tutorial" by John Adeojo from Data-Centric Solutions, used under CC BY 4.0 / Desaturated from original.

## Example Citation


