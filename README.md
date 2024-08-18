# Food Safety News & Reviews Application

## Overview

The **Food Safety News & Reviews** application is a Streamlit-based tool designed to aggregate and manage food safety-related news from multiple RSS feeds. Users can view, filter, and select articles from various sources to create a personalized review report. The app supports customization of the selected articles and provides options to download or edit the review.

## Features

- **Multiple RSS Feeds**: The app aggregates articles from multiple RSS feeds, including EU Legislation, EFSA, EU Food Safety, Food Quality & Safety, Food Safety News, and others.
  
- **Customizable Feed Selection**: Users can select which feeds to include in their news aggregation from the sidebar, with "Food Quality & Safety" pre-selected by default. Other feeds can be added or removed as needed.
  
- **Date Filtering**: Users can filter articles based on a specific date range, ensuring that only relevant articles are displayed.

- **Article Display**: Articles are displayed in a structured format that includes the publication date, title, summary, and a link to the full article. Users can easily browse through the latest updates.

- **Add to Review**: Each article has an associated "+" button, allowing users to add the article to a personalized review list. This feature is useful for collecting articles for later reference or creating a report.

- **Edit Mode**: Users can enter an edit mode to modify the summaries of selected articles in their review list, allowing for tailored commentary or notes.

- **Review Export**: Once articles are selected for review, users can download the list as a CSV file or use it to generate a report.

- **Download Options**: The app provides the option to download the final review as a CSV file, making it easy to share or archive.

## How to Use

1. **Select Feeds**: Start by selecting the RSS feeds from which you want to aggregate news. By default, "Food Quality & Safety" is selected, but you can add or remove feeds via the sidebar.

2. **Filter by Date**: Use the date filters to specify the range of articles you want to see. The articles will be filtered according to the dates you select.

3. **Browse Articles**: Scroll through the list of articles displayed in the main area. Each article will show the publication date, title, summary, and a link to the full content.

4. **Add Articles to Review**: Click the "+" button next to any article you wish to add to your personalized review. The article will be added to your review list.

5. **Edit Review**: If you want to customize the summaries of the articles you've selected, click "Edit Selected Articles for Report" in the sidebar. This will allow you to modify the text for each article in your review list.

6. **Download or Share**: Once you're satisfied with your review, you can download it as a CSV file by clicking "Download Review as CSV" in the sidebar. This file includes all selected articles with their titles, summaries, and links.

## Installation

To run this application locally, follow these steps:

1. Clone the repository.
2. Install the required dependencies with `pip install -r requirements.txt`.
3. Run the application with `streamlit run app.py`.

## Contributing

Contributions are welcome! Feel free to submit a pull request or report issues.

## License

This project is licensed under the MIT License.
