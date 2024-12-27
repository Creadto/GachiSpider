"""
    Title: Robots Validation
    Description: This code is a test code for robots.txt validation.
    Features:
    - This code is a test code for robots.txt validation.
"""
import requests
from spider.utils.matcher import Matcher

response = requests.get("https://www.linkedin.com/robots.txt")
matcher = Matcher(response.text, "googlebot")
print(matcher.allow_by(url="https://www.linkedin.com/company/hot-topic"))
