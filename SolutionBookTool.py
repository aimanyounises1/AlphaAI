import requests
import json
from urllib3 import disable_warnings
from urllib3.exceptions import InsecureRequestWarning
from urllib.parse import urlencode
from bs4 import BeautifulSoup, Comment
import html2text

# Disable SSL verification warnings
disable_warnings(InsecureRequestWarning)

# Configuration - load from environment variables
import os
personal_access_token = os.getenv("PERSONAL_ACCESS_TOKEN_SB", "your_personal_access_token_here")
domain = os.getenv("SOLUTIONBOOK_DOMAIN", "your-confluence-domain.com")

# Proxy settings - configure via environment variables if needed
proxies = {
    'http': os.getenv('HTTP_PROXY'),
    'https': os.getenv('HTTPS_PROXY'),
} if os.getenv('HTTP_PROXY') else {}

# API endpoint
api_url = f"https://{domain}/rest/api/content"

# Headers
headers = {
    "Accept": "application/json",
    "Authorization": f"Bearer {personal_access_token}"
}


def log_request(method, url, **kwargs):
    print(f"\n{method} Request:")
    print(f"URL: {url}")
    if 'params' in kwargs:
        print(f"Params: {json.dumps(kwargs['params'], indent=2)}")
    if 'headers' in kwargs:
        print(f"Headers: {json.dumps(kwargs['headers'], indent=2)}")
    print(f"Full URL: {url}?{urlencode(kwargs.get('params', {}))}")


def print_response_info(response):
    print(f"Status code: {response.status_code}")
    print("Response headers:")
    for header, value in response.headers.items():
        print(f"{header}: {value}")
    print("\nResponse content:")
    try:
        print(json.dumps(response.json(), sort_keys=True, indent=4, separators=(",", ": ")))
    except json.JSONDecodeError:
        print(response.text)


def save_response_content(response_content, filename="response_content.json"):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(response_content, f, sort_keys=True, indent=4, separators=(",", ": "))
    print(f"Response content saved to {filename}")


def clean_html_content(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')

    # Remove script and style elements
    for element in soup(["script", "style"]):
        element.decompose()

    # Remove comments
    for comment in soup.find_all(text=lambda text: isinstance(text, Comment)):
        comment.extract()

    # Remove specific Confluence macros
    for macro in soup.find_all('ac:structured-macro'):
        macro.decompose()

    # Remove most attributes from tags, keeping only essential ones
    for tag in soup.recursiveChildGenerator():
        if hasattr(tag, 'attrs'):
            tag.attrs = {key: value for key, value in tag.attrs.items()
                         if key in ['href', 'src', 'alt', 'title']}

    # Convert specific elements to more readable format
    for table in soup.find_all('table'):
        table['border'] = '1'
        table['style'] = 'border-collapse: collapse;'

    for td in soup.find_all('td'):
        td['style'] = 'padding: 5px;'

    # Replace Confluence's custom tags with standard HTML
    for div in soup.find_all('div', class_='confluence-information-macro'):
        div.name = 'blockquote'
        div.attrs = {}

    # Convert the soup back to a string
    clean_html = str(soup)

    # Remove empty lines
    clean_html = '\n'.join(line for line in clean_html.split('\n') if line.strip())

    return clean_html


def html_to_text(html_content):
    h = html2text.HTML2Text()
    h.ignore_links = False
    h.ignore_images = False
    h.body_width = 0  # Disable line wrapping
    return h.handle(html_content)


def login():
    # Test authentication
    test_url = f"https://{domain}/rest/api/space"
    log_request('GET', test_url, headers=headers)
    test_response = requests.get(test_url, headers=headers, proxies=proxies, verify=False, timeout=30)
    print("Authentication test result:")
    print_response_info(test_response)

    if test_response.status_code != 200:
        print("Authentication failed. Please check your personal access token.")
        return False
    return True


def search_pages(title):
    cql = f'title~"{title}"'
    search_params = {
        "limit": 10,
        "data": 0,
        "expand": "container,metadata.currentuser.viewed,metadata.currentuser.favourited",
        "cql": cql
    }
    search_url = f"{api_url}/search"
    log_request('GET', search_url, params=search_params, headers=headers)
    response = requests.get(search_url, headers=headers, params=search_params, proxies=proxies, verify=False,
                            timeout=30)
    print("Search API call result:")
    print_response_info(response)
    save_response_content(response.json(), "search_results.json")
    return response


def fetch_and_clean_page_content(page_id):
    content_params = {
        "expand": "body.storage,version"
    }
    content_url = f"{api_url}/{page_id}"
    log_request('GET', content_url, params=content_params, headers=headers)
    response = requests.get(content_url, headers=headers, params=content_params, proxies=proxies, verify=False,
                            timeout=30)
    print("Content API call result:")
    print_response_info(response)

    if response.status_code == 200:
        content_json = response.json()
        if 'body' in content_json and 'storage' in content_json['body'] and 'value' in content_json['body']['storage']:
            html_content = content_json['body']['storage']['value']
            clean_html = clean_html_content(html_content)

            # Save HTML file
            html_filename = f"clean_page_content_{page_id}.html"
            with open(html_filename, "w", encoding="utf-8") as f:
                f.write(clean_html)
            print(f"Clean page content saved to {html_filename}")

            # Convert to text and save text file
            text_content = html_to_text(clean_html)
            text_filename = f"clean_page_content_{page_id}.txt"
            with open(text_filename, "w", encoding="utf-8") as f:
                f.write(text_content)
            print(f"Text version of page content saved to {text_filename}")
        else:
            print("No storage content found in the expected path.")
    else:
        print(f"Failed to fetch page content. Status code: {response.status_code}")

    save_response_content(response.json(), f"page_content_{page_id}.json")
    return response


def upload_attachment(page_id, attachment):
    attachment_url = f"{api_url}/{page_id}/child/attachment"
    headers['X-Atlassian-Token'] = 'no-check'
    files = {
        'file': (attachment['name'], attachment['content'], 'application/octet-stream')
    }
    log_request('POST', attachment_url, headers=headers)
    response = requests.post(attachment_url, headers=headers, files=files, proxies=proxies, verify=False, timeout=30)
    print("Attachment upload call result:")
    print_response_info(response)
    return response


def main():
    try:
        # Login
        if not login():
            return

        # Choose action: Search page or upload attachment
        action = input("Choose action (search/upload): ").strip().lower()

        if action == "search":
            title = input("Enter title keyword to search for pages: ").strip()
            search_response = search_pages(title)

            if search_response.status_code == 200:
                search_data = search_response.json()
                if search_data.get('results'):
                    for result in search_data['results']:
                        print(
                            f"\nFound page ID: {result['id']}, Title: {result['title']}, Space Key: {result['container']['key']}")
                        print("\nPage details:")
                        print(f"Web UI link: {result['_links']['webui']}")
                        print("\nViewing metadata (friendlyLastSeen):")
                        try:
                            print(f"Last seen: {result['metadata']['currentuser']['viewed']['friendlyLastSeen']}")
                        except KeyError:
                            print("No viewing metadata available.")

                        # Fetch, clean, and save the full content of the page
                        fetch_and_clean_page_content(result['id'])
                else:
                    print("No pages found")
            else:
                print("Failed to execute search")

        elif action == "upload":
            # Prompt for page ID to attach the file to
            page_id = input("Enter Page ID to upload attachment: ")

            # Example attachment data (you can adapt this as needed)
            # Note: In a real scenario, the file content should be read from an actual file.
            attachment = {
                "name": "example.txt",
                "content": b"This is the content of the file",  # Example binary content
                "kind": "selected-text"
            }

            upload_response = upload_attachment(page_id, attachment)
            if upload_response.status_code in [200, 201]:
                print("Attachment uploaded successfully")
            else:
                print("Failed to upload attachment")

        else:
            print("Invalid action. Please choose 'search' or 'upload'.")

    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    main()
