liveblogAnalyticsController.$inject = ['$scope', '$http', 'config', '$location', 'api', 'analytics', 'blog', 'notify'];

function liveblogAnalyticsController($scope, $http, config, $location, api, analytics, blog, notify) {
    const self = this;
    const close = function() { // Return to blog list page
        $location.path('/liveblog/edit/' + blog._id);
    };

    $scope.loadAnalytics = function(sortType, websiteUrl, page = 1, isDetail = false) {
        const q = {page: page, max_results: 500};

        if (websiteUrl) {
            localStorage.setItem('websiteUrl', websiteUrl);
        }
        if (!isDetail)
            localStorage.removeItem('websiteUrl');

        $http({
            url: config.server.url + '/blogs/' + blog._id + '/' + sortType + '/bloganalytics',
            method: 'GET',
            params: {q: q, websiteUrl: localStorage.getItem('websiteUrl')},
            headers: {
                'Content-Type': 'application/json;charset=utf-8',
            },
        })
            .then((response) => {
                if (response.data.length > 0) {
                    if (response.config.params.q.page === 1) {
                        $scope.analytics_data = response.data;
                    } else {
                        $scope.analytics_data.concat(response.data);
                    }
                } else {
                    $scope.analytics_data = [];
                }
            });
    };

    $scope.downloadCSV = function() { // Convert relevant item fields to CSV
        let fileContent = '';
        const filename = `liveblog_analytics_${blog._id}`;

        $scope.analytics_data.forEach((arr, index) => {
            const item = $scope.analytics_data[index];
            const filtered = [item.blog_id, item.context_url, item.website_url, item.hits];

            fileContent += filtered.join(',') + '\n';
        });

        const blob = new Blob([fileContent], {
            type: 'text/csv;charset=utf-8;',
        });

        if (navigator.msSaveBlob) { // IE 10+
            navigator.msSaveBlob(blob, filename);
            return; // early exit
        }

        const link = document.createElement('a');

        if (link.download === undefined) {
            return;
        } // detect HTML5 download attribute

        const url = URL.createObjectURL(blob);

        link.setAttribute('href', url);
        link.setAttribute('download', filename);
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
    };

    $scope.loadAnalytics('year', null); // load all, calls aren't expensive

    angular.extend(self, {
        blog: blog,
        close: close,
        tab: 'embeds',
        changeTab: function(tab) {
            self.tab = tab;
        },
    });
}

export default liveblogAnalyticsController;
