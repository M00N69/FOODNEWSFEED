import streamlit as st
import feedparser
import pandas as pd
from datetime import datetime
from pytz import timezone
from groq import Groq
import requests

# Configurer la page pour un affichage en mode large
st.set_page_config(layout="wide")

# URL brute du README.md sur GitHub (ou vous pouvez ajouter le contenu directement ici)
readme_url = "https://raw.githubusercontent.com/M00N69/FOODNEWSFEED/main/README.md"

def load_readme(url):
    response = requests.get(url)
    if response.status_code == 200:
        return response.text
    else:
        return "Sorry, we couldn't load the README file from GitHub."

# Define your list of RSS feeds
rss_feeds = {
    "EU Legislation": "https://eur-lex.europa.eu/EN/display-feed.rss?myRssId=e1Wry6%2FANeUpe1f1%2BCToXcHk31CTyaJK",
    "Food safety Magazine": "https://www.food-safety.com/rss/topic/296",
    "Food SafetyTech": "https://foodsafetytech.com/feed/",
    "Food Navigator": "https://www.foodnavigator.com/Info/Latest-News",
    "EFSA": "https://www.efsa.europa.eu/en/all/rss",
    "EU Food Safety": "https://food.ec.europa.eu/node/2/rss_en",
    "Food Quality & Safety": "https://www.foodqualityandsafety.com/category/eupdate/feed/",
    "Food Safety News": "https://feeds.lexblog.com/foodsafetynews/mRcs",
    "Food Manufacture": "https://www.foodmanufacture.co.uk/Info/FoodManufacture-RSS",
    "Food Packaging Forum": "https://www.foodpackagingforum.org/news/feed/",
    "Frech Recalls RAPPELCONSO": "https://rappel.conso.gouv.fr/rss?categorie=01",
    "INRS secu": "https://www.inrs.fr/rss/?feed=actualites",
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

# Function to summarize the content of an article via Groq
def summarize_article_with_groq(url):
    client = get_groq_client()
    messages = [
        {"role": "system", "content": "Please summarize the following article:"},
        {"role": "user", "content": url}
    ]

    # Choisir un modèle Groq
    model_id = "mixtral-8x7b-32768"  # Assurez-vous que ce modèle peut gérer des URL

    # Appel à l'API Groq
    chat_completion = client.chat.completions.create(
        messages=messages,
        model=model_id
    )

    return chat_completion.choices[0].message.content

def get_groq_client():
    """Initialise et renvoie un client Groq avec la clé API."""
    return Groq(api_key=st.secrets["GROQ_API_KEY"])

# Sidebar for navigation
with st.sidebar:
    st.header("Navigation")

    # Initialisation de la session state si elle n'existe pas
    if 'showing_readme' not in st.session_state:
        st.session_state['showing_readme'] = False

    # Gestion des boutons pour afficher le guide ou revenir à la vue principale
    if st.session_state['showing_readme']:
        if st.button("🔙 Back to Main View"):
            st.session_state['showing_readme'] = False
    else:
        if st.button("📄 Show Application Guide"):
            st.session_state['showing_readme'] = True

    # Si le guide est affiché, on ne montre pas le reste des options
    if not st.session_state['showing_readme']:
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

# Main section to display either the README or the articles
if st.session_state['showing_readme']:
    # Load and display the README
    readme_content = load_readme(readme_url)
    st.markdown(readme_content)
else:
    # Parse feeds based on selected sources
    feeds_df = parse_feeds(selected_feeds)

    # Filter articles by date
    feeds_df['published'] = pd.to_datetime(feeds_df['published'])
    filtered_df = feeds_df[(feeds_df['published'] >= pd.to_datetime(min_date)) & (feeds_df['published'] <= pd.to_datetime(max_date))]

    st.markdown("---")
    st.header("Selected Articles")

    if not filtered_df.empty:
        # Display articles manually with a button to add each one to the review
        for i, row in filtered_df.iterrows():
            with st.container():
                cols = st.columns([2, 6, 2, 1, 1])
                cols[0].markdown(f"**{row['published'].strftime('%Y-%m-%d')}**")
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
                st.markdown(f"**Published on:** {article['published'].strftime('%Y-%m-%d')}")
                st.markdown(f"{article['summary']}")
                st.markdown(f"[Read More]({article['link']})")

        st.markdown("---")
        review_text = st.text_area("Add your review here:", height=150)

        st.markdown("---")
        download_format = st.selectbox("Download Format:", ["PDF", "Email"])
        # PDF and Email logic remains unchanged

    st.write("App finished setup.")
