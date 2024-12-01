from flask import Flask, request, render_template, send_file
import requests
from bs4 import BeautifulSoup
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from io import StringIO
import json
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from pymongo import MongoClient  # Import MongoDB client
from datetime import datetime 
# MongoDB Configuration
client = MongoClient('mongodb://localhost:27017/')  # Replace with your MongoDB URI
db = client['seo_analyzer']
results_collection = db['analysis_results']

app = Flask(__name__)

# Download necessary NLTK data files
nltk.download('stopwords')
nltk.download('punkt')

def capture_screenshot(url, output_file, viewport_size):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument(f"--window-size={viewport_size}")  # Set viewport size
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    driver.get(url)
    driver.save_screenshot(output_file)
    driver.quit()

def analyze_seo(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Keyword Density Analysis
    def calculate_keyword_density(text, keywords):
        word_count = len(text.split())
        keyword_density = {keyword: (freq / word_count) * 100 for keyword, freq in keywords.items()}
        return keyword_density

    body_text = soup.get_text().lower()
    keywords = {"example": body_text.count("example")}  # Replace with dynamic keyword extraction logic
    keyword_density = calculate_keyword_density(body_text, keywords)

    # Mobile-Friendliness Check
    def check_mobile_friendly(soup):
        viewport = soup.find('meta', attrs={'name': 'viewport'})
        if viewport:
            return "Viewport tag exists. The page is likely mobile-friendly."
        else:
            return "Viewport tag is missing! Consider adding it to make your page responsive."

    mobile_friendly = check_mobile_friendly(soup)

    # Schema Markup Detection
    def detect_schema_markup(soup):
        schema_types = []
        for script in soup.find_all('script', type='application/ld+json'):
            try:
                json_content = json.loads(script.string)
                if '@type' in json_content:
                    schema_types.append(json_content['@type'])
            except json.JSONDecodeError:
                continue
        return schema_types

    schema_types = detect_schema_markup(soup)

    # Accessibility Checks
    def check_accessibility(soup):
        accessibility_issues = []
        for img in soup.find_all('img'):
            if not img.get('alt'):
                accessibility_issues.append(f"Image with src '{img.get('src')}' is missing alt text.")
        # Add more checks as needed
        return accessibility_issues

    accessibility_issues = check_accessibility(soup)

    # Page Load Time Analysis
    def analyze_page_load_time(url):
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        driver.get(url)
        navigation_start = driver.execute_script("return window.performance.timing.navigationStart")
        load_event_end = driver.execute_script("return window.performance.timing.loadEventEnd")
        load_time = load_event_end - navigation_start
        driver.quit()
        return load_time / 1000  # Convert to seconds

    page_load_time = analyze_page_load_time(url)

    # Broken Link Checker
    def check_broken_links(soup, base_url):
        broken_links = []
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            if not href.startswith(('http://', 'https://')):
                href = base_url + href
            try:
                response = requests.head(href)
                if response.status_code >= 400:
                    broken_links.append(href)
            except requests.RequestException:
                broken_links.append(href)
        return broken_links

    broken_links = check_broken_links(soup, url)

    # Social Media Integration Analysis
    def check_social_media_integration(soup):
        social_media_tags = {
            'og:title': 'Open Graph Title',
            'og:description': 'Open Graph Description',
            'twitter:card': 'Twitter Card'
        }
        missing_tags = []
        for tag, description in social_media_tags.items():
            if not soup.find('meta', attrs={'property': tag}) and not soup.find('meta', attrs={'name': tag}):
                missing_tags.append(f"{description} ({tag}) is missing.")
        return missing_tags

    social_media_issues = check_social_media_integration(soup)

    # Existing SEO analysis
    good = []
    bad = []
    keywords = []
    title_keywords = []
    seo_title = None
    seo_description = None
    links_ratio = {'internal': 0, 'external': 0}
    score = 100  # Start with a perfect score of 100
    recommendations = []

    # Check title
    title_tag = soup.find('title')
    if title_tag and title_tag.get_text():
        seo_title = title_tag.get_text().strip()
        good.append("Title Exists! Great!")
    else:
        bad.append("Title does not exist! Add a Title")
        recommendations.append("Add a title to your page to improve SEO ranking.")
        score -= 10  # Deduct points for missing title

    # Check meta description
    meta_desc = soup.find('meta', attrs={'name': 'description'})
    if meta_desc and meta_desc.get('content') and len(meta_desc.get('content')) > 50:
        good.append("Description Exists! Great!")
        seo_description=meta_desc.get('content').strip()
    else:
        bad.append("Description is missing, too short, or not relevant! Add a proper Meta Description")
        recommendations.append("Include a meta description that accurately describes the page content and includes relevant keywords.")
        score -= 10  # Deduct points for missing or poor description
    # Check headings
    hs = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']
    h_tags = []
    for h in soup.find_all(hs):
        good.append(f"{h.name} --> {h.text.strip()}")
        h_tags.append(h.name)

    h1_tags = soup.find_all('h1')
    if not h1_tags:
        bad.append("No H1 found!")
        recommendations.append("Add a single H1 tag that accurately describes the content of the page.")
        score -= 10  # Deduct points for missing H1
    elif len(h1_tags) > 1:
        bad.append(f"Multiple H1 tags found: {len(h1_tags)}")
        recommendations.append("Use only one H1 tag per page to ensure clear content hierarchy.")
        score -= 5  # Deduct points for multiple H1s
    else:
        good.append(f"One H1 tag found: {h1_tags[0].text.strip()}")

    # Check images for alt attributes
    image_alt_attributes = []
    for img in soup.find_all('img'):
        if not img.get('alt'):
            bad.append(f"Image with src '{img.get('src')}' is missing alt text")
            recommendations.append(f"Add alt text to the image with src '{img.get('src')}' to improve accessibility and SEO.")
            score -= 5  # Deduct points for missing alt text
        elif img.get('alt').strip() == '':
            bad.append(f"Image with src '{img.get('src')}' has empty alt text")
            recommendations.append(f"Provide meaningful alt text for the image with src '{img.get('src')}'.")
        else:
            image_alt_attributes.append(img.get('alt').strip())

    # Extract keywords
    bod = soup.find('body').text
    words = [i.lower() for i in word_tokenize(bod)]
    sw = stopwords.words('english')
    new_words = [i for i in words if i not in sw and i.isalpha()]
    freq = nltk.FreqDist(new_words)
    keywords = freq.most_common(10)

    # Calculate internal and external links
    internal_links = 0
    external_links = 0
    for link in soup.find_all('a', href=True):
        href = link.get('href')
        if href.startswith(url):
            internal_links += 1
        else:
            external_links += 1

    links_ratio = {'internal': internal_links, 'external': external_links}

    # Extract keywords from title
    if seo_title:
        title_words = [i.lower() for i in word_tokenize(seo_title)]
        title_keywords = [i for i in title_words if i not in sw and i.isalpha()]

    # Capture screenshots
    mobile_screenshot_path = 'static/mobile_search_preview.png'
    desktop_screenshot_path = 'static/desktop_search_preview.png'
    capture_screenshot(url, mobile_screenshot_path, "360,640")  # Mobile viewport
    capture_screenshot(url, desktop_screenshot_path, "1280,1024")  # Desktop viewport

    return good, bad, keywords, score, seo_title, seo_description, image_alt_attributes, links_ratio, title_keywords, recommendations, keyword_density, mobile_friendly, schema_types, accessibility_issues, page_load_time, broken_links, social_media_issues, mobile_screenshot_path, desktop_screenshot_path

def generate_report(good, bad, keywords, score, seo_title, seo_description, image_alt_attributes, links_ratio, title_keywords, recommendations, keyword_density, mobile_friendly, schema_types, accessibility_issues, page_load_time, broken_links, social_media_issues):
    # Generate a text report with SEO analysis results and recommendations
    report = StringIO()
    report.write(f"SEO Analysis Report\n")
    report.write(f"Overall Score: {score}\n\n")
    report.write(f"SEO Title: {seo_title}\n")
    report.write(f"SEO Description: {seo_description}\n\n")

    report.write("Top Keywords:\n")
    for keyword, frequency in keywords:
        report.write(f"{keyword}: {frequency}\n")
    report.write("\n")

    report.write("Title Keywords:\n")
    for keyword in title_keywords:
        report.write(f"{keyword}\n")
    report.write("\n")

    report.write("Keyword Density:\n")
    for keyword, density in keyword_density.items():
        report.write(f"{keyword}: {density:.2f}%\n")
    report.write("\n")

    report.write("Mobile-Friendliness:\n")
    report.write(f"{mobile_friendly}\n\n")

    report.write("Schema Markup:\n")
    for schema in schema_types:
        report.write(f"{schema}\n")
    report.write("\n")

    report.write("Accessibility Issues:\n")
    for issue in accessibility_issues:
        report.write(f"{issue}\n")
    report.write("\n")

    report.write(f"Page Load Time: {page_load_time:.2f} seconds\n\n")

    report.write("Broken Links:\n")
    for link in broken_links:
        report.write(f"{link}\n")
    report.write("\n")

    report.write("Social Media Integration Issues:\n")
    for issue in social_media_issues:
        report.write(f"{issue}\n")
    report.write("\n")

    report.write("The Good:\n")
    for item in good:
        report.write(f"{item}\n")
    report.write("\n")

    report.write("The Bad:\n")
    for item in bad:
        report.write(f"{item}\n")
    report.write("\n")

    report.write("Recommendations:\n")
    for recommendation in recommendations:
        report.write(f"{recommendation}\n")
    report.write("\n")

    report.write("Image ALT Attributes:\n")
    for alt in image_alt_attributes:
        report.write(f"{alt}\n")
    report.write("\n")

    report.write(f"Internal Links: {links_ratio['internal']}\n")
    report.write(f"External Links: {links_ratio['external']}\n")

    return report.getvalue()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    url = request.form.get('url')
    if not url:
        return "URL is required", 400

    results = analyze_seo(url)
    if results[0] is None:
        return "Error processing URL", 500

    good, bad, keywords, score, seo_title, seo_description, image_alt_attributes, links_ratio, title_keywords, recommendations, keyword_density, mobile_friendly, schema_types, accessibility_issues, page_load_time, broken_links, social_media_issues, mobile_screenshot_path, desktop_screenshot_path = results
    result_data = {
        "url": url,
        "timestamp": datetime.utcnow(),
        "score": score,
        "seo_title": seo_title,
        "seo_description": seo_description,
        "keywords": keywords,
        "title_keywords": title_keywords,
        "keyword_density": keyword_density,
        "mobile_friendly": mobile_friendly,
        "schema_types": schema_types,
        "accessibility_issues": accessibility_issues,
        "page_load_time": page_load_time,
        "broken_links": broken_links,
        "social_media_issues": social_media_issues,
        "links_ratio": links_ratio,
        "good": good,
        "bad": bad,
        "recommendations": recommendations
    }
    results_collection.insert_one(result_data)  # Insert into MongoDB


    report_text = generate_report(good, bad, keywords, score, seo_title, seo_description, image_alt_attributes, links_ratio, title_keywords, recommendations, keyword_density, mobile_friendly, schema_types, accessibility_issues, page_load_time, broken_links, social_media_issues)

    with open('static/seo_report.txt', 'w') as report_file:
        report_file.write(report_text)

    return render_template('results.html', good=good, bad=bad, keywords=keywords, score=score, seo_title=seo_title, seo_description=seo_description, image_alt_attributes=image_alt_attributes, links_ratio=links_ratio, title_keywords=title_keywords, recommendations=recommendations, keyword_density=keyword_density, mobile_friendly=mobile_friendly, schema_types=schema_types, accessibility_issues=accessibility_issues, page_load_time=page_load_time, broken_links=broken_links, social_media_issues=social_media_issues, mobile_screenshot_path=mobile_screenshot_path, desktop_screenshot_path=desktop_screenshot_path)

@app.route('/download_report')
def download_report():
    return send_file('static/seo_report.txt', as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
