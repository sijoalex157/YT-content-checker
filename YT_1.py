import streamlit as st
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import string
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer

# Download NLTK resources
nltk.download("punkt")
nltk.download("stopwords")
nltk.download("wordnet")
nltk.download('vader_lexicon')

# Function to preprocess comments
def preprocess_comments(comments):
    preprocessed_comments = []
    stop_words = set(stopwords.words("english"))
    lemmatizer = WordNetLemmatizer()

    for comment_info in comments:
        comment = comment_info["comment"]

        # Convert to lowercase
        comment = comment.lower()

        # Remove punctuation
        comment = comment.translate(str.maketrans("", "", string.punctuation))

        # Tokenize
        tokens = word_tokenize(comment)

        # Remove stop words and lemmatize
        filtered_tokens = [
            lemmatizer.lemmatize(token) for token in tokens if token not in stop_words
        ]

        # Join tokens back into a string
        preprocessed_comment = " ".join(filtered_tokens)

        # Add preprocessed comment to the list
        preprocessed_comments.append(preprocessed_comment)

    return preprocessed_comments

# Function to perform sentiment analysis
def analyze_sentiment(comments):
    sid = SentimentIntensityAnalyzer()
    sentiments = []

    for comment in comments:
        # Get sentiment scores for the comment
        sentiment_scores = sid.polarity_scores(comment)

        # Classify the sentiment as positive, negative, or neutral based on compound score
        if sentiment_scores["compound"] >= 0.05:
            sentiment = "Positive"
        elif sentiment_scores["compound"] <= -0.05:
            sentiment = "Negative"
        
        else:
            sentiment = "Neutral"

        # Add sentiment classification to the list
        sentiments.append(sentiment)

    return sentiments

# Function to extract top comments
def get_top_comments(video_id):
    youtube = build("youtube", "v3", developerKey="AIzaSyBWLxLPQPF_B01KQ4-VcTfzY9i_2Ix1uSM")

    comments = []
    nextPageToken = None
    total_comments = 0
    while total_comments < 10000:
        try:
            response = youtube.commentThreads().list(
                part="snippet",
                videoId=video_id,
                textFormat="plainText",
                maxResults=min(100, 10000 - total_comments),  # Maximum comments per page
                pageToken=nextPageToken,
            ).execute()

            # Extract comments and their like counts
            for item in response["items"]:
                comment = item["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
                like_count = item["snippet"]["topLevelComment"]["snippet"]["likeCount"]
                comments.append({"comment": comment, "like_count": like_count})
                total_comments += 1

            # Check if there are more pages
            nextPageToken = response.get("nextPageToken")
            if not nextPageToken:
                break

        except HttpError as e:
            print("An HTTP error %d occurred:\n%s" % (e.resp.status, e.content))
            break

    # Sort comments by like count in descending order
    sorted_comments = sorted(comments, key=lambda x: x["like_count"], reverse=True)

    # Return top 10,000 comments or less if total comments are less than 10,000
    return sorted_comments[:min(total_comments, 10000)]



# Streamlit UI
st.title("Youtube Video Content Quality")

# Input box for YouTube video link
video_link = st.text_input("Enter YouTube Video Link:")

if st.button("Analyze Video Content Quality"):
    if video_link:
        # Extract video ID from URL
        video_id = video_link.split("=")[-1]

        # Get top comments
        top_comments = get_top_comments(video_id)

        # Preprocess comments
        preprocessed_comments = preprocess_comments(top_comments)

        # Perform sentiment analysis
        sentiments = analyze_sentiment(preprocessed_comments)

        # Calculate sentiment ratio
        positive_count = sentiments.count("Positive")
        negative_count = sentiments.count("Negative")
        neutral_count = sentiments.count("Neutral")
        total_count = len(sentiments)

        # Determine box office performance based on overall sentiment and additional conditions
        if positive_count > (negative_count + neutral_count):
            box_office_performance = "Good Content"
        elif positive_count < (negative_count + neutral_count):
            box_office_performance = "Poor Content"
        else:
            if neutral_count > positive_count or neutral_count > negative_count:
                box_office_performance = "Mixed Reactions"

        # Display results
        st.write(f"Total Comments Analyzed: {total_count}")
        st.write(f"Positive Comments: {positive_count}")
        st.write(f"Negative Comments: {negative_count}")
        st.write(f"Neutral Comments: {neutral_count}")
        st.write(f"Performance: {box_office_performance}")





