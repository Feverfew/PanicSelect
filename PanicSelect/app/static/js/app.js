'use strict';
angular.module("PanicSelect", ['ngRoute', 'ngResource', 'ngMaterial', 'ngMessages', 'ngMdIcons']);

angular.module('PanicSelect').config(['$routeProvider', '$locationProvider', '$mdThemingProvider',
        function ($routeProvider, $locationProvider, $mdThemingProvider) {
            $routeProvider
                .when('/', {
                    templateUrl: 'static/partials/landing-index.html',
                })
                .when('/about', {
                    templateUrl: 'static/partials/about.html',
                })
                .when('/donate', {
                    templateUrl: 'static/partials/donate.html',
                })
            $locationProvider.html5Mode({
                enabled: true,
                requireBase: false
            })
            $mdThemingProvider.theme('default')
                .primaryPalette('blue')
                .accentPalette('orange');
        }]);
    
angular.module('PanicSelect')
    .factory('Champion', function ($resource) {
        return $resource('/api/v1.0/ratings', {}, {
            query: {
                method: 'GET',
                isArray: false
            }
        });
    });

angular.module('PanicSelect')
    .factory('ChampionDetail', function ($resource) {
        return $resource('/api/v1.0/details/:champion/:role', { champion: '@champion', role: '@role'}, {
            query: {
                method: 'GET',
                isArray: false
            }
        });
    });

angular.module('PanicSelect')
    .controller('NavController', ['$scope', '$mdSidenav', function NavController($scope, $mdSidenav) {
        $scope.open = function () {
            $mdSidenav('sideNav').open()
        };
        $scope.close = function () {
            $mdSidenav('sideNav').close()
        };
    }]);

angular.module('PanicSelect')
    .controller('ChampionDetailController', ['$scope', '$mdDialog', function ChampionDetailController($scope, $mdDialog) {
        $scope.hide = function () {
            $mdDialog.hide();
        };
        $scope.cancel = function () {
            $mdDialog.cancel();
        };
        $scope.answer = function (answer) {
            $mdDialog.hide(answer);
        };
        $scope.answer = null;
    }]);

angular.module('PanicSelect')
    .controller('ChampionOverviewController',['$scope', 'Champion',
    'ChampionDetail', '$mdDialog', '$mdMedia', '$q', '$timeout', 
    '$mdToast', function ($scope, Champion, ChampionDetail, $mdDialog, $mdMedia,
     $q, $timeout, $mdToast) {
        var self = this;
        self.simulateQuery = false;
        // list of `champion` value/display objects
        self.champion_list = loadAll();
        self.querySearch = querySearch;
        // ******************************
        // Internal methods
        // ******************************
        /**
         * Search for states... use $timeout to simulate
         * remote dataservice call.
         */
        function querySearch(query) {
            var results = query ? self.champion_list.filter(createFilterFor(query)) : self.champion_list, deferred;
            if (self.simulateQuery) {
                deferred = $q.defer();
                $timeout(function () { deferred.resolve(results); }, Math.random() * 1000, false);
                return deferred.promise;
            } else {
                return results;
            }
        }
        /**
         * Build `states` list of key/value pairs
         */
        function loadAll() {
            var champion_list = "Aatrox, Ahri, Akali, Alistar, Amumu, Anivia, Annie, Ashe, Azir, Bard, Blitzcrank, Brand, Braum, Caitlyn, Cassiopeia, Cho'Gath, Corki, Darius, diana, Dr. Mundo, Draven, Ekko, Elise, Evelynn, Ezreal, Fiddlesticks, Fiora, Fizz, Galio, Gangplank, Garen, Gnar, Gragas, Graves, Hecarim, Heimerdinger, Illaoi, Irelia, Janna Jarvan IV, Jax, Jayce, Jinx, Kalista, Karma, Karthus, Kassadin, Katarina, Kayle, Kennen, Kha'Zix, Kindred, Kog'Maw, LeBlanc, Lee Sin, Leona, Lissandra, Lucian, Lulu, Lux, Malphite, Malzahar, Maokai, Master Yi, Miss Fortune, Mordekaiser, Morgana, Nami, Nasus, Nautilus, Nidalee, Nocturne, Nunu, Olaf, Orianna, Pantheon, Poppy, Quinn, Rammus, Rek'Sai, Renekton, Rengar, Riven, Rumble, Ryze, Sejuani, Shaco, Shen, Shyvana, Singed, Sion, Sivir, Skarner, Sona, Soraka, Swain, Syndra, Tahm Kench, Taliyah, Talon, Taric, Teemo, Thresh, Tristana, Trundle, Tryndamere, Twisted Fate, Twitch, Udyr, Urgot, Varus, Vayne, Veigar, Vel'Koz, Vi, Viktor, Vladimir, Volibear, Warwick, Wukong, Xerath, Xin Zhao, Yasuo, Yorick, Zac, Zed, Ziggs, Zilean, Zyra";
            return champion_list.split(/, +/g).map(function (champion_list) {
                return {
                    value: champion_list.toLowerCase(),
                    display: champion_list
                };
            });
        }
        /**
         * Create filter function for a query string
         */
        function createFilterFor(query) {
            var lowercaseQuery = angular.lowercase(query);
            return function filterFn(champion_list) {
                return (champion_list.value.indexOf(lowercaseQuery) === 0);
            };
        }
        $scope.champions = null;
        $scope.customFullscreen = $mdMedia('xs') || $mdMedia('sm');
        $scope.isLoading = false;
        $scope.searchChampions = function () {
            $scope.isLoading = true;
            var matchup;
            if ($scope.matchup != null){
                matchup = $scope.matchup.value.replace(/ /g, '');
                matchup = matchup.replace(/'/g, '');
            }
            
            var query = Champion.query({ summoner: $scope.summoner, region: $scope.region, role: $scope.role, matchup: matchup}, 
                function (champions) {
                    $scope.isLoading = false;
                    $scope.errorsExist = false;
                    $scope.champions = champions.champions;
                }, function (champions) {
                    if (champions.status != 200) {
                        $scope.isLoading = false;
                        $scope.errorsExist = true;
                        $scope.champions = null;
                        $scope.errorMessages = champions.data.message;
                    }
                }
            );
            $scope.$apply;
        }
        $scope.showChampionDetailsDialog = function (champ, ev) {
            $scope.champ = champ;
            $mdDialog.show({
                controller: 'ChampionDetailController',
                templateUrl: 'static/partials/champion-detail.html',
                parent: angular.element(document.body),
                scope: $scope,
                preserveScope: true,
                targetEvent: ev,
                clickOutsideToClose: true
                
            }); 
            var details = ChampionDetail.get({ champion: champ.key, role: $scope.role }, function (details) {
                $scope.details = details;
                console.log(details.key);
            });
        };
    }]);
