import streamlit as st
import feedparser
import pandas as pd
from datetime import datetime
from pytz import timezone
from groq import Groq
import requests
import re
from bs4 import BeautifulSoup
import time

# Configuring the page layout
st.set_page_config(layout="wide", page_title="Food News Feed", page_icon="🍽️")

# Enhanced CSS with better color scheme and responsive design
st.markdown(
    """
    <style>
    [data-testid="stSidebar"] {
        background-color: #2398B2;  
        color: white;
    }
    .sidebar-content {
        color: white;
    }
    .sidebar-content a {
        color: #f0f0f0;
    }
    .banner {
        background-image: url('https://github.com/M00N69/BUSCAR/blob/main/logo%2002%20copie.jpg?raw=true');
        background-size: cover;
        background-position: center;
        padding: 80px;
        margin-bottom: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .article-container {
        padding: 15px;
        border-radius: 5px;
        margin-bottom: 15px;
        border-left: 4px solid #2398B2;
        background-color: #f9f9f9;
        transition: all 0.3s ease;
    }
    .article-container:hover {
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        background-color: #f0f0f0;
    }
    .article-title {
        color: #2398B2;
        font-weight: bold;
        margin-bottom: 8px;
    }
    .article-date {
        color: #666;
        font-size: 0.9rem;
    }
    .article-summary {
        margin-top: 10px;
        line-height: 1.5;
    }
    .article-source {
        color: #888;
        font-style: italic;
        font-size: 0.8rem;
    }
    .dataframe td {
        white-space: normal !important;
        word-wrap: break-word !important;
    }
    .stButton>button {
        background-color: #2398B2;
        color: white;
        border-radius: 5px;
    }
    .stButton>button:hover {
        background-color: #1d7a8f;
    }
    .review-section {
        background-color: #f5f5f5;
        padding: 20px;
        border-radius: 10px;
        margin-top: 30px;
    }
    .review-article {
        background-color: white;
        padding: 15px;
        margin-bottom: 15px;
        border-radius: 5px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .stProgress .st-bo {
        background-color: #2398B2;
    }
    .loading-text {
        text-align: center;
        color: #555;
    }
    .sidebar-logo {
        margin-top: 20px;
        width: 100%;
        border-radius: 5px;
    }
    .filter-container {
        background-color: rgba(255,255,255,0.9);
        padding: 15px;
        border-radius: 5px;
        margin-bottom: 20px;
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

if 'article_contents' not in st.session_state:
    st.session_state['article_contents'] = {}

# URL of the README.md on GitHub
readme_url = "https://raw.githubusercontent.com/M00N69/FOODNEWSFEED/main/README.md"

def load_readme(url):
    response = requests.get(url)
    if response.status_code == 200:
        return response.text
    else:
        return "Sorry, we couldn't load the README file from GitHub."

# Function to fetch and extract article content
def fetch_article_content(url):
    """Fetch article content using BeautifulSoup"""
    if url in st.session_state['article_contents']:
        return st.session_state['article_contents'][url]
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Try multiple strategies to find the article content
        article_content = ""
        
        # Strategy 1: Look for article tags
        article_tag = soup.find('article')
        if article_tag:
            paragraphs = article_tag.find_all('p')
            article_content = ' '.join([p.get_text().strip() for p in paragraphs])
        
        # Strategy 2: Look for common content div classes
        if not article_content:
            content_divs = soup.select('.content, .article-content, .entry-content, .post-content, #content, .story-body')
            if content_divs:
                paragraphs = content_divs[0].find_all('p')
                article_content = ' '.join([p.get_text().strip() for p in paragraphs])
        
        # Strategy 3: Just grab all p tags within the main body
        if not article_content:
            body = soup.find('body')
            if body:
                paragraphs = body.find_all('p')
                article_content = ' '.join([p.get_text().strip() for p in paragraphs])
                
                # Cleanup - remove short paragraphs which are often navigation/ads
                article_content = ' '.join([p for p in article_content.split('.') if len(p.strip()) > 40])
        
        # Save to session state cache
        if article_content:
            st.session_state['article_contents'][url] = article_content
            return article_content
        else:
            return "Could not extract article content. Try using the Recap feature instead."
            
    except Exception as e:
        return f"Error fetching article: {str(e)}"

# Define your list of RSS feeds
rss_feeds = {
    "Food safety Magazine": "https://www.food-safety.com/rss/topic/296",
    "Food SafetyTech": "https://foodsafetytech.com/feed/",
    "Food Navigator": "https://www.foodnavigator.com/Info/Latest-News",
    "Food GOV UK": "https://www.food.gov.uk/rss-feed/news",
    "US CDC": "https://www2c.cdc.gov/podcasts/createrss.asp?c=146",
    "US FDA Press Release": "https://www.fda.gov/about-fda/contact-fda/stay-informed/rss-feeds/press-releases/rss.xml",
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
    "Legifrance Alimentaire": "https://agriculture.gouv.fr/rss.xml",
    "DGCCRF, French Fraud": "https://www.economie.gouv.fr/dgccrf/rss",
    "INRS secu": "https://www.inrs.fr/rss/?feed=actualites",
    "ANSES": "https://www.anses.fr/fr/flux-actualites.rss",
    "Health BE": "https://www.health.belgium.be/fr/rss/news.xml",
    "Food Ingredient first": "https://resource.innovadatabase.com/rss/fifnews.xml"
}

# Function to parse all RSS feeds with better error handling
def parse_feeds(selected_feeds):
    data = []
    for feed_name, feed_url in rss_feeds.items():
        if feed_name in selected_feeds:
            try:
                parsed_feed = feedparser.parse(feed_url)
                
                if not parsed_feed.entries:
                    st.warning(f"No entries found for {feed_name}")
                    continue
                    
                for entry in parsed_feed.entries[:25]:  # Get the latest 25 articles
                    
                    # Extract date with multiple fallback methods
                    published_date = "Unknown"
                    
                    # Method 1: Standard published_parsed
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        try:
                            published_date = datetime(*entry.published_parsed[:6]).strftime("%Y-%m-%d")
                        except:
                            pass
                            
                    # Method 2: Check for updated_parsed
                    if published_date == "Unknown" and hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                        try:
                            published_date = datetime(*entry.updated_parsed[:6]).strftime("%Y-%m-%d")
                        except:
                            pass
                    
                    # Method 3: Try different date formats in string fields
                    if published_date == "Unknown":
                        date_fields = ['published', 'updated', 'pubDate']
                        date_formats = [
                            '%a, %d %b %Y %H:%M:%S %z',
                            '%Y-%m-%dT%H:%M:%S%z',
                            '%Y-%m-%d %H:%M:%S',
                            '%d %b %Y',
                            '%d/%m/%Y'
                        ]
                        
                        for field in date_fields:
                            if hasattr(entry, field) and entry[field]:
                                for date_format in date_formats:
                                    try:
                                        date_str = entry[field]
                                        dt = datetime.strptime(date_str, date_format)
                                        published_date = dt.strftime("%Y-%m-%d")
                                        break
                                    except:
                                        continue
                            if published_date != "Unknown":
                                break
                    
                    # Method 4: Extract from description using regex
                    if published_date == "Unknown" and hasattr(entry, 'description'):
                        description = entry.description
                        date_patterns = [
                            r'(\d{2}/\d{2}/\d{4})',
                            r'(\d{4}-\d{2}-\d{2})',
                            r'(\d{1,2} [A-Za-z]+ \d{4})'
                        ]
                        
                        for pattern in date_patterns:
                            date_match = re.search(pattern, description)
                            if date_match:
                                try:
                                    if pattern == r'(\d{2}/\d{2}/\d{4})':
                                        published_date = datetime.strptime(date_match.group(1), "%d/%m/%Y").strftime("%Y-%m-%d")
                                    elif pattern == r'(\d{4}-\d{2}-\d{2})':
                                        published_date = date_match.group(1)
                                    elif pattern == r'(\d{1,2} [A-Za-z]+ \d{4})':
                                        published_date = datetime.strptime(date_match.group(1), "%d %B %Y").strftime("%Y-%m-%d")
                                    break
                                except:
                                    continue
                    
                    # Get a better summary
                    summary = ""
                    if hasattr(entry, 'summary'):
                        # Clean HTML tags
                        summary = BeautifulSoup(entry.summary, "html.parser").get_text()
                    elif hasattr(entry, 'description'):
                        summary = BeautifulSoup(entry.description, "html.parser").get_text()
                    else:
                        summary = "No summary available"
                    
                    # Limit summary length
                    summary = summary[:500] + '...' if len(summary) > 500 else summary
                    
                    # Get image if available
                    image_url = None
                    if hasattr(entry, 'media_content') and entry.media_content:
                        image_url = entry.media_content[0].get('url', None)
                    elif hasattr(entry, 'links'):
                        for link in entry.links:
                            if link.get('type', '').startswith('image'):
                                image_url = link.get('href', None)
                                break
                    
                    # Extract from content if available
                    if not image_url and hasattr(entry, 'content'):
                        for content in entry.content:
                            if 'value' in content:
                                soup = BeautifulSoup(content['value'], 'html.parser')
                                img_tag = soup.find('img')
                                if img_tag and 'src' in img_tag.attrs:
                                    image_url = img_tag['src']
                                    break
                    
                    data.append({
                        "feed": feed_name,
                        "title": entry.title,
                        "link": entry.link,
                        "summary": summary,
                        "published": published_date,
                        "image": image_url
                    })
            except Exception as e:
                st.error(f"Error parsing feed {feed_name}: {str(e)}")
    
    try:
        df = pd.DataFrame(data)
        if not df.empty:
            df = df.sort_values(by="published", ascending=False)  # Sort by date, latest first
        return df
    except Exception as e:
        st.error(f"Error creating DataFrame: {str(e)}")
        return pd.DataFrame()  # Return empty DataFrame on error

# Function to summarize the content of an article via Groq
def summarize_article_with_groq(url):
    try:
        # First try to fetch the article content ourselves
        article_content = fetch_article_content(url)
        
        if article_content == "Could not extract article content. Try using the Recap feature instead.":
            # If we failed to get content, just send the URL to Groq
            content_to_send = url
        else:
            # Send the content we extracted
            content_to_send = f"Article URL: {url}\n\nArticle Content: {article_content}"
        
        client = get_groq_client()
        messages = [
            {"role": "system", "content": "You are a helpful assistant that summarizes food safety articles. Your summaries should be concise (3-4 paragraphs maximum), well-structured, and highlight the key points of the article. Focus on the facts and avoid personal opinions."},
            {"role": "user", "content": f"Please summarize the following food safety article content into 3-4 paragraphs highlighting the key points: {content_to_send}"}
        ]

        # Choose a Groq model
        model_id = "llama-3.1-8b-instant"

        # Call to Groq API
        chat_completion = client.chat.completions.create(
            messages=messages,
            model=model_id
        )

        return chat_completion.choices[0].message.content
    except Exception as e:
        return f"Error generating summary: {str(e)}"

def get_groq_client():
    """Initializes and returns a Groq client with the API key."""
    return Groq(api_key=st.secrets["GROQ_API_KEY"])

# Toggle button to switch between README and main content
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    if st.button("📖 Toggle About this APP", use_container_width=True):
        st.session_state['showing_readme'] = not st.session_state['showing_readme']

# Main section to display either the README or the articles
if st.session_state['showing_readme']:
    # Load and display the README with better formatting
    readme_content = load_readme(readme_url)
    st.markdown(readme_content)
else:
    # Sidebar navigation with improved styling
    with st.sidebar:
        st.markdown('<div class="sidebar-content">', unsafe_allow_html=True)
        st.header("📊 Navigation")
    
        # Initialize selected_feeds if not already set
        if 'selected_feeds' not in st.session_state:
            st.session_state['selected_feeds'] = ["Food safety Magazine"]
    
        # Add buttons to select all feeds or only one specific feed
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Select All", use_container_width=True):
                st.session_state['selected_feeds'] = list(rss_feeds.keys())
    
        with col2:
            if st.button("Reset", use_container_width=True):
                st.session_state['selected_feeds'] = ["Food safety Magazine"]
    
        st.subheader("News Sources")
    
        # Multiselect for feeds with pre-selected options based on button clicks
        selected_feeds = st.multiselect("Select Feeds:", list(rss_feeds.keys()), default=st.session_state['selected_feeds'])
    
        # Update session state based on multiselect changes
        st.session_state['selected_feeds'] = selected_feeds
        
        st.write("---")
        st.subheader("Date Filter")
    
        # Date filter with better default ranges
        min_date = st.date_input("Start date", value=pd.to_datetime("2023-01-01").date())
        max_date = st.date_input("End date", value=datetime.now().date())
    
        paris_timezone = timezone('Europe/Paris')
        st.write(f"Last Update: {datetime.now(paris_timezone).strftime('%Y-%m-%d %H:%M:%S')}")
        
        st.write("---")
        
        # Option to download the selected review as CSV
        if "review_articles" in st.session_state and st.session_state["review_articles"]:
            st.subheader("Export Options")
            review_df = pd.DataFrame(st.session_state["review_articles"])
            csv = review_df.to_csv(index=False)
            st.download_button(
                label="📥 Download Review as CSV",
                data=csv,
                file_name=f"food_safety_review_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )
    
        # Option to edit the review
        if "review_articles" in st.session_state and st.session_state["review_articles"]:
            if st.button("✏️ Edit Selected Articles", use_container_width=True):
                st.session_state["edit_mode"] = True
                
        # Clear review button
        if "review_articles" in st.session_state and st.session_state["review_articles"]:
            if st.button("🗑️ Clear Review", use_container_width=True):
                st.session_state["review_articles"] = []
                st.success("Review cleared!")
                
        st.markdown('</div>', unsafe_allow_html=True)

    # Main content
    st.header("📰 Food Safety News Feed")
    
    # Show a progress bar while loading feeds
    with st.spinner('Loading feeds...'):
        progress_bar = st.progress(0)
        
        # Parse feeds based on selected sources
        feeds_df = parse_feeds(selected_feeds)
        progress_bar.progress(100)
        time.sleep(0.5)  # Short pause to show completion
        progress_bar.empty()  # Remove progress bar

    # Filter articles by date with error handling
    try:
        if not feeds_df.empty:
            feeds_df['published'] = pd.to_datetime(feeds_df['published'], errors='coerce')
            filtered_df = feeds_df[(feeds_df['published'] >= pd.to_datetime(min_date)) & 
                                  (feeds_df['published'] <= pd.to_datetime(max_date))]
        else:
            filtered_df = pd.DataFrame()
    except Exception as e:
        st.error(f"Error filtering by date: {str(e)}")
        filtered_df = feeds_df  # Use unfiltered data as fallback

    # Search functionality
    search_term = st.text_input("🔍 Search articles:", placeholder="Enter keywords")
    if search_term and not filtered_df.empty:
        search_term = search_term.lower()
        filtered_df = filtered_df[
            filtered_df['title'].str.lower().str.contains(search_term, na=False) | 
            filtered_df['summary'].str.lower().str.contains(search_term, na=False)
        ]

    st.markdown("---")
    
    # Display number of articles found
    if not filtered_df.empty:
        st.subheader(f"Found {len(filtered_df)} articles")
    else:
        st.subheader("No articles found")

    # Display articles with improved styling
    if not filtered_df.empty:
        # Display articles in a more visual way
        for i, row in filtered_df.iterrows():
            with st.container():
                st.markdown(f"""
                <div class="article-container">
                    <div class="article-date">{row['published'].strftime('%Y-%m-%d') if pd.notnull(row['published']) else 'Unknown'}</div>
                    <div class="article-title">{row['title']}</div>
                    <div class="article-source">Source: {row['feed']}</div>
                </div>
                """, unsafe_allow_html=True)
                
                # Article actions in columns
                col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                
                with col1:
                    st.markdown(f"{row['summary'][:200]}...")
                
                with col2:
                    st.markdown(f"[Read Article]({row['link']})")
                
                with col3:
                    add_button = st.button("➕ Add", key=f"add_{i}")
                
                with col4:
                    summarize_button = st.button("🔄 Recap", key=f"summarize_{i}")
                
                # Handle button actions
                if add_button:
                    if "review_articles" not in st.session_state:
                        st.session_state["review_articles"] = []
                    
                    # Check if article is already in the review
                    existing_titles = [article['title'] for article in st.session_state["review_articles"]]
                    if row['title'] in existing_titles:
                        st.warning(f"Article already in review: {row['title']}")
                    else:
                        st.session_state["review_articles"].append(row)
                        st.success(f"Article added to review: {row['title']}")
                
                if summarize_button:
                    with st.spinner("Generating article summary..."):
                        summary = summarize_article_with_groq(row['link'])
                    
                    with st.expander(f"Summary for: {row['title']}", expanded=True):
                        st.markdown(summary)
                        if st.button("Add with this summary", key=f"add_summary_{i}"):
                            row_copy = row.copy()
                            row_copy['summary'] = summary
                            
                            # Check if article is already in the review
                            existing_titles = [article['title'] for article in st.session_state["review_articles"]]
                            if row['title'] in existing_titles:
                                # Update the existing entry
                                for idx, article in enumerate(st.session_state["review_articles"]):
                                    if article['title'] == row['title']:
                                        st.session_state["review_articles"][idx]['summary'] = summary
                                        break
                                st.success(f"Updated summary for: {row['title']}")
                            else:
                                # Add as new
                                st.session_state["review_articles"].append(row_copy)
                                st.success(f"Added article with summary: {row['title']}")

    else:
        st.info("No articles available for the selected sources and date range. Try adjusting your filters.")

    # Display selected articles for review and allow editing
    if "review_articles" in st.session_state and st.session_state["review_articles"]:
        st.markdown("---")
        st.header("📋 Your Review")

        if st.session_state.get("edit_mode", False):
            st.write("Edit the articles below:")

            review_df = pd.DataFrame(st.session_state["review_articles"])
            updated_articles = []
            
            for i, article in review_df.iterrows():
                with st.container():
                    st.markdown(f"### {i+1}. {article['title']}")
                    edited_summary = st.text_area(f"Edit Summary for {i+1}", value=article['summary'], height=200)
                    
                    article_copy = article.copy()
                    article_copy['summary'] = edited_summary
                    updated_articles.append(article_copy)
                    
                    st.markdown(f"[Read More]({article['link']})")
                    
                    if st.button("Remove", key=f"remove_{i}"):
                        continue
            
            if st.button("Save Edits"):
                st.session_state["review_articles"] = [article for article in updated_articles if article is not None]
                st.session_state["edit_mode"] = False
                st.success("Edits saved successfully!")

        else:
            # Display in a nicer format
            review_df = pd.DataFrame(st.session_state["review_articles"])
            
            st.markdown('<div class="review-section">', unsafe_allow_html=True)
            
            for i, article in review_df.iterrows():
                st.markdown('<div class="review-article">', unsafe_allow_html=True)
                st.markdown(f"### {i+1}. {article['title']}")
                st.markdown(f"**Published on:** {article['published'].strftime('%Y-%m-%d') if pd.notnull(article['published']) else 'Unknown'}")
                st.markdown(f"**Source:** {article['feed']}")
                st.markdown(f"{article['summary']}")
                st.markdown(f"[Read Full Article]({article['link']})")
                st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("---")
        
        # Add a section for review notes
        st.subheader("Review Notes")
        review_text = st.text_area("Add your review notes here:", height=150)
        
        if st.button("Save Notes"):
            st.session_state["review_notes"] = review_text
            st.success("Notes saved!")

        st.markdown("---")
        
        # Export options
        st.subheader("Export Options")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Export as PDF", use_container_width=True):
                st.info("PDF export functionality will be implemented here")
        
        with col2:
            if st.button("Export as Email", use_container_width=True):
                st.info("Email export functionality will be implemented here")

# --- Logo and Link in Sidebar ---
with st.sidebar:
    st.markdown(
        f"""
        <div class="sidebar-logo-container">
            <a href="https://www.visipilot.com" target="_blank">
                <img src="https://raw.githubusercontent.com/M00N69/RAPPELCONSO/main/logo%2004%20copie.jpg" alt="Visipilot Logo" class="sidebar-logo">
            </a>
        </div>
        """, unsafe_allow_html=True
    )
