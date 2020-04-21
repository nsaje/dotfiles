import {PublisherBlacklistLevel} from '../../../app.constants';

export interface PublisherBlacklistActionLevel {
    name: string;
    level: PublisherBlacklistLevel;
    permissions?: string[];
}
