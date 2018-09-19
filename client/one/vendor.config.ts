import * as highcharts from 'highcharts';

(<any>window).Highcharts = highcharts;
(<any>window).Highcharts.setOptions({
    lang: {
        decimalPoint: '.',
        thousandsSep: ',',
    },
});
