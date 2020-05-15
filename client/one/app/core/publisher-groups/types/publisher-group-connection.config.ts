import {PublisherGroupConnectionType} from './publisher-group-connection-type';

export const CONNECTION_TYPE_NAMES: {
    [key in PublisherGroupConnectionType]: string;
} = {
    agencyBlacklist: 'Blacklisted in agency',
    agencyWhitelist: 'Whitelisted in agency',
    accountBlacklist: 'Blacklisted in account',
    accountWhitelist: 'Whitelisted in account',
    campaignBlacklist: 'Blacklisted in campaign',
    campaignWhitelist: 'Whitelisted in campaign',
    adGroupBlacklist: 'Blacklisted in ad group',
    adGroupWhitelist: 'Whitelisted in ad group',
};
