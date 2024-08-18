import streamlit as st
import feedparser
import pandas as pd
from datetime import datetime
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
from pytz import timezone
import textwrap

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
def parse_feeds():
    data = []
    for feed_name, feed_url in rss_feeds.items():
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
    df = pd.DataFrame(data).sort_values(by="feed", ascending=True)  # Sort by feed
    return df

# Main app logic
st.title("Food Safety News & Reviews")

# Parse feeds once at the start
feeds_df = parse_feeds()

# Sidebar for navigation
with st.sidebar:
    st.header("Navigation")
    st.write("Feeds data loaded.")
    feeds = feeds_df["feed"].unique()
    if len(feeds) == 0:
        st.write("No feeds available.")
    else:
        selected_feed = st.selectbox("Select a Feed:", list(feeds))
        paris_timezone = timezone('Europe/Paris')
        st.write(f"Last Update: {datetime.now(paris_timezone).strftime('%Y-%m-%d %H:%M:%S')}")

st.markdown("---")

# Display news for the selected feed
st.header(f"{selected_feed} Articles")

for index, row in feeds_df[feeds_df["feed"] == selected_feed].iterrows():
    st.write(f"**{row['title']}**")
    if row["image"]:
        st.image(row["image"], caption="Image from the article")

    st.write(f"**{row['published']}**")
    st.write(f"{row['summary']}")  # No translation needed
    st.write(f"[Read More]({row['link']})")

    # Allow users to add articles to review
    if st.button("Add to Review", key=f"review_{index}"):
        if "review_articles" not in st.session_state:
            st.session_state["review_articles"] = []
        st.session_state["review_articles"].append(row)
        st.success(f"Article added to review!")

# Display review section
st.markdown("---")
st.header("Your Review")

# Display selected articles for review
if "review_articles" in st.session_state:
    st.write("Selected Articles:")
    for i, article in enumerate(st.session_state["review_articles"]):
        st.write(f"**{i+1}. {article['title']}**")
        st.write(f"**{article['published']}**")
        st.write(f"{article['summary']}")
        st.write(f"[Read More]({article['link']})")

    # Add review text area
    st.markdown("---")
    review_text = st.text_area("Add your review here:", height=150)

    # Download/Email Options
    st.markdown("---")
    download_format = st.selectbox("Download Format:", ["PDF", "Email"])
    if download_format == "PDF":
        # Convert review to PDF
        output = io.BytesIO()
        doc = SimpleDocTemplate(output, pagesize=letter)
        styles = getSampleStyleSheet()
        Story = []
        Story.append(Paragraph("Food Safety News Review", styles["Heading1"]))
        Story.append(Spacer(1, 12))
        Story.append(Paragraph(f"Date: {datetime.now().strftime('%Y-%m-%d')}", styles["Normal"]))
        Story.append(Spacer(1, 12))
        Story.append(Paragraph("Selected Articles:", styles["Heading2"]))

        for i, article in enumerate(st.session_state["review_articles"]):
            data = [
                [Paragraph(f"{i+1}. {article['title']}", styles["Heading3"])],
                [Paragraph(f"**{article['published']}**", styles["Normal"])],
                [Paragraph(article["summary"], styles["Normal"])],
                [Paragraph(f"[Read More]({article['link']})", styles["Normal"])]
            ]
            Story.append(Table(data, style=[('VALIGN', (0, 0), (-1, -1), 'TOP'), ('ALIGN', (0, 0), (-1, -1), 'LEFT')]))
            Story.append(Spacer(1, 12))

        Story.append(Spacer(1, 12))
        Story.append(Paragraph("Review:", styles["Heading2"]))
        Story.append(Spacer(1, 12))
        Story.append(Paragraph(review_text, styles["Normal"]))

        doc.build(Story)
        output.seek(0)
        st.download_button(
            label="Download Review as PDF",
            data=output,
            file_name="food_safety_review.pdf",
            mime="application/pdf"
        )
    elif download_format == "Email":
        st.markdown(
            f"""
            <a href="mailto:?subject=Food Safety News Review&body={review_text}">Send Review via Email</a>
            """,
            unsafe_allow_html=True
        )

st.write("App finished setup.")
