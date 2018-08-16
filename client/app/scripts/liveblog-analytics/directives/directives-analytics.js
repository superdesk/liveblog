lbAnalyticsListCtrl.$inject = ['$scope', '$element'];

export default function lbAnalyticsListCtrl($scope, $element) {
    $scope.predicate = '';

    $scope.order = function(predicate) {
        $scope.reverse = $scope.predicate === predicate ? !$scope.reverse : false;
        $scope.predicate = predicate;
    };

    $scope.isReversePredicate = function(predicate) {
        return $scope.reverse && $scope.predicate === predicate;
    };


    $scope.setPage = function($index) {
        $scope.currentPage = $index;
    };
    $scope.flag = false;
    $scope.pageSize = 25;
    $scope.currentPage = 0;

    $scope.pages = new Array(Math.ceil($scope.analytics.length / $scope.pageSize));

    return null;
}
