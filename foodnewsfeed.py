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
    # Preselect "Food Quality & Safety" feed
    default_feeds = ["Food Quality & Safety"]
    selected_feeds = st.multiselect("Select Feeds:", feeds, default=default_feeds)

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
    def generate_button_html(index):
        return f'<button class="add-review-btn" onclick="window.dispatchEvent(new CustomEvent(\'add_to_review\', {{ detail: {index} }}))">➕</button>'

    filtered_df['Add to Review'] = filtered_df.index.to_series().apply(generate_button_html)
    
    # Display the table with the "Add to Review" buttons as the last column
    filtered_df['link'] = filtered_df['link'].apply(lambda x: f'<a href="{x}" target="_blank">Read More</a>')
    st.write(filtered_df.to_html(escape=False, index=False, columns=["published", "title", "summary", "link", "Add to Review"]), unsafe_allow_html=True)

    # Capture button click events using custom JavaScript
    st.markdown("""
        <script>
        const addReviewBtns = document.querySelectorAll('.add-review-btn');
        addReviewBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                const index = btn.getAttribute('onclick').match(/detail: (\d+)/)[1];
                const evt = new CustomEvent('add_to_review', { detail: index });
                window.dispatchEvent(evt);
            });
        });
        window.addEventListener('add_to_review', event => {
            const index = parseInt(event.detail);
            console.log('Adding to review:', index);
            window.streamlitAPI.rerun();
        });
        </script>
        """, unsafe_allow_html=True)

    # Add selected articles to review in session_state
    for index in filtered_df.index:
        if st.session_state.get(f"add_{index}_to_review", False):
            if "review_articles" not in st.session_state:
                st.session_state["review_articles"] = []
            st.session_state["review_articles"].append(filtered_df.loc[index])
            st.session_state[f"add_{index}_to_review"] = False

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



