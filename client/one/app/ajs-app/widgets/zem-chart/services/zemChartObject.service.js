angular.module('one.widgets').service('zemChartObject', function() {
    function Chart() {
        this.hasData = true;
        this.metrics = {
            options: [],
            metaData: null,
        };
        this.legend = {
            usedColors: [],
            items: [],
        };
        this.config = createHighChartDefaults();

        this.clearData = function() {
            this.hasData = false;
            this.legend.items = [];
            this.config.series = [];
        };
    }

    function createHighChartDefaults() {
        return {
            chart: {},
            title: {
                text: null,
            },
            xAxis: {
                type: 'datetime',
                minTickInterval: 24 * 3600 * 1000,
            },
            yAxis: [
                {
                    title: {
                        text: null,
                    },
                    min: 0,
                    gridLineWidth: 1,
                },
                {
                    title: {
                        text: null,
                    },
                    min: 0,
                    gridLineWidth: 0,
                    opposite: true,
                },
            ],
            tooltip: {
                shared: true,
                useHTML: true,
                headerFormat: '<div class="tooltip-header">{point.key}</div>',
                backgroundColor: '#fff',
                borderColor: '#d2d2d2',
                shadow: false,
            },
            plotOptions: {
                series: {
                    animation: false,
                    marker: {
                        states: {
                            hover: {
                                radius: 3,
                            },
                        },
                    },
                },
            },
            legend: {
                enabled: false,
            },
            credits: {
                enabled: false,
            },
        };
    }

    function createChart() {
        return new Chart();
    }

    return {
        createChart: createChart,
    };
});
