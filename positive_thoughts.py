from datetime import datetime
import mysql.connector
import logging
import random
import sys
import os
import pandas as pd
import markovify
import requests
import ftfy
import language_tool_python
from flask import Flask, request, url_for, redirect, send_from_directory
from fuzzywuzzy import fuzz
from textblob import TextBlob

logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
app = Flask(__name__)


@app.route("/favicon.ico")
def favicon():
    """Adding site favicon."""
    try:
        return send_from_directory(
            os.path.join(app.root_path, "static"),
            "favicon.ico",
            mimetype="image/vnd.microsoft.icon",
        )
    except:
        logging.exception("Failed to link Favicon.")


@app.route("/")
def positivipy():
    """Returns an HTML page with positively minded paragraph of text."""
    # Include structured data for search engines.
    structured_data = """<script type="application/ld+json">
    {
      "@context" : "http://schema.org",
      "@type" : ["SoftwareApplication","WebApplication"],
      "name" : "positivipy",
      "applicationCategory":"DeveloperApplication",
      "operatingSystem":"All"
    }
    </script>"""
    try:
        codes, language_name, example_code = status_codes()
        codes = codes.to_html(border=0, justify="left")
        # recent_upvotes = get_votes_from_db()
        html_page = f"""<!DOCTYPE html><html lang="en"><head>{structured_data}<meta name="positivipy API" description="read computer generated positive quotes and translate them into 50+ languages"><link rel="shortcut icon" type="image/x-icon" href="static/favicon.ico">
                        <link rel='stylesheet' href="/static/styles/styles.css">
                        <Title>positivipy</Title></head>
                        <body><h2><a href="https://positivethoughts.pythonanywhere.com" style="text-decoration:none">+</a> positivipy</h2>
                        <p>A Markov chain text model of positive thinkers, artists and creators</p><br>
                        <div class="form"><form action="/get_quote?l=en&q=new&t=no" method="post" style="width:600px;">
                        <input type="submit" value="start positivipy"></form>
                        <br><br><details><Summary>positivipy API</Summary><br>translate computer generated positivity into <a href="https://developers.google.com/admin-sdk/directory/v1/languages">50+ languages</a> via textblob and the Google Translate API.
                        <br><br><b>Example URL to translate to {language_name}</b>: <br><pre>https://positivethoughts.pythonanywhere.com/get_quote?l={example_code}&t=yes</pre>
                        <b>URL Parameters</b><br><pre>l: default "en", language code to translate quote into<br>t: "yes" or "no", specifies if translation is applied</pre></details>
                        </p><details><Summary>See Language Codes</Summary>{codes}</details><br><details><Summary>Made With</Summary>CSS, <a href="https://www.facebook.com/positivedailythought">Facebook Posts</a>,
                        python, flask, <a href="https://ftfy.readthedocs.io/en/latest/index.html">ftfy</a>, fuzzywuzzy, HTML, <a href="https://languagetool.org/">Language Tool</a>, markovify, mysql, pandas, pythonanywhere, requests and textblob
                        (<a href="https://lofipython.com/generating-positive-thoughts-with-google-vision-ocr-and-markov-chains/">about</a>)</body></html>"""
        return html_page
    except:
        logging.exception("Failed to post!")
        return "Ooops! Something went wrong!"


def status_codes():
    """Language codes to set the language to translate text."""
    codes = {
        "Amharic": "am",
        "Arabic": "ar",
        "Basque": "eu",
        "Bengali": "bn",
        "English": "en-GB",
        "Portuguese (Brazil)": "pt-BR",
        "Bulgarian": "bg",
        "Catalan": "ca",
        "Cherokee": "chr",
        "Croatian": "hr",
        "Czech": "cs",
        "Danish": "da",
        "Dutch": "nl",
        "English": "en",
        "Estonian": "et",
        "Filipino": "fil",
        "Finnish": "fi",
        "French": "fr",
        "German": "de",
        "Greek": "el",
        "Gujarati": "gu",
        "Hebrew": "iw",
        "Hindi": "hi",
        "Hungarian": "hu",
        "Icelandic": "is",
        "Indonesian": "id",
        "Italian": "it",
        "Japanese": "ja",
        "Kannada": "kn",
        "Korean": "ko",
        "Latvian": "lv",
        "Lithuanian": "lt",
        "Malay": "ms",
        "Malayalam": "ml",
        "Marathi": "mr",
        "Norwegian": "no",
        "Polish": "pl",
        "Portuguese (Portugal)": "pt-PT",
        "Romanian": "ro",
        "Russian": "ru",
        "Serbian": "sr",
        "Chinese (PRC)": "zh-CN",
        "Slovak": "sk",
        "Slovenian": "sl",
        "Spanish": "es",
        "Swahili": "sw",
        "Swedish": "sv",
        "Tamil": "ta",
        "Telugu": "te",
        "Thai": "th",
        "Chinese (Taiwan)": "zh-TW",
        "Turkish": "tr",
        "Urdu": "ur",
        "Ukrainian": "uk",
        "Vietnamese": "vi",
        "Welsh": "cy",
    }
    language_name, example_code = random.choice(list(codes.items()))
    codes_df = pd.DataFrame(codes.items(), columns=["Language", "Code"])
    return codes_df, language_name, example_code


@app.route("/get_quote", methods=["GET", "POST"])
def get_quote():
    """Returns str, positive quote text.
    - Use a Markov chain on text of 771 PTD Facebook posts to generate text, stored in a .csv.
    - Use fuzzywuzzy to speculate the source authors based on Levenshtein distance.
    """
    # Build a markov chain model.
    quote = request.args.get("q")
    text, posts = quotes_dataset()
    language = request.args.get("l")
    if language == "en":
        alt_lang = "es"
    elif language == "es":
        alt_lang = "en"
    else:
        alt_lang = "en"
    translate = request.args.get("t")
    if quote == "new" or str(quote) == "None":
        text_model = markovify.Text(text)
        quote = text_model.make_sentence()
        quote = clean_quote(quote)
        quote = fix_spelling_and_grammar(quote)
        posts["MatchRatio"] = posts.Quotes.astype(str).apply(fuzz_ratio, args=(quote,))
        sources = posts.nlargest(n=3, columns=["MatchRatio"], keep="first")
        authors = sources.Authors.astype(str).tolist()
        ratios = sources.MatchRatio.astype(str).tolist()
        while len(authors) < 1:
            authors.append("Unknown")
            ratios.append("")
        ratio_one = ratios[0]
        ratio_two = ratios[1]
        if language != "en":
            quote = translate_text(quote, language)
    else:
        quote = translate_text(quote, language)
        ratio_one = request.args.get("one")
        ratio_two = request.args.get("two")
        authors = request.args.get("a").split(",")
    if str(quote).lower() == "none":
        text_model = markovify.Text(text)
        quote = text_model.make_sentence()
        quote = clean_quote(quote)
        quote = fix_spelling_and_grammar(quote)
        posts["MatchRatio"] = posts.Quotes.astype(str).apply(fuzz_ratio, args=(quote,))
        sources = posts.nlargest(n=3, columns=["MatchRatio"], keep="first")
        authors = sources.Authors.astype(str).tolist()
        ratios = sources.MatchRatio.astype(str).tolist()
        while len(authors) < 1:
            authors.append("Unknown")
            ratios.append("")
        ratio_one = ratios[0]
        ratio_two = ratios[1]
    add_quote_to_db(quote)
    codes, language_name, example_code = status_codes()
    codes = codes.to_html(border=0, justify="left")
    fb_url = "https://www.facebook.com/positivedailythought"
    blog_url = "https://lofipython.com/generating-positive-thoughts-with-google-vision-ocr-and-markov-chains/"
    translation_url = f"/get_quote?l={alt_lang}&t=yes&q={quote}&one={ratio_one}&two={ratio_two}&a={authors[0]},{authors[1]}"
    html_page = f"""<!DOCTYPE html><html lang="en"><head>
                    <meta name="positivipy text generator" description="read computer generated positive quotes and translate them into 50+ languages">
                    <link rel="shortcut icon" type="image/x-icon" href="/static/favicon.ico">
                    <link rel="stylesheet" href="/static/styles/styles.css">
                    <Title>positivipy</Title></head>
                    <body><h2><a href="https://positivethoughts.pythonanywhere.com" style="text-decoration:none">+</a> positivipy</h2>
                    <p>A Markov chain text model of positive thinkers, artists and creators</p>
                    <h1>{quote}</h1><p><b>Top Matches</b><br>
                    {ratio_one} <meter min=0 max=100 value={ratio_one}></meter> {authors[0]}<br>
                    {ratio_two} <meter min=0 max=100 value={ratio_two}></meter> {authors[1]}<br><br>
                    <form action="/get_quote?l={language}&q=new" method="post" style="width:600px;">
                    <input type="submit" title="see a new quote" value="Another?"></form><br><br>
                    <details><Summary>Options</Summary>
                    <a href="{translation_url}">Translate ({alt_lang})</a>
                    <div id="outer"><div class="upvote form">
                    <br>upvote<br>
                    <form action="/add_vote_to_db?q={quote}&v=up" method="post" style="font-size:20px;">
                    <input type="submit" title="up vote this quote" value="↑"><br></form></div>
                    <br>downvote<br>
                    <div class="downvote form">
                    <form action="/add_vote_to_db?q={quote}&v=down" method="post" style="font-size:20px;">
                    <input type="submit" title ="down vote this quote" value="↓"></form></div>
                    <div class="refresh quote form"></form></details><br>
                    </div><details><Summary>API</Summary>Translation URL API example to translate to {language_name}: <br><pre>https://positivethoughts.pythonanywhere.com/get_quote?l={example_code}&t=yes</pre></details>
                    </p><details><Summary>See Language Codes</Summary>{codes}</details>
                    <br><details><Summary>Made With </Summary>CSS, <a href="{fb_url}">facebook posts</a>, flask, <a href="https://ftfy.readthedocs.io/en/latest/index.html">ftfy</a>, fuzzywuzzy, HTML, <a href="https://languagetool.org/">Language Tool</a>, markovify, mysql, <a href="https://pandas.pydata.org/docs/">pandas</a>, Python, pythonanywhere, requests and <a href="https://textblob.readthedocs.io/en/dev/">textblob<a/> (<a href="{blog_url}">about</a>)</details></p></body></html>"""
    return html_page


def fuzz_ratio(quote, markov_text):
    """For each quote, calculate its fuzzy match ratio.
    Return it in a new column named 'MatchRatio'.
    fuzz.ratio("this is a test", "this is a test!")

    fuzzy wuzzy docs: https://github.com/seatgeek/fuzzywuzzy
    thanks SeatGeek!
    """
    return fuzz.ratio(quote, markov_text)


def quotes_dataset():
    """Load the manually cleaned data from Github.

    Returns:
    1) text: string to pass to markovify
    2) posts: pandas dataframe
    """
    quotes_url = "https://raw.githubusercontent.com/erickbytes/positivipy/main/Positive_Thoughts_Manually_Cleaned.csv"
    posts = pd.read_csv(quotes_url)
    posts = posts.drop_duplicates()
    quotes = posts.Quotes.fillna("").astype(str).str.capitalize().tolist()
    text = ". ".join(quotes)
    posts.Authors = (
        posts.Authors.fillna("Unknown")
        .astype(str)
        .str.strip()
        .str.title()
        .str.replace(" Az", "")
        .str.replace(" Picture", "")
        .str.replace(" Forbes", "")
        .str.replace("~", "")
        .str.strip()
    )
    posts = posts[
        posts.Authors.notnull()
        & ~posts.Authors.str.isspace()
        & posts.Authors.str.contains(pat="[a-zA-Z]", na=False, regex=True)
    ].reset_index(drop=True)
    return text, posts


def add_quote_to_db(quote):
    """Pass data as SQL parameters with mysql to add generated quotes to DB."""
    try:
        conn = mysql.connector.connect(
            host="user.mysql.pythonanywhere-services.com",
            db="user$database",
            user="user_name",
            password="password",
        )
        cursor = conn.cursor()
        record_tuple = (quote, datetime.now())
        sql = """INSERT INTO Quotes (Quote, Date) VALUES (%s, %s) """
        cursor.execute(sql, record_tuple)
        conn.commit()
    except mysql.connector.Error as error:
        logging.info("Failed to insert into MySQL table {}".format(error))
    except:
        logging.exception("Error inserting records to DB.")
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()
        return "MySQL connection is closed"


def clean_quote(quote):
    """Apply formatting and correction to text returned by Markov chain.
    It seems to have trouble with punctuation in some cases.

    accepts --> str
    returns --> str
    """
    if quote.startswith("."):
        quote = quote[1:]
    if "!" in quote:
        quote = "! ".join([q.strip().capitalize() for q in quote.split("!")])
    if "?" in quote:
        quote = "? ".join([q.strip().capitalize() for q in quote.split("?")])
    if "." in quote:
        quote = ". ".join([q.strip().capitalize() for q in quote.split(".")])
    quote = (
        quote.replace(" i ", " I ")
        .replace("..", ".")
        .replace("i'", "I'")
        .replace(". .", ".")
        .replace("!.", "!")
        .replace(",.", ".")
        .replace("?.", "?")
        .replace(". .", ".")
        .replace("Lifehack", " ")
        .replace("Art to self", " ")
    )
    # remove first character if period
    if quote.strip().startswith("."):
        quote = str(quote[1:]).strip()
    # use ftfy for any odd character fixes
    quote = ftfy.fix_text(quote)
    return quote


@app.route("/add_vote_to_db", methods=["GET", "POST"])
def add_vote_to_db():
    """Pass data as SQL parameters to update Votes table with user votes.
    accepts: list of tuples for 2 columns"""
    try:
        quote = request.args.get("q")
        vote = request.args.get("v")
        conn = mysql.connector.connect(
            host="user.mysql.pythonanywhere-services.com",
            db="user$database",
            user="user_name",
            password="password",
        )
        cursor = conn.cursor()
        sql = """INSERT INTO Votes (up_or_down, quote, date) VALUES (%s, %s, %s) """
        record_tuple = (vote, quote, str(datetime.now()))
        cursor.execute(sql, record_tuple)
        conn.commit()
    except mysql.connector.Error as error:
        logging.info("Failed to insert into MySQL table {}".format(error))
    except:
        logging.exception("Error inserting records to DB.")
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()
        logging.info("MySQL connection is closed")
        return redirect(url_for("get_quote"))


def get_votes_from_db():
    """Get the number of upvotes or downvotes for a quote from the DB."""
    try:
        conn = mysql.connector.connect(
            host="user.mysql.pythonanywhere-services.com",
            db="user$database",
            user="user_name",
            password="password",
        )
        votes_df = pd.read_sql(sql="""SELECT * FROM Votes""", con=conn)
        if conn.is_connected():
            conn.close()
        upvotes = votes_df[votes_df.up_or_down == "up"].tail(3)
        upvotes = (
            upvotes.rename(columns={"quote": "recent upvotes"})
            .drop(["date", "up_or_down"], axis=1)
            .to_html(index=False, border=0, justify="left")
        )
        return upvotes
    except mysql.connector.Error as error:
        logging.info("Failed to insert into MySQL table {}".format(error))
    except:
        logging.exception("Error inserting records to DB.")


def translate_text(quote, language):
    """Translate text with the TextBlob module."""
    try:
        if isinstance(quote, list):
            quote = "".join(list)
        quote = str(quote).replace(",", " ")
        logging.info(quote)
        b = TextBlob(quote)
        translation = b.translate(to=language)
        return str(translation)
    except:
        logging.exception(f"Failed to translate text {str(quote)}")
        redirect(url_for("get_quote"))


def fix_spelling_and_grammar(quote):
    """Use language tool API correction and textblob spell check
    Then apply textblob's spell check to the text.
    python library: https://pypi.org/project/language-tool-python/"""
    try:
        # use the public API, language English
        tool = language_tool_python.LanguageToolPublicAPI("en-US")
        quote = tool.correct(quote)
        b = TextBlob(quote)
        return str(b.correct())
    except:
        logging.exception("failed to get corrected text from Language Tool API")
        return quote
