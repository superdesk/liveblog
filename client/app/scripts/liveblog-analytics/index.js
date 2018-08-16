import './styles/analytics.scss';

import analiticsListTpl from 'scripts/liveblog-analytics/views/view-list.ng1';

import liveblogAnalyticsController from './controllers/controller-analytics';
import lbAnalyticsListCtrl from './directives/directives-analytics';

export default angular
    .module('liveblog.analytics', ['liveblog.security'])
    .config(['apiProvider', function(apiProvider) {
        apiProvider
        /*
      * 'analytics' being one of the resources that we discovered
      * earlier by requesting http://localhost:5000/api -- endpoints are described with href, title pairs.
      * The apiProvider service then wraps around $http and inserts a blog_id via
      * .getById(<id>) into href before calling the endpoint. Heads up: apiProvider.query() does
      * not function like $resource.
      */

            .api('analytics', {
                type: 'http',
                backend: {rel: 'analytics'},
            });
    }])
    .controller('LiveblogAnalyticsController', liveblogAnalyticsController)

    .directive('lbAnalyticsList', () => ({
        restrict: 'E',
        scope: {
            analytics: '=',
            analyticsDetail: '&analyticsFn',
            downloadCSV: '&downloadcsvFn',
        },
        templateUrl: analiticsListTpl,
        controllerAs: 'analyticsList',
        controller: lbAnalyticsListCtrl,
        link: function(scope, element, attrs) {
            scope.$watch('analytics', (newValue, oldValue) => {
                if (newValue != oldValue) {
                    scope.setPage = function($index) {
                        scope.currentPage = $index;
                    };

                    scope.pageSize = 25;
                    scope.currentPage = 0;
                    scope.pages = new Array(Math.ceil(scope.analytics.length / scope.pageSize));
                }
            });

            scope.fetchAnalyticsDetail = function(sortType, websiteUrl, page, isDetail) {
                scope.flag = true;

                if (!isDetail)
                    scope.flag = false;

                scope.analyticsDetail({arg1: sortType, arg2: websiteUrl, arg3: page, arg4: isDetail});
            };
            scope.callDownloadCSV = function() {
                scope.downloadCSV();
            };
        },
    }))

    .filter('startFrom', () => function(input, start) {
        return input.slice(parseInt(start, 10));
    });
