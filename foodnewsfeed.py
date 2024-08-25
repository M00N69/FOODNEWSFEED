import streamlit as st
import feedparser
import pandas as pd
from datetime import datetime
from pytz import timezone
from groq import Groq
import requests
import re

# Configuring the page layout
st.set_page_config(layout="wide")

# Custom CSS with corrected color code
st.markdown(
    """
    <style>
    [data-testid="stSidebar"] {
        background-color: #2398B2;  
    }
    .banner {
        background-image: url('https://github.com/M00N69/BUSCAR/blob/main/logo%2002%20copie.jpg?raw=true');
        background-size: cover;
        padding: 75px;
        text-align: center;
    }
    .dataframe td {
        white-space: normal !important;
        word-wrap: break-word !important;
    }
    </style>
    <div class="banner"></div>
    """,
    unsafe_allow_html=True
)

# Initialize session state variables
if 'showing_readme' not in st.session_state:
    st.session_state['showing_readme'] = True

if 'review_articles' not in st.session_state:
    st.session_state['review_articles'] = []

# URL brute du README.md sur GitHub (ou vous pouvez ajouter le contenu directement ici)
readme_url = "https://raw.githubusercontent.com/M00N69/FOODNEWSFEED/main/README.md"

def load_readme(url):
    response = requests.get(url)
    if response.status_code == 200:
        return response.text
    else:
        return "Sorry, we couldn't load the README file from GitHub."

# Toggle button to switch between README and main content
if st.button("Toggle About this APP"):
    st.session_state['showing_readme'] = not st.session_state['showing_readme']

# Define your list of RSS feeds
rss_feeds = {
    "Food safety Magazine": "https://www.food-safety.com/rss/topic/296",
    "Food SafetyTech": "https://foodsafetytech.com/feed/",
    "Food Navigator": "https://www.foodnavigator.com/Info/Latest-News",
    "Food GOV UK": "https://www.food.gov.uk/rss-feed/news",
    "US CDC": "https://www2c.cdc.gov/podcasts/createrss.asp?c=146",
    "US FDA Press Reelase": "https://www.fda.gov/about-fda/contact-fda/stay-informed/rss-feeds/press-releases/rss.xml",
    "Food in Canada": "https://www.foodincanada.com/feed/",
    "CODEX Hygiene meeting": "https://www.fao.org/fao-who-codexalimentarius/meetings/detail/rss/fr/?meeting=CCFH&session=54",
    "RASFF EU Feed": "https://webgate.ec.europa.eu/rasff-window/backend/public/consumer/rss/all/",
    "EFSA": "https://www.efsa.europa.eu/en/all/rss",
    "EU Food Safety": "https://food.ec.europa.eu/node/2/rss_en",
    "Food Quality & Safety": "https://www.foodqualityandsafety.com/category/eupdate/feed/",
    "Food Safety News": "https://feeds.lexblog.com/foodsafetynews/mRcs",
    "Food Manufacture": "https://www.foodmanufacture.co.uk/Info/FoodManufacture-RSS",
    "Food Packaging Forum": "https://www.foodpackagingforum.org/news/feed/",
    "Food Safety Expert": "https://www.foodsafety-experts.com/feed/",
    "French Recalls RAPPELCONSO": "https://rappel.conso.gouv.fr/rss?categorie=01",
    "Legifrance Alimentaire": " https://agriculture.gouv.fr/rss.xml",
    "DGCCRF, French Fraud": "https://www.economie.gouv.fr/dgccrf/rss",
    "INRS secu": "https://www.inrs.fr/rss/?feed=actualites",
    "ANSES": "https://www.anses.fr/fr/flux-actualites.rss",
    "Food Ingredient first": "https://resource.innovadatabase.com/rss/fifnews.xml"
}

# Function to parse all RSS feeds
def parse_feeds(selected_feeds):
    data = []
    for feed_name, feed_url in rss_feeds.items():
        if feed_name in selected_feeds:
            parsed_feed = feedparser.parse(feed_url)
            for entry in parsed_feed.entries[:25]:  # Get the latest 25 articles
                
                # Extract date from 'description' if 'published_parsed' is not available
                if hasattr(entry, 'published_parsed'):
                    published_date = datetime(*entry.published_parsed[:6]).strftime("%Y-%m-%d")
                else:
                    # Attempt to extract date from description using regex
                    description = entry.description if hasattr(entry, 'description') else ""
                    date_match = re.search(r'(\d{2}/\d{2}/\d{4})', description)
                    if date_match:
                        published_date = datetime.strptime(date_match.group(1), "%d/%m/%Y").strftime("%Y-%m-%d")
                    else:
                        published_date = "Unknown"
                
                data.append({
                    "feed": feed_name,
                    "title": entry.title,
                    "link": entry.link,
                    "summary": entry.summary,
                    "published": published_date,
                    "image": entry.get("media_content", [None])[0].get("url", None) if "media_content" in entry else None
                })
    
    df = pd.DataFrame(data).sort_values(by="published", ascending=False)  # Sort by date, latest first
    return df

# Function to summarize the content of an article via Groq
def summarize_article_with_groq(url):
    client = get_groq_client()
    messages = [
        {"role": "system", "content": "Please summarize the following article:"},
        {"role": "user", "content": url}
    ]

    # Choose a Groq model
    model_id = "llama-3.1-8b-instant"  # Ensure this model can handle URLs

    # Call to Groq API
    chat_completion = client.chat.completions.create(
        messages=messages,
        model=model_id
    )

    return chat_completion.choices[0].message.content

def get_groq_client():
    """Initializes and returns a Groq client with the API key."""
    return Groq(api_key=st.secrets["GROQ_API_KEY"])

# Main section to display either the README or the articles
if st.session_state['showing_readme']:
    # Load and display the README
    readme_content = load_readme(readme_url)
    st.markdown(readme_content)
else:
    # Sidebar navigation
    with st.sidebar:
        st.header("Navigation")

        st.write("Select the news sources:")
        
        feeds = list(rss_feeds.keys())
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

        # Option to edit the review
        if st.button("Edit Selected Articles for Report"):
            st.session_state["edit_mode"] = True

    # Parse feeds based on selected sources
    feeds_df = parse_feeds(selected_feeds)

    # Filter articles by date
    feeds_df['published'] = pd.to_datetime(feeds_df['published'], errors='coerce')
    filtered_df = feeds_df[(feeds_df['published'] >= pd.to_datetime(min_date)) & (feeds_df['published'] <= pd.to_datetime(max_date))]

    st.markdown("---")
    st.header("Selected Articles")

    if not filtered_df.empty:
        # Display articles manually with a button to add each one to the review
        for i, row in filtered_df.iterrows():
            with st.container():
                cols = st.columns([2, 6, 1, 1, 1])
                cols[0].markdown(f"**{row['published'].strftime('%Y-%m-%d') if pd.notnull(row['published']) else 'Unknown'}**")
                cols[1].markdown(f"**{row['title']}**")
                cols[2].markdown(f"[Read More]({row['link']})")
                add_button = cols[3].button("➕", key=f"add_{i}")
                summarize_button = cols[4].button("Recap", key=f"summarize_{i}")
                
                if add_button:
                    if "review_articles" not in st.session_state:
                        st.session_state["review_articles"] = []
                    st.session_state["review_articles"].append(row)
                    st.success(f"Article added to review: {row['title']}")
                
                if summarize_button:
                    summary = summarize_article_with_groq(row['link'])
                    st.expander(f"Summary for {row['title']}").write(summary)

    else:
        st.write("No articles available for the selected sources and date range.")

    # Display selected articles for review and allow editing
    if "review_articles" in st.session_state and st.session_state["review_articles"]:
        st.markdown("---")
        st.header("Your Review")

        if st.session_state.get("edit_mode", False):
            st.write("Edit the articles below:")

            review_df = pd.DataFrame(st.session_state["review_articles"])
            for i, article in review_df.iterrows():
                st.markdown(f"### {i+1}. {article['title']}")
                edited_summary = st.text_area(f"Edit Summary for {i+1}", value=article['summary'])
                review_df.at[i, 'summary'] = edited_summary
                st.markdown(f"[Read More]({article['link']})")

            if st.button("Save Edits"):
                st.session_state["review_articles"] = review_df.to_dict('records')
                st.session_state["edit_mode"] = False
                st.success("Edits saved successfully!")

        else:
            review_df = pd.DataFrame(st.session_state["review_articles"])
            for i, article in review_df.iterrows():
                st.markdown(f"### {i+1}. {article['title']}")
                st.markdown(f"**Published on:** {article['published'].strftime('%Y-%m-%d') if pd.notnull(article['published']) else 'Unknown'}")
                st.markdown(f"{article['summary']}")
                st.markdown(f"[Read More]({article['link']})")

        st.markdown("---")
        review_text = st.text_area("Add your review here:", height=150)

        st.markdown("---")
        download_format = st.selectbox("Download Format:", ["PDF", "Email"])
        # PDF and Email logic remains unchanged

    st.write("App finished setup.")

# --- Logo and Link in Sidebar ---
    st.sidebar.markdown(
        f"""
        <div class="sidebar-logo-container">
            <a href="https://www.visipilot.com" target="_blank">
                <img src="https://raw.githubusercontent.com/M00N69/RAPPELCONSO/main/logo%2004%20copie.jpg" alt="Visipilot Logo" class="sidebar-logo">
            </a>
        </div>
        """, unsafe_allow_html=True
    )

