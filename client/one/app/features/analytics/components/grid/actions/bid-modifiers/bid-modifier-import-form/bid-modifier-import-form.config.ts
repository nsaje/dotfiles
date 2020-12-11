import {Breakdown} from '../../../../../../../app.constants';
import {
    TARGETING_DEVICE_OPTIONS,
    TARGETING_ENVIRONMENT_OPTIONS,
} from '../../../../../../entity-manager/entity-manager.config';

const CSV_INFO_TEXT_PUBLISHER = `
    First column in the CSV file contains the publisher name and
    the second column contains the media source name as reported
    in the dashboard. For the media source name please refer to
    source slug column. The third column contains the bid
    modifier. The first row in the CSV file is ignored.
`;

const CSV_INFO_TEXT_PLACEMENT = `
    First column in the CSV file contains the placement identifier
    and the second column contains the media source name as
    reported in the dashboard. For the placement identifier please
    refer to placement id column and for the media source name
    please refer to source slug column. The third column contains
    the bid modifier. The first row in the CSV file is ignored.
`;

const CSV_INFO_TEXT_MEDIA_SOURCE = `
    First column in the CSV file contains the media source name
    as reported in the dashboard. For the media source name
    please refer to source slug column. The second column
    contains the bid modifier. The first row in the CSV file is
    ignored.
`;

const CSV_INFO_TEXT_GENERAL = `
    First column in the CSV file contains the {dimension} and
    the second column the bid modifier. The first row in the CSV
    file is ignored.
`;

const BID_VALUES_INFO_TEXT_GENERAL = `
    Bid modifier values should range from 0 up. The resulting {dimension}
    bid is obtained by multiplying existing {target} bid with
    the number from the imported CSV file.
`;

const COUNTRY_CODE_TEXT = `
    For a list of valid country codes please refer to
    <a
        href="https://en.wikipedia.org/wiki/List_of_ISO_3166_country_codes"
        target="_blank"
        >this page</a
    >
    (Alpha 2-code)
`;

const SPECIFIER_OPTIONS_TEXT_GENERAL = `Valid {dimension} are: {options}.`;

export const IMPORT_INSTRUCTIONS: {
    [key in string]: string[];
} = {
    [Breakdown.PUBLISHER]: [
        CSV_INFO_TEXT_PUBLISHER,
        BID_VALUES_INFO_TEXT_GENERAL.replace(
            '{dimension}',
            'publisher'
        ).replace('{target}', 'publisher'),
    ],
    [Breakdown.PLACEMENT]: [
        CSV_INFO_TEXT_PLACEMENT,
        BID_VALUES_INFO_TEXT_GENERAL.replace(
            '{dimension}',
            'placement'
        ).replace('{target}', 'placement'),
    ],
    [Breakdown.MEDIA_SOURCE]: [
        CSV_INFO_TEXT_MEDIA_SOURCE,
        BID_VALUES_INFO_TEXT_GENERAL.replace(
            '{dimension}',
            'media source'
        ).replace('{target}', 'ad group'),
    ],
    [Breakdown.CONTENT_AD]: [
        CSV_INFO_TEXT_GENERAL.replace('{dimension}', 'content ad id'),
        BID_VALUES_INFO_TEXT_GENERAL.replace('{dimension}', 'ad').replace(
            '{target}',
            'ad group'
        ),
    ],
    [Breakdown.COUNTRY]: [
        CSV_INFO_TEXT_GENERAL.replace('{dimension}', 'country code'),
        COUNTRY_CODE_TEXT,
        BID_VALUES_INFO_TEXT_GENERAL.replace('{dimension}', 'country').replace(
            '{target}',
            'ad group'
        ),
    ],
    [Breakdown.STATE]: [
        CSV_INFO_TEXT_GENERAL.replace('{dimension}', 'state code'),
        BID_VALUES_INFO_TEXT_GENERAL.replace('{dimension}', 'state').replace(
            '{target}',
            'ad group'
        ),
    ],
    [Breakdown.DMA]: [
        CSV_INFO_TEXT_GENERAL.replace('{dimension}', 'DMA code'),
        BID_VALUES_INFO_TEXT_GENERAL.replace('{dimension}', 'DMA').replace(
            '{target}',
            'ad group'
        ),
    ],
    [Breakdown.DEVICE]: [
        CSV_INFO_TEXT_GENERAL.replace('{dimension}', 'device specifier'),
        SPECIFIER_OPTIONS_TEXT_GENERAL.replace(
            '{dimension}',
            'device specifier'
        ).replace(
            '{options}',
            TARGETING_DEVICE_OPTIONS.map(option => option.value).join(', ')
        ),
        BID_VALUES_INFO_TEXT_GENERAL.replace('{dimension}', 'device').replace(
            '{target}',
            'ad group'
        ),
    ],
    [Breakdown.ENVIRONMENT]: [
        CSV_INFO_TEXT_GENERAL.replace('{dimension}', 'environment specifier'),
        SPECIFIER_OPTIONS_TEXT_GENERAL.replace(
            '{dimension}',
            'environment specifier'
        ).replace(
            '{options}',
            TARGETING_ENVIRONMENT_OPTIONS.map(option => option.value).join(', ')
        ),
        BID_VALUES_INFO_TEXT_GENERAL.replace(
            '{dimension}',
            'environment'
        ).replace('{target}', 'ad group'),
    ],
    [Breakdown.OPERATING_SYSTEM]: [
        CSV_INFO_TEXT_GENERAL.replace(
            '{dimension}',
            'operating system specifier'
        ),
        BID_VALUES_INFO_TEXT_GENERAL.replace(
            '{dimension}',
            'operating system'
        ).replace('{target}', 'ad group'),
    ],
    [Breakdown.BROWSER]: [
        CSV_INFO_TEXT_GENERAL.replace('{dimension}', 'browser specifier'),
        BID_VALUES_INFO_TEXT_GENERAL.replace('{dimension}', 'browser').replace(
            '{target}',
            'ad group'
        ),
    ],
    [Breakdown.CONNECTION_TYPE]: [
        CSV_INFO_TEXT_GENERAL.replace(
            '{dimension}',
            'connection type specifier'
        ),
        BID_VALUES_INFO_TEXT_GENERAL.replace(
            '{dimension}',
            'connection type'
        ).replace('{target}', 'ad group'),
    ],
};
