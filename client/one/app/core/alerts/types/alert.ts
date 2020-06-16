import {AlertType} from '../../../app.constants';

export interface Alert {
    type: AlertType;
    message: string;
    isClosable?: boolean;
}
