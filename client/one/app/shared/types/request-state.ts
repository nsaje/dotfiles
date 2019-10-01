export interface RequestState {
    inProgress?: boolean;
    error?: boolean;
    errorMessage?: string;
    count?: number;
    next?: string | null;
    previous?: string | null;
}
