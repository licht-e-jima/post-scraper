from requests.exceptions import HTTPError

from facebook_scraper import get_posts
from instascrape.scrapers.profile import Profile
from instascrape.exceptions.exceptions import InstagramLoginRedirectError, WrongSourceError
from fastapi import FastAPI, HTTPException
import numpy as np


import functools

def handle_requests(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except HTTPError as e:
            response = e.response
            if response is None:
                raise HTTPException(status_code=500, detail=e.strerror)

            raise HTTPException(status_code=response.status_code, detail=response.text)
    return wrapper


app = FastAPI()

@app.get("/")
def root():
    return "Hello World!"

@app.get("/facebook_posts")  # TODO: response model を定義する
@handle_requests
def facebook_posts(account: str, pages: int = 2) -> list[dict]:
    """facebook の投稿を取得する

    Args:
        account (str): アカウント名
        pages (int, optional): 取得するページ数(Default: 2)

    Returns:
        list[dict]: 投稿一覧
            [
                {
                    "comments": int,
                    "image": "image_url" | None,
                    "images": [
                        "image_url"
                    ],
                    "is_live": bool,
                    "likes": int,
                    "link": str,
                    "post_id": str,
                    "post_text": str,
                    "post_url": str,
                    "shared_text": str,
                    "shares": int,
                    "text": str,
                    "time": str,
                    "user_id": str,
                    "username": str,
                    "video": None,
                    "video_id": None,
                    "video_thumbnail": None
                }
            ]
    """
    posts = []
    for post in get_posts(account, pages=pages):
        post["time"] = post["time"].isoformat()
        posts.append(post)
    return posts

@app.get("/instagram_posts")  # TODO: response model を定義する
@handle_requests
def instagram_posts(account: str, amt: int = 12) -> list[dict]:
    """instagram の投稿を取得する

    Args:
        account (str): アカウント名
        amt (int, optional): 取得する最新投稿数(Default: 12)

    Returns:
        list[dict]: 投稿一覧
            [
                {
                    "accessibility_caption": str | None,
                    "caption": str | None,
                    "comments": int,
                    "comments_disabled": bool,
                    "dimensions": int | None,
                    "display_url": str,
                    "fact_check_information": None,
                    "fact_check_overall_rating": None,
                    "full_name": str | None,
                    "id": str,
                    "is_video": bool,
                    "likes": int,
                    "location": None,
                    "shortcode": str,
                    "tagged_users": None,
                    "timestamp": int,
                    "upload_date": str,
                    "username": str | None
                }
            ]
    """
    user = Profile(account)
    try:
        user.scrape()
    except (InstagramLoginRedirectError, WrongSourceError) as e:
        raise HTTPException(status_code=400, detail=str(e))

    recent_posts = user.get_recent_posts(amt)
    posts = []
    for p in recent_posts:
        post = p.to_dict()
        post["upload_date"] = post["upload_date"].isoformat()
        post = {
            k: (None if isinstance(v, float) and np.isnan(v) else v)
            for k, v
            in post.items()
        }
        posts.append(post)
    return posts

if __name__ == "__main__":
    import os
    import uvicorn

    port = os.getenv("PORT")
    host = os.getenv("HOST") or "0.0.0.0"
    assert port is not None

    uvicorn.run(app=app, host=host, port=int(port))
