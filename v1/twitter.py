import sys
import re
import subprocess
import json
import translate

TWITTER_STATUS_REGEX = re.compile(
    r"https?://(?:www\.)?"
    r"(?:twitter\.com|x\.com|xcancel\.com|nitter\.[^/]+)"
    r"/(?P<username>[^/]+)/status/(?P<id>\d+)",
    re.IGNORECASE,
)


def find_twitter_matches(args):
    text = " ".join(args)
    return list(TWITTER_STATUS_REGEX.finditer(text))


def extract_metadata(url):
    id_match = re.search(r"status/(\d+)", url)
    user_match = re.search(
        r"(?:https?://)?(?:www\.)?[^/]+/([^/]+)/status", url)
    tweet_id = id_match.group(1) if id_match else None
    username = user_match.group(1) if user_match else "i"
    return username, tweet_id


def get_tweet_info(url):
    # Calling the cached binary directly
    cmd = [
        "yt-dlp",
        "--quiet",
        "--no-warnings",
        "--skip-download",
        "--print-json",
        "--ignore-no-formats-error",
        url
    ]
    try:
        # check=True will raise an error if yt-dlp fails
        result = subprocess.run(
            cmd, capture_output=True, text=True, check=True)
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"yt-dlp error: {e.stderr}")
        return None


def main(url):
    username, tweet_id = extract_metadata(url)
    info = get_tweet_info(url)

    if not info:
        print("🐦 Twitter / X")
        print("Error: Could not access this tweet (it might be private or deleted).")
        return

    # 1. Text Processing (5 lines / 350 chars)
    # X often puts the tweet text in 'description' or 'title'
    text = info.get('description') or info.get('title') or ""
    # Clean up common yt-dlp suffixes like " - X" or " - Twitter"
    text = re.sub(r" - (X|Twitter)$", "", text).strip()

    lines = text.splitlines()[:5]
    truncated_text = "\n".join(lines)
    if len(truncated_text) > 350:
        truncated_text = truncated_text[:347] + "..."

    # 2. Media Extraction
    media = []

    # Check for Videos
    if info.get('url'):
        media.append(info['url'])

    # Check for Images (stored in thumbnails)
    # We look for 'orig' in the URL to get the highest resolution
    thumbnails = info.get('thumbnails', [])
    for t in thumbnails:
        img_url = t.get('url', '')
        if 'media' in img_url and img_url not in media:
            # Convert to high-res 'orig' format if it's a standard thumbnail
            img_url = re.sub(r"name=\w+", "name=orig", img_url)
            media.append(img_url)

    # 3. Plaintext Chat Output
    text = truncated_text if truncated_text else "Twitter / X"
    print(f"🐦 {text} 🐦")

    tl = translate.smart(truncated_text)
    if "<english>" not in tl:
        print(tl)

    if media:
        for m in list(dict.fromkeys(media))[:5]:
            print(f"- {m}")

    print(f"🐦 https://xcancel.com/{username}/status/{tweet_id} 🐦")


if __name__ == "__main__":
    matches = find_twitter_matches(sys.argv[1:])
    if matches:
        for match in matches:
            main(match.group(0))
