
import requests
import sqlite3
import logging
import sys
from typing import List, Dict


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("app.log", encoding='utf-8')
    ]
)
logger = logging.getLogger("PostsApp")


class PostsAPIClient:
    """Client to interact with the JSONPlaceholder posts API."""

    BASE_URL = "https://jsonplaceholder.typicode.com"

    def __init__(self):
        self.session = requests.Session()

    def fetch_posts(self) -> List[Dict]:
        """Fetches posts from the JSONPlaceholder API.
        
        Returns:
            List of posts as dictionaries
        Raises:
            requests.RequestException: if the HTTP request fails
            ValueError: if the response content is invalid or empty
        """
        url = f"{self.BASE_URL}/posts"
        logger.info("Fetching posts data from API: %s", url)
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            posts = response.json()
            if not isinstance(posts, list):
                raise ValueError("Invalid response format: Expected a list of posts")
            logger.info("Successfully fetched %d posts", len(posts))
            return posts
        except requests.RequestException as e:
            logger.error("HTTP request failed: %s", e)
            raise
        except ValueError as e:
            logger.error("Response processing failed: %s", e)
            raise


class PostsDatabase:
    """Handles SQLite operations for posts."""

    def __init__(self, db_path: str = "posts.db"):
        self.db_path = db_path
        self.connection = None

    def __enter__(self):
        """Allows use with 'with' statement."""
        self.connection = sqlite3.connect(self.db_path)
        self._initialize_schema()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self.connection:
            self.connection.commit()
            self.connection.close()

    def _initialize_schema(self):
        """Creates the posts table if it does not exist."""
        logger.debug("Initializing database schema if not present")
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY,
            userId INTEGER NOT NULL,
            title TEXT NOT NULL,
            body TEXT NOT NULL
        );
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute(create_table_sql)
            self.connection.commit()
            logger.info("Database schema initialized")
        except sqlite3.Error as e:
            logger.error("Failed to initialize database schema: %s", e)
            raise

    def insert_posts(self, posts: List[Dict]):
        """Inserts multiple post records into the database.
        
        Args:
            posts: List of post dictionaries
        """
        insert_sql = """
        INSERT OR REPLACE INTO posts (id, userId, title, body)
        VALUES (?, ?, ?, ?);
        """
        try:
            cursor = self.connection.cursor()
            records = [(post['id'], post['userId'], post['title'], post['body']) for post in posts]
            cursor.executemany(insert_sql, records)
            self.connection.commit()
            logger.info("Inserted or replaced %d posts into the database", len(records))
        except sqlite3.Error as e:
            logger.error("Failed to insert posts into database: %s", e)
            raise


def normalize_post(post: Dict) -> Dict:
    """
    Normalizes a single post dictionary to ensure consistent field types and values.

    JSONPlaceholder posts look like:
    {
      "userId": 1,
      "id": 1,
      "title": "sunt aut facere repellat provident occaecati excepturi optio reprehenderit",
      "body": "quia et suscipit\nsuscipit ..."
    }

    This function ensures the right fields are present and type cast correctly.
    """
    try:
        normalized = {
            'userId': int(post['userId']),
            'id': int(post['id']),
            'title': str(post['title']).strip(),
            'body': str(post['body']).strip(),
        }
        return normalized
    except (KeyError, ValueError, TypeError) as e:
        logger.warning("Skipping invalid post due to error: %s - post data: %s", e, post)
        return None


def normalize_posts(posts: List[Dict]) -> List[Dict]:
    """Normalize a list of post dictionaries."""
    normalized_posts = []
    for post in posts:
        normalized = normalize_post(post)
        if normalized:
            normalized_posts.append(normalized)
    logger.info("Normalized %d posts", len(normalized_posts))
    return normalized_posts


def main():
    try:
        client = PostsAPIClient()
        raw_posts = client.fetch_posts()

        normalized_posts = normalize_posts(raw_posts)

        with PostsDatabase() as db:
            db.insert_posts(normalized_posts)

        logger.info("Posts fetched, normalized, and saved successfully.")
    except Exception as e:
        logger.exception("An unhandled exception occurred: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
