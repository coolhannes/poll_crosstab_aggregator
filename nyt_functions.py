import re

import pandas as pd
import requests
from bs4 import BeautifulSoup


# Function to get question text
def get_question_text(question_block):
    question_text = question_block.find(
        "p", class_="g-table-text g-tab-question"
    ).get_text(strip=True)
    return question_text


# Function to get demographic categories and their spans
def get_demo_categories_and_spans(question_block):
    categories_and_spans = []
    pattern = re.compile(r"^tab-group")

    # Find all th elements that match the pattern and are within the limit of categories expected
    for th in question_block.find_all("th", class_=pattern):
        category_text = th.find(
            "p", class_="g-table-text g-tab-label g-table-heading"
        ).get_text(strip=True)
        colspan = int(th["colspan"]) if th.has_attr("colspan") else 1
        categories_and_spans.append((category_text, colspan))

    return categories_and_spans


# Function to get demographic groups
def get_demo_groups(question_block):
    demo_groups = [
        "All",
    ]
    demo_groups_row = question_block.find("tr", class_="g-demo-groups")

    for th in demo_groups_row.find_all("th"):
        demo = th.get_text(strip=True)
        demo_groups.append(demo)

    return demo_groups


# Function to map categories to their respective groups
def map_categories_to_groups(categories_and_spans, demo_groups):
    mapped_categories_to_groups = {}
    group_index = 0

    for category, span in categories_and_spans:
        mapped_categories_to_groups[category] = demo_groups[
            group_index : group_index + span
        ]
        group_index += span

    concatenated_list = []

    for key, values in mapped_categories_to_groups.items():
        for value in values:
            concatenated_list.append(f"{key}_{value}")

    return concatenated_list


# Main loop to process each question block


def get_crosstabs(url):

    data = []

    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")

    # Extract the main table
    main_table = soup.find("table", class_="nyt-crosstabs")

    for question_block in main_table.find_all("tbody"):

        question_text = get_question_text(question_block)

        # Check if there are no response rows
        if not question_block.find_all("tr", class_=re.compile(r"^g-row")):
            # This is a question-only section, so skip it
            continue

        categories_and_spans = get_demo_categories_and_spans(question_block)
        demo_groups = get_demo_groups(question_block)
        mapped_categories_to_groups = map_categories_to_groups(
            categories_and_spans, demo_groups
        )

        # Get responses
        response_rows_pattern = re.compile(r"^g-row")
        response_rows = question_block.find_all(
            "tr", class_=response_rows_pattern, limit=12
        )

        for response_row in response_rows:

            try:
                response_label = response_row.find(
                    "p", class_=re.compile(r"^g-table-text")
                ).get_text(strip=True)
            except:
                continue

            percentages = [
                td.get_text(strip=True)
                for td in response_row.find_all("p", class_="g-table-text g-tab-pct")
            ]

            # Combine question, response, and percentages
            row = [question_text, response_label] + percentages
            data.append(row)

        columns = ["Question", "Response"] + mapped_categories_to_groups
        df = pd.DataFrame(data, columns=columns)

    return df
