from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required
from flasgger import swag_from
import validators

from src.constants.http_status_code import (
    HTTP_400_BAD_REQUEST,
    HTTP_409_CONFLICT,
    HTTP_201_CREATED,
    HTTP_200_OK,
    HTTP_404_NOT_FOUND,
    HTTP_204_NO_CONTENT,
)
from src.database import Bookmark, db


bookmarks = Blueprint("bookmarks", __name__, url_prefix="/api/v1/bookmarks")


@bookmarks.post("/")
@jwt_required()
@swag_from("./docs/bookmarks/addbook.yaml")
def add_book():
    return add_bookmark()


@bookmarks.get("/")
@jwt_required()
@swag_from("./docs/bookmarks/books.yaml")
def get_all_bookmarks():
    return get_all_bookmarks_of_current_user()


@bookmarks.get("/<int:id>")
@jwt_required()
@swag_from("./docs/bookmarks/book.yaml")
def get_bookmark(id):
    current_user = get_jwt_identity()

    bookmark = Bookmark.query.filter_by(user_id=current_user, id=id).first()

    if not bookmark:
        return jsonify({"message": "Bookmark not found"}), HTTP_404_NOT_FOUND

    return (
        jsonify(
            {
                "id": bookmark.id,
                "url": bookmark.url,
                "short_url": bookmark.short_url,
                "visit": bookmark.visits,
                "body": bookmark.body,
                "updated_at": bookmark.updated_at,
                "created_at": bookmark.created_at,
            }
        ),
        HTTP_200_OK,
    )


@bookmarks.put("<int:id>")
@bookmarks.patch("<int:id>")
@jwt_required()
@swag_from("./docs/bookmarks/editbook.yaml")
def edit_bookmark(id):
    current_user = get_jwt_identity()
    bookmark = Bookmark.query.filter_by(user_id=current_user, id=id).first()
    if not bookmark:
        return jsonify({"message": "Bookmark not found"}), HTTP_404_NOT_FOUND

    return update_bookmark(bookmark)


@bookmarks.delete("<int:id>")
@jwt_required()
@swag_from("./docs/bookmarks/deletebook.yaml")
def delete_bookmark(id):
    current_user = get_jwt_identity()
    bookmark = Bookmark.query.filter_by(user_id=current_user, id=id).first()
    if not bookmark:
        return jsonify({"message": "Bookmark not found"}), HTTP_404_NOT_FOUND

    return delete_bookmark(bookmark)


@bookmarks.get("/stats")
@jwt_required()
@swag_from("./docs/bookmarks/stats.yaml")
def get_stats():
    current_user = get_jwt_identity()
    data = []

    items = Bookmark.query.filter_by(user_id=current_user).all()

    for item in items:
        new_link = {
            "visits": item.visits,
            "url": item.url,
            "id": item.id,
            "short_url": item.short_url,
        }

        data.append(new_link)

    return jsonify({"data": data}), HTTP_200_OK


def add_bookmark():
    body = request.get_json().get("body", "")
    url = request.get_json().get("url", "")

    return verify_bookmark_exist(url) or add_bookmark_query(url, body)


def add_bookmark_query(url: str, body: str):
    current_user = get_jwt_identity()
    bookmark = Bookmark(url=url, body=body, user_id=current_user)
    db.session.add(bookmark)
    db.session.commit()

    return (
        jsonify(
            {
                "id": bookmark.id,
                "url": bookmark.url,
                "short_url": bookmark.short_url,
                "visit": bookmark.visits,
                "body": bookmark.body,
                "updated_at": bookmark.updated_at,
                "created_at": bookmark.created_at,
            }
        ),
        HTTP_201_CREATED,
    )


def verify_bookmark_exist(url: str):
    if not validators.url(url):
        return jsonify({"error": "Invalid URL"}), HTTP_400_BAD_REQUEST

    if Bookmark.query.filter_by(url=url).first():
        return jsonify({"error": "Bookmark already exists"}), HTTP_409_CONFLICT

    return None


def get_all_bookmarks_of_current_user():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 5, type=int)
    current_user = get_jwt_identity()
    bookmarks = Bookmark.query.filter_by(user_id=current_user).paginate(
        page=page, per_page=per_page
    )

    data = [
        {
            "id": bookmark.id,
            "url": bookmark.url,
            "short_url": bookmark.short_url,
            "visit": bookmark.visits,
            "body": bookmark.body,
            "updated_at": bookmark.updated_at,
            "created_at": bookmark.created_at,
        }
        for bookmark in bookmarks
    ]
    meta = {
        "page": bookmarks.page,
        "pages": bookmarks.pages,
        "total_count": bookmarks.total,
        "prev_page": bookmarks.prev_num,
        "next_page": bookmarks.next_num,
        "has_next": bookmarks.has_next,
        "has_prev": bookmarks.has_prev,
    }
    return jsonify({"data": data, "meta": meta}), HTTP_200_OK


def update_bookmark(bookmark: Bookmark):
    body = request.get_json().get("body", "")
    url = request.get_json().get("url", "")

    if not validators.url(url):
        return jsonify({"error": "Invalid URL"}), HTTP_400_BAD_REQUEST

    bookmark.url = url
    bookmark.body = body

    db.session.commit()

    return (
        jsonify(
            {
                "id": bookmark.id,
                "url": bookmark.url,
                "short_url": bookmark.short_url,
                "visit": bookmark.visits,
                "body": bookmark.body,
                "updated_at": bookmark.updated_at,
                "created_at": bookmark.created_at,
            }
        ),
        HTTP_200_OK,
    )


def delete_bookmark(bookmark: Bookmark):
    db.session.delete(bookmark)
    db.session.commit()

    return jsonify({}), HTTP_204_NO_CONTENT
