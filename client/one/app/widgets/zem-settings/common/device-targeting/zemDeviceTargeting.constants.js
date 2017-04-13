angular.module('one.widgets').factory('zemDeviceTargetingConstants', function () { // eslint-disable-line max-len

    var VERSIONS_ANDROID = [
        {value: null, name: '-'},
        {value: 'android_2_1', name: '2.1 Eclair'},
        {value: 'android_2_2', name: '2.2 Froyo'},
        {value: 'android_2_3', name: '2.3 Gingerbread'},
        {value: 'android_3_0', name: '3.0 Honeycomb'},
        {value: 'android_3_1', name: '3.1 Honeycomb'},
        {value: 'android_3_2', name: '3.2 Honeycomb'},
        {value: 'android_4_0', name: '4.0 Ice Cream Sandwich'},
        {value: 'android_4_1', name: '4.1 Jelly Bean'},
        {value: 'android_4_2', name: '4.2 Jelly Bean'},
        {value: 'android_4_3', name: '4.3 Jelly Bean'},
        {value: 'android_4_4', name: '4.4 KitKat'},
        {value: 'android_5_0', name: '5.0 Lollipop'},
        {value: 'android_5_1', name: '5.1 Lollipop'},
        {value: 'android_6_0', name: '6.0 Marshmallow'},
        {value: 'android_7_0', name: '7.0 Nougat'},
        {value: 'android_7_1', name: '7.1 Nougat'},
    ];

    var VERSIONS_IOS = [
        {value: 'ios_3_2', name: '3.2'},
        {value: 'ios_4_0', name: '4.0'},
        {value: 'ios_4_1', name: '4.1'},
        {value: 'ios_4_2', name: '4.2'},
        {value: 'ios_4_3', name: '4.3'},
        {value: 'ios_5_0', name: '5.0'},
        {value: 'ios_5_1', name: '5.1'},
        {value: 'ios_6_0', name: '6.0'},
        {value: 'ios_6_1', name: '6.1'},
        {value: 'ios_7_0', name: '7.0'},
        {value: 'ios_7_1', name: '7.1'},
        {value: 'ios_8_0', name: '8.0'},
        {value: 'ios_8_1', name: '8.1'},
        {value: 'ios_8_2', name: '8.2'},
        {value: 'ios_8_3', name: '8.3'},
        {value: 'ios_8_4', name: '8.4'},
        {value: 'ios_9_0', name: '9.0'},
        {value: 'ios_9_1', name: '9.1'},
        {value: 'ios_9_2', name: '9.2'},
        {value: 'ios_9_3', name: '9.3'},
        {value: 'ios_10_0', name: '10.0'},
        {value: 'ios_10_1', name: '10.1'},
        {value: 'ios_10_2', name: '10.2'},
        {value: 'ios_10_3', name: '10.3'},
    ];

    var VERSIONS_OSX = [
        {value: 'macosx_10_4', name: '10.4 Tiger'},
        {value: 'macosx_10_5', name: '10.5 Leopard'},
        {value: 'macosx_10_6', name: '10.6 Snow Leopard'},
        {value: 'macosx_10_7', name: '10.7 Lion'},
        {value: 'macosx_10_8', name: '10.8 Mountain Lion'},
        {value: 'macosx_10_9', name: '10.9 Mavericks'},
        {value: 'macosx_10_10', name: '10.10 Yosemite'},
        {value: 'macosx_10_11', name: '10.11 El Capitan'},
        {value: 'macosx_10_12', name: '10.12 Sierra'},
    ];

    var VERSIONS_WINDOWS = [
        {value: 'windows_98', name: '98'},
        {value: 'windows_2000', name: '2000'},
        {value: 'windows_xp', name: 'XP'},
        {value: 'windows_vista', name: 'Vista'},
        {value: 'windows_7', name: '7'},
        {value: 'windows_8', name: '8'},
        {value: 'windows_8_1', name: '8.1'},
        {value: 'windows_10', name: '10'},
    ];

    var VERSIONS_WINPHONE = [
        {value: 'winphone_7', name: '7'},
        {value: 'winphone_8_0', name: '8.0'},
        {value: 'winphone_8_1', name: '8.1'},
        {value: 'winphone_10', name: '10'},
    ];

    var deviceTargetingConstants = {};

    deviceTargetingConstants.DEVICES = [
        {name: 'Desktop', value: constants.adTargetDevice.DESKTOP},
        {name: 'Tablet', value: constants.adTargetDevice.TABLET},
        {name: 'Mobile', value: constants.adTargetDevice.MOBILE},
    ];

    deviceTargetingConstants.OPERATING_SYSTEMS = [
        {
            devices: [constants.adTargetDevice.DESKTOP],
            value: 'windows', name: 'Microsoft Windows',
            versions: VERSIONS_WINDOWS
        },
        {
            devices: [constants.adTargetDevice.DESKTOP],
            value: 'macosx', name: 'Apple macOS',
            versions: VERSIONS_OSX
        },
        {
            devices: [constants.adTargetDevice.DESKTOP],
            value: 'linux', name: 'Linux',
            versions: null,
        },
        {
            devices: [constants.adTargetDevice.MOBILE, constants.adTargetDevice.TABLET],
            value: 'ios', name: 'Apple iOS',
            versions: VERSIONS_IOS
        },
        {
            devices: [constants.adTargetDevice.MOBILE, constants.adTargetDevice.TABLET],
            value: 'android', name: 'Google Android',
            versions: VERSIONS_ANDROID
        },
        {
            devices: [constants.adTargetDevice.MOBILE, constants.adTargetDevice.TABLET],
            value: 'winphone', name: 'Microsoft Windows',
            versions: VERSIONS_WINPHONE
        },
    ];

    deviceTargetingConstants.PLACEMENTS = [
        {
            value: 'site',
            name: 'Website',
            devices: [
                constants.adTargetDevice.DESKTOP,
                constants.adTargetDevice.MOBILE,
                constants.adTargetDevice.TABLET
            ]
        },
        {
            value: 'app',
            name: 'In-app',
            devices: [
                constants.adTargetDevice.MOBILE,
                constants.adTargetDevice.TABLET
            ]
        },
    ];

    return deviceTargetingConstants;
});
