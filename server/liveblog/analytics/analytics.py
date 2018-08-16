from flask import Blueprint, request
from flask_cors import CORS
from superdesk.resource import Resource
from superdesk.services import BaseService
from superdesk import get_resource_service
from flask import current_app as app
from flask import make_response
from bson import ObjectId
import logging
import json
import datetime
from bson.json_util import dumps

logger = logging.getLogger('superdesk')

analytics_blueprint = Blueprint('analytics', __name__)
CORS(analytics_blueprint)

analytics_schema = {
    'blog_id': Resource.rel('blogs', embeddable=True, required=True, type="objectid"),
    'website_url': {
        'type': 'string',
    },
    'contexturl': {
        'type': 'string',
    },
    'updated': {
        'type': 'datetime',
    },
    'hits': {
        'type': 'integer'
    }
}


class AnalyticsResource(Resource):
    datasource = {
        'source': 'analytics',
        'default_sort': [('hits', 1)]
    }

    public_methods = ['GET']
    privileges = {'GET': 'analytics'}

    schema = analytics_schema


class AnalyticsService(BaseService):
    notification_key = 'analytics'


@analytics_blueprint.route('/api/blogs/<blog_id>/<sort_type>/bloganalytics', methods=['GET'])
def get_analytics(blog_id, sort_type):
    website_url = request.args.get('websiteUrl')

    start = datetime.datetime.now() - datetime.timedelta(days=7)

    if sort_type == 'month':
        start = datetime.datetime.now() - datetime.timedelta(days=30)
    elif sort_type == 'year':
        start = datetime.datetime.now() - datetime.timedelta(days=365)

    db_client = app.data.mongo.pymongo('analytics').db['analytics']

    if website_url:
        response_data = dumps(db_client.find({
            "blog_id": ObjectId(blog_id),
            "website_url": website_url,
            "updated": {"$gte": start}
        }).limit(500))
    else:
        response_data = dumps(
            db_client.aggregate([
                {
                    "$match":
                    {
                        "blog_id": ObjectId(blog_id),
                        "website_url": {"$exists": True},
                    }
                },
                {
                    "$group":
                    {
                        "_id": {"website_url": "$website_url"},
                        "hits": {"$sum": "$hits"}
                    }
                }
            ])
        )
        limit = 500 - len(json.loads(response_data))
        limit = limit if limit > 0 else 500
        response_without_domain = dumps(
            db_client.find({
                "blog_id": ObjectId(blog_id),
                "website_url": {"$exists": False}
            }).limit(limit)
        )
        response_data = dumps(json.loads(response_data) + json.loads(response_without_domain))

    return make_response(response_data, 200)


@analytics_blueprint.route('/api/bloganalytics/<blog_state>', methods=['GET'])
def get_blog_analytics(blog_state):
    db_client = app.data.mongo.pymongo('analytics').db['analytics']

    if blog_state == 'active':
        blog_status = 'open'
    else:
        blog_status = 'closed'

    response_data = dumps(
        db_client.aggregate([
            {
                "$sort": {"updated": -1},
            },
            {
                "$group":
                {
                    "_id": {"blog_id": "$blog_id"},
                    "hits": {"$sum": "$hits"},
                    "updated": {"$first": "$updated"},
                    "website_count": {"$sum": 1},
                }
            },
            {
                "$lookup":
                {
                    "from": "blogs",
                    "localField": "_id.blog_id",
                    "foreignField": "_id",
                    "as": "blog_details",
                }
            },
            {
                "$match":
                {
                    "blog_details.blog_status": blog_status,
                }
            }
        ])
    )

    return make_response(response_data, 200)


@analytics_blueprint.route('/api/analytics/hit', methods=['POST'])
def analytics_hit():
    data = request.get_json()
    context_url = data['context_url']
    website_url = data['website_url']
    blog_id = data['blog_id']
    # check ip of origin of request
    # request may have been forwarded by proxy
    if 'X-Forwarded-For' in request.headers:
        ip = request.headers.getlist("X-Forwarded-For")[0].rpartition(' ')[-1]
    else:
        ip = request.remote_addr or 'untrackable'

    # use ip as key and blog_id as value in cache
    cache = app.cache
    cached = cache.get(ip)
    if cached == blog_id:
        return make_response('hit already registered', 406)

    # short term cache is enough here, as we just want to guard against hammering of db
    cache.set(ip, blog_id, timeout=5 * 60)

    # check blog with given id exists
    blogs_service = get_resource_service('blogs')
    blog = blogs_service.find_one(req=None, checkUser=False, _id=blog_id)
    if blog is None:
        data = json.dumps({
            '_status': 'ERR',
            '_error': 'No blog available for syndication with given id "{}".'.format(blog_id)
        })
        response = make_response(data, 409)
        return response

    # if ip is new and blog exists, add a record of a hit in db
    client = app.data.mongo.pymongo('analytics').db['analytics']
    # use upsert to be thread safe (upsert updates the record if it exists, or else creates it)
    client.update({'blog_id': ObjectId(blog_id), 'website_url': website_url, 'context_url': context_url}, {
        "$set": {"updated": datetime.datetime.now()}, "$inc": {"hits": 1}}, upsert=True)

    return make_response('success', 200)
