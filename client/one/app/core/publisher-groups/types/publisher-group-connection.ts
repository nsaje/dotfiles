import {PublisherGroupConnectionLocation} from './publisher-group-connection-location';

export interface PublisherGroupConnection {
    id: number;
    name: string;
    location: PublisherGroupConnectionLocation;
}
