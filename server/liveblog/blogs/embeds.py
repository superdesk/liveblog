#!/usr/bin/env python
# -*- coding: utf-8; -*-
#
# This file is part of Superdesk.
#
# Copyright 2013, 2014, 2015 Sourcefabric z.u. and contributors.
#
# For the full copyright and license information, please see the
# AUTHORS and LICENSE files distributed with this source code, or
# at https://www.sourcefabric.org/superdesk/license

import copy
import json
import logging
import os

import superdesk
from eve.io.mongo import MongoJSONEncoder
from flask import current_app as app
from flask import json, render_template, request, url_for
from liveblog.themes import ASSETS_DIR as THEMES_ASSETS_DIR
from liveblog.themes import UnknownTheme
from superdesk import get_resource_service
from superdesk.errors import SuperdeskApiError

from .app_settings import BLOGLIST_ASSETS, BLOGSLIST_ASSETS_DIR
from .utils import is_relative_to_current_folder

logger = logging.getLogger('superdesk')
embed_blueprint = superdesk.Blueprint('embed_liveblog', __name__, template_folder='templates')
THEMES_DIRECTORY = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir, 'themes'))


def collect_theme_assets(theme, assets=None, template=None):
    assets = assets or {'scripts': [], 'styles': [], 'devScripts': [], 'devStyles': []}
    # Load the template.
    if not template:
        template_file_name = os.path.join(THEMES_DIRECTORY, THEMES_ASSETS_DIR, theme['name'], 'template.html')
        if os.path.isfile(template_file_name):
            template = open(template_file_name, encoding='utf-8').read()

    # Add assets from parent theme.
    if theme.get('extends', None):
        parent_theme = get_resource_service('themes').find_one(req=None, name=theme.get('extends'))
        if parent_theme:
            assets, template = collect_theme_assets(parent_theme, assets=assets, template=template)
        else:
            error_message = 'Embed: "%s" theme depends on "%s" but this theme is not registered.' \
                % (theme.get('name'), theme.get('extends'))
            logger.info(error_message)
            raise UnknownTheme(error_message)

    # Add assets from theme.
    for asset_type in ('scripts', 'styles', 'devScripts', 'devStyles'):
        theme_folder = theme['name']
        for url in theme.get(asset_type, []):
            if is_relative_to_current_folder(url):
                if theme.get('public_url', False):
                    url = '%s%s' % (theme.get('public_url'), url)
                else:
                    url = url_for('themes_assets.static', filename=os.path.join(theme_folder, url), _external=False)
            assets[asset_type].append(url)

    return assets, template


@embed_blueprint.route('/embed/<blog_id>')
def embed(blog_id, api_host=None, theme=None):
    api_host = api_host or request.url_root
    blog = get_resource_service('client_blogs').find_one(req=None, _id=blog_id)
    if not blog:
        return 'blog not found', 404

    # Retrieve picture url from relationship.
    if blog.get('picture', None):
        blog['picture'] = get_resource_service('archive').find_one(req=None, _id=blog['picture'])

    # Retrieve the wanted theme and add it to blog['theme'] if is not the registered one.
    try:
        theme_name = request.args.get('theme', theme)
    except RuntimeError:
        # This method can be called outside from a request context.
        theme_name = theme

    theme = get_resource_service('themes').find_one(req=None, name=blog['blog_preferences'].get('theme'))
    if theme is None and theme_name is None:
        raise SuperdeskApiError.badRequestError(
            message='You will be able to access the embed after you register the themes')

    # If a theme is provided, overwrite the default theme.
    if theme_name:
        theme_package = os.path.join(THEMES_DIRECTORY, THEMES_ASSETS_DIR, theme_name, 'theme.json')
        theme = json.loads(open(theme_package).read())

    try:
        assets, template_file = collect_theme_assets(theme)
    except UnknownTheme as e:
        return str(e), 500

    if not template_file:
        logger.error('Template file not found for theme "%s". Theme: %s' % (theme.get('name'), theme))
        return 'Template file not found', 500

    # Compute the assets root.
    if theme.get('public_url', False):
        assets_root = theme.get('public_url')
    else:
        assets_root = [THEMES_ASSETS_DIR, blog['blog_preferences'].get('theme')]
        assets_root = '/{}/'.format('/'.join(assets_root))

    theme_service = get_resource_service('themes')
    theme_settings = theme_service.get_default_settings(theme)

    if theme.get('seoTheme', False):
        # Fetch initial blog posts for SEO theme
        blog_instance = Blog(blog)
        api_response = blog_instance.posts(wrap=True)
        embed_template = jinja2.Environment(loader=ThemeTemplateLoader(theme)).from_string(template_content)
        template_content = embed_template.render(
            blog=blog,
            theme=theme,
            api_response=api_response,
            theme_settings=theme_settings,
            theme_options=theme_json,
            options=bson_dumps(theme_json)
        )

    scope = {
        'blog': blog,
        'theme': theme,
        'settings': theme_settings,
        'assets': assets,
        'api_host': api_host,
        'template_content': template_content,
        'debug': app.config.get('LIVEBLOG_DEBUG'),
        'assets_root': assets_root
    }
    return render_template('embed.html', **scope)


@embed_blueprint.route('/embed/<blog_id>/overview')
def embed_overview(blog_id, api_host=None):
    ''' Show a theme with all the available themes in different iframes '''
    blog = get_resource_service('client_blogs').find_one(req=None, _id=blog_id)
    themes = get_resource_service('themes').get_local_themes_packages()
    blog['_id'] = str(blog['_id'])
    scope = {
        'blog': blog,
        'themes': [t[0] for t in themes]
    }
    return render_template('iframe-for-every-themes.html', **scope)


@embed_blueprint.app_template_filter('tojson')
def tojson(obj):
    return json.dumps(obj, cls=MongoJSONEncoder)


@embed_blueprint.app_template_filter('is_relative_to_current_folder')
def is_relative_to_current_folder_filter(s):
    return is_relative_to_current_folder(s)
