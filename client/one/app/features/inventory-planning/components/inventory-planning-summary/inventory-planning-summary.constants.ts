export const CHART_X_AXIS_STEP = 0.001;

export const CHART_CONFIG = {
    title: {
        text: <string> null,
    },
    xAxis: {
        title: {
            text: 'CPM',
        },
        tickInterval: 0.1,
        gridLineWidth: 1,
    },
    yAxis: {
        title: {
            text: '% Auctions Won',
        },
        min: 0,
        max: 100,
        gridLineWidth: 1,
    },
    plotOptions: {
        series: {
            animation: false,
            states: {
                hover: false,
            },
            marker: {
                states: {
                    hover: {
                        enabled: false,
                    },
                },
            },
        },
    },
    chart: {
        spacingBottom: 0,
        spacingLeft: 0,
    },
    legend: {
        enabled: false,
    },
    credits: {
        enabled: false,
    },
};
