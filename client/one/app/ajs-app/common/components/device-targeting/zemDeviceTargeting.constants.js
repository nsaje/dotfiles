angular.module('one.common').factory('zemDeviceTargetingConstants', function() {
    // eslint-disable-line max-len

    var VERSIONS_ANDROID = [
        {value: null, name: '-'},
        {value: 'ANDROID_2_1', name: '2.1 Eclair'},
        {value: 'ANDROID_2_2', name: '2.2 Froyo'},
        {value: 'ANDROID_2_3', name: '2.3 Gingerbread'},
        {value: 'ANDROID_3_0', name: '3.0 Honeycomb'},
        {value: 'ANDROID_3_1', name: '3.1 Honeycomb'},
        {value: 'ANDROID_3_2', name: '3.2 Honeycomb'},
        {value: 'ANDROID_4_0', name: '4.0 Ice Cream Sandwich'},
        {value: 'ANDROID_4_1', name: '4.1 Jelly Bean'},
        {value: 'ANDROID_4_2', name: '4.2 Jelly Bean'},
        {value: 'ANDROID_4_3', name: '4.3 Jelly Bean'},
        {value: 'ANDROID_4_4', name: '4.4 KitKat'},
        {value: 'ANDROID_5_0', name: '5.0 Lollipop'},
        {value: 'ANDROID_5_1', name: '5.1 Lollipop'},
        {value: 'ANDROID_6_0', name: '6.0 Marshmallow'},
        {value: 'ANDROID_7_0', name: '7.0 Nougat'},
        {value: 'ANDROID_7_1', name: '7.1 Nougat'},
        {value: 'ANDROID_8_0', name: '8.0 Oreo'},
        {value: 'ANDROID_8_1', name: '8.1 Oreo'},
        {value: 'ANDROID_9_0', name: '9.0 Pie'},
    ];

    var VERSIONS_IOS = [
        {value: 'IOS_3_2', name: '3.2'},
        {value: 'IOS_4_0', name: '4.0'},
        {value: 'IOS_4_1', name: '4.1'},
        {value: 'IOS_4_2', name: '4.2'},
        {value: 'IOS_4_3', name: '4.3'},
        {value: 'IOS_5_0', name: '5.0'},
        {value: 'IOS_5_1', name: '5.1'},
        {value: 'IOS_6_0', name: '6.0'},
        {value: 'IOS_6_1', name: '6.1'},
        {value: 'IOS_7_0', name: '7.0'},
        {value: 'IOS_7_1', name: '7.1'},
        {value: 'IOS_8_0', name: '8.0'},
        {value: 'IOS_8_1', name: '8.1'},
        {value: 'IOS_8_2', name: '8.2'},
        {value: 'IOS_8_3', name: '8.3'},
        {value: 'IOS_8_4', name: '8.4'},
        {value: 'IOS_9_0', name: '9.0'},
        {value: 'IOS_9_1', name: '9.1'},
        {value: 'IOS_9_2', name: '9.2'},
        {value: 'IOS_9_3', name: '9.3'},
        {value: 'IOS_10_0', name: '10.0'},
        {value: 'IOS_10_1', name: '10.1'},
        {value: 'IOS_10_2', name: '10.2'},
        {value: 'IOS_10_3', name: '10.3'},
        {value: 'IOS_11_0', name: '11.0'},
        {value: 'IOS_12_0', name: '12.0'},
        {value: 'IOS_12_1', name: '12.1'},
    ];

    var VERSIONS_OSX = [
        {value: 'MACOSX_10_4', name: '10.4 Tiger'},
        {value: 'MACOSX_10_5', name: '10.5 Leopard'},
        {value: 'MACOSX_10_6', name: '10.6 Snow Leopard'},
        {value: 'MACOSX_10_7', name: '10.7 Lion'},
        {value: 'MACOSX_10_8', name: '10.8 Mountain Lion'},
        {value: 'MACOSX_10_9', name: '10.9 Mavericks'},
        {value: 'MACOSX_10_10', name: '10.10 Yosemite'},
        {value: 'MACOSX_10_11', name: '10.11 El Capitan'},
        {value: 'MACOSX_10_12', name: '10.12 Sierra'},
        {value: 'MACOSX_10_13', name: '10.13 High Sierra'},
        {value: 'MACOSX_10_14', name: '10.14 Mojave'},
    ];

    var VERSIONS_WINDOWS = [
        {value: 'WINDOWS_98', name: '98'},
        {value: 'WINDOWS_2000', name: '2000'},
        {value: 'WINDOWS_XP', name: 'XP'},
        {value: 'WINDOWS_VISTA', name: 'Vista'},
        {value: 'WINDOWS_7', name: '7'},
        {value: 'WINDOWS_8', name: '8'},
        {value: 'WINDOWS_8_1', name: '8.1'},
        {value: 'WINDOWS_10', name: '10'},
    ];

    var VERSIONS_WINPHONE = [
        {value: 'WINPHONE_7', name: '7'},
        {value: 'WINPHONE_8_0', name: '8.0'},
        {value: 'WINPHONE_8_1', name: '8.1'},
        {value: 'WINPHONE_10', name: '10'},
    ];

    var DEVICE_TYPE = {
        DESKTOP: 'DESKTOP',
        TABLET: 'TABLET',
        MOBILE: 'MOBILE',
    };

    var DEVICES = [
        {name: 'Desktop', value: DEVICE_TYPE.DESKTOP},
        {name: 'Tablet', value: DEVICE_TYPE.TABLET},
        {name: 'Mobile', value: DEVICE_TYPE.MOBILE},
    ];

    var OPERATING_SYSTEMS = [
        {
            devices: [DEVICE_TYPE.DESKTOP],
            value: 'WINDOWS',
            name: 'Microsoft Windows',
            versions: VERSIONS_WINDOWS,
        },
        {
            devices: [DEVICE_TYPE.DESKTOP],
            value: 'MACOSX',
            name: 'Apple macOS',
            versions: VERSIONS_OSX,
        },
        {
            devices: [DEVICE_TYPE.DESKTOP],
            value: 'LINUX',
            name: 'Linux',
            versions: null,
        },
        {
            devices: [DEVICE_TYPE.MOBILE, DEVICE_TYPE.TABLET],
            value: 'IOS',
            name: 'Apple iOS',
            versions: VERSIONS_IOS,
        },
        {
            devices: [DEVICE_TYPE.MOBILE, DEVICE_TYPE.TABLET],
            value: 'ANDROID',
            name: 'Google Android',
            versions: VERSIONS_ANDROID,
        },
        {
            devices: [DEVICE_TYPE.MOBILE, DEVICE_TYPE.TABLET],
            value: 'WINPHONE',
            name: 'Windows Phone',
            versions: VERSIONS_WINPHONE,
        },
    ];

    var PLACEMENTS = [
        {
            value: 'SITE',
            name: 'Website',
            devices: [
                DEVICE_TYPE.DESKTOP,
                DEVICE_TYPE.MOBILE,
                DEVICE_TYPE.TABLET,
            ],
        },
        {
            value: 'APP',
            name: 'In-app',
            devices: [DEVICE_TYPE.MOBILE, DEVICE_TYPE.TABLET],
        },
    ];

    return {
        DEVICE_TYPE: DEVICE_TYPE,
        DEVICES: DEVICES,
        OPERATING_SYSTEMS: OPERATING_SYSTEMS,
        PLACEMENTS: PLACEMENTS,
    };
});
