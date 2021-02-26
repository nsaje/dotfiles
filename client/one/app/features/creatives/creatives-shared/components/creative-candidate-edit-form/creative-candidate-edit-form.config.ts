import {CreativeCandidate} from '../../../../../core/creatives/types/creative-candidate';
import {AdType} from '../../../../../app.constants';

interface FieldConfig {
    field: keyof CreativeCandidate;
    label?: string;
    placeholder?: string;
    maxLength?: number;
    shownForAdTypes: AdType[];
    template:
        | 'text'
        | 'text-title'
        | 'textarea'
        | 'textarea-adTag'
        | 'select-type'
        | 'select-size'
        | 'select-imageCrop'
        | 'select-callToAction'
        | 'tags'
        | 'trackers';
    bindLabel?: string;
    bindValue?: string;
    canUseAsDefault?: boolean;
}

const ALL_AD_TYPES: AdType[] = Object.values(AdType);

export const FIELDS_CONFIG: FieldConfig[] = [
    {
        field: 'url',
        label: 'URL',
        maxLength: 936,
        shownForAdTypes: ALL_AD_TYPES,
        template: 'text',
    },
    {
        field: 'title',
        maxLength: 90,
        shownForAdTypes: ALL_AD_TYPES,
        template: 'text-title',
    },
    {
        field: 'type',
        label: 'Ad Type',
        shownForAdTypes: [AdType.IMAGE, AdType.AD_TAG],
        template: 'select-type',
        bindLabel: 'name',
        bindValue: 'id',
    },
    /* TODO: Ad Size
    {
        field: 'size',
        label: 'Ad Size',
        shownForAdTypes: [AdType.AD_TAG],
        template: 'select-size',
    },*/
    {
        field: 'adTag',
        label: 'Ad Tag',
        placeholder: 'Paste your HTML or JS code here...',
        shownForAdTypes: [AdType.AD_TAG],
        template: 'textarea-adTag',
    },
    /* TODO: Image
    {
        field: 'image',
        label: 'Image',
        shownForAdTypes: [AdType.CONTENT, AdType.VIDEO, AdType.IMAGE],
    },
    {
        field: 'imageUrl',
        label: 'Image URL',
        shownForAdTypes: [AdType.CONTENT, AdType.VIDEO, AdType.IMAGE],
    },*/
    {
        field: 'imageCrop',
        label: 'Image crop',
        shownForAdTypes: [AdType.CONTENT, AdType.VIDEO],
        canUseAsDefault: true,
        template: 'select-imageCrop',
        bindLabel: 'name',
        bindValue: 'value',
    },
    /* TODO: Brand logo
    {
        field: 'icon',
        label: 'Brand logo',
        shownForAdTypes: [AdType.CONTENT, AdType.VIDEO],
    },
    {
        field: 'iconUrl',
        label: 'Brand logo URL',
        shownForAdTypes: [AdType.CONTENT, AdType.VIDEO],
    },*/
    /* TODO: Video
    {
        field: 'video',
        label: 'Video',
        shownForAdTypes: [AdType.VIDEO],
    },*/
    {
        field: 'description',
        label: 'Description',
        maxLength: 150,
        shownForAdTypes: [AdType.CONTENT, AdType.VIDEO],
        canUseAsDefault: true,
        template: 'textarea',
    },
    {
        field: 'displayUrl',
        label: 'Display URL',
        maxLength: 35,
        shownForAdTypes: ALL_AD_TYPES,
        template: 'text',
        canUseAsDefault: true,
    },
    {
        field: 'brandName',
        label: 'Brand name',
        maxLength: 25,
        shownForAdTypes: [AdType.CONTENT, AdType.VIDEO],
        template: 'text',
        canUseAsDefault: true,
    },
    {
        field: 'callToAction',
        label: 'Call to action',
        maxLength: 25,
        shownForAdTypes: [AdType.CONTENT, AdType.VIDEO],
        canUseAsDefault: true,
        template: 'select-callToAction',
        bindLabel: 'name',
        bindValue: 'value',
    },
    {
        field: 'tags',
        label: 'Tags',
        shownForAdTypes: ALL_AD_TYPES,
        template: 'tags',
    },
    {
        field: 'trackers',
        label: 'Trackers',
        shownForAdTypes: [AdType.CONTENT, AdType.VIDEO, AdType.IMAGE],
        template: 'trackers',
    },
];
