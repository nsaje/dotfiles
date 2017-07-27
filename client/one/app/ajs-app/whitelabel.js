/*exported overwrittes*/

var overwrittes = {
    greenpark: {
        chartColors: {
            TOTALS: ['#6594fa', '#c1d4fd'],
            GOALS: ['#99cc00', '#d6eb99'],
            DATA: [
                ['#41d4c4', '#b3eee7'],
                ['#182145', '#a3a6b5'],
                ['#fecb63', '#ffeac1'],
            ],
        },
    },
    adtechnacity: {
        chartColors: {
            TOTALS: ['#555f7b', '#bbbfca'],
            GOALS: ['#99cc00', '#d6eb99'],
            DATA: [
                ['#29aae3', '#a9ddf4'],
                ['#0aaf9f', '#9ddfd9'],
                ['#f15f74', '#f9bfc7'],
            ],
        },
    },
};

// [Workaround - Webpack] Make constants/options global
window.overwrittes = overwrittes;
