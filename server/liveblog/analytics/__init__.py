import superdesk
from .analytics import AnalyticsResource, AnalyticsService


def init_app(app):
    # Analytics
    endpoint_name = 'analytics'
    service = AnalyticsService(endpoint_name, backend=superdesk.get_backend())
    AnalyticsResource(endpoint_name, app=app, service=service)


superdesk.privilege(name='analytics', label='Analytics Management', description='User can manage analytics')
