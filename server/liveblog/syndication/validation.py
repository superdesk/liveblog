import urllib.parse
from flask import current_app as app
from superdesk.validator import SuperdeskValidator
from .utils import send_api_request, validate_secure_url
from .exceptions import APIConnectionError

# TODO: add validation for webhook url.


class SyndicationValidator(SuperdeskValidator):
    def _validate_httpsurl(self, httpsurl, field, value):
        if httpsurl:
            if not validate_secure_url(value):
                return self._error(field, "The provided url is not safe.")

            key_field = httpsurl.get('key_field')
            check_auth = httpsurl.get('check_auth')
            chech_auth_enabled = app.config.get('SYNDICATION_VALIDATE_AUTH', False)

            if check_auth and key_field:
                api_key = self.document.get(key_field)
                if not api_key:
                    return self._error(field, "Unable to find api_key for the given resource url.")

                if chech_auth_enabled:
                    api_url = urllib.parse.urljoin(value, 'syndication/blogs')
                    try:
                        response = send_api_request(api_url, api_key, json_loads=False, timeout=5)
                    except APIConnectionError:
                        return self._error(field, "Unable to connect to the the given url.")
                    if response.status_code != 200:
                        return self._error(field, "Unable to authenticate to the the given url.")
