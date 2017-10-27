export const CHART_X_AXIS_STEP = 0.01;
export const MAX_PLOTTED_CPM = 30;

export const CHART_CONFIG = {
    title: {
        text: <string> null,
    },
    xAxis: {
        title: {
            text: 'CPM',
        },
        gridLineWidth: 1,
    },
    yAxis: {
        title: {
            text: '% Auctions Won',
        },
        min: 0,
        max: 100,
        tickInterval: 10,
        gridLineWidth: 1,
    },
    plotOptions: {
        series: {
            color: '#3f547f',
            animation: false,
            marker: {
                radius: 3,
                symbol: 'square',
                lineWidth: 2,
                fillColor: '#3f547f',
                lineColor: <string> null,
                states: {
                    hover: {
                        radius: 3,
                    },
                },
            },
            states: {
                hover: {
                    lineWidth: 2,
                },
            },
        },
    },
    tooltip: {
        shared: true,
        useHTML: true,
        shadow: false,
        headerFormat: '',
        pointFormat: 'CPM: <strong>${point.x}</strong><br>Auctions Won: <strong>{point.y}%</strong>', // tslint:disable-line no-invalid-template-strings max-line-length
        backgroundColor: '#fff',
        borderColor: '#d2d2d2',
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
