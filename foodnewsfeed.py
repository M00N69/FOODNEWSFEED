import streamlit as st
import feedparser
import pandas as pd
from datetime import datetime
from pytz import timezone

# Configurer la page pour un affichage en mode large
st.set_page_config(layout="wide")

# Define your list of RSS feeds
rss_feeds = {
    "EU Legislation": "https://eur-lex.europa.eu/EN/display-feed.rss?myRssId=e1Wry6%2FANeUpe1f1%2BCToXcHk31CTyaJK",
    "EFSA": "https://www.efsa.europa.eu/en/all/rss",
    "EU Food Safety": "https://food.ec.europa.eu/node/2/rss_en",
    "Food Quality & Safety": "https://www.foodqualityandsafety.com/category/eupdate/feed/",
    "Food Safety News": "https://feeds.lexblog.com/foodsafetynews/mRcs",
    "Food Manufacture": "https://www.foodmanufacture.co.uk/Info/FoodManufacture-RSS",
    "Food Packaging Forum": "https://www.foodpackagingforum.org/news/feed/",
    "ANSES": "https://www.anses.fr/fr/flux-actualites.rss"
}

# Function to parse all RSS feeds
def parse_feeds(selected_feeds):
    data = []
    for feed_name, feed_url in rss_feeds.items():
        if feed_name in selected_feeds:
            parsed_feed = feedparser.parse(feed_url)
            for entry in parsed_feed.entries[:8]:  # Get the latest 8 articles
                data.append({
                    "feed": feed_name,
                    "title": entry.title,
                    "link": entry.link,
                    "summary": entry.summary,
                    "published": datetime(*entry.published_parsed[:6]).strftime("%Y-%m-%d"),
                    "image": entry.get("media_content", [None])[0].get("url", None) if "media_content" in entry else None
                })
    df = pd.DataFrame(data).sort_values(by="published", ascending=False)  # Sort by date, latest first
    return df

# Sidebar for navigation
with st.sidebar:
    st.header("Navigation")
    st.write("Select the news sources:")

    feeds = list(rss_feeds.keys())
    selected_feeds = st.multiselect("Select Feeds:", feeds, default=feeds)  # All feeds selected by default

    # Date filter
    min_date = st.date_input("Start date", value=pd.to_datetime("2023-01-01"))
    max_date = st.date_input("End date", value=datetime.now().date())

    paris_timezone = timezone('Europe/Paris')
    st.write(f"Last Update: {datetime.now(paris_timezone).strftime('%Y-%m-%d %H:%M:%S')}")

    # Option to download the selected review as CSV
    if "review_articles" in st.session_state and st.session_state["review_articles"]:
        review_df = pd.DataFrame(st.session_state["review_articles"])
        csv = review_df.to_csv(index=False)
        st.download_button(label="Download Review as CSV", data=csv, file_name="review.csv", mime="text/csv")

# Parse feeds based on selected sources
feeds_df = parse_feeds(selected_feeds)

# Filter articles by date
feeds_df['published'] = pd.to_datetime(feeds_df['published'])
filtered_df = feeds_df[(feeds_df['published'] >= pd.to_datetime(min_date)) & (feeds_df['published'] <= pd.to_datetime(max_date))]

# Main section to display articles
st.markdown("---")
st.header("Selected Articles")

if not filtered_df.empty:
    # Add a column for "Add to Review" buttons
    def add_to_review_button(row):
        # Create a unique key for each button based on the row index
        button_label = f"Add {row.name}"
        if st.button("➕", key=button_label, help="Add to Review"):
            st.session_state["review_articles"].append(row)

    filtered_df["Add to Review"] = filtered_df.apply(add_to_review_button, axis=1)
    
    # Display the table with the "Add to Review" buttons as the last column
    filtered_df_display = filtered_df[["published", "title", "summary", "link"]]
    filtered_df_display['link'] = filtered_df_display['link'].apply(lambda x: f'<a href="{x}" target="_blank">Read More</a>')
    
    st.write(filtered_df_display.to_html(escape=False, index=False), unsafe_allow_html=True)

else:
    st.write("No articles available for the selected sources and date range.")

# Display selected articles for review
if "review_articles" in st.session_state and st.session_state["review_articles"]:
    st.markdown("---")
    st.header("Your Review")

    review_df = pd.DataFrame(st.session_state["review_articles"])
    for i, article in review_df.iterrows():
        st.markdown(f"### {i+1}. {article['title']}")
        st.markdown(f"**Published on:** {article['published'].strftime('%Y-%m-%d')}")
        st.markdown(f"{article['summary']}")
        st.markdown(f"[Read More]({article['link']})")

    st.markdown("---")
    review_text = st.text_area("Add your review here:", height=150)

    st.markdown("---")
    download_format = st.selectbox("Download Format:", ["PDF", "Email"])
    # PDF and Email logic remains unchanged

st.write("App finished setup.")


