import {Subscription} from 'rxjs/Subscription';

export interface Request {
    subscription?: Subscription;
    inProgress?: boolean;
    success?: boolean;
    error?: boolean;
    successMessage?: string;
    errorMessage?: string;
}
