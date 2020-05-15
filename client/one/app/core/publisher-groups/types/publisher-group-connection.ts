import {PublisherGroupConnectionType} from './publisher-group-connection-type';

export interface PublisherGroupConnection {
    id: number;
    name: string;
    location: PublisherGroupConnectionType;
}
