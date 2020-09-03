import {FormattedBrowser} from '../../types/formatted-browser';
import {BrowserFamily} from '../../../../app.constants';
import {DeviceType} from '../operating-system/types/device-type';

export const BROWSER_NAMES: {
    [key in BrowserFamily]: string;
} = {
    [BrowserFamily.CHROME]: 'Chrome',
    [BrowserFamily.SAFARI]: 'Safari',
    [BrowserFamily.FIREFOX]: 'Firefox',
    [BrowserFamily.IE]: 'Internet Explorer',
    [BrowserFamily.OPERA]: 'Opera',
    [BrowserFamily.EDGE]: 'Edge',
    [BrowserFamily.SAMSUNG]: 'Samsung',
    [BrowserFamily.ANDROID]: 'Android',
    [BrowserFamily.YANDEX]: 'Yandex',
    [BrowserFamily.DALVIK]: 'Dalvik',
    [BrowserFamily.IN_APP]: 'In app',
};

export const AVAILABLE_BROWSERS: FormattedBrowser[] = [
    {family: BrowserFamily.CHROME, name: BROWSER_NAMES[BrowserFamily.CHROME]},
    {family: BrowserFamily.SAFARI, name: BROWSER_NAMES[BrowserFamily.SAFARI]},
    {family: BrowserFamily.FIREFOX, name: BROWSER_NAMES[BrowserFamily.FIREFOX]},
    {family: BrowserFamily.IE, name: BROWSER_NAMES[BrowserFamily.IE]},
    {family: BrowserFamily.OPERA, name: BROWSER_NAMES[BrowserFamily.OPERA]},
    {family: BrowserFamily.EDGE, name: BROWSER_NAMES[BrowserFamily.EDGE]},
    {family: BrowserFamily.SAMSUNG, name: BROWSER_NAMES[BrowserFamily.SAMSUNG]},
    {family: BrowserFamily.ANDROID, name: BROWSER_NAMES[BrowserFamily.ANDROID]},
    {family: BrowserFamily.YANDEX, name: BROWSER_NAMES[BrowserFamily.YANDEX]},
    {family: BrowserFamily.DALVIK, name: BROWSER_NAMES[BrowserFamily.DALVIK]},
    {family: BrowserFamily.IN_APP, name: BROWSER_NAMES[BrowserFamily.IN_APP]},
];

export const BROWSER_DEVICE_MAPPING: {
    [key in BrowserFamily]: DeviceType[];
} = {
    [BrowserFamily.CHROME]: ['DESKTOP', 'TABLET', 'MOBILE'],
    [BrowserFamily.SAFARI]: ['DESKTOP', 'TABLET', 'MOBILE'],
    [BrowserFamily.FIREFOX]: ['DESKTOP', 'TABLET', 'MOBILE'],
    [BrowserFamily.IE]: ['DESKTOP'],
    [BrowserFamily.OPERA]: ['DESKTOP', 'TABLET', 'MOBILE'],
    [BrowserFamily.EDGE]: ['DESKTOP', 'TABLET', 'MOBILE'],
    [BrowserFamily.SAMSUNG]: ['TABLET', 'MOBILE'],
    [BrowserFamily.ANDROID]: ['TABLET', 'MOBILE'],
    [BrowserFamily.YANDEX]: ['DESKTOP', 'TABLET', 'MOBILE'],
    [BrowserFamily.DALVIK]: ['TABLET', 'MOBILE'],
    [BrowserFamily.IN_APP]: ['TABLET', 'MOBILE'],
};
