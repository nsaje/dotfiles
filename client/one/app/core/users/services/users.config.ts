import {APP_CONFIG} from '../../../app.config';

const usersApiUrl = `${APP_CONFIG.apiRestInternalUrl}/users`;

export const USERS_CONFIG = {
    requests: {
        users: {
            list: {
                name: 'list',
                url: `${usersApiUrl}/`,
            },
            create: {
                name: 'create',
                url: `${usersApiUrl}/`,
            },
            get: {
                name: 'get',
                url: `${usersApiUrl}/{userId}`,
            },
            edit: {
                name: 'edit',
                url: `${usersApiUrl}/{userId}`,
            },
            remove: {
                name: 'remove',
                url: `${usersApiUrl}/{userId}`,
            },
            validate: {
                name: 'validate',
                url: `${usersApiUrl}/validate/`,
            },
            resendEmail: {
                name: 'resendEmail',
                url: `${usersApiUrl}/{userId}/resendemail/`,
            },
        },
    },
};
